import json
import csv
import os
import sys
import pandas as pd

from ml.final_eval_v1 import ml_stage

# Add the preprocessing directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "preprocessing"))

from main import preprocessing_stage

def avengers_assemble():
    """
    Main function to assemble the solution pipeline.
    """
    # Define input and output paths
    input_train_path = os.path.join(os.path.dirname(__file__), "input")
    output_preprocessing_path = os.path.join(os.path.dirname(__file__), "preprocessing", "all_clients")
    output_csv_path = os.path.join(os.path.dirname(__file__), "output", "solution.csv")
    ml_predictions_path = os.path.join(os.path.dirname(__file__), "ml", "intermediate.csv")

    # Step 1: Preprocessing stage
    preprocessing_stage(input_train_path, output_preprocessing_path)

    # Step 2: ML stage
    ml_stage()

    # Step 2: Load ML predictions
    print("Loading ML predictions...")
    if not os.path.exists(ml_predictions_path):
        raise FileNotFoundError(f"ML predictions file not found at {ml_predictions_path}")
    ml_predictions = pd.read_csv(ml_predictions_path)["label"].tolist()

    # Step 3: Write results to CSV and calculate accuracy
    print("Writing results to CSV and calculating accuracy...")
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)

    total_clients = 0
    correct_predictions = 0

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=';')

        # Iterate through processed client files in numeric order
        for idx, client_file_name in enumerate(sorted(os.listdir(output_preprocessing_path), key=lambda x: int(os.path.splitext(x)[0].split('_')[1]))):
            client_file_path = os.path.join(output_preprocessing_path, client_file_name)
            if client_file_name.endswith('.json'):
                # Load client data
                with open(client_file_path, 'r', encoding='utf-8') as client_file:
                    client_data = json.load(client_file)

                # Extract preprocessing score
                preprocessing_score = client_data.get("internal_score", {}).get("preprocessing", False)

                # Determine decision
                if not preprocessing_score:
                    decision = "Reject"
                else:
                    # Use ML prediction if preprocessing score is True
                    ml_prediction = ml_predictions[idx]
                    decision = "Accept" if ml_prediction == 1 else "Reject"

                # Extract the actual label
                # actual_label = client_data.get("label", {}).get("label", "")

                # Compare decision with actual label
                # if decision == actual_label:
                #     correct_predictions += 1
                # total_clients += 1

                # Write client ID and decision to the CSV
                client_id = os.path.splitext(client_file_name)[0]  # Remove .json extension
                csv_writer.writerow([client_id, decision])

    # Calculate and print accuracy
    accuracy = correct_predictions / total_clients if total_clients > 0 else 0
    print(f"Accuracy: {accuracy:.2%}")

if __name__ == "__main__":
    avengers_assemble()