from utils.logfiles import setup_logger
from utils.tracker import File_And_Tracker
from pages.tariff_list_page import TariffListPage
from pages.tariff_browser_page import TariffBrowserPage
import time
import os

logger = setup_logger('file_downloader')


def download_files(driver, driver_setup, pipelines, current_dir):
    try:      

        for pipeline_name in pipelines:
            logger.info(f"Retrieved pipeline {pipeline_name}.")
        
            start_time = time.time()

            tracker_file = File_And_Tracker(main_path=current_dir, pipelines=pipeline_name)
            pipeline_folder = tracker_file.create_pipeline_folder()
            logger.info(f"Created {pipeline_name} directory to store the file.")

            download_dir = os.path.abspath(pipeline_folder)

            driver_setup.set_download_path(download_dir)
            
            process_first_page = TariffListPage(driver, pipelinename=pipeline_name)
            process_second_page = TariffBrowserPage(driver)

            company_name, tariff_option, tariff_text = (
                process_first_page.process_tariff_list()
            )

            # Skip pipeline if no tariff exists
            if tariff_option is None:

                logger.info(f"Skipping {pipeline_name} pipeline - no files available")

                tracker_file.create_excel_tracker_files(
                    company_name=company_name,
                    tariff_program=tariff_text,
                    is_effective="No",
                    file_status="No File Available",
                    time_taken=0
                )

                driver_setup.navigate_back()
                continue

            tariff_option.click()

            process_second_page.process_tariff_browser()

            file = tracker_file.get_latest_file(file_path=download_dir)
            if file:
                logger.info(f"Latest downloaded file: {file}.")

            end_time = time.time() 
            time_taken = end_time - start_time
            
            tracker_file.create_excel_tracker_files(
                company_name=company_name, 
                tariff_program=tariff_text, 
                is_effective="Yes", 
                file_status="Downloaded", 
                time_taken=time_taken
            )

            driver_setup.navigate_back()
            driver_setup.navigate_back()

    except Exception as e:
        logger.exception(f"An error occurred while downloading file for {pipeline_name}: {e}")
        
