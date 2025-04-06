import os
import json

def load_process_all(clients_json_path):
    """
    Loads each client JSON file, extracts unique categories for specific fields, and prints them.

    Args:
        clients_json_path (str): Path to the folder containing client JSON files.
    """
    if not os.path.exists(clients_json_path):
        raise FileNotFoundError(f"The folder {clients_json_path} does not exist.")
    
    # Initialize sets to store unique categories for each field
    investment_risk_profile_set = set()
    investment_horizon_set = set()
    investment_experience_set = set()
    type_of_mandate_set = set()
    currency_set = set()  # New set for currencies

    # Iterate through all JSON files in the folder
    for client_file_name in os.listdir(clients_json_path):
        client_file_path = os.path.join(clients_json_path, client_file_name)
        
        if client_file_name.endswith('.json'):
            # Load the client data
            with open(client_file_path, 'r') as client_file:
                client_data = json.load(client_file)
                client_profile = client_data.get("client_profile", {})
                
                # Collect unique values for each field
                investment_risk_profile = client_profile.get("investment_risk_profile")
                if investment_risk_profile:
                    investment_risk_profile_set.add(investment_risk_profile)
                
                investment_horizon = client_profile.get("investment_horizon")
                if investment_horizon:
                    investment_horizon_set.add(investment_horizon)
                
                investment_experience = client_profile.get("investment_experience")
                if investment_experience:
                    investment_experience_set.add(investment_experience)
                
                type_of_mandate = client_profile.get("type_of_mandate")
                if type_of_mandate:
                    type_of_mandate_set.add(type_of_mandate)
                
                currency = client_profile.get("currency")  # Extract currency
                if currency == "USA":
                    print("USA")
                if currency:
                    currency_set.add(currency)
    
    # Print the unique categories for each field
    print("Unique categories for investment_risk_profile:", investment_risk_profile_set)
    print("Unique categories for investment_horizon:", investment_horizon_set)
    print("Unique categories for investment_experience:", investment_experience_set)
    print("Unique categories for type_of_mandate:", type_of_mandate_set)
    print("Unique currencies:", currency_set)  # Print unique currencies

# Example usage
if __name__ == "__main__":
    clients_json_path = "preprocessing/all_clients"
    load_process_all(clients_json_path)