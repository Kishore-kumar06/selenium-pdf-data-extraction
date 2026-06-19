from utils.logfiles import setup_logger
from utils.tracker import File_And_Tracker
from utils.verify_network import check_connection
from src.selenium_operations.driver_setup import DriverSetup
from pages.tariff_list_page import TariffListPage
from pages.tariff_browser_page import TariffBrowserPage
from utils.pandas_operations import ReadPipelines
import time
import os

logger = setup_logger('file_downloader')
    
def selenium_download_process(driver, driver_setup, current_dir):
    try:      
    
        data = ReadPipelines(os.getenv("INPUT_FILE"))
        df = data.read_and_clean_csv()

        pipelines = df['PipelineName']
        
        tracker_file = File_And_Tracker(main_path=current_dir)

        completed_pipelines = tracker_file.get_processed_files()

        for pipeline_name in pipelines:
            logger.info(f"Retrieved pipeline {pipeline_name}.")

            if pipeline_name in completed_pipelines:
                logger.info(f"Pipeline {pipeline_name} already exist. Skipping...")
                continue
        
            start_time = time.time()
            try:
                process_first_page = TariffListPage(driver, pipelinename=pipeline_name)
                process_second_page = TariffBrowserPage(driver)

                company_name, tariff_option, tariff_text = process_first_page.process_tariff_list()

                # Skip pipeline if no tariff exists
                if tariff_option is None:

                    logger.info(f"Skipping {pipeline_name} pipeline - no files available")

                    tracker_file.create_excel_tracker_files(
                        pipeline=pipeline_name,
                        company_name=company_name,
                        tariff_program=tariff_text,
                        is_effective="No",
                        file_status="No File Available",
                        time_taken=0
                    )

                    driver_setup.navigate_back()
                    continue

                tariff_option.click()

                pipeline_folder = tracker_file.create_pipeline_folder(pipeline_name)

                download_dir = os.path.abspath(pipeline_folder)

                if download_dir:
                    driver_setup.set_download_path(download_dir)

                process_second_page.process_tariff_browser(pipeline_name) 

                file = tracker_file.get_latest_file(file_path=download_dir, pipeline=pipeline_name)
                if file:
                    logger.info(f"Latest downloaded file: {file}.")

                end_time = time.time() 
                time_taken = end_time - start_time
                
                tracker_file.create_excel_tracker_files(
                    pipeline=pipeline_name,
                    company_name=company_name, 
                    tariff_program=tariff_text, 
                    is_effective="Yes", 
                    file_status="Downloaded", 
                    time_taken=time_taken
                )

                driver_setup.navigate_back()
                driver_setup.navigate_back()

                tracker_file.write_downloaded_pipelines(pipeline_name)
 
            except Exception as e:
                logger.exception(f"Pipeline failed: {pipeline_name}")

    except Exception as e:
        logger.exception(f"An error occurred while downloading file for {pipeline_name}: {e}")
   
        

def download_files():

    try:
        retries = 5
        wait_time = 2
        success = False

        for attempt in range(1, retries + 1):
            driver_setup = None
            driver = None
        
            try:
                if check_connection() == False:
                    logger.error("Internet Disconnected")
                    print("Internet Disconnected")
                    raise ConnectionError("Internet Disconnected")
                
                driver_setup = DriverSetup(browser_name="chrome", headless=False)

                current_dir = os.getcwd()

                driver = driver_setup.setup_browser() # driver setup
                driver_setup.open_url(os.getenv("URL"))

                selenium_download_process(driver, driver_setup, current_dir)
            
                logger.info("Process completed successfully.")
                success = True
                break

            except (Exception, ConnectionError) as e:
                logger.exception(f"Attempt {attempt} failed. {e}")
                print(f"Attempt {attempt} failed. {e}")
                
                if attempt < retries:
                    logger.error(f"Retrying in {wait_time} seconds...")
                    print(f"Retrying in {wait_time} seconds...")
                
                    time.sleep(wait_time)
                    wait_time *= 2  
            finally:
                if driver:
                    driver_setup.quit_browser()

        if not success:
            logger.error("All attempts failed to complete the download process.")
    
    except Exception as e:
        logger.exception(f"An error occured while automating file downloads. {e}")
    
    
        