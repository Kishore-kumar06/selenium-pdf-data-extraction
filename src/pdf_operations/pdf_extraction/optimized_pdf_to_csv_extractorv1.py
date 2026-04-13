import pdfplumber
import pandas as pd
import re
from datetime import datetime
from dotenv import load_dotenv
import os
from ..pdf_helpers.data_extraction_helper import PDFHelpers
load_dotenv()


def detect_matrix_header(table, page):
    try:
        destination = (table[0][2] or "").strip()
        origin = (table[2][0] or "").strip()

        # Fix reversed "Origins"
        if origin == "snigirO":
            origin = origin[::-1]

        if ("Destination" in destination or "Destinations" in destination) and \
            ("Origin" in origin or "Origins" in origin):
            # print(f"Page {page} value: {destination}")
            return True
        else:            
            return False

    except Exception as e:
        print(e)


def four_column_header(table, page):
    try:
        '''
        Reference
        'Origins', 'Destinations', 'Rate Tier 1', 'Rate Tier 2'
        '''
        destination = (table[0][1] or "").strip()
        origin = (table[0][0] or "").strip()
        rate1 = (table[0][2] or "").strip()
        rate2 = (table[0][3] or "").strip()

        if ("Destinations" in destination) and \
            ("Origins" in origin) and \
                ("Rate Tier 1" in rate1) and \
                    ("Rate Tier 2" in rate2):
            # print(f"Page {page} value: {destination}")
            return True
        else:
            return False

    except Exception as e:
        print(e)



def extract_records(
    unpivoted_data,
    pipeline_name,
    origin,
    destination,
    effective_date,
    expiry_date,
    rate_tier,
    rate_type,
    bpd,
    rate
):
    try:

        record = {
            "Pipeline Name": pipeline_name,
            "PointfOrigin": origin,
            "PointOfDestination": destination,
            "LiquidTariffNumber": "",
            "Effective Date": effective_date,
            "End Date": expiry_date,
            "TariffStatus": "Effective",
            "RateTier": rate_tier,
            "RateType": rate_type,
            "TermYear": "",
            "MinBPD": bpd.get("MinBPD", ""),
            "MaxBPD": bpd.get("MaxBPD", ""),
            "AcreageDedicationMinAcres": "",
            "AcreageDedicationMaxAcres": "",
            "LiquidRateCentsPerBbl": rate,
            "SurchargeCentsPerBbl": "",
            "LiquidFuelType": "Crude",
        }

        unpivoted_data.append(record)

    except Exception as e:
        print(f"Error in extract_records: {e}")


def extract_matrix_data(cleaned_table, bpd_ranges,
                        unpivoted_data,
                        pipeline_name,
                        origin,
                        destination,
                        effective_date,
                        expiry_date,
                        rate_tier,
                        rate_type,
                        bpd,
                        rate
                        ):
    try:
                        
        if cleaned_table:
            # --- Unpivoting logic ---
            # Headers (Destinations) are in row 1, starting from index 2
            # Origins are in column 1 (Column 2) of each data row
            # Data starts from row 2
            # Rates are from index 2 onwards

            # unpivoted_data = []
            if len(cleaned_table) > 1:
                dest_headers = cleaned_table[1]
                
                for row in cleaned_table[2:]:
                    if len(row) < 2:
                        continue

                    # Origin value is in Column 2 (index 1)
                    origin = row[1]
                    if origin:
                        origin = origin.replace("\n", " ").strip()

                    if (
                        not origin
                        or origin.lower() == "none"
                        or origin == ""
                    ):
                        continue

                    for col_idx in range(2, len(row)):
                        if col_idx >= len(dest_headers):
                            break

                        destination = dest_headers[col_idx]
                        if destination:
                            destination = destination.replace(
                                "\n", " "
                            ).strip()
                        else:
                            destination = f"Unknown_Dest_{col_idx}"

                        rate = row[col_idx]
                        if rate:
                            rate = rate.replace("\n", " ").strip()

                        for bpd in bpd_ranges:
                            extract_records(
                                unpivoted_data,
                                pipeline_name,
                                origin,
                                destination,
                                effective_date,
                                expiry_date,
                                rate_tier,
                                rate_type,
                                bpd,
                                rate
                            )

    except Exception as r:
        print(f"Error while extracting matrix data. {r}")



def extract_four_column_table(cleaned_table, header_index, origin_col, dest_col, tier_cols, bpd_ranges,
                        unpivoted_data,
                        pipeline_name,
                        origin,
                        destination,
                        effective_date,
                        expiry_date,
                        rate_tier,
                        rate_type,
                        bpd,
                        rate
                        ):
    try:
                        
        if cleaned_table:
            # --- Unpivoting logic ---
            # Headers (Destinations) are in row 1, starting from index 2
            # Origins are in column 1 (Column 2) of each data row
            # Data starts from row 2
            # Rates are from index 2 onwards
            

            previous_origin = ""
            previous_dest = ""

            for row in cleaned_table[header_index + 1:]:
                if len(row) <= max(tier_cols.keys()):
                    continue

                origin = row[origin_col].strip()
                dest = row[dest_col].strip()

                if origin:
                    previous_origin = origin
                else:
                    origin = previous_origin

                if dest:
                    previous_dest = dest
                else:
                    dest = previous_dest

                if not origin or not dest:
                    continue

                origin = " ".join(origin.split())
                dest = " ".join(dest.split())
                origin_parts = [o.strip() for o in re.split(r'(?=[A-Z][a-zA-Z]+\s+Located in)', origin) if o.strip()]

                for col_index, tier_name in tier_cols.items():
                    if col_index >= len(row):
                        continue

                    rate = row[col_index].strip()
                    if not rate:
                        continue

                    rate_match = re.search(r"\d+\.\d{2}", rate)
                    if rate_match:
                        valid_rate = rate_match.group()
                    elif rate.lower() == "n/a":
                        valid_rate = "N/A"
                    else:
                        continue

                    for single_origin in origin_parts:
                        for bpd in bpd_ranges:
                            records.append(
                                build_record(
                                    pipeline_name,
                                    effective_date,
                                    single_origin,
                                    dest,
                                    valid_rate,
                                    expiry_date_value,
                                    tier_name,
                                    tariff_rate_type,
                                    min_bpd=bpd["MinBPD"],
                                    max_bpd=bpd["MaxBPD"],
                                )
                            )
            break

    except Exception as r:
        print(f"Error while extracting matrix data. {r}")



def verify_tables(pdf, start_page_number, end_page_number):
    try:
        print(f"--- Extracting Rates Table from {pdf} ---\n")

        unpivoted_data = []
        tariff_rate_type = ""

        pdf_helpers = PDFHelpers(pdf=pdf, pipeline_name="", effective_date="", text="")
        pipeline_name = pdf_helpers.extract_pipelinename_metadata()
        effective_date = pdf_helpers.extract_effectivedate_metadata()

        print(f"Extracted Pipeline Name: {pipeline_name}")
        print(f"Extracted Effective Date: {effective_date}")

        # enumerate start value adjusted so it prints the actual PDF page number
        # Note: pdfplumber is 0-indexed, so start_page_number=2 is Page 3.
        for i, page in enumerate(pdf.pages[start_page_number:end_page_number], start=start_page_number + 1):

            text = page.extract_text()

            if not text:
                continue

            try:
                rate_type = pdf_helpers.extract_tariff_rate_type(text=text)

                if rate_type:
                    tariff_rate_type = rate_type
                else:
                    if rate_type == "":
                        tariff_rate_type = tariff_rate_type

                expiry_date_value = pdf_helpers.extract_expiry_date(text=text)

                bpd_ranges = pdf_helpers.extract_bpd_ranges(text=text)

                # If no BPD found → create single blank BPD
                if not bpd_ranges:
                    bpd_ranges = [{"MinBPD": "", "MaxBPD": ""}] # continuing 

                rate_tier = pdf_helpers.extract_rate_tiers(text=text)

            except Exception as e:
                print(e)
            
            # Extract table using pdfplumber's table extraction
            tables = page.extract_tables()

            
            # 'Origin', 'Destination', 'Rate'
            # row 1 '', 'Destination' | row2 'Origin', 'Deeprock North Terminal in\nCushing, OK'
            # r1 '', None, 'Destination' | r2 'Origin', 'Minimum Volume', 'McPherson Located in\nMcPherson County, KS' | r2 'Origin', 'Production Dedication Volume',
            # r1 '', None, 'Destination', None | r2 ['Origin', 'Minimum Volume',,]
            # 'Origin', 'Destination', 'Long-term Incentive Rate'
            # 'Origin', 'Destination', 'Committed Rate', 'Extra Barrel Rate'
            # 'Origin', 'Destination', '5,000 – 11,999 BPD', None, '12,000 – 23,999 BPD', None, '24,000 or greater BPD', None
            # 'Origin', 'Destination', 'Minimum Volume\nCommitment', 'Shipper A\nExtra Barrel\nRate', 'Shipper B\nIncentive\nRate', 'Shipper B\nExtra Barrel\nRate'
            # 'Origin', 'Destination','Volume', 'Secondary Origin Barrel\nRate'
            # 'Origin', 'Destination','Buckingham Barrel Rate'
            if tables:
                print(f"Found {len(tables)} table(s) on page {i}.")

                for table in tables:
                    # Basic safety checks
                    if not table or len(table) <= 2 or not table[0] or len(table[0]) <= 2:
                        continue

                    # Clean the table data
                    cleaned_table = []
                    for row in table:
                        cleaned_row = [
                            cell.replace("\n", " ").strip() if cell else ""
                            for cell in row
                        ]
                        # Only add rows with some content
                        if any(cell for cell in cleaned_row):
                            cleaned_table.append(cleaned_row)

                    if detect_matrix_header(cleaned_table, i):
                        extract_matrix_data(
                            cleaned_table=cleaned_table,
                            bpd_ranges=bpd_ranges,
                            unpivoted_data=unpivoted_data,
                            pipeline_name=pipeline_name,
                            origin="",
                            destination="",
                            effective_date=effective_date,
                            expiry_date=expiry_date_value,
                            rate_tier=rate_tier,
                            rate_type=tariff_rate_type,
                            bpd=bpd_ranges,
                            rate=""
                        )
                    
                

                     
            if unpivoted_data:
                df_final = unpivoted_data
        
        tariff_rate_type = ""  # Reset for next page
        return df_final
    
    except Exception as ex:
        print(ex)
    

def start_extraction():
    try:
        # --- Execution ---
        file_name = os.getenv("PDF_FILE_NAME")
        
        with pdfplumber.open(file_name) as pdf:
            
            tariff_data = []
            data = verify_tables(pdf,2,15)
            tariff_data.extend(data)

            final_data = pd.DataFrame(tariff_data)

            if final_data is not None and len(final_data) > 0:

                # Export to CSV
                output_file = "sample_tariff_data_v4.csv"
                final_data.to_csv(output_file, index=False)
                print(f"\nData successfully exported to {output_file}")
            else:
                print("\nFailed to extract table data.")

    except Exception as e:
        print(e)
