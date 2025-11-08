import csv
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def save_data_to_csv(data, filepath):
    """
    Saves a list of dictionaries (system data snapshots) to a CSV file.
    Assumes all dictionaries have consistent keys for headers.
    """
    if not data:
        logger.warning("No data provided to save to CSV.")
        return

    try:
        # Get all possible headers from all data points for comprehensive columns
        all_keys = sorted(list(set.union(*map(set, data))))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_keys)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        logger.info(f"Data successfully saved to CSV: {filepath}")
    except Exception as e:
        logger.error(f"Error saving data to CSV at {filepath}: {e}", exc_info=True)
        raise

def save_data_to_excel(data, filepath):
    """
    Saves a list of dictionaries (system data snapshots) to an Excel file.
    Requires pandas and openpyxl ('pip install pandas openpyxl').
    """
    if not data:
        logger.warning("No data provided to save to Excel.")
        return

    try:
        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)
        logger.info(f"Data successfully saved to Excel: {filepath}")
    except ImportError:
        logger.error("Pandas or Openpyxl not installed. Please run 'pip install pandas openpyxl'.", exc_info=True)
        raise ImportError("Pandas or Openpyxl not installed. Cannot save to Excel.")
    except Exception as e:
        logger.error(f"Error saving data to Excel at {filepath}: {e}", exc_info=True)
        raise