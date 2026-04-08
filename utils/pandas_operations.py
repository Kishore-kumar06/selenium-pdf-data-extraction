import pandas as pd
import os
from .logfiles import setup_logger

logger = setup_logger("pandas_operations")

class ReadPipelines:
    def __init__(self, file_path=None):
        self.file_path = file_path

        if not self.file_path:
            logger.error("Input file path not provided or found in environment variables.\n")
            raise ValueError("Input file path not provided or found in environment variables.")
        

    # This function reads and clean pipeline names from csv file to be used for selenium operations. It removes any leading or trailing whitespace from the pipeline names and drops any rows with missing values.
    def read_and_clean_csv(self, file_path=None):
        try:
            if file_path is None:
                file_path = self.file_path

                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path} \n")
                    raise FileNotFoundError(f"File not found: {file_path}")
                else:
                    df = pd.read_csv(file_path)
                    
                    if df.empty:
                        logger.warning(f"CSV file is empty: {file_path} \n")

                    # Drop rows with any null values
                    df.dropna(inplace=True)

                    # Validate required column
                    if 'PipelineName' not in df.columns:
                        logger.error("Column 'PipelineName' not found in CSV. \n")
                        raise KeyError("Column 'PipelineName' not found in CSV.")

                    df['PipelineName'] = df['PipelineName'].str.strip()
                    return df
                        
        except Exception as e:
            logger.error(f"Error reading or cleaning CSV: {e} \n")
            return None
        
        


