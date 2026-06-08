import pdfplumber
import pandas as pd
import os
from datetime import datetime
from utils.helpers import load_pdf_files
from .extract_3_column_headers_table_data import extract_data


files = ["Andeavor Logistics Rio Pipeline","Arrowhead Ingleside Pipeline","Bakken Pipeline"]

def export_data():
    try:
        start = datetime.now()
        curr_path = os.getcwd()
        tariff_data = []
        
        pdf_file = load_pdf_files()
        for file in pdf_file:
            file_name_without_ext = os.path.splitext(os.path.basename(file))[0]
            
            if file_name_without_ext not in files:
                print(f"Skipping file: {file} as it is not in the target list.")
                continue

            with pdfplumber.open(file) as pdf:
                data = extract_data(pdf)
                tariff_data.extend(data)
                final_data = pd.DataFrame(tariff_data)

                input_file = os.path.basename(file).replace('.PDF','_v1.csv').replace('.pdf', '_v1.csv')

                if final_data is not None and len(final_data) > 0:
                    output_file = os.path.join(os.getenv("EXTRACTED_DATA_OUTPUT_PATH"), input_file)
                    final_data.to_csv(output_file, index=False, encoding="utf-8")
                    tariff_data.clear()
                    # print(f"\nData successfully exported to {input_file}")
                else:
                    print(f"\nFailed to extract {input_file} table data.")

        end = datetime.now()
        diff = end - start
        print(f"Exported all files in {diff}.")

    except Exception as e:
        print(f"Error in final export: {e}")    

