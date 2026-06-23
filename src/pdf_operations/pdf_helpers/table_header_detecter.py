import re
from .data_lookup import DataLookup


class TableHeaderHelper:

    ORIGIN_PREFIXES = ("origin point", "origin", "origins", "from", "receipt")
    DESTINATION_PREFIXES = ("destination point", "destination", "destinations", "delivery", "to")
    RATE_PREFIXES = ("uncommitted", "committed", "maximum", "volume", "rate", "rates", "base", "joint", "incentive", "contract")
    VOLUME_TUER_PREFIXES = ("total", "volume tier", "st", "tier", "commitment level")

    @staticmethod
    def is_origin_header(text):
        if not text:
            return False
        cleaned_text = DataLookup.normalize_header_cell(text)
        return cleaned_text.startswith(TableHeaderHelper.ORIGIN_PREFIXES)
    

    @staticmethod
    def is_destination_header(text):
        if not text:
            return False
        cleaned_text = DataLookup.normalize_header_cell(text)
        return cleaned_text.startswith(TableHeaderHelper.DESTINATION_PREFIXES)
    

    @staticmethod
    def is_rate_header(text):
        if not text:
            return False
        cleaned_text = DataLookup.normalize_header_cell(text)
        
        # Guard against short word collisions by checking exact matches for broad words
        if cleaned_text in ("for", "long", "pla"):
            return True
            
        return cleaned_text.startswith(TableHeaderHelper.RATE_PREFIXES)
    

    @staticmethod
    def is_volume_tier_header(text):
        if not text:
            return False
        cleaned_text = DataLookup.normalize_header_cell(text)
        return cleaned_text.startswith(TableHeaderHelper.VOLUME_TUER_PREFIXES)