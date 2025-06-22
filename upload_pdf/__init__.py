from azure.storage.blob import BlobServiceClient

blob_service_client = BlobServiceClient.from_connection_string("UseDevelopmentStorage=true")
container_client = blob_service_client.get_container_client("input")

try:
    container_client.create_container()
except Exception:
    pass  # Already exists

with open("sample.pdf", "rb") as f:
    container_client.upload_blob("uploadedsample.pdf", f, overwrite=True)

print("✅ sample.pdf uploaded to input container.")