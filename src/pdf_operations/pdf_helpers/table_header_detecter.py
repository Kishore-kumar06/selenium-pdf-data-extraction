import re
from .data_lookup import DataLookup


class TableHeaderHelper:

    @staticmethod
    def is_origin_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        patterns = [
            "origin",
            "origins",
            "from",
            "from:",
            "origin(s)",
            "receipt",
            "origin point"
        ]

        return any(
            pattern in text
            for pattern in patterns
        )

    @staticmethod
    def is_destination_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        patterns = [
            "destination",
            "to",
            "destination point",
            "destinations",
            "destination(s)",
            "destination-dest",
            "delivery/destination",
        ]

        return any(
            pattern in text
            for pattern in patterns
        )

    @staticmethod
    def is_rate_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        patterns = [
           "uncommitted",
           "committed",
           "maximum",
            "volume",
            "rate",
            "rates",
           "rate:(2)",
           "base",
           "intersect",
           "joint",
           "non-anchor",
           "contract",
           "incentive",
           "for",
           "DESTINATION –",
           "long",
           "anchor",
           "pla"

        ]

        return any(
            pattern in text
            for pattern in patterns
        )
    
    @staticmethod
    def is_volume_tier_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        patterns = [
           "volume tier",
           "total",
           "st",
           "minimum volume",
           "fixed volume",
           "actual shipments",
           "terms"
        ]

        return any(
            pattern in text
            for pattern in patterns
        )