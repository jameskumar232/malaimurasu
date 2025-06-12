import os
import requests
import urllib3
from PyPDF2 import PdfMerger
from datetime import datetime, timedelta
from time import sleep

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://epaper.malaimurasu.com"
CITIES = {
    "Chennai": "CHE",
    "Madurai": "MDU",
    "Coimbattore": "COM",
    "Vellore": "VEL",
    "Selam": "SLM",
    "Tirunelveli": "TVL"
}
MAX_RETRIES = 3
MAX_CONSECUTIVE_MISSING_PAGES = 3

# Get yesterday’s date
date_obj = datetime.utcnow() + timedelta(hours=5, minutes=30) - timedelta(days=1)
DATE = date_obj.strftime("%Y-%m-%d")
date_path = date_obj.strftime("%Y/%m/%d")

def download_pdf(url, dest):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=10, verify=False)
            if response.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"HTTP {response.status_code} for {url}")
        except requests.exceptions.Timeout:
            print(f"Timeout. Retrying {url}... ({attempt}/{MAX_RETRIES})")
        except Exception as e:
            print(f"Error downloading {url}: {e}")
        sleep(1)
    return False

def download_and_merge(city, code):
    print(f"\nProcessing {city} for date {DATE}")
    merger = PdfMerger()
    downloaded = 0
    missing_count = 0
    page = 1
    temp_files = []

    while missing_count < MAX_CONSECUTIVE_MISSING_PAGES:
        page_code = f"{code}_P{str(page).zfill(2)}.pdf"
        url = f"{BASE_URL}/{date_path}/{city}/{page_code}"
        dest = page_code
        print(f"Trying: {url}")

        success = download_pdf(url, dest)

        if success:
            merger.append(dest)
            temp_files.append(dest)
            downloaded += 1
            missing_count = 0
        else:
            print(f"Skipped (not available or failed after retry): {url}")
            missing_count += 1

        page += 1

    if downloaded > 0:
        output_file = f"{city}.pdf"
        merger.write(output_file)
        merger.close()
        print(f"Saved: {output_file} with {downloaded} pages.")
    else:
        print(f"No pages downloaded for {city}.")

    for file in temp_files:
        if os.path.exists(file):
            os.remove(file)

for city, code in CITIES.items():
    download_and_merge(city, code)
