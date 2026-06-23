import re


class DataLookup:
   
    @staticmethod
    def is_rate(value):
        """
        Verifies if a cell contains a valid rate value.
        Accepts formats like: '250', '184.24', '[I] 268.19', '[U] 120.5'
        """
        try:
            if value is None:
                return False
            # Clean spaces and strip common tariff reference mark indicators [I], [U], [W], etc.
            cleaned = re.sub(r"\[[A-Z]\]", "", str(value)).strip()
            # Match integers or decimal numbers
            return bool(re.fullmatch(r"\d+(?:\.\d+)?", cleaned))
        except Exception as e:
            print(f"Error checking if value is a rate: {e}")
            return False


    @staticmethod
    def clean(value):
        try:     
            if value is None:
                return ""
            return re.sub(r"\s+", " ", str(value)).strip()
        except Exception as e:
            print(f"Error cleaning value: {e}")
            return ""
        
        
    @staticmethod
    def normalize_exact_header_cell(value):
        try:
            if value is None:
                return ""
            value = str(value).replace("\r", "\n")
            value = re.sub(r"[ \t]+", " ", value)      # Multiple spaces to single space
            value = re.sub(r"\n+", "\n", value)        # Multiple newlines to single newline
            value = re.sub(r"\(\d+\)", "", value)      # Remove footnotes like (1), (2)
            value = value.replace(":", "")
            return value.strip()
        except Exception as e:
            print(f"Error normalizing exact header cell: {e}")
            return ""
            

    @staticmethod
    def normalize_header_cell(value):
        try:
            value = DataLookup.clean(value).lower()
            value = value.replace(":", "")
            value = re.sub(r"\(\d+\)", "", value)      # Remove footnotes
            if value.startswith('[w]') or value.startswith('[n]'):
                value = value.replace('[w]','').replace('[n]','').strip()
            return re.sub(r"\s+", " ", value).strip()
        except Exception as e:
            print(f"Error normalizing header cell: {e}")
            return ""