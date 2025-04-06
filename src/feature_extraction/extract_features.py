import os, sys
import json
import math
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm import SYSTEM_PROMPT, ClientFeatures, make_user_prompt
from cpi import extract_cpi_scores_2023
from exchange_rates import get_current_exchange_rates


def load_and_format_client_json(json_path: Path) -> Dict[str, Any]:
    """Loads a JSON file, removes the label, and formats it into readable text."""
    with open(json_path, "r", encoding="utf-8") as f:
        client_data = json.load(f)
    return client_data


def extract_features_from_client_json(client_json: Dict[str, Any]) -> Dict[str, Any]:
    """Sends client text to OpenAI and returns extracted features as a dict."""
    # Load API key and initialize client
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    #client_text = json.dumps(client_json, ensure_ascii=False)

    try:
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": make_user_prompt(client_json)}
            ],
            response_format=ClientFeatures,
        )

        # Extract content
        message = response.choices[0].message.content

        try:
            return json.loads(message)
        except json.JSONDecodeError:
            print("⚠️ Warning: OpenAI response is not valid JSON. Returning raw string.")
            return {"raw_response": message}

    except Exception as e:
        print("❌ Error during ChatCompletion API call:")
        return {"error": str(e)}


def append_asset_values(features: Dict[str, Any], client_json: Dict[str, Any], exchange_rates: Dict[str, float]) -> None:
    """Extracts and log-scales EUR-converted asset values: savings, inheritance, real estate."""
    currency = client_json.get("client_profile", {}).get("currency", "EUR")
    rate = exchange_rates.get(currency, 1.0)

    aum = client_json.get("client_profile", {}).get("aum", {})
    
    savings = aum.get("savings", 0) * rate
    inheritance = aum.get("inheritance", 0) * rate
    real_estate = aum.get("real_estate_value", 0) * rate

    features["log_savings_eur"] = math.log1p(savings)
    features["log_inheritance_eur"] = math.log1p(inheritance)
    features["log_real_estate_value_eur"] = math.log1p(real_estate)


def append_salary_stats(features: Dict[str, Any], client_json: Dict[str, Any], exchange_rates: Dict[str, float]) -> None:
    """Extracts salary stats and log-scales totals/averages in EUR."""
    currency = client_json.get("client_profile", {}).get("currency", "EUR")
    rate = exchange_rates.get(currency, 1.0)

    employment = client_json.get("client_profile", {}).get("employment_history", [])
    salaries = []
    total_salary = 0
    tenures = []

    for job in employment:
        start = job.get("start_year")
        end = job.get("end_year")
        salary = job.get("salary", 0) * rate
        if start and end:
            years = end - start + 1
            total_salary += salary * years
            salaries.append(salary)
            tenures.append(years)

    average_salary = sum(salaries) / len(salaries) if salaries else 0

    features["log_last_yearly_salary_eur"] = math.log1p(salaries[-1]) if salaries else 0
    features["log_average_yearly_salary_eur"] = math.log1p(average_salary)
    features["log_total_salary_eur"] = math.log1p(total_salary)
    features["total_years_worked"] = sum(tenures)
    features["average_tenure"] = sum(tenures) / len(tenures) if tenures else 0


def append_age(features: Dict[str, Any], client_json: Dict[str, Any]) -> None:
    """Calculates and appends current age."""
    birth_date_str = client_json.get("client_profile", {}).get("birth_date")
    if birth_date_str:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        features["age"] = age

def append_cpi_scores(features: Dict[str, Any], client_json: Dict[str, Any]) -> None:
    """
    Appends the Corruption Perceptions Index (CPI) scores for the client's passport country
    and country of domicile to the features dictionary.
    """
    # Retrieve the CPI scores dictionary
    cpi_scores = extract_cpi_scores_2023(Path(__file__).resolve().parent / "./TI-CPI.csv")

    # Extract the passport country and country of domicile from the client data
    passport_country = client_json.get("passport", {}).get("country", "").strip()
    domicile_country = client_json.get("client_profile", {}).get("country_of_domicile", "").strip()

    # Function to determine risk category based on CPI score
    def get_risk_category(cpi_score):
        if cpi_score is None:
            return 1  # Default to neutral if CPI score is not available
        elif cpi_score >= 50:
            return 0  # Low risk
        elif 30 <= cpi_score < 50:
            return 1  # Neutral
        else:
            return 2  # High risk

    # Assign risk categories
    features["passport_country_risk"] = get_risk_category(cpi_scores.get(passport_country))
    features["domicile_country_risk"] = get_risk_category(cpi_scores.get(domicile_country))


def append_one_hot_investment_profile(features: Dict[str, Any], client_json: Dict[str, Any]) -> None:
    """
    One-hot encodes investment profile attributes and appends them to the features dictionary.
    """
    profile = client_json.get("client_profile", {})

    # Sensible orderings
    risk_levels = ['Conservative', 'Low', 'Moderate', 'Balanced', 'Considerable', 'High', 'Aggressive']
    experience_levels = ['Inexperienced', 'Experienced', 'Expert']
    mandate_types = ['Execution-Only', 'Advisory', 'Hybrid', 'Discretionary']

    # Get values
    risk_profile = profile.get("investment_risk_profile")
    experience = profile.get("investment_experience")
    mandate = profile.get("type_of_mandate")

    # One-hot encode each category
    for level in risk_levels:
        features[f"risk_profile_{level.lower()}"] = 1 if risk_profile == level else 0

    for level in experience_levels:
        features[f"investment_experience_{level.lower()}"] = 1 if experience == level else 0

    for level in mandate_types:
        key = f"type_of_mandate_{level.lower().replace('-', '_')}"
        features[key] = 1 if mandate == level else 0


def transform_median_salary(features: Dict[str, Any], client_json: Dict[str, Any], exchange_rates: Dict[str, float]) -> None:
    currency = client_json.get("client_profile", {}).get("currency", "EUR")
    rate = exchange_rates.get(currency, 1.0)

    median_salary = features.get("median_salary", 0)
    median_salary_eur = median_salary * rate

    features.pop("median_salary", None)
    features["log_median_salary_eur"] = math.log1p(median_salary_eur)


def append_textual_features(features: Dict[str, Any], client_json: Dict[str, Any]) -> None:
    # Nationality from passport
    passport_data = client_json.get("passport", {})
    features["nationality"] = passport_data.get("nationality", "")
    
    # Preferred markets from client_profile
    preferred_markets = client_json.get("client_profile", {}).get("preferred_markets", [])
    features["preferred_markets"] = preferred_markets
    
    # Latest position: if any job has end_year = None, assume it's currently held and pick that one
    employment_history = client_json.get("client_profile", {}).get("employment_history", [])
    latest_job = None

    if employment_history:
        # Prefer job with end_year = None (currently held)
        current_jobs = [job for job in employment_history if job.get("end_year") is None]
        if current_jobs:
            latest_job = current_jobs[0]  # assume first is fine if multiple current
        else:
            # fallback: choose job with highest end_year
            latest_job = max(employment_history, key=lambda job: job.get("end_year") or 0)
        
        features["position"] = latest_job.get("position", "")
    else:
        features["position"] = ""


def save_json_to_file(data: dict, output_path: Path) -> None:
    """Saves a dictionary as a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def process_client_file(json_file: Path, exchange_rates: Dict[str, float], output_dir: Path):
    try:
        output_filename = f"features_{json_file.name}"
        output_path = output_dir / output_filename
        if output_path.exists():
            return f"Already exists: {output_path}"

        client_json = load_and_format_client_json(json_file)
        label = client_json.get("label", {})
        permitted = client_json.get("internal_score", {}).get("preprocessing", False)
        if not permitted:
            return f"Skipping {output_path}: filtered by preprocessing"

        features = extract_features_from_client_json(client_json)

        # Check for invalid results
        if "error" in features:
            return f"Error in LLM extraction for {json_file.name}: {features['error']}"

        if "raw_response" in features:
            return f"Unexpected raw response in {json_file.name}:\n{features['raw_response']}"

        # Append all derived features
        append_asset_values(features, client_json, exchange_rates)
        append_salary_stats(features, client_json, exchange_rates)
        transform_median_salary(features, client_json, exchange_rates)
        append_age(features, client_json)
        append_cpi_scores(features, client_json)
        append_one_hot_investment_profile(features, client_json)
        append_textual_features(features, client_json)

        # Wrap in final structure with label
        final_output = {
            "features": features,
            "label": label  # get label or empty dict if missing
        }

        # Output path: features_client_X.json
        save_json_to_file(final_output, output_path)
        return str(output_path)
    except Exception as e:
        return f"Failed to process {json_file.name}: {e}"


if __name__ == "__main__":
    input_dir = Path(__file__).resolve().parent.parent / "preprocessing" / "all_clients"
    output_dir = Path(__file__).resolve().parent / "extracted_features"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Centralize exchange rates
    exchange_rates = get_current_exchange_rates()
    client_files = list(input_dir.glob("client_*.json"))
    parallel = True

    if not parallel:
        result = process_client_file(client_files[0], exchange_rates, output_dir)
        print(result)
        sys.exit(1)

    with ThreadPoolExecutor(max_workers=6) as executor:  # Tune number based on your API rate limit
        futures = [executor.submit(process_client_file, path, exchange_rates, output_dir) for path in client_files]
        try:
            for future in as_completed(futures):
                result = future.result()
                if result:
                    print(f"Processed: {result}")
        except KeyboardInterrupt:
            print("\nInterrupted by user. Shutting down...")
            executor.shutdown(cancel_futures=True)
            sys.exit(1)