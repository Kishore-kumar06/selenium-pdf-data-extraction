import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime
import tkinter as tk
from tkinter.filedialog import askopenfilename

# root = tk.Tk()
# root.withdraw()

def get_transformed_files(curr_path):
    try:
        transformed_files_path = os.path.join(curr_path, 'input_data_files_page6')

        for root, dirs, files in os.walk(transformed_files_path):
            for file in files:
                full_path = os.path.join(root, file)
                yield full_path

    except Exception as er:
        print(f"An error occurred while fetching transformed files: {er}")


def extract_pipelinename_metadata(pdf):
    pipeline_name = ""

    page1_text = pdf.pages[0].extract_text()
    lines = [line.strip() for line in page1_text.splitlines() if line.strip()]

    suffix_pattern = r"(?:LLC|LP|L\.P\.?|L\.L\.C\.?|Inc|INC|Ltd|COMPANY)"
    
    full_pipeline_pattern = re.compile(
        rf"^.*(?:Pipeline)?.*{suffix_pattern}\.?$",
        re.IGNORECASE
    )

    continuation_pattern = re.compile(
        rf"^(?:PIPELINE,\s+)?{suffix_pattern}\.?$",
        re.IGNORECASE
    )

    for i, line in enumerate(lines):
        clean_line = re.sub(r"\s+", " ", line).strip().replace('"', '')

        if full_pipeline_pattern.search(clean_line):
            # If current line is only continuation like "PIPELINE L.L.C" or "L.L.C"
            # merge with previous line
            if continuation_pattern.search(clean_line) and i > 0:
                prev_line = re.sub(r"\s+", " ", lines[i - 1]).strip().replace('"', '')
                pipeline_name = f"{prev_line} {clean_line}"
            else:
                pipeline_name = clean_line
            break

    return pipeline_name



def extract_effectivedate_metadata(pdf):
    effective_date = ""

    page1_text = pdf.pages[0].extract_text()

    match_effective = re.search(r"\bEffective(?:\s+Date)?\b\s*:?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",page1_text,re.IGNORECASE)
    if match_effective:
        effective_date = match_effective.group(1)
    # Convert to datetime
    dt_obj = datetime.strptime(effective_date, "%B %d, %Y")

        # Convert to DD-MM-YYYY
    effective_date = dt_obj.strftime("%d-%m-%Y")

    return effective_date


def extract_tariff_rate_type(text):
    try:
        text_clean = text.replace("\r", "")
        lines = text_clean.split("\n")

        tariff_lines = []
        capture = False

        for i, line in enumerate(lines):

            clean_line = line.strip()

            # Condition:
            # 1. Line must contain RATES
            # 2. Line must be fully uppercase
            if "RATES" in clean_line:

                tariff_lines.append(clean_line)
                # Capture next uppercase lines (header continuation)
                for j in range(1, 3):
                    if i + j < len(lines):
                        next_line = lines[i + j].strip()
                        if next_line and next_line.isupper():
                            tariff_lines.append(next_line)
                        else:
                            break

                break  # Stop after first valid header
            else:
                continue

        if tariff_lines != "":   
            tariff_rate_type = " ".join(tariff_lines)
            return tariff_rate_type.strip()
        else:
            return None

    except Exception as e:
        print(f"Error extracting tariff rate type: {e}")
        return ""
    

def extract_expiry_date(text):
    try:

        expiry_date = ""

        expiry_match = re.search(
            r"expire[s]?\s+on.*?([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})",
            text,
            re.IGNORECASE
        )

        if expiry_match:
            raw_date = expiry_match.group(1).strip()

            # Convert to datetime
            dt_obj = datetime.strptime(raw_date, "%B %d, %Y")

            # Convert to DD-MM-YYYY
            expiry_date = dt_obj.strftime("%d-%m-%Y")

        if expiry_date:
            return expiry_date
        else:
            return ""

    except Exception as e:
        print(f"Error extracting expiry date: {e}")
        return ""


def parse_volume_to_minmax(volume_text: str):
    """
    Convert volume strings like:
      - "10,000 BPD"
      - "3,000 – 4,999 BPD"
      - "0 – 15,000 BPD"
      - "13,000 bpd or greater"
    into (MinBPD, MaxBPD).
    """
    if not volume_text:
        return ("", "")

    t = volume_text.replace("–", "-").replace("—", "-")
    t_low = t.lower()

    # Range: 3,000 - 4,999 BPD
    m = re.search(r"(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*bpd", t_low)
    if m:
        min_bpd = int(m.group(1).replace(",", ""))
        max_bpd = int(m.group(2).replace(",", ""))
        return (min_bpd, max_bpd)

    # Or greater: 13,000 bpd or greater  OR  13,000 or greater bpd
    m = re.search(r"(\d{1,3}(?:,\d{3})*)\s*bpd\s*or\s*greater", t_low)
    if not m:
        m = re.search(r"(\d{1,3}(?:,\d{3})*)\s*or\s*greater\s*bpd", t_low)
    if m:
        min_bpd = int(m.group(1).replace(",", ""))
        return (min_bpd, None)

    # Single: 10,000 BPD
    m = re.search(r"(\d{1,3}(?:,\d{3})*)\s*bpd", t_low)
    if m:
        min_bpd = int(m.group(1).replace(",", ""))
        return (min_bpd, min_bpd)

    return ("", "")


def extract_bpd_ranges(text):
    try:
        results = []

        # Normalize text (remove weird PDF chars)
        text = text.replace("–", "-").replace("—", "-")

        # Pattern 1: Range (5,000 - 11,999 BPD)
        range_pattern = r"(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*BPD"

        # Pattern 2: 13,000 BPD or greater
        greater_pattern_1 = r"(\d{1,3}(?:,\d{3})*)\s*BPD\s*or\s*greater"

        # Pattern 3: 13,000 or greater BPD
        greater_pattern_2 = r"(\d{1,3}(?:,\d{3})*)\s*or\s*greater\s*BPD"

        # Extract ranges
        for min_bpd, max_bpd in re.findall(range_pattern, text, re.IGNORECASE):
            results.append({
                "MinBPD": int(min_bpd.replace(",", "")),
                "MaxBPD": int(max_bpd.replace(",", ""))
            })

        # Extract "or greater"
        greater_matches = re.findall(greater_pattern_1, text, re.IGNORECASE)
        greater_matches += re.findall(greater_pattern_2, text, re.IGNORECASE)

        for min_bpd in greater_matches:
            results.append({
                "MinBPD": int(min_bpd.replace(",", "")),
                "MaxBPD": None
            })

        return results if results else []

    except Exception as e:
        print(f"Error extracting BPD ranges: {e}")
        return []


def extract_rate_tiers(text):
    try:
        pattern = r"\b(?:Rate\s*Tier|Tier)\s*(\d+|[IVXLC]+)\b"

        matches = re.findall(pattern, text, re.IGNORECASE)

        if not matches:
            return None

        cleaned_tiers = []

        for tier_value in matches:
            tier_value = tier_value.strip()
            cleaned_tiers.append(f"Rate Tier {tier_value}")

        # Remove duplicates while preserving order
        cleaned_tiers = list(dict.fromkeys(cleaned_tiers))

        if cleaned_tiers and len(cleaned_tiers) > 0:
            return cleaned_tiers
        else:
            return None

    except Exception as e:
        print(f"Error extracting rate tiers: {e}")
        return ""
    


# def clean(text):
#     if text:
#         return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
#     return ""


def is_rate(value):
    if not value:
        return False
    return bool(re.fullmatch(r"\d+\.\d+", value.strip()))


def clean(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()

def normalize_exact_header_cell(value):
    """
    Normalize header cell for exact EXPECTED_HEADERS comparison.
    Keeps words intact, but standardizes spaces/newlines.
    """
    value = "" if value is None else str(value)
    value = value.replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)      # multiple spaces -> single space
    value = re.sub(r"\n+", "\n", value)        # multiple newlines -> single newline
    value = re.sub(r"\(\d+\)", "", value)  # remove (1) (2) etc
    value = value.replace(":", "")         # remove :
    return value.strip()

def normalize_row(row):
    return [normalize_exact_header_cell(col) for col in row]

def is_rate(value):
    """
    Accept:
    184.24
    250
    [I] 184.24
    [U] 250.55
    """
    value = clean(value)
    value = re.sub(r"\[[A-Z]\]", "", value).strip()
    return bool(re.fullmatch(r"\d+(?:\.\d+)?", value))


EXPECTED_HEADERS = [
    ["From"],
    ["FROM"],
    ["FROM:"],
    ["Origin"],
    ["ORIGIN"],
    ["From"],
    ["From"],
    ["FROM"],
    ["FROM"],
    ["FROM"],
    ["From"],
    ["ORIGIN(S)"],
    ["ORIGIN(S)"],
    ["ORIGINS"],
    ["RECEIPT POINTS/ORIGIN"],
    ["FROM Origin Point(s)"],
    ["ORIGIN"],
    ["FROM (Origin)"],
    ["From (Origin)"],
    ["FROM"],
    ["FROM"],
    ["From"],
    ["FROM"],
    ["Origin Point"],
    ["TO: (Destination)"]
]

# def find_expected_header(table):
#     """
#     Identify expected header row and return column indices.
    
#     Returns:
#         (origin_idx, destination_idx, rate_idx, data_start_row)
#     or
#         (None, None, None, None)
#     """

#     if not table:
#         return None, None, None, None

#     rows_to_check = min(3, len(table))

#     for row_idx in range(rows_to_check):

#         row = table[row_idx]

#         if not row or len(row) < 3:
#             continue

#         # Clean header row values
#         row = [clean(cell) for cell in row]

       
#         # Case 1: table has "Item" column
#         if row[0].strip().lower().endswith("item") or row[0].strip().lower().startswith("table"):

#             if len(row) < 4:
#                 continue
#             first_three = row[1:2]
#             expected_index = (1, 2, 3, row_idx + 1)
#         # Case 2: normal header
#         elif row[0] == '':
#             first_three = row[1:2]
#             expected_index = (0, 3, 7, row_idx + 1)
#         elif row[2].startswith('VOLUME'):
#             first_three = row[:1]
#             expected_index = (0, 1, 3, row_idx + 1)
#         else:
#             first_three = row[:1]
#             expected_index = (0, 1, 2, row_idx + 1)

#         # Compare with expected headers
#         for expected in EXPECTED_HEADERS:
#             if first_three == expected:
#                 return expected_index

#     return None, None, None, None




def normalize_header_cell(value):
    value = clean(value).lower()
    value = value.replace(":", "")
    value = re.sub(r"\(\d+\)", "", value)   # remove (1), (2)
    if value.startswith('[w]') or value.startswith('[n]'):
        value = value.replace('[w]','').replace('[n]','').strip()
    value = re.sub(r"\s+", " ", value).strip()
    return value

def is_origin_header(value):
    value = normalize_header_cell(value)
    return (
        value.startswith("origin point")
        or value.startswith("origin")
        or value.startswith("from")
    )

def is_destination_header(value):
    value = normalize_header_cell(value)
    return(
        value.startswith("destination point")
        or value.startswith("destination")
        or value.startswith("to")
    )

def is_rate_header(value):
    value = normalize_header_cell(value)
    return (
        value.startswith("uncommitted")
        or value.startswith("committed")
        or value.startswith("maximum")
        or value.startswith("volume")
        or value.startswith("rate")
        or value.startswith("base")
        or value.startswith("interstate")
    )

def is_volume_tier_header(value):
    value = normalize_header_cell(value)
    if value.startswith("volume tier") or value.startswith("fixed volume") or value.startswith("actual hipments"):
        return value

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

    rows_to_check = min(3, len(table))

    for row_idx in range(rows_to_check):
        row = table[row_idx]
        if not row:
            continue

        row = [clean(cell) for cell in row]

        has_item_col = len(row) > 0 and normalize_header_cell(row[0]) == "item"
        start_idx = 1 if has_item_col else 0

        origin_idx = None
        destination_idx = None
        rate_indices = []
        has_volume_tier = False

        for col_idx in range(start_idx, len(row)):
            if row[0].startswith('Gathering'):
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

        row = [clean(cell) for cell in row]
        max_idx = max([origin_idx, destination_idx] + rate_indices)

        if len(row) <= max_idx:
            continue

        origin = clean(row[origin_idx])
        destination = clean(row[destination_idx])

        # if any rate column has data, likely continuation
        for r_idx in rate_indices:
            rate_val = clean(row[r_idx]) if len(row) > r_idx else ""
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
    rate_text = clean(rate_text)

    # Match tokens like:
    # [I] 203.87 1
    # [U] 250.44 2
    # [N] 300 4
    pattern = r"\[[A-Z]\]\s*\d+(?:\.\d+)?(?:\s+\d+|\s+\([a-z]\))?"

    matches = re.findall(pattern, rate_text)
    return matches


def extract_data(pdf):
    unpivoted_data = []

    last_header_info = None

    pipeline_name = extract_pipelinename_metadata(pdf)
    effective_date = extract_effectivedate_metadata(pdf)

    # Works whether PDF has 1 page or 100 pages
    for page_num, page in enumerate(pdf.pages, start=1):
        text = page.extract_text()
        if not text:
            continue

        tables = page.extract_tables()
        if not tables:
            continue

        for table in tables:
            if not table:
                continue

            cleaned_table = []
            for row in table:
                if row:
                    cleaned_table.append([clean(cell) for cell in row])

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

            # Extract data rows only after matched header row
            for row in cleaned_table[data_start_row:]:
                max_idx = max([origin_idx, destination_idx] + rate_indices)
                if len(row) <= max_idx:
                    continue

                origin = clean(row[origin_idx])
                destination = clean(row[destination_idx])

                if origin:
                    last_origin = origin
                else:
                    origin = last_origin

                if destination:
                    last_destination = destination
                else:
                    destination = last_destination

                for rate_idx in rate_indices:
                    rate = clean(row[rate_idx]) if len(row) > rate_idx else ""
                    if not rate:
                        continue

                    # # Skip repeated header inside body
                    # if normalize_row([origin, destination, rate])[:3] in EXPECTED_HEADERS:
                    #     continue

                    
                    # rate = re.sub(r"\[[A-Z]\]", "", rate).strip()
                    # rate = rate

                    split_rates = split_rate_cell(rate)

                    # Case 1: combined multiple rates in one cell
                    if split_rates:
                        for single_rate in split_rates:
                            unpivoted_data.append(
                                {
                                    "Pipeline Name": pipeline_name,
                                    "EffectiveDate": effective_date,
                                    "Page": page_num,
                                    "PointOfOrigin": origin,
                                    "PointOfDestination": destination,
                                    "LiquidRateCentsPerBbl": single_rate,
                                }
                            )

                    # Case 2: normal single rate
                    elif rate:
                        unpivoted_data.append(
                            {
                                "Pipeline Name": pipeline_name,
                                "EffectiveDate": effective_date,
                                "Page": page_num,
                                "PointOfOrigin": origin,
                                "PointOfDestination": destination,
                                "LiquidRateCentsPerBbl": rate,
                            }
                        )

    return unpivoted_data


            
# --- Execution ---
# file_name = r"D:\Project\python_freelance_project\reference_files\GasTariffSource\OilTariffFiles\Pony Express Pipeline.PDF"

def extract():
    curr_path = os.getcwd()
    tariff_data = []
    # file_path = askopenfilename()
    # print(file_path)
    for file in get_transformed_files(curr_path):
        
        input_file = os.path.basename(file).replace('.PDF','.csv')

        with pdfplumber.open(file) as pdf:
            
            data = extract_data(pdf)
            tariff_data.extend(data)

            final_data = pd.DataFrame(tariff_data)

            if final_data is not None and len(final_data) > 0:

                # Export to CSV
                # output_csvfile = ''.join(input_file,'.csv')
                output_file = os.path.join('Page6_extracted_files', input_file)
                final_data.to_csv(output_file, index=False, encoding="utf-8")
                tariff_data.clear()
                # final_data.to_csv(output_file, index=False)
                print(f"\nData successfully exported to {input_file}")
            else:
                print(f"\nFailed to extract {input_file} table data.")
        


if __name__=="__main__":
    extract()