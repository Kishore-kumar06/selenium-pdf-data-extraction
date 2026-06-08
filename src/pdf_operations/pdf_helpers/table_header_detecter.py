import re
from .data_lookup import DataLookup


class TableHeaderHelper:

    @staticmethod
    def is_origin_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        origin_headers = (
            "origin point",
            "origin",
            "origins",
            "from",
            "from:",
            "origin(s)",
            "receipt",
            "receipt points/origin",
            "receipt points origin"
        )

        return text.startswith(origin_headers)

    @staticmethod
    def is_destination_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        destination_headers = (
            "destination point",
            "destination",
            "destination(s)",
            "destinations",
            "destination-dest",
            "delivery/destination",
            "delivery destination",
            "to"
        )

        return text.startswith(destination_headers)

    @staticmethod
    def is_rate_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        rate_headers = (
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
           "incentive",
           "contract",
           "for",
           "DESTINATION –",
           "long",
           "anchor",
           "pla"

        )

        return text.startswith(rate_headers)
    
    @staticmethod
    def is_volume_tier_header(text):

        if not text:
            return False

        text = DataLookup.normalize_header_cell(text)

        volume_tier = (
           "total",
           "volume tier",
           "st",
           "minimum volume",
           "fixed volume",
           "actual shipments",
           "terms",
           "term"
        )

        return text.startswith(volume_tier)