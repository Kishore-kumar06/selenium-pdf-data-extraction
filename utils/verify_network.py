import requests
from utils.logfiles import setup_logger

logger = setup_logger("network")

def check_connection():
    try:
        response = requests.get("https://www.google.com", timeout=30)
        if response:
            return True

    except Exception as r:
        logger.error(f"An error occured while connecting to internet. {r}")
        return False