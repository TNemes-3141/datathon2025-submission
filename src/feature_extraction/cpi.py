import csv
from pathlib import Path

def extract_cpi_scores_2023(csv_path):
    cpi_scores = {}

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            if row['Indicator ID'] == 'TI.CPI.Score':
                country = row['Economy Name']
                score_2023 = row['2023']
                try:
                    cpi_scores[country] = int(score_2023)
                except ValueError:
                    cpi_scores[country] = None  # or skip if preferred

    return cpi_scores

# Example usage
if __name__ == "__main__":
    path_to_csv = Path(__file__).resolve().parent / "./TI-CPI.csv"  # Replace with your actual file path
    scores = extract_cpi_scores_2023(path_to_csv)
    for country, score in scores.items():
        print(f"{country}: {score}")
