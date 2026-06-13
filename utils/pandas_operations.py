import pandas as pd
import os
from .logfiles import setup_logger

logger = setup_logger("pandas_operations")

class ReadPipelines:
    def __init__(self, file_path=None):
        self.file_path = file_path

        if not self.file_path:
            logger.error("Input file path not provided or found in environment variables.")
    

    # This function fetches the pipeline names from the csv file to be used as a input search parameter for downloading the files.
    def read_and_clean_csv(self, file_path=None):
        try:
            if file_path is None:
                file_path = self.file_path

                if not os.path.exists(file_path):
                    logger.error(f"File not found: {file_path}")
                else:
                    df = pd.read_csv(file_path)
                    
                    if df.empty:
                        logger.error(f"CSV file is empty: {file_path}")

                    # Drop rows with any null values
                    df.dropna(inplace=True)

                    # Validate required column
                    if 'PipelineName' not in df.columns:
                        logger.error("Column 'PipelineName' not found in CSV.")

                    df['PipelineName'] = df['PipelineName'].str.strip()
                    return df
                        
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise FileNotFoundError(f"Error reading CSV file: {e}")
           
        
        


