import os
from azure.storage.blob import BlobServiceClient

def main(summary: str):
    blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
    container = blob_service_client.get_container_client("output")
    container.upload_blob(name="summary.txt", data=summary, overwrite=True)