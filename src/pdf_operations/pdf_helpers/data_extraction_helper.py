import re
from datetime import datetime

class PDFHelpers:
    def __init__(self, pdf, pipeline_name, effective_date, text=""):
        self.pdf = pdf
        self.pipeline_name = pipeline_name
        self.effective_date = effective_date
        self.text = text

    def extract_pipelinename_metadata(self):
        self.pipeline_name = ""

        page1_text = self.pdf.pages[0].extract_text()
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

        self.pipeline_name = pipeline_name
        return self.pipeline_name
    

    def extract_effectivedate_metadata(self):
        self.effective_date = ""

        page1_text = self.pdf.pages[0].extract_text()

        match_effective = re.search(r"\bEffective(?:\s+Date)?\b\s*:?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",page1_text,re.IGNORECASE)
        if match_effective:
            effective_date = match_effective.group(1)
        # Convert to datetime
        dt_obj = datetime.strptime(effective_date, "%B %d, %Y")

            # Convert to DD-MM-YYYY
        effective_date = dt_obj.strftime("%d-%m-%Y")

        self.effective_date = effective_date
        return self.effective_date
    
    def extract_tariff_rate_type(self, text=None):
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

        except Exception as e:
            print(f"Error extracting tariff rate type: {e}")
            return ""

    def extract_expiry_date(self, text=None):
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

    
    def extract_bpd_ranges(self, text=None):
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
        

    def extract_rate_tiers(self, text=None):
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


    