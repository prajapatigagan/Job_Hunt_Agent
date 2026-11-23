import time
import requests
import logging

APP_URL = "https://your-app-name.streamlit.app"

INTERVAL = 300  # 5 minutes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def keep_alive():
    while True:
        try:
            response = requests.get(
                APP_URL,
                timeout=30
            )

            logging.info(
                f"Server status: {response.status_code}"
            )

        except requests.RequestException as error:
            logging.error(f"Keep-alive failed: {error}")

        time.sleep(INTERVAL)


if _name_ == "_main_":
    keep_alive()