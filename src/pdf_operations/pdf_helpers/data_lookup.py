import re


class DataLookup:
   
    def is_rate(value):
        try:
            if value is None:
                return False
            return bool(re.fullmatch(r"\d+\.\d+", value.strip()))
        
        except Exception as e:
            print(f"Error checking if value is a rate: {e}")
            return False


    def clean(value):
        try:     
            if value is None:
                return ""
            return re.sub(r"\s+", " ", str(value)).strip()
        except Exception as e:
            print(f"Error cleaning value: {e}")
            return ""
        
    def normalize_exact_header_cell(value):

        try:

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

            if not value:
                return ""
            else:
                return value.strip()
        
        except Exception as e:
            print(f"Error normalizing header cell: {e}")
            return ""
        

    def normalize_header_cell(value):
        try:
            value = re.sub(r"\s+", " ", str(value)).strip()
            # value = DataLookup.clean(value).lower()
            value = value.replace(":", "")
            value = re.sub(r"\(\d+\)", "", value)   # remove (1), (2)
            if value.startswith('[w]') or value.startswith('[n]'):
                value = value.replace('[w]','').replace('[n]','').strip()
            value = re.sub(r"\s+", " ", value).strip()
            
            return value
        except Exception as e:
            print(f"Error normalizing header cell: {e}")
            return "" 