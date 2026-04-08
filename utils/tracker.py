from dotenv import load_dotenv
import os
import datetime
from openpyxl import Workbook, load_workbook
from utils.logfiles import setup_logger

logger = setup_logger("file_and_tracker")
load_dotenv()


class File_And_Tracker:
    def __init__(self, main_path, pipelines, company_name, tariff_program, is_effective, file_status, time_taken, file_path):
        self.main_path = main_path
        self.pipelines = pipelines
        self.company_name = company_name
        self.tariff_program = tariff_program
        self.is_effective = is_effective
        self.file_status = file_status
        self.time_taken = time_taken
        self.file_path = file_path

    
    # This function creates an Excel file to track the status of downloaded files. It takes the main path, sub-path, pipeline name, company name, tariff program, effective status, file status, and time taken as input. If the tracker file for the current date already exists, it appends a new entry to it; otherwise, it creates a new tracker file with headers and the first entry.
    def create_excel_tracker_files(main_path, pipelines, company_name, tariff_program, is_effective, file_status, time_taken):
        try:
            tracker_path = os.path.join(main_path, os.getenv("TRACEBACK_FILE"))
        
            if not os.path.exists(tracker_path):
                os.makedirs(tracker_path)
                logger.info(f"Tracker directory created at: {tracker_path}\n")
            else:
                logger.info(f"Tracker directory already exists at: {tracker_path}\n")

            today = datetime.date.today()
            tracker_file = os.path.join(tracker_path, f"file_tracker_{today}.xlsx")

            new_entry = [pipelines, company_name, tariff_program, is_effective, file_status, time_taken]

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

            except Exception as e:
                logger.error(f"Error recording tracker file: {e}\n")
                print(f"Error recording tracker file: {e}")   

        except Exception as e:
            logger.error(f"Error creating tracker file: {e}\n")
            print(f"Error creating tracker file: {e}")

    
    # This function creates a folder for each pipeline inside the specified main path and sub-path to store the downloaded pdf files.
    def create_pipeline_folder(self):
        try:
            output_path = os.path.join(self.main_path, os.getenv("DOWNLOAD_DIR"))

            if not os.path.exists(output_path):
                logger.debug(f"Output directory does not exist. Creating directory at: {output_path}\n")
                os.makedirs(output_path)

            pipeline_folder = os.path.join(output_path, self.pipelines)
            if not os.path.exists(pipeline_folder):
                logger.debug(f"Pipeline folder does not exist for {self.pipelines}. Creating folder at: {pipeline_folder}\n")
                os.makedirs(pipeline_folder)
                logger.info(f"Folder created for {self.pipelines}")
                return pipeline_folder.replace("\\", "/")  # Return the path with forward slashes for consistency
            else:
                logger.info(f"Folder already exists for {self.pipelines}") 
                return None

        except Exception as e:
            logger.error(f"Error creating pipeline folder: {e}")

   

    def get_latest_file(self, pipeline_name=None):
        try:
            # Build full path
            base_path = os.path.abspath(self.file_path)

            if pipeline_name:
                target_path = os.path.join(base_path, pipeline_name)
            else:
                target_path = base_path

            if not os.path.exists(target_path):
                raise FileNotFoundError(f"Folder not found: {target_path}")

            files = [
                os.path.join(target_path, f)
                for f in os.listdir(target_path)
                if not f.endswith(".crdownload")  # ignore temp files
            ]

            if not files:
                raise ValueError("No files found in directory.")

            latest_file = max(files, key=os.path.getctime)

            return latest_file

        except Exception as e:
            print(f"Error getting latest file: {e}")
            return None
