import os, sys
import json
import glob
from tqdm import tqdm
from pathlib import Path

# Adjust this path if needed
directory = Path(__file__).resolve().parent / "extracted_features"
client_directory = Path(__file__).resolve().parent.parent / "preprocessing" / "all_clients"

# List all feature files
feature_files = sorted(glob.glob(os.path.join(directory, 'features_client_*.json')))

for feature_file in tqdm(feature_files, desc="Processing feature files"):
    # Extract client number
    base_name = os.path.basename(feature_file)
    client_id = base_name.split('_')[-1].replace('.json', '')  # e.g., "0"

    # Build corresponding client file path
    client_file = os.path.join(client_directory, f'client_{client_id}.json')

    if not os.path.exists(client_file):
        #print(f"Warning: {client_file} does not exist. Skipping.")
        continue

    # Load feature and label data
    with open(feature_file, 'r', encoding='utf-8') as f_feat:
        features_data = json.load(f_feat)

    with open(client_file, 'r', encoding='utf-8') as f_client:
        client_data = json.load(f_client)

    # Construct new structure
    updated_data = {
        "features": features_data,
        "label": client_data.get("label", {})
    }

    # Save back to the same feature file
    with open(feature_file, 'w', encoding='utf-8') as f_out:
        json.dump(updated_data, f_out, indent=2)

    #print(f"Updated: {feature_file}")
