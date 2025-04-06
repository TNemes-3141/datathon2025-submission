import os
import zipfile
import json
import pandas as pd

def extract_and_merge_jsons_2_list(input_folder):
    """
    Extracts and merges JSON files from nested zip files in the input folder.

    Args:
        input_folder (str): Path to the folder containing zip files.

    Returns:
        a list of all merged json files. 
    """
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"The folder {input_folder} does not exist.")
    
    merged_data = []

    # Iterate through all zip files in the input folder
    for zip_file_name in sorted(os.listdir(input_folder)):
        zip_file_path = os.path.join(input_folder, zip_file_name)
        
        if zipfile.is_zipfile(zip_file_path):
            with zipfile.ZipFile(zip_file_path, 'r') as outer_zip:
                # Extract each client zip file
                for client_zip_name in sorted(outer_zip.namelist()):
                    if client_zip_name.endswith('.zip'):
                        with outer_zip.open(client_zip_name) as client_zip_file:
                            with zipfile.ZipFile(client_zip_file) as client_zip:
                                # Create a dictionary to store client data
                                client_data = {}
                                # Extract specific JSON files for the client
                                for json_file_name in client_zip.namelist():
                                    # Extract the actual file name (e.g., "passport.json")
                                    _, actual_file_name = os.path.split(json_file_name)
                                    if actual_file_name in [
                                        "passport.json",
                                        "client_profile.json",
                                        "client_description.json",
                                        "account_form.json",
                                        "label.json",
                                    ]:
                                        with client_zip.open(json_file_name) as json_file:
                                            json_data = json.load(json_file)
                                            # Use the file name (without .json) as the key
                                            key = os.path.splitext(actual_file_name)[0]
                                            client_data[key] = json_data
                                # Add the client data to the merged data if all fields are present
                                if client_data:
                                    merged_data.append(client_data)
    
    return merged_data


def convert_dtype(df):
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype('string')
    return df


# if applicable, convert strings to float or even int64

def try_convert_str2float(col: pd.Series, threshold: float = 1.0) -> pd.Series:
    """
    Attempt to convert a text column to numeric (int or float).

    Parameters:
      col       : A pandas Series of type string.
      threshold : The fraction of non-null values that must convert successfully
                  to accept the conversion (default 1.0 means all values must convert).

    Returns:
      The converted Series if the conversion rate meets the threshold,
      otherwise the original Series.
    """
    # Attempt to convert all values to numeric.
    converted = pd.to_numeric(col, errors='coerce')

    # Count non-null values in the original and in the converted series.
    original_non_null = col.notna().sum()
    converted_non_null = converted.notna().sum()

    # If the column is entirely null, return as is.
    if original_non_null == 0:
        return col

    conversion_rate = converted_non_null / original_non_null

    if conversion_rate >= threshold:
        # Check if all non-null converted values are integers.
        if converted.dropna().apply(lambda x: float(x).is_integer()).all():
            # Convert to pandas nullable integer type.
            return converted.astype('Int64')
        else:
            return converted
    else:
        # If too many values couldn't be converted, keep the original column.
        return col

def try_mixed_convert_str2float(df):
    for col in df.select_dtypes(include=["string"]).columns:
        df[col] = try_convert_str2float(df[col], threshold=1.0)
    return df
# df now has its text columns converted to numeric types (int or float) when possible.

# turn list of json into pandas dataframe
def list_json_2_df(list_json):
    df = pd.json_normalize(list_json)
    
    
    #df = df.rename(columns = {'label.label':'label'})
    #df['label'] = df['label'].replace({'Accept':1, 'Reject':0})
    

    df = try_mixed_convert_str2float(convert_dtype(df))

    return df

def create_data():
    # todo!!!
    input_folder_path = "input"

    df = list_json_2_df(extract_and_merge_jsons_2_list(input_folder_path))
    print(df.head(2))
    return df





# import autogluon
from autogluon.tabular import TabularPredictor


def ml_stage():

    ds = create_data()

    # todo !!! test_ds specify, no label column!!!!!

    test_ds = ds.drop(columns=["label"], errors="ignore")
    # todo!!! specify directory!!!
    #print(test_ds)
    predictor = TabularPredictor.load(f"ml/ag-20250406_022427", require_py_version_match=False)
    y_pred = predictor.predict(test_ds)

    #print(y_pred)
    # Write y_pred into a CSV file
    output_path = "ml/intermediate.csv"
    y_pred.to_csv(output_path, index=False)
    print(f"Predictions saved to {output_path}")
    # output is y_pred, pandas.series