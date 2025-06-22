import logging
import os
import requests
import time

def main(blob_name: str) -> str:
    endpoint = os.environ["COGNITIVE_SERVICES_ENDPOINT"]
    key = os.environ["AZURE_FORMRECOGNIZER_KEY"]
    blob_base_url = os.environ["BLOB_STORAGE_ENDPOINT"]

    blob_url = f"{blob_base_url}/input/{blob_name}"
    headers = {"Content-Type": "application/json", "Ocp-Apim-Subscription-Key": key}
    body = {"urlSource": blob_url}

    response = requests.post(f"{endpoint}/formrecognizer/documentModels/prebuilt-document:analyze?api-version=2023-07-31", headers=headers, json=body)
    result_url = response.headers["operation-location"]

    for _ in range(20):
        result = requests.get(result_url, headers=headers).json()
        if result.get("status") == "succeeded":
            pages = result["analyzeResult"]["pages"]
            return " ".join(page.get("content", "") for page in pages)
        time.sleep(1)
    raise Exception("Text extraction failed")