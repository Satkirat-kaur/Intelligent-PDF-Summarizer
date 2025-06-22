import logging
import os
from azure.storage.blob import BlobServiceClient
import azure.functions as func
import azure.durable_functions as df
from azure.identity import DefaultAzureCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import json
from datetime import datetime

my_app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Connect to Blob Storage
blob_service_client = BlobServiceClient.from_connection_string(os.environ.get("BLOB_STORAGE_ENDPOINT"))

# Blob trigger to start orchestration
@my_app.blob_trigger(arg_name="myblob", path="input", connection="BLOB_STORAGE_ENDPOINT")
@my_app.durable_client_input(client_name="client")
async def blob_trigger(myblob: func.InputStream, client):
    logging.info(f"Python blob trigger function processed blob: Name: {myblob.name}, Size: {myblob.length} bytes")
    blobName = myblob.name.split("/")[1]
    await client.start_new("process_document", client_input=blobName)

# Orchestrator function
@my_app.orchestration_trigger(context_name="context")
def process_document(context):
    blobName: str = context.get_input()

    retry_opts = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=3)

    result = yield context.call_activity_with_retry("analyze_pdf", retry_opts, blobName)
    result2 = yield context.call_activity_with_retry("summarize_text", retry_opts, result)
    result3 = yield context.call_activity_with_retry("write_doc", retry_opts, {
        "blobName": blobName,
        "summary": result2
    })

    return logging.info(f"Successfully uploaded summary to {result3}")

# Analyze PDF content from blob
@my_app.activity_trigger(input_name='blobName')
def analyze_pdf(blobName):
    logging.info(f"In analyze_pdf activity")
    container_client = blob_service_client.get_container_client("input")
    blob_client = container_client.get_blob_client(blobName)
    blob = blob_client.download_blob().readall()

    endpoint = os.environ["COGNITIVE_SERVICES_ENDPOINT"]
    credential = DefaultAzureCredential()
    document_analysis_client = DocumentAnalysisClient(endpoint, credential)

    poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=blob, locale="en-US")
    result = poller.result().pages

    full_text = ''
    for page in result:
        for line in page.lines:
            full_text += line.content + ' '

    return full_text

# Mocked local summarization
@my_app.activity_trigger(input_name='results')
def summarize_text(results):
    logging.info("In summarize_text activity (mocked locally)")
    mocked_summary = {
        "content": f"Summary (mocked): {results[:200]}..."
    }
    return mocked_summary

# Save summary to output container
@my_app.activity_trigger(input_name='results')
def write_doc(results):
    logging.info("In write_doc activity")
    container_client = blob_service_client.get_container_client("output")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    fileName = f"{results['blobName'].replace('.', '-')}-{timestamp}.txt"
    content = results['summary']['content']

    logging.info("Uploading to blob: " + content)
    container_client.uplo_
