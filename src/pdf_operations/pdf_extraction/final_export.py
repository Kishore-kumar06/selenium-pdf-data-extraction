from dotenv import load_dotenv
import pdfplumber
import pandas as pd
import os
from datetime import datetime
from utils.helpers import load_pdf_files
from .extract_3_column_headers_table_data import extract_data
from .extract_borderless_table_data import extract_borderless_data

load_dotenv()

# Only these pipelines will be exported
SUPPORTED_PIPELINES = {
    "ANDEAVOR LOGISTICS RIO PIPELINE",
    "ARROWHEAD INGLESIDE PIPELINE",
    "BAKKEN PIPELINE",
    "BENGAL PIPELINE",
    "BLACK LAKE PIPELINE",
    "BLUESTEM PIPELINE",
    "BATON ROUGE PIPELINE",
    "CHEYENNE PIPELINE",
    "DIAMOND PIPELINE",
    "MIDWAY PIPELINE",
    "PANOLA PIPELINE",
    "TARGA GULF COAST NGL PIPELINE",
    "TEXAS EXPRESS PIPELINE"
}

BORDERLESS_PIPELINES = {
    "BATON ROUGE PIPELINE",
    "CHEYENNE PIPELINE",
    "DIAMOND PIPELINE",
    "MIDWAY PIPELINE",
    "PANOLA PIPELINE",
    "TARGA GULF COAST NGL PIPELINE",
    "TEXAS EXPRESS PIPELINE"
}


def normalize_file_name(file_path):
    """
    Normalize filename for comparison.
    """

    file_name = os.path.basename(file_path)

    normalized_name = (
        os.path.splitext(file_name)[0]
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .upper()
    )

    return normalized_name


def should_process_pdf(file_path):
    """
    Check whether current PDF
    belongs to supported pipelines.
    """

    normalized_name = normalize_file_name(
        file_path
    )

    return normalized_name.startswith(
        tuple(SUPPORTED_PIPELINES)
    )


def is_borderless_pipeline(file_path):
    """
    Check whether current pipeline
    uses borderless extraction logic.
    """

    normalized_name = normalize_file_name(
        file_path
    )

    return normalized_name.startswith(
        tuple(BORDERLESS_PIPELINES)
    )


def export_data():
    try:
        start = datetime.now()

        processed_count = 0
        skipped_count = 0
        failed_count = 0
        
        pdf_files = load_pdf_files()

        for file in pdf_files:
            file_name = os.path.basename(file)

            # ---------------------------------
            # Skip Unsupported Pipelines
            # ---------------------------------

            if not should_process_pdf(
                file
            ):

                skipped_count += 1

                print(
                    f"Skipping unsupported PDF: "
                    f"{file_name}"
                )

                continue

            try:
                with pdfplumber.open(file) as pdf:

                    # -------------------------
                    # Borderless Extraction
                    # -------------------------

                    if is_borderless_pipeline(file):

                        data = extract_borderless_data(pdf, source_name=file)

                    # -------------------------
                    # Normal Extraction
                    # -------------------------

                    else:

                        print("Using normal extraction")

                        data = extract_data(pdf)

                    if not data:

                        failed_count += 1

                        print(f"No table data extracted: {file_name}")
                        continue

                    final_data = pd.DataFrame(data)

                    output_file_name = (os.path.splitext(file_name)[0]+ ".csv")

                    output_file = os.path.join(os.getenv("EXTRACTED_DATA_OUTPUT_PATH"),output_file_name)

                    final_data.to_csv(output_file, index=False, encoding="utf-8")

                    processed_count += 1

                    print(f"Exported: {output_file_name}")
            
            except Exception as e:

                failed_count += 1

                print(
                    f"Failed processing "
                    f"{file_name}: {e}"
                )

                continue
        end = datetime.now()

        diff = end - start
        print("\nExecution Summary")
        print("-" * 40)
        print(f"Processed PDFs : {processed_count}")
        print(f"Skipped PDFs   : {skipped_count}")
        print(f"Failed PDFs    : {failed_count}")
        print(f"Execution Time : {diff}")

    except Exception as e:
        print(f"Error in final export: {e}")    

