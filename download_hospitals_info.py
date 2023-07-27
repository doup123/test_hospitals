import os
import requests
import pandas as pd
def download_file(url, output_file_path):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes

        with open(output_file_path, 'wb') as file:
            file.write(response.content)

        print("File downloaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")