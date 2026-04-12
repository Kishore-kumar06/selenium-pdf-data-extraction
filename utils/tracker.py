from dotenv import load_dotenv
import os
import datetime
from openpyxl import Workbook, load_workbook
from utils.logfiles import setup_logger
import time
import shutil

logger = setup_logger("file_and_tracker")
load_dotenv()

class File_And_Tracker:
    def __init__(self, main_path, pipelines):
        self.main_path = os.path.abspath(main_path)
        self.pipelines = pipelines

    # This function creates an Excel file to track the status of downloaded files. It takes the main path, sub-path, pipeline name, company name, tariff program, effective status, file status, and time taken as input. If the tracker file for the current date already exists, it appends a new entry to it; otherwise, it creates a new tracker file with headers and the first entry.
    def create_excel_tracker_files(self, company_name, tariff_program, is_effective, file_status, time_taken):
        try:
            tracker_path = os.path.join(self.main_path, os.getenv("TRACEBACK_FILE"))
        
            # Ensure directory exists
            os.makedirs(tracker_path, exist_ok=True)
            logger.info(f"Tracker directory ready at: {tracker_path}. \n")    

            # File name (date-based)
            today = datetime.date.today().strftime("%Y-%m-%d")
            tracker_file = os.path.join(tracker_path, f"file_tracker_{today}.xlsx")

            new_entry = [self.pipelines, company_name, tariff_program, is_effective, file_status, time_taken]

            try:
                if os.path.exists(tracker_file):
                    wb = load_workbook(tracker_file)
                    ws = wb.active
                    ws.append(new_entry)
                else:
                    wb = Workbook()
                    ws = wb.active
                    ws.append(['Pipeline', 'Company Name', 'Tariff Title', 'Effective Status', 'File Status', 'Time Taken'])
                    ws.append(new_entry)
                
                wb.save(tracker_file)
                logger.info(f"Tracker updated successfully: {tracker_file}. \n")
                print(f"Tracker updated: {tracker_file}")

            except Exception as e:
                logger.error(f"Error recording tracker file: {e}. \n")
                print(f"Error recording tracker file: {e}")   

        except Exception as e:
            logger.error(f"Error creating tracker file: {e}. \n")
            print(f"Error creating tracker file: {e}")

    
    # This function creates a folder for each pipeline inside the specified main path and sub-path to store the downloaded pdf files.
    def create_pipeline_folder(self):
        try:
            output_path = os.path.join(self.main_path, os.getenv("DOWNLOAD_DIR"))

            if not os.path.exists(output_path):
                os.makedirs(output_path)

            pipeline_folder = os.path.join(output_path, self.pipelines)
            if not os.path.exists(pipeline_folder):
                logger.debug(f"Pipeline folder does not exist for {self.pipelines}. Creating folder at: {pipeline_folder}. \n")
                os.makedirs(pipeline_folder)
                logger.info(f"Folder created for {self.pipelines}. \n")
                return pipeline_folder.replace("\\", "/")  # Return the path with forward slashes for consistency
            else:
                logger.info(f"Folder already exists for {self.pipelines}. \n") 
                return None

        except Exception as e:
            logger.error(f"Error creating pipeline folder: {e}. \n")

   
    def get_latest_file(self, file_path):
        try:
            target_path = os.path.abspath(file_path)

            if not os.path.exists(target_path):
                logger.error(f"Folder not found: {target_path}. \n")
                raise FileNotFoundError(f"Folder not found: {target_path}")

            files = [
                os.path.join(target_path, f)
                for f in os.listdir(target_path)
                if os.path.isfile(os.path.join(target_path, f)) and not f.endswith(".crdownload")
            ]

            if not files:
                time.sleep(3)
                logger.error(f"No files found in directory {file_path}. \n")
                raise ValueError("No files found in directory.")

            # Get latest file
            downloaded_file = max(files, key=os.path.getctime)
        
            # Extract extension
            _, file_extension = os.path.splitext(downloaded_file)

            # New file name
            new_file_name = f"{self.pipelines}{file_extension}"

            # New full path
            latest_file_path = os.path.join(target_path, new_file_name)

            # Rename file
            os.rename(downloaded_file, latest_file_path)

            return latest_file_path

        except Exception as e:
            logger.error(f"Error getting latest file: {e}. \n")
            print(f"Error getting latest file: {e}")
            return None