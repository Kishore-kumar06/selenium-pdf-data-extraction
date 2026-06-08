import os
import re

import re
from ..pdf_helpers.data_extraction_helper import PDFHelpers    
from ..pdf_helpers.data_lookup import DataLookup
from ..pdf_helpers.table_header_detecter import TableHeaderHelper



def find_expected_header(table):
    """
    Detect likely tariff-table header in the first few rows only.
    Skips unrelated tables by requiring both origin and destination headers and at least one rate header.
    """
    if not table:
        return None

    rows_to_check = min(4, len(table))

    for row_idx in range(rows_to_check):
        row = table[row_idx]
        if not row:
            continue

        row = [DataLookup.clean(cell) for cell in row]
        if len(row) < 2:
            continue

        # Skip broken rows only when both last two columns are blank
        if row[-1].strip() == "" and row[-2].strip() == "":
            continue

        first_cell = DataLookup.normalize_header_cell(row[0]) if row else ""
        if first_cell.startswith("gathering") or first_cell.startswith("cancels"):
            continue

        # User-requested header layout handling
        if (
            first_cell.endswith("item")
            or first_cell.startswith("table")
            or first_cell.startswith("route")
        ):
            if len(row) < 4:
                continue
            scan_indices = list(range(1, len(row)))
        elif row[0] == "":
            scan_indices = list(range(1, len(row)))
        else:
            scan_indices = list(range(len(row)))

        origin_idx = None
        destination_idx = None
        rate_indices = []
        has_volume_tier = False

        for col_idx in scan_indices:
            cell = row[col_idx]
            if TableHeaderHelper.is_origin_header(cell) and origin_idx is None:
                origin_idx = col_idx
            elif TableHeaderHelper.is_destination_header(cell) and destination_idx is None:
                destination_idx = col_idx
            elif TableHeaderHelper.is_volume_tier_header(cell):
                has_volume_tier = True
            elif TableHeaderHelper.is_rate_header(cell):
                rate_indices.append(col_idx)

        if origin_idx is not None and destination_idx is not None and rate_indices:
            return {
                "origin_idx": origin_idx,
                "destination_idx": destination_idx,
                "rate_indices": rate_indices,
                "data_start_row": row_idx + 1,
                "has_item_col": first_cell == "item",
                "has_volume_tier": has_volume_tier,
            }

    return None


# ------------------------------------------------------------
# Value helpers
# ------------------------------------------------------------
RATE_TOKEN_RE = re.compile(r"\[[A-Z]\]\s*\d+(?:\.\d+)?(?:\s+\d+|\s+\([a-z]\))?|N/?A|\d+(?:\.\d+)?", re.IGNORECASE)
NUMERIC_RATE_RE = re.compile(r"^(?:\[[A-Z]\]\s*)?\d+(?:\.\d+)?(?:\s+\d+|\s+\([a-z]\))?$|^N/?A$", re.IGNORECASE)
RATE_SUFFIX_RE = re.compile(r"^(.*?)(\[[A-Z]\]\s*\d+(?:\.\d+)?|N/?A|\d+(?:\.\d+)?)$", re.IGNORECASE)


def split_rate_cell(rate_text):
    rate_text = DataLookup.clean(rate_text)
    if not rate_text:
        return []
    bracketed = re.findall(r"\[[A-Z]\]\s*\d+(?:\.\d+)?(?:\s+\d+|\s+\([a-z]\))?", rate_text, re.IGNORECASE)
    if bracketed:
        return [DataLookup.clean(m) for m in bracketed]
    na_matches = re.findall(r"N/?A", rate_text, re.IGNORECASE)
    if na_matches:
        return [DataLookup.clean(m).upper() for m in na_matches]
    return [rate_text] if is_rate(rate_text) else []


def is_rate(value):
    return bool(NUMERIC_RATE_RE.match(DataLookup.clean(value)))


def extract_destination_after_dash(value):
    value = DataLookup.clean(value).replace("–", "-").replace("—", "-")
    if value.lower().startswith("destination"):
        parts = value.split("-", 1)
        if len(parts) > 1:
            return DataLookup.clean(parts[1])
    return value


def strip_page_number_tail(value):
    return re.sub(r"\s+\d+$", "", DataLookup.clean(value))


def split_multiple_origins(text):
    """
    Split packed origin text when multiple origins are printed continuously.
    Rules:
    - split on standalone 'or' / 'OR'
    - when multiple parenthetical locations are packed together, split by each '(...)' block
    """
    text = DataLookup.clean(text)
    if not text:
        return []

    parts = re.split(r"\s+\b(?:or|OR)\b\s+", text)
    results = []

    for part in parts:
        part = DataLookup.clean(part)
        if not part:
            continue

        paren_chunks = [DataLookup.clean(m) for m in re.findall(r"[^()]+?\([^()]+\)", part)]
        if len(paren_chunks) >= 2:
            results.extend(paren_chunks)
        else:
            results.append(part)

    cleaned_results = []
    for item in results:
        item = strip_page_number_tail(item)
        if item and item not in cleaned_results:
            cleaned_results.append(item)

    return cleaned_results


# ------------------------------------------------------------
# Word-line helpers
# ------------------------------------------------------------
def _cluster_words_to_lines(words, y_tolerance=3):
    words = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
    lines = []
    for word in words:
        if not lines or abs(word["top"] - lines[-1]["top"]) > y_tolerance:
            lines.append({"top": word["top"], "words": [word]})
        else:
            lines[-1]["words"].append(word)
    return lines


def _line_text(line):
    return " ".join(w["text"] for w in line["words"])


def _detect_header_lines(lines):
    header_indices = []
    for i, line in enumerate(lines):
        text_upper = _line_text(line).upper()
        if (("ORIGIN" in text_upper or "FROM" in text_upper) and ("DESTINATION" in text_upper or " TO " in f" {text_upper} ") and "RATE" in text_upper):
            header_indices.append(i)
    return header_indices


def _parse_single_rate_section_from_words(page, header_idx, next_header_idx=None):
    """
    Parse borderless 3-column layouts using x-position zones.
    Handles:
    - rows where county/state line comes after the rate line (Targa)
    - shared destination printed once for many origins (Texas Express)
    - many packed origins to one destination and one rate (Panola)
    """
    records = []
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    if not words:
        return records

    lines = _cluster_words_to_lines(words)
    header = lines[header_idx]
    header_words = header["words"]

    try:
        x_origin = min(w["x0"] for w in header_words if w["text"].upper().startswith(("ORIGIN", "FROM")))
        x_dest = min(w["x0"] for w in header_words if w["text"].upper().startswith(("DESTINATION", "TO")))
        rate_words = [
            w for w in header_words
            if ("RATE" in w["text"].upper() or "INTERSTATE" in w["text"].upper() or "BASE" in w["text"].upper() or "CONTRACT" in w["text"].upper())
        ]
        x_rate = max(w["x0"] for w in rate_words)
    except ValueError:
        return records

    split_origin_dest = (x_origin + x_dest) / 2
    split_dest_rate = (x_dest + x_rate) / 2

    stop_pattern = re.compile(r"Footnote|EXPLANATION|Subject to Rules|ITEM NO|ITEM \d+|Viscosity Fee|\*Applicable", re.IGNORECASE)
    skip_pattern = re.compile(r"Rates in Cents|In cents per Barrel|42 United States|42 U\.S\. Gallons|^\(Origin\)|^\(Destination\)|Local Rates|Joint Rates|Contract Rates", re.IGNORECASE)

    pending_origin_parts = []
    pending_destination_parts = []
    shared_destination_parts = []
    current_row = None

    end_idx = next_header_idx if next_header_idx is not None else len(lines)

    for line in lines[header_idx + 1:end_idx]:
        joined = _line_text(line).strip()
        if stop_pattern.search(joined):
            break
        if skip_pattern.search(joined):
            continue

        origin_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if w["x0"] < split_origin_dest))
        destination_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if split_origin_dest <= w["x0"] < split_dest_rate))
        rate_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if w["x0"] >= split_dest_rate))

        suffix_match = RATE_SUFFIX_RE.match(rate_text)
        if suffix_match and is_rate(suffix_match.group(2)):
            prefix = DataLookup.clean(suffix_match.group(1))
            if prefix:
                destination_text = DataLookup.clean(f"{destination_text} {prefix}")
            rate_text = DataLookup.clean(suffix_match.group(2))

        if not origin_text and not destination_text and not rate_text:
            continue

        if is_rate(rate_text):
            if current_row is not None:
                records.append(current_row)

            current_row = {
                "origin": DataLookup.clean(" ".join(pending_origin_parts + ([origin_text] if origin_text else []))),
                "destination": DataLookup.clean(" ".join(pending_destination_parts + ([destination_text] if destination_text else []))),
                "rate": rate_text,
            }
            pending_origin_parts = []
            pending_destination_parts = []
        else:
            if origin_text and destination_text:
                if current_row is not None:
                    current_row["origin"] = DataLookup.clean(f"{current_row['origin']} {origin_text}")
                    current_row["destination"] = DataLookup.clean(f"{current_row['destination']} {destination_text}")
                else:
                    pending_origin_parts.append(origin_text)
                    pending_destination_parts.append(destination_text)
            elif origin_text:
                if current_row is not None:
                    current_row["origin"] = DataLookup.clean(f"{current_row['origin']} {origin_text}")
                else:
                    pending_origin_parts.append(origin_text)
            elif destination_text:
                shared_destination_parts.append(destination_text)
                if current_row is not None:
                    current_row["destination"] = DataLookup.clean(f"{current_row['destination']} {destination_text}")
                else:
                    pending_destination_parts.append(destination_text)

    if current_row is not None:
        records.append(current_row)

    shared_destination = strip_page_number_tail(" ".join(shared_destination_parts))
    normalized_records = []
    for row in records:
        dest = strip_page_number_tail(row["destination"]) or shared_destination
        if row["origin"] and dest and row["rate"]:
            normalized_records.append({
                "origin": strip_page_number_tail(row["origin"]),
                "destination": dest,
                "rate": row["rate"],
            })

    return normalized_records


# ------------------------------------------------------------
# Specialized parsers for difficult PDFs
# ------------------------------------------------------------
def extract_midway_style_from_text(page_text, pipeline_name="", effective_date="", expiry_date_value="", rate_tier="", rate_type="", bpd=None, page_num=None):
    records = []
    if not page_text:
        return records

    text = re.sub(r"[ \t]+", " ", page_text)
    text = re.sub(r"\n+", "\n", text)

    block_pattern = re.compile(
        r"FROM.*?TO.*?RATE\s*RATE.*?\(1\)(.*?)Viscosity\s*Fee",
        re.IGNORECASE | re.DOTALL,
    )
    block_match = block_pattern.search(text)
    if not block_match:
        return records

    block = DataLookup.clean(block_match.group(1))
    rate_matches = re.findall(r"\[[A-Z]\]\s*\d+(?:\.\d+)?", block)
    if len(rate_matches) < 2:
        return records

    # Split origins around 'or' as requested
    origin_destination_text = block
    for rate in rate_matches:
        origin_destination_text = origin_destination_text.replace(rate, "")
    origin_destination_text = DataLookup.clean(origin_destination_text)

    # Heuristic: last Kansas segment is destination
    dest_match = re.search(r"(Broome Station, Coffeyville.*?Kansas)", origin_destination_text, re.IGNORECASE)
    if not dest_match:
        return records
    destination = DataLookup.clean(dest_match.group(1))
    origin_text = DataLookup.clean(origin_destination_text.replace(dest_match.group(1), ""))
    origin_list = split_multiple_origins(origin_text)

    for origin in origin_list:
        for rate in rate_matches:
            records.append(
                {
                    # "Pipeline Name": pipeline_name,
                    # "EffectiveDate": effective_date,
                    # "Page": page_num,
                    # "PointOfOrigin": origin,
                    # "PointOfDestination": destination,
                    # "LiquidRateCentsPerBbl": DataLookup.clean(rate),

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
                    "LiquidRateCentsPerBbl": DataLookup.clean(rate),
                    "SurchargeCentsPerBbl": "",
                    "LiquidFuelType": "Crude",
                }
            )
    return records


def extract_cheyenne_from_words(page, pipeline_name="", effective_date="", expiry_date_value="", rate_type="", rate_tier="", bpd=None, page_num=None):
    records = []
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    lines = _cluster_words_to_lines(words)

    origin = ""
    destination = ""
    rates = []
    saw_header = False

    for line in lines:
        text = _line_text(line)
        upper = text.upper()
        if "ORIGIN" in upper and "DESTINATION" in upper and "CONTRACT" in upper:
            saw_header = True
            continue
        if not saw_header:
            continue
        if upper.startswith("ROUTING"):
            break

        rate_matches = re.findall(r"\[[A-Z]\]\s*\d+(?:\.\d+)?", text)
        if rate_matches:
            rates.extend(DataLookup.clean(r) for r in rate_matches)

        # Look for the actual origin/destination row
        if "Wyoming" in text and text.count("Wyoming") >= 2 and "Platte Station" in text and "Cheyenne" in text:
            match = re.match(r"(Platte Station, Guernsey, Wyoming)\s+(Cheyenne, Wyoming)", DataLookup.clean(text))
            if match:
                origin = DataLookup.clean(match.group(1))
                destination = DataLookup.clean(match.group(2))

    if origin and destination and rates:
        for rate in rates:
            records.append(
                {
                    # "Pipeline Name": pipeline_name,
                    # "EffectiveDate": effective_date,
                    # "Page": page_num,
                    # "PointOfOrigin": origin,
                    # "PointOfDestination": destination,
                    # "LiquidRateCentsPerBbl": rate,

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
                    "LiquidRateCentsPerBbl": rate,
                    "SurchargeCentsPerBbl": "",
                    "LiquidFuelType": "Crude",
                }
            )
    return records


def extract_diamond_from_words(page, pipeline_name="", effective_date="", expiry_date_value="", rate_type="", rate_tier="", bpd=None, page_num=None):
    records = []
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    lines = _cluster_words_to_lines(words)

    # Column positions from the visual header line on this tariff layout
    split_origin_dest = (113 + 240) / 2
    split_dest_base = (240 + 318) / 2
    split_base_contract = (318 + 448) / 2

    origins = []
    dest_parts = []
    base_rates = []
    contract_rates = []
    capture = False

    for line in lines:
        text = _line_text(line)
        upper = text.upper()
        if "FROM" in upper and "TO" in upper and "BASE RATE" in upper:
            capture = True
            continue
        if not capture:
            continue
        if upper.startswith("NOTE 1"):
            break

        origin_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if w["x0"] < split_origin_dest))
        dest_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if split_origin_dest <= w["x0"] < split_dest_base))
        base_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if split_dest_base <= w["x0"] < split_base_contract))
        contract_text = DataLookup.clean(" ".join(w["text"] for w in line["words"] if w["x0"] >= split_base_contract))

        if origin_text and origin_text not in {"FROM", "TO"}:
            origins.append(origin_text)
        if dest_text and dest_text not in {"TO"}:
            dest_parts.append(dest_text)

        for token in split_rate_cell(base_text):
            if is_rate(token):
                base_rates.append(token)
        for token in split_rate_cell(contract_text):
            if is_rate(token):
                contract_rates.append(token)

    destination = DataLookup.clean(" ".join([p for p in dest_parts if p not in {"Memphis,"} or True]))
    if destination:
        destination = destination.replace("Memphis, Shelby County, Tennessee", "Memphis, Shelby County, Tennessee")
    if not destination:
        destination = "Memphis, Shelby County, Tennessee"

    # remove header noise
    origins = [o for o in origins if o not in {"FROM", "TO"}]

    if origins:
        # Base rate for each origin in order found
        for origin, rate in zip(origins, base_rates):
            records.append(
                {
                    # "Pipeline Name": pipeline_name,
                    # "EffectiveDate": effective_date,
                    # "Page": page_num,
                    # "PointOfOrigin": origin,
                    # "PointOfDestination": destination,
                    # "LiquidRateCentsPerBbl": rate,

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
                    "LiquidRateCentsPerBbl": rate,
                    "SurchargeCentsPerBbl": "",
                    "LiquidFuelType": "Crude",

                }
            )

        # Contract rates apply to first origin only on this tariff page
        first_origin = origins[0]
        for rate in contract_rates:
            records.append(
                {
                    # "Pipeline Name": pipeline_name,
                    # "EffectiveDate": effective_date,
                    # "Page": page_num,
                    # "PointOfOrigin": first_origin,
                    # "PointOfDestination": destination,
                    # "LiquidRateCentsPerBbl": rate,

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
                    "LiquidRateCentsPerBbl": rate,
                    "SurchargeCentsPerBbl": "",
                    "LiquidFuelType": "Crude",

                    
                }
            )
    return records


def extract_generic_word_sections(page, pipeline_name="", effective_date="", expiry_date_value="", rate_tier="", rate_type="", bpd=None, page_num=None, split_origins=False):
    records = []
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    if not words:
        return records
    lines = _cluster_words_to_lines(words)
    header_indices = _detect_header_lines(lines)
    if not header_indices:
        return records

    for idx, header_idx in enumerate(header_indices):
        next_idx = header_indices[idx + 1] if idx + 1 < len(header_indices) else None
        section_rows = _parse_single_rate_section_from_words(page, header_idx, next_idx)
        for row in section_rows:
            origin_values = split_multiple_origins(row["origin"]) if split_origins else [row["origin"]]
            for origin in origin_values:
                records.append(
                    {
                        # "Pipeline Name": pipeline_name,
                        # "EffectiveDate": effective_date,
                        # "Page": page_num,
                        # "PointOfOrigin": origin,
                        # "PointOfDestination": extract_destination_after_dash(row["destination"]),
                        # "LiquidRateCentsPerBbl": row["rate"],

                        "Pipeline Name": pipeline_name,
                        "PointOfOrigin": origin,
                        "PointOfDestination": extract_destination_after_dash(row["destination"]),
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
                        "LiquidRateCentsPerBbl": row["rate"],
                        "SurchargeCentsPerBbl": "",
                        "LiquidFuelType": "Crude",
                    }
                )
    return records


def extract_midway_from_words(page, pipeline_name="", effective_date="", expiry_date_value="", rate_tier="", rate_type="", bpd=None, page_num=None):
    records = []
    page_text = page.extract_text() or ""
    lines = [DataLookup.clean(line) for line in page_text.splitlines() if DataLookup.clean(line)]

    capture = False
    block_lines = []
    for line in lines:
        upper = line.upper()
        if upper == "FROM TO" or ("FROM" in upper and "TO" in upper and "RATE" in upper):
            capture = True
            continue
        if not capture:
            continue
        if upper.startswith("(1)") or upper.startswith("VISCOSITY FEE"):
            break
        if upper in {"BASE CONTRACT", "RATE RATE (1)", "ALL RATES IN CENTS PER BARREL OF 42 UNITED STATES GALLONS", "LIST OF POINTS FROM AND TO WHICH RATES APPLY AND RATES"}:
            continue
        block_lines.append(line)

    if not block_lines:
        return records

    rates = []
    destination_parts = []
    origin_parts = []

    for line in block_lines:
        rate_tokens = re.findall(r"\[[A-Z]\]\s*\d+(?:\.\d+)?", line)
        cleaned_line = line
        for token in rate_tokens:
            cleaned_line = cleaned_line.replace(token, " ")
        cleaned_line = DataLookup.clean(cleaned_line)
        if rate_tokens:
            rates.extend(rate_tokens)

        if not cleaned_line:
            continue

        if cleaned_line.lower() == "or" or "cushing terminal" in cleaned_line.lower() or "osage station" in cleaned_line.lower() or "osage county" in cleaned_line.lower() or "lincoln county" in cleaned_line.lower():
            origin_parts.append(cleaned_line)
        elif "broome station" in cleaned_line.lower() or "montgomery county" in cleaned_line.lower() or cleaned_line.lower() == "kansas":
            destination_parts.append(cleaned_line)

    destination = DataLookup.clean(" ".join(destination_parts))
    origins = split_multiple_origins(DataLookup.clean(" ".join(origin_parts)))

    for origin in origins:
        for rate in rates:
            records.append({
                # "Pipeline Name": pipeline_name,
                # "EffectiveDate": effective_date,
                # "Page": page_num,
                # "PointOfOrigin": origin,
                # "PointOfDestination": destination,
                # "LiquidRateCentsPerBbl": DataLookup.clean(rate),

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
                "LiquidRateCentsPerBbl": DataLookup.clean(rate),
                "SurchargeCentsPerBbl": "",
                "LiquidFuelType": "Crude",
            })
    return records


# ------------------------------------------------------------
# Table extraction (keeps existing logic, but cleaner)
# ------------------------------------------------------------
def is_continuation_table(table, header_info):
    if not table or not header_info:
        return False

    origin_idx = header_info["origin_idx"]
    destination_idx = header_info["destination_idx"]
    rate_indices = header_info["rate_indices"]

    for row in table[:3]:
        if not row:
            continue
        row = [DataLookup.clean(cell) for cell in row]
        max_idx = max([origin_idx, destination_idx] + rate_indices)
        if len(row) <= max_idx:
            continue

        origin = DataLookup.clean(row[origin_idx])
        destination = DataLookup.clean(row[destination_idx])
        for r_idx in rate_indices:
            rate_val = DataLookup.clean(row[r_idx]) if len(row) > r_idx else ""
            if rate_val and (origin or destination):
                return True
    return False


def extract_from_tables(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd, page_num, last_header_info=None):
    unpivoted_data = []
    tables = page.extract_tables() or []
    if not tables:
        return unpivoted_data, last_header_info

    for table in tables:
            if not table:
                continue

            cleaned_table = []
            for row in table:
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
                                        "LiquidRateCentsPerBbl": current_rate,
                                        "SurchargeCentsPerBbl": "",
                                        "LiquidFuelType": "Crude",
                                    }
                                )

                # -------------------------------------------------
                # CASE 2: multiple rate columns -> keep duplicates
                # -------------------------------------------------
                else:
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
                                    "LiquidRateCentsPerBbl": rate_val,
                                    "SurchargeCentsPerBbl": "",
                                    "LiquidFuelType": "Crude",
                                }
                            )

    return unpivoted_data, last_header_info


# ------------------------------------------------------------
# Main extraction routing
# ------------------------------------------------------------
def extract_borderless_data(pdf, source_name=""):
    unpivoted_data = []
    last_header_info = None

    pdf_helpers = PDFHelpers(pdf=pdf, pipeline_name="", effective_date="", text="")
    pipeline_name = pdf_helpers.extract_pipelinename_metadata()
    effective_date = pdf_helpers.extract_effectivedate_metadata()
    source_lower = os.path.basename(source_name).lower()

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

        page_records, last_header_info = extract_from_tables(
            page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num, last_header_info
        )

        print(
            f"\nPage {page_num}"
        )

        print(
            f"extract_from_tables count: "
            f"{len(page_records)}"
        )

        if not page_records:
            if "midway pipeline" in source_lower or ("Viscosity Fee" in text and "CONTRACT RATE" in text and "BASE RATE" in text):
                page_records = extract_midway_from_words(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num) or extract_midway_style_from_text(text, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num)
            elif "cheyenne pipeline" in source_lower:
                page_records = extract_cheyenne_from_words(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num)
            elif "diamond pipeline" in source_lower:
                page_records = extract_diamond_from_words(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num)
            elif "baton rouge pipeline" in source_lower:
                print(
                    "Using Baton Rouge extraction"
                )

                page_records = (
                    extract_generic_word_sections(
                        page,
                        pipeline_name,
                        effective_date,
                        page_num,
                        split_origins=True
                    )
                )

                print(
                    f"Baton Rouge rows: "
                    f"{len(page_records)}"
                )
            elif "panola pipeline" in source_lower:
                page_records = extract_generic_word_sections(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num, split_origins=True)
            elif "texas express pipeline" in source_lower:
                page_records = extract_generic_word_sections(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num, split_origins=False)
            elif "targa gulf coast ngl pipeline" in source_lower:
                page_records = extract_generic_word_sections(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num, split_origins=False)
            else:
                # generic borderless fallback (also useful for Baton Rouge-like layouts)
                page_records = extract_generic_word_sections(page, pipeline_name, effective_date, expiry_date_value, rate_tier, rate_type, bpd_ranges, page_num, split_origins=True)

        if page_records:
            unpivoted_data.extend(
                page_records
            )

    return unpivoted_data


# # ------------------------------------------------------------
# # Execution helper
# # ------------------------------------------------------------
# def extract():
#     start = datetime.now()
#     curr_path = os.getcwd()
#     tariff_data = []

#     for file in get_transformed_files(curr_path):
#         input_file = os.path.basename(file).replace('.PDF', '_v5.csv').replace('.pdf', '_v5.csv')

#         with pdfplumber.open(file) as pdf:
#             data = extract_data(pdf, source_name=file)
#             tariff_data.extend(data)
#             final_data = pd.DataFrame(tariff_data)

#             if final_data is not None and len(final_data) > 0:
#                 output_file = os.path.join('Page6_extracted_files', input_file)
#                 final_data.to_csv(output_file, index=False, encoding='utf-8')
#                 tariff_data.clear()
#                 # print(f"\nData successfully exported to {input_file}")
#             else:
#                 print(f"\nFailed to extract {input_file} table data.")

#     end = datetime.now()
#     print(f"Completed in: {end - start}")


# if __name__ == "__main__":
#     extract()
