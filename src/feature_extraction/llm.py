from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path
import json

def load_and_format_client_json(json_path: Path) -> Dict[str, Any]:
    """Loads a JSON file, removes the label, and formats it into readable text."""
    with open(json_path, "r", encoding="utf-8") as f:
        client_data = json.load(f)
    return client_data

SYSTEM_PROMPT = '''You will be acting as a part of a pipeline meant to automate the client onboarding and selection process for a private bank. Your goal is to create a structured JSON of features that you extract from the data and textual description of clients.

You should adhere to the specifications given to you rigorously.

Only reply in JSON format and only fill out the fields described in the schema. Do not add any additional fields. Do NOT format your reply as a Markdown code block (three backticks); only output in plain text format. Comments in your JSON code should be avoided at all cost.'''

def make_user_prompt(client_json: Dict[str, Any]) -> str:
    higher_education = client_json.get("client_profile", {}).get("higher_education", {})
    employment = client_json.get("client_profile", {}).get("employment_history", [])
    inheritance = client_json.get("client_profile", {}).get("inheritance_details", {})
    description = client_json.get("client_description", {})
    birthdate = client_json.get("passport", {}).get("birth_date", "")
    currency = client_json.get("client_profile", {}).get("currency", "")

    return f'''
This is the structured and unstructured data of a client. Use it to extract the following fields and fill out the JSON accordingly.

---
{higher_education}
This is the higher education history of the client. Use it to fill out the one-hot encoded `degree_bachelor`, `degree_other`, `degree_master`, `degree_phd`, and `degree_postdoc` fields of the JSON. 
If a degree is obtained, set it to 1, otherwise 0. If only one degree is listed, you may assume it is a Bachelor's degree. If `higher_education` is empty, set all to 0.
This is also used to determine the `max_degree_prestige`, which ranges from 1 to 5. Score the most prestigious university the client attended, from 1 (not known at all) to 5 (Oxbridge, Ivy Leagues). If no university is listed, set to 0.
Use the graduation year(s) in the higher education list together with the client's birth date ({birthdate}) to evaluate `consistency_education`. If the client's age at graduation (graduation year - birth year) is between 20 and 35, set `consistency_education` to True. If it is outside that range or inconsistent (e.g., future graduation or extreme mismatch), set it to False.

---
{employment}
Use this list to:
- Compute the `seniority` score: choose the highest-ranking role based on the scale Junior=1, Senior=2, Manager=3, Director=4, C-level=5, Chairman=6.
- Evaluate `employment_progress`: set to True if job responsibilities and salaries generally increase over time; otherwise False.
Use this section also to compute:
- `consistency_employment`: check whether start and end years of employment make sense with respect to the client's age (born {birthdate}) and follow a logical, believable sequence. Large gaps (e.g., >3 years unexplained), jobs extending unrealistically far into the future, or implausibly high salaries for junior roles (e.g. >100k for entry-level positions) should lead to `consistency_employment: False`.
Otherwise, set to True.
- `median_salary`: set to a rough estimate of the median salary (in client currency of {currency}) for the *most recent* position (based on title and general knowledge), even if the reported salary differs. If the client has no employment history, set this to 0.

---
{inheritance}
This describes the person from whom the client received inheritance. Use their profession to determine their `testator_seniority`, using the same scale as for the client's own seniority: Junior=1, Senior=2, Manager=3, Director=4, C-level=5, Chairman=6. If no testator is given or it cannot be mapped, set to 0.

---
{description}
This section and the employment history should be used to determine the following fields:

- `founded_company`: Set to True only if the client founded a company or entrepreneurial venture is explicitly mentioned. Otherwise, set to False.
- `company_sold`: Only if there is mention of companies being sold by the client, set to the numerical value of the total price that the companies got sold for. Otherwise, set to 0.
- `marital_status_single`, `marital_status_married`, `marital_status_divorced`, `marital_status_widowed`: Determine the one-hot marital status encoding *only* if it is clearly stated in the client description. If not stated, set all to 0.
- `num_children`: Set to the number of children explicitly mentioned. If it is stated that the client has no children, set to 0.

'''

class ClientFeatures(BaseModel):
    degree_bachelor: int
    degree_other: int
    degree_master: int
    degree_phd: int
    degree_postdoc: int
    max_degree_prestige: int
    seniority: int
    testator_seniority: int
    employment_progress: bool
    founded_company: bool
    company_sold: int
    marital_status_single: int
    marital_status_married: int
    marital_status_divorced: int
    marital_status_widowed: int
    num_children: int
    consistency_education: bool
    consistency_employment: bool
    median_salary: int

if __name__ == "__main__":
    client_json = load_and_format_client_json("C:\\Users\\nemes\\Code\\Apps\\datathon2025\\preprocessing\\all_clients\\client_4.json")
    print(make_user_prompt(client_json))