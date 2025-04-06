import zipfile
import os
import json

def extract_and_merge_jsons(input_folder, output_folder):
    """
    Extracts and merges JSON files from nested zip files in the input folder.

    Args:
        input_folder (str): Path to the folder containing zip files.
        output_folder (str): Path to the output JSON files where merged data will be stored.
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"The folder {input_folder} does not exist.")
    
    merged_data = []

    expected_json_files = {
        "passport.json",
        "client_profile.json",
        "client_description.json",
        "account_form.json",
        "label.json",
    }

    for zip_file_name in sorted(os.listdir(input_folder)):
        zip_file_path = os.path.join(input_folder, zip_file_name)
        
        if zipfile.is_zipfile(zip_file_path):
            with zipfile.ZipFile(zip_file_path, 'r') as outer_zip:
                for client_zip_name in sorted(outer_zip.namelist()):
                    if client_zip_name.endswith('.zip'):
                        with outer_zip.open(client_zip_name) as client_zip_file:
                            with zipfile.ZipFile(client_zip_file) as client_zip:
                                client_data = {}
                                found_files = set()

                                for json_file_name in client_zip.namelist():
                                    base_name = os.path.basename(json_file_name)
                                    if base_name in expected_json_files:
                                        with client_zip.open(json_file_name) as json_file:
                                            json_data = json.load(json_file)
                                            key = os.path.splitext(base_name)[0]
                                            client_data[key] = json_data
                                            found_files.add(base_name)

                                if client_data:
                                    missing = expected_json_files - found_files
                                    if missing:
                                        print(f"[INFO] {client_zip_name} is missing: {missing}")
                                    merged_data.append(client_data)

    os.makedirs(output_folder, exist_ok=True)
    for idx, client_data in enumerate(merged_data):
        client_file_path = os.path.join(output_folder, f"client_{idx}.json")
        with open(client_file_path, 'w') as client_file:
            json.dump(client_data, client_file, indent=4)

    print(f"Merged JSON data written to {output_folder}")
    print(f"Total number of clients processed: {len(merged_data)}")


# Example usage
if __name__ == "__main__":
    input_folder_path = "eval_input"
    output_json_path = "preprocessing/all_clients"
    extract_and_merge_jsons(input_folder_path, output_json_path)
