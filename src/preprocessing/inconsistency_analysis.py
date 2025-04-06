import os
import json
import re
from datetime import datetime
import pycountry
from countryinfo import CountryInfo
from functools import lru_cache
import country_conversion_helper

def static_analysis(client_data, path):
    """
    Performs static analysis on a client_data object to check for inconsistencies.

    Args:
        client_data (dict): The client data object.

    Returns:
        dict: The modified client data object with an "internal_score" field.
    """
    inconsistencies = []

    # Helper functions
    def is_valid_date(date_str, date_format="%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            return None

    def is_email_valid(email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def is_phone_number_valid(phone):
        return phone.replace("+", "").replace(" ", "").isdigit()

    # Intra-document checks
    passport = client_data.get("passport", {})
    client_profile = client_data.get("client_profile", {})
    account_form = client_data.get("account_form", {})

    # Passport checks
    birth_date = passport.get("birth_date")
    issue_date = passport.get("passport_issue_date")
    expiry_date = passport.get("passport_expiry_date")
    mrz = passport.get("passport_mrz", [])
    passport_number = passport.get("passport_number")
    country = passport.get("country")
    country_code = passport.get("country_code")
    nationality = passport.get("nationality")

    if birth_date:
        birth_date_obj = is_valid_date(birth_date)
        #TODO: 18 * 365 is not correct
        reference_date = datetime(2025, 4, 1, 0, 0)
        if not birth_date_obj or birth_date_obj >= reference_date:
            inconsistencies.append("Invalid or inconsistent birth date in passport.")
        else:
            # Calculate the exact age considering leap years
            age_days = (reference_date - birth_date_obj).days
            leap_days = sum(1 for year in range(birth_date_obj.year, reference_date.year + 1)
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0))
            exact_age_years = (age_days - leap_days) / 365
            if exact_age_years < 18:
                inconsistencies.append("Client is under 18 years old based on birth date.")


    if issue_date and expiry_date:
        issue_date_obj = is_valid_date(issue_date)
        expiry_date_obj = is_valid_date(expiry_date)
        if not issue_date_obj or not expiry_date_obj or issue_date_obj >= expiry_date_obj:
            inconsistencies.append("Passport issue date is not before expiry date.")
        if expiry_date_obj <= datetime.now():
            inconsistencies.append("Passport expiry date is not in the future.")
        if issue_date_obj >= datetime.now():
            inconsistencies.append("Passport issue date is in the future.")

    if mrz and len(mrz) == 2:
        #TODO: Add MRZ consistency checks and checksum validation logic here
        pass

    if not passport_number or not re.match(r"^[A-Z0-9]+$", passport_number):

        inconsistencies.append("Invalid passport number format.")

    if country and country_code and nationality:
        # Use the pycountry library to validate country and country code mapping
        country_obj = pycountry.countries.get(alpha_3=country_code) or pycountry.countries.get(alpha_2=country_code)
        if country_obj:
            if country.lower() != country_obj.name.lower():
                inconsistencies.append(f"Country code does not match the country. Expected: {country_obj.name.lower()}, Provided: {country.lower()}.")
            
            expected_nationality = country_conversion_helper.get_nationality_from_alpha3(country_code)
            if expected_nationality and expected_nationality.lower() != nationality.lower():
                inconsistencies.append(f"Nationality does not match the expected nationality based on country code. Expected: {expected_nationality.lower()}, Provided: {nationality.lower()}.")
        else:
            inconsistencies.append("Invalid country code.")
   

    # Client profile checks
    address = client_profile.get("address", {})
    email = client_profile.get("email_address")
    inheritance = client_profile.get("aum", {}).get("inheritance", 0)
    real_estate_value = client_profile.get("aum", {}).get("real_estate_value", 0)
    inheritance_details = client_profile.get("inheritance_details", {})
    real_estate_details = client_profile.get("real_estate_details", [])
    inheritance_year = inheritance_details.get("inheritance year")
    currency = client_profile.get("currency", {})

    if not address or not all(key in address for key in ["city", "street name", "street number", "postal code"]):
        inconsistencies.append("Address in client profile is missing or incorrectly formatted.")

    if email and not is_email_valid(email):
        inconsistencies.append("Invalid email address in client profile.")

    if inheritance > 0 and not inheritance_details:
        inconsistencies.append("Inheritance details are missing despite inheritance > 0.")

    if real_estate_value > 0 and not real_estate_details:
        inconsistencies.append("Real estate details are missing despite real estate value > 0.")

    if inheritance_year:
        inheritance_year_obj = is_valid_date(f"{inheritance_year}-01-01", "%Y-%m-%d")
        if not inheritance_year_obj or inheritance_year_obj >= datetime.now():
            inconsistencies.append("Inheritance year is not in the past or within lifetime.")

    phone_number = client_profile.get("phone_number")
    if phone_number and not is_phone_number_valid(phone_number):
        inconsistencies.append("Phone number in client profile is not numerical.")

    if currency:
        if not currency in ["DKK", "NOK", "CHF", "EUR", "GBP", "USD", "ISK"]:
            #print(currency + " " + path)
            inconsistencies.append(f"Currency {currency} is not accepted")


    # Account form checks
    account_name = account_form.get("name")
    first_name = account_form.get("first_name")
    middle_name = account_form.get("middle_name", "")
    last_name = account_form.get("last_name")
    account_email = account_form.get("email_address")
    account_phone = account_form.get("phone_number")
    account_address = account_form.get("address", {})
    country_of_domicile = account_form.get("country_of_domicile")


    if account_name and "".join(f"{first_name}{middle_name}{last_name}".split()).lower() != "".join(account_name.split()).lower():
        inconsistencies.append("Name in account form does not match first, middle, and last name (ignoring case and whitespace).")

    if not account_address or not all(key in account_address for key in ["city", "street name", "street number", "postal code"]):
        inconsistencies.append("Address in account form is missing or incorrectly formatted.")

    if account_email and not is_email_valid(account_email):
        inconsistencies.append("Invalid email address in account form.")

    if account_phone and not is_phone_number_valid(account_phone):
        inconsistencies.append("Phone number in account form is not numerical.")


    # Intra-document checks
    passport = client_data.get("passport", {})
    client_profile = client_data.get("client_profile", {})
    account_form = client_data.get("account_form", {})

    # Passport checks
    birth_date = passport.get("birth_date")
    issue_date = passport.get("passport_issue_date")
    expiry_date = passport.get("passport_expiry_date")
    gender_passport = passport.get("gender")
    nationality_passport = passport.get("nationality")
    passport_number = passport.get("passport_number")

    # Client profile checks
    gender_profile = client_profile.get("gender")
    nationality_profile = client_profile.get("nationality")
    name_profile = client_profile.get("name")
    address_profile = client_profile.get("address")
    phone_profile = client_profile.get("phone_number")
    email_profile = client_profile.get("email_address")

    # Account form checks
    first_name = account_form.get("first_name")
    middle_name = account_form.get("middle_name", "")
    last_name = account_form.get("last_name")
    name_account = account_form.get("name")
    address_account = account_form.get("address")
    phone_account = account_form.get("phone_number")
    email_account = account_form.get("email_address")
    country_of_domicile = account_form.get("country_of_domicile")

    # Inter-document checks
    # Passport and Client Profile
    if gender_passport and gender_profile and gender_passport.lower() != gender_profile.lower():
        inconsistencies.append("Gender in passport and client profile do not match.")

    if nationality_passport and nationality_profile and nationality_passport.lower() != nationality_profile.lower():
        inconsistencies.append("Nationality in passport and client profile do not match.")

    if birth_date and client_profile.get("birth_date") and birth_date != client_profile.get("birth_date"):
        inconsistencies.append("Birth date in passport and client profile do not match.")

    if issue_date and expiry_date and client_profile.get("passport_issue_date") and client_profile.get("passport_expiry_date"):
        if issue_date != client_profile.get("passport_issue_date") or expiry_date != client_profile.get("passport_expiry_date"):
            inconsistencies.append("Passport issue or expiry date in passport and client profile do not match.")

    # Client Profile and Account Form
    if name_profile and name_account and name_profile.lower() != name_account.lower():
        inconsistencies.append("Name in client profile and account form do not match.")

    if address_profile and address_account and address_profile != address_account:
        inconsistencies.append("Address in client profile and account form do not match.")

    if phone_profile and phone_account and phone_profile != phone_account:
        inconsistencies.append("Phone number in client profile and account form do not match.")

    if email_profile and email_account and email_profile.lower() != email_account.lower():
        inconsistencies.append("Email address in client profile and account form do not match.")

    # Passport and Account Form
    if first_name and middle_name and last_name and name_account:
        full_name = "".join(f"{first_name}{middle_name}{last_name}".split()).lower()
        if full_name != "".join(name_account.split()).lower():
            inconsistencies.append("Full name in passport and account form do not match.")

    if passport_number and account_form.get("passport_number") and client_profile.get("passport_number") and passport_number != account_form.get("passport_number") and passport_number != client_data.get("passport_number"):
        inconsistencies.append("Passport number in passport or account form or client data do not match.")

    # Final result
    accepted = len(inconsistencies) == 0
    result = {
        "preprocessing": accepted,
        "explanation": "; ".join(inconsistencies)
    }

    


    # Add the internal score field
    client_data["internal_score"] = result

    return client_data

def load_process_all(clients_json_path):
    """
    Loads each client JSON file, processes them individually, and adds an additional field.

    Args:
        clients_json_path (str): Path to the folder containing client JSON files.
    """
    if not os.path.exists(clients_json_path):
        raise FileNotFoundError(f"The folder {clients_json_path} does not exist.")
    
    rejected_count = 0
    false_negative_count = 0
    false_negatives = set()
    
    # Iterate through all JSON files in the folder
    for client_file_name in os.listdir(clients_json_path):
        client_file_path = os.path.join(clients_json_path, client_file_name)
        
        if client_file_name.endswith('.json'):
            # Load the client data
            with open(client_file_path, 'r') as client_file:
                client_data = json.load(client_file)
                client_data = static_analysis(client_data=client_data, path = client_file_path)
                if not client_data.get("internal_score", {}).get("preprocessing", {}):
                    rejected_count += 1
                    if client_data.get("label", {}).get("label",{}) == "Accept":
                        false_negative_count += 1
                        false_negatives.add(client_data.get("internal_score", {}).get("explanation", {}))

            
            # Save the updated client data back to the same file
            with open(client_file_path, 'w') as client_file:
                json.dump(client_data, client_file, indent=4)
    
    print(f"Static analysis completed. Updated files are stored in {clients_json_path}. Rejected {rejected_count} Clients with {false_negative_count} potential false negatives {false_negatives}")

# Example usage
if __name__ == "__main__":
    clients_json_path = "preprocessing/all_clients"
    load_process_all(clients_json_path)