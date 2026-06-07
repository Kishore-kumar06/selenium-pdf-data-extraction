import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
from utils.helpers import load_pdf_files
from ..pdf_helpers.data_extraction_helper import PDFHelpers    
from ..pdf_helpers.data_lookup import DataLookup
from ..pdf_helpers.table_header_detecter import TableHeaderHelper


def normalize_row(row):
    return [DataLookup.normalize_exact_header_cell(col) for col in row]

def is_rate(value):
    """
    Accept:
    184.24
    250
    [I] 184.24
    [U] 250.55
    """
    value = DataLookup.clean(value)
    value = re.sub(r"\[[A-Z]\]", "", value).strip()
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", value))



def is_origin_header(value):
    value = DataLookup.normalize_header_cell(value)
    return (
        value.startswith("origin point")
        or value.startswith("origin")
        or value.startswith("origins")
        or value.startswith("from")
        or value.startswith("from:")
        or value.startswith("origin(s)")
        or value.startswith("receipt")
    )

def is_destination_header(value):
    value = DataLookup.normalize_header_cell(value)
    return(
        value.startswith("destination point")
        or value.startswith("destination")
        or value.startswith("destination(s)")
        or value.startswith("destinations")
        or value.startswith("destination-dest")
        or value.startswith("delivery/destination")
        or value.startswith("to")
    )

def is_rate_header(value):
    value = DataLookup.normalize_header_cell(value)
    return (
        value.startswith("uncommitted")
        or value.startswith("committed")
        or value.startswith("maximum")
        or value.startswith("volume")
        or value.startswith("rate")
        or value.startswith("rates")
        or value.startswith("rate:(2)")
        or value.startswith("base")
        or value.startswith("interstate")
        or value.startswith("joint")
        or value.startswith("non-anchor")
        or value.startswith("incentive")
        or value.startswith("contract")
        or value.startswith("for")
        or value.startswith("DESTINATION –")
        or value.startswith("long")
        or value.startswith("anchor")
        or value.startswith("pla")
    )

def is_volume_tier_header(value):
    value = DataLookup.normalize_header_cell(value)
    return (
        value.startswith("total")
        or value.startswith("volume tier")
        or value.startswith("st")
        or value.startswith("minimum volume")
        or value.startswith("fixed volume")
        or value.startswith("actual shipments")
        or value.startswith("term")
        
    )
    # if value.startswith("volume tier") or value.startswith("total monthly") or value.startswith("st") or value.startswith("minimum volume") or value.startswith("fixed volume") or value.startswith("actual shipments"):
    #     return value



def find_expected_header(table):
    """
    Returns:
        {
            "origin_idx": int,
            "destination_idx": int,
            "rate_indices": list[int],
            "data_start_row": int,
            "has_item_col": bool,
            "has_volume_tier": bool,
        }
    or None
    """
    if not table:
        return None

    rows_to_check = min(7, len(table))

    header_found = False

    for row_idx in range(rows_to_check):
        row = table[row_idx]

        if len(row) == 2:
            continue

        if not row:
            continue

        row = [DataLookup.clean(cell) for cell in row]

        # first_col = row[0] if len(row) > 0 else ""

        # # Skip rows until expected origin-like header appears
        # if not header_found:
        #     if not is_origin_header(first_col):
        #         continue
        #     header_found = True

        # if header_found:

        has_item_col = len(row) > 0 and DataLookup.normalize_header_cell(row[0]) == "item"
        start_idx = 1 if has_item_col else 0

        origin_idx = None
        destination_idx = None
        rate_indices = []
        has_volume_tier = False

        for col_idx in range(start_idx, len(row)):
            if row[0].startswith('Gathering') or row[0].startswith('Cancels'):
                continue

            cell = row[col_idx]

            if is_origin_header(cell):
                origin_idx = col_idx
                print(origin_idx)
            elif is_destination_header(cell):
                destination_idx = col_idx
            elif is_volume_tier_header(cell):
                has_volume_tier = True
            elif is_rate_header(cell):
                print(cell)
                rate_indices.append(col_idx)

        if origin_idx is not None and destination_idx is not None and rate_indices:
            return {
                "origin_idx": origin_idx,
                "destination_idx": destination_idx,
                "rate_indices": rate_indices,
                "data_start_row": row_idx + 1,
                "has_item_col": has_item_col,
                "has_volume_tier": has_volume_tier,
            }

    return None


def is_continuation_table(table, header_info):
    """
    Decide whether current table is continuation of previous table.
    """
    if not table or not header_info:
        return False

    origin_idx = header_info["origin_idx"]
    destination_idx = header_info["destination_idx"]
    rate_indices = header_info["rate_indices"]

    for row in table[:3]:   # check only first few rows
        if not row:
            continue

        row = [DataLookup.clean(cell) for cell in row]
        max_idx = max([origin_idx, destination_idx] + rate_indices)

        if len(row) <= max_idx:
            continue

        origin = DataLookup.clean(row[origin_idx])
        destination = DataLookup.clean(row[destination_idx])

        # if any rate column has data, likely continuation
        for r_idx in rate_indices:
            rate_val = DataLookup.clean(row[r_idx]) if len(row) > r_idx else ""
            if rate_val and (origin or destination):
                return True
            if rate_val:
                return True

    return False


def split_rate_cell(rate_text):
    """
    Split a combined rate cell like:
    '[I] 203.87 1 [I] 220.14 2 [I] 244.64 3'
    into:
    ['[I] 203.87 1', '[I] 220.14 2', '[I] 244.64 3']
    """
    rate_text = DataLookup.clean(rate_text)

    # Match tokens like:
    # [I] 203.87 1
    # [U] 250.44 2
    # [N] 300 4
    pattern = r"\[[A-Z]\]\s*\d+(?:\.\d+)?(?:\s+\d+|\s+\([a-z]\))?"

    matches = re.findall(pattern, rate_text)
    return matches



def extract_destination_after_dash(value):
    value = DataLookup.clean(value)

    # Normalize dash types
    value = value.replace("–", "-").replace("—", "-")

    # Check if it starts with Destination
    if value.lower().startswith("destination"):
        parts = value.split("-", 1)  # split only on first dash
        if len(parts) > 1:
            return DataLookup.clean(parts[1])

    return value


def extract_data(pdf):
    pipeline_name = ""
    effective_date = ""
    rate_type = ""
    expiry_date_value = ""
    rate_tier = ""
    bpd_ranges = []
    unpivoted_data = []


    last_header_info = None

    pdf_helpers = PDFHelpers(pdf=pdf, pipeline_name="", effective_date="", text="")
    pipeline_name = pdf_helpers.extract_pipelinename_metadata()
    effective_date = pdf_helpers.extract_effectivedate_metadata()

    print(f"Extracted Pipeline Name: {pipeline_name}")
    print(f"Extracted Effective Date: {effective_date}")

    # Works whether PDF has 1 page or 100 pages
    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        
        try:
            tariff_rate_type = ""
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
        

        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            if not table:
                continue

            cleaned_table = []
            for row in table:
                # if '\n' in str(row[0]):
                #     origin_parts = str(row[0]).split('\n')

                #     total_rows = len(origin_parts)
                #     for i in range(0, total_rows):
                #         if i == 0:
                #             row[0] = origin_parts[0]
                #         else:
                #             new_row = row.copy()
                #             new_row[0] = origin_parts[i]
                #             cleaned_table.append([DataLookup.clean(cell) for cell in new_row])
                
                # if '\n' in str(row[1]):
                #     destination_parts = str(row[1]).split('\n')

                #     total_rows = len(destination_parts)
                #     for i in range(0, total_rows):
                #         if i == 0:
                #             row[1] = destination_parts[0]
                #         else:
                #             new_row = row.copy()
                #             new_row[1] = destination_parts[i]
                #             cleaned_table.append([DataLookup.clean(cell) for cell in new_row])

                if row:
                    cleaned_table.append([DataLookup.clean(cell) for cell in row])

            if not cleaned_table:
                continue

            # 1. Try detecting fresh header in current table
            header_info = find_expected_header(cleaned_table)

            # 2. If no header, try using previous page's header as continuation
            if header_info:
                active_header = header_info
                last_header_info = header_info
            elif last_header_info and is_continuation_table(cleaned_table, last_header_info):
                active_header = dict(last_header_info)
                active_header["data_start_row"] = 0   # whole table is data
            else:
                continue

            origin_idx = active_header["origin_idx"]
            destination_idx = active_header["destination_idx"]
            rate_indices = active_header["rate_indices"]
            data_start_row = active_header["data_start_row"]

            last_origin = ""
            last_destination = ""
            last_rate = ""

            # only for single-rate-column duplicate control
            seen_single_rate_rows = set()
            
            for row in cleaned_table[data_start_row:]:
                if len(row) > 1 and str(row[-2]).startswith("Minimum"):
                    rate_indices = [4]

                max_idx = max([origin_idx, destination_idx] + rate_indices)
                if len(row) <= max_idx:
                    continue

                origin = DataLookup.clean(row[origin_idx]) if len(row) > origin_idx else ""
                destination = DataLookup.clean(row[destination_idx]) if len(row) > destination_idx else ""
                raw_rates = [DataLookup.clean(row[idx]) if len(row) > idx else "" for idx in rate_indices]

                # skip fully empty rows
                if not origin and not destination and not any(raw_rates):
                    continue

                last_cell = row[-1]
                last_cell_before = row[-2]

                if len(row) > 3:
                    if row[-3] == 'For all barrels' and last_cell == 'For all barrels' and last_cell_before == 'For all barrels':
                        continue

                    if last_cell == '' and last_cell_before == '':
                        continue

                # carry forward origin / destination
                if origin:
                    last_origin = origin
                else:
                    origin = last_origin
                
                if destination:
                    last_destination = destination
                else:
                    destination = last_destination

                rates_to_process = []

                # -------------------------------------------------
                # CASE 1: only one rate column -> eliminate duplicates
                # -------------------------------------------------
                if len(rate_indices) == 1:
                    current_rate = raw_rates[0]

                    if current_rate:
                        last_rate = current_rate
                    else:
                        current_rate = last_rate

                    if current_rate:
                        split_rates = split_rate_cell(current_rate)

                        if split_rates:
                            for bpd in bpd_ranges:
                                for single_rate in split_rates:
                                    
                                    dedupe_key = (page_num, origin, destination, single_rate)
                                    if dedupe_key not in seen_single_rate_rows:
                                        seen_single_rate_rows.add(dedupe_key)
                                        unpivoted_data.append(
                                            {
                                                # "Pipeline Name": pipeline_name,
                                                # "EffectiveDate": effective_date,
                                                # "Page": page_num,
                                                # "PointOfOrigin": origin,
                                                # "PointOfDestination": destination,
                                                # "LiquidRateCentsPerBbl": single_rate,

                                                "Pipeline Name": pipeline_name,
                                                "PointOfOrigin": origin,
                                                "PointOfDestination": destination,
                                                "LiquidTariffNumber": "",
                                                "Effective Date": effective_date,
                                                "End Date": expiry_date_value,
                                                "TariffStatus": "Effective",
                                                "RateTier": rate_tier,
                                                "RateType": rate_type,
                                                "TermYear": "",
                                                "MinBPD": bpd.get("MinBPD", ""),
                                                "MaxBPD": bpd.get("MaxBPD", ""),
                                                "AcreageDedicationMinAcres": "",
                                                "AcreageDedicationMaxAcres": "",
                                                "LiquidRateCentsPerBbl": single_rate,
                                                "SurchargeCentsPerBbl": "",
                                                "LiquidFuelType": "Crude",

                                                
                                            }
                                        )
                        elif current_rate:
                            for bpd in bpd_ranges:
                                dedupe_key = (page_num, origin, destination, current_rate)
                                if dedupe_key not in seen_single_rate_rows:
                                    seen_single_rate_rows.add(dedupe_key)
                                    unpivoted_data.append(
                                        {
                                            # "Pipeline Name": pipeline_name,
                                            # "EffectiveDate": effective_date,
                                            # "Page": page_num,
                                            # "PointOfOrigin": origin,
                                            # "PointOfDestination": destination,
                                            # "LiquidRateCentsPerBbl": current_rate,

                                            "Pipeline Name": pipeline_name,
                                            "PointfOrigin": origin,
                                            "PointOfDestination": destination,
                                            "LiquidTariffNumber": "",
                                            "Effective Date": effective_date,
                                            "End Date": expiry_date_value,
                                            "TariffStatus": "Effective",
                                            "RateTier": rate_tier,
                                            "RateType": rate_type,
                                            "TermYear": "",
                                            "MinBPD": bpd.get("MinBPD", ""),
                                            "MaxBPD": bpd.get("MaxBPD", ""),
                                            "AcreageDedicationMinAcres": "",
                                            "AcreageDedicationMaxAcres": "",
                                            "LiquidRateCentsPerBbl": current_rate,
                                            "SurchargeCentsPerBbl": "",
                                            "LiquidFuelType": "Crude",
                                        }
                                    )

                # -------------------------------------------------
                # CASE 2: multiple rate columns -> keep duplicates
                # -------------------------------------------------
                else:
                    for bpd in bpd_ranges:
                        for rate_val in raw_rates:
                            if not rate_val:
                                continue

                            split_rates = split_rate_cell(rate_val)

                            if split_rates:
                                for single_rate in split_rates:
                                    unpivoted_data.append(
                                        {
                                            # "Pipeline Name": pipeline_name,
                                            # "EffectiveDate": effective_date,
                                            # "Page": page_num,
                                            # "PointOfOrigin": origin,
                                            # "PointOfDestination": destination,
                                            # "LiquidRateCentsPerBbl": single_rate,

                                            "Pipeline Name": pipeline_name,
                                            "PointfOrigin": origin,
                                            "PointOfDestination": destination,
                                            "LiquidTariffNumber": "",
                                            "Effective Date": effective_date,
                                            "End Date": expiry_date_value,
                                            "TariffStatus": "Effective",
                                            "RateTier": rate_tier,
                                            "RateType": rate_type,
                                            "TermYear": "",
                                            "MinBPD": bpd.get("MinBPD", ""),
                                            "MaxBPD": bpd.get("MaxBPD", ""),
                                            "AcreageDedicationMinAcres": "",
                                            "AcreageDedicationMaxAcres": "",
                                            "LiquidRateCentsPerBbl": single_rate,
                                            "SurchargeCentsPerBbl": "",
                                            "LiquidFuelType": "Crude",
                                        }
                                    )
                            elif rate_val:
                                unpivoted_data.append(
                                    {
                                        # "Pipeline Name": pipeline_name,
                                        # "EffectiveDate": effective_date,
                                        # "Page": page_num,
                                        # "PointOfOrigin": origin,
                                        # "PointOfDestination": destination,
                                        # "LiquidRateCentsPerBbl": rate_val,

                                        "Pipeline Name": pipeline_name,
                                        "PointfOrigin": origin,
                                        "PointOfDestination": destination,
                                        "LiquidTariffNumber": "",
                                        "Effective Date": effective_date,
                                        "End Date": expiry_date_value,
                                        "TariffStatus": "Effective",
                                        "RateTier": rate_tier,
                                        "RateType": rate_type,
                                        "TermYear": "",
                                        "MinBPD": bpd.get("MinBPD", ""),
                                        "MaxBPD": bpd.get("MaxBPD", ""),
                                        "AcreageDedicationMinAcres": "",
                                        "AcreageDedicationMaxAcres": "",
                                        "LiquidRateCentsPerBbl": rate_val,
                                        "SurchargeCentsPerBbl": "",
                                        "LiquidFuelType": "Crude",
                                }
                                )

    return unpivoted_data



            
# --- Execution ---
# file_name = r"D:\Project\python_freelance_project\reference_files\GasTariffSource\OilTariffFiles\Pony Express Pipeline.PDF"

def extract():
    start = datetime.now()
    curr_path = os.getcwd()
    tariff_data = []
    # file_path = askopenfilename()
    # print(file_path)
    pdf_file = load_pdf_files()
    for file in pdf_file:
        input_file = os.path.basename(file).replace('.PDF','_v1.csv').replace('.pdf', '_v1.csv')

        with pdfplumber.open(file) as pdf:
            data = extract_data(pdf)
            tariff_data.extend(data)
            final_data = pd.DataFrame(tariff_data)

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
        