from aksharamukha  import transliterate
import os
import re #Comes with anaconda
from google.cloud import vision #pip install google-cloud-vision
from google.cloud import storage #pip install google-cloud-storage
from google.protobuf import json_format #pip install protobuf
from datetime import datetime
import sys
import json
from urllib.parse import urlparse

def create_log_file_if_not_exists(log_file='processed_files.log'):
    """Create the processed log file if it doesn't exist."""
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            pass

def create_error_log_if_not_exists(log_file='errored_files.log'):
    """Create the error log file if it doesn't exist."""
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            pass

def mark_as_processed(filename, log_file='processed_files.log'):
    """Mark a file as processed by adding its name to the log file."""
    with open(log_file, 'a') as log:
        log.write(filename + '\n')


def mark_as_errored(filename, log_file='errored_files.log'):
    """Mark a file as processed by adding its name to the log file."""
    with open(log_file, 'a') as log:
        log.write(filename + '\n')


def is_processed(filename, log_file='processed_files.log'):
    """Check whether a file has been processed."""
    with open(log_file, 'r') as log:
        processed_files = log.read().splitlines()
    return filename in processed_files


def has_errored(filename, log_file='errored_files.log'):
    """Check whether a file has been processed."""
    with open(log_file, 'r') as log:
        errored_files = log.read().splitlines()
    return filename in errored_files

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

#Recursively makes a list of all pdfs in a project bucket
def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)

    file_names = [blob.name for blob in blobs]

    pdf_list = [file_name for file_name in file_names if file_name[-3:]== 'pdf']
    txt_list = [file_name for file_name in file_names if file_name[-3:]== 'txt']

    return pdf_list,txt_list

# How does this OCR work?
# You put all your pdf files into one folder, and upload that folder to google drive.
# In the input file, give the path to that folder in line 1, and the just names of the pdfs, including extension later.
# Output will be written to folders made inside your primary folder. The folders will have the same name as the pdf.

#This function parses the provided input text file which contains paths to pdfs in the Google Bucket.
#It returns 1. complete_pdf_path_list, which contains paths to all the pdfs, 2. path to just the bucket.

#This function parses the provided input text file which contains paths to pdfs in the Google Bucket.
#It returns 1. complete_pdf_path_list, which contains paths to all the pdfs, 2. path to just the bucket.

def parse_input_txt(input_txt_name):

    with open(input_txt_name) as file:
        file_contents = file.read()

    ocr_input_split = file_contents.splitlines()
    if (ocr_input_split[0][0] != '#' or ocr_input_split[2][0] != '#'):
        sys.exit('ERROR: Either Line 0 or Line 2 do not start with a hash.')

    if (ocr_input_split[1][:5] != 'gs://' or ocr_input_split[1][-1] != '/'):
        sys.exit('ERROR: The folder path (line 1) is not of form gs://abracadabra/')

    #This list contains all the files to be OCRed
    folder_path = ocr_input_split[1]
    complete_pdf_path_list = [(folder_path + file_name) for file_name in ocr_input_split[3:]]

    #Test to make sure all the files are compatible.

    #complete_pdf_path_list a list of paths to all the pdfs. bucket_path is a string containing the bucket in which the files sit.
    return complete_pdf_path_list, folder_path

#The output_folder is the folder into which all the data is dumped. If does not exist, will be created.
#i_want_json is a boolean that controls whether json files are written into output folder.
def OCR(input_file_path, txt_file_path):

        #Note: This code takes roughly ~3 mins to OCR a 20mb file with 300 pages.
    bucket_name = urlparse(input_file_path).netloc
    output_folder_path = 'gs://' + bucket_name  +'/' + os.path.basename(input_file_path)

    #Set source path for .pdf
    gcs_source_uri = input_file_path
    pdf_file_name = re.match(r'gs:\/\/.+\/(.+)\..+$', input_file_path).group(1)
    #Set destination path as folder of same name as file, in the same folder.

    gcs_destination_uri = output_folder_path

    client = vision.ImageAnnotatorClient()

    #This sets how many pages are OCRed into one json file
    batch_size = 1
    mime_type = 'application/pdf'
    feature = vision.Feature(
        type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    #Configure .pdf file source path.
    gcs_source = vision.GcsSource(uri=gcs_source_uri)

    input_config = vision.InputConfig(
        gcs_source=gcs_source, mime_type=mime_type)

    #Configure Json file path.

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size)
    #print ('Input and output paths have been loaded.')

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config,
        output_config=output_config)

    start_now = datetime.now()
    current_time = start_now.strftime("%H:%M:%S")

    print ('Requested at', current_time, end = '\t')

    operation = client.async_batch_annotate_files(requests=[async_request])
    operation.result(timeout=1000)

    end_now = datetime.now()
    current_time = end_now.strftime("%H:%M:%S")
    #print ('Completed:', current_time, end = ' ')
    duration = end_now - start_now
    time = duration.total_seconds()
    print ('Total time:', time/60.0)

    storage_client = storage.Client()
    match = re.match(r'gs://([^/]+)/(.+)', gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)
    bucket = storage_client.get_bucket(bucket_name)



    # List object with the given prefix
    blob_list = list(bucket.list_blobs(prefix=prefix))
    #print('Output files:')
    #for blob in blob_list:
        #print(blob.name)


    #Now we reorder blob_list properly because it is currently sorted as 1,10,100,101,102.....2,20,200,201...
    sorting_indices = [] #The nth element of this array is the nth blob's page number.
    sorted_blobs= blob_list.copy() #Blobs will be sorted into this array. It is a copy of blob_list to have same size.
    #We build the sorting_indices array (see definition above) by capturing the number just before .json.
    for blob in blob_list:
        sorting_indices.append(re.match(r'.+-to-(.+).json$', blob.name).group(1))
    #Now we add elements into the sorted_blobs array
    for blob in blob_list:
        index = blob_list.index(blob) #We find the index of the blob in question.
        sorted_blobs[int(sorting_indices[index])-1] = blob #We move that blob to the correct page number location.

    print ("Breakpoint 1a")

    #output = sorted_blobs[0]
    #json_string = output.download_as_string()
    #response = json.loads(json_string)
    #first_page_response = response['responses'][0]
    #annotation = first_page_response['fullTextAnnotation']


    #text_file = open(gd_folder_path + pdf_file_name + '.txt', "w")
    text_file = open( os.path.join(txt_file_path[1:], pdf_file_name + '.txt') , "w")
    text_file_iast = open(os.path.join(txt_file_path[1:], pdf_file_name + '_iast.txt'), "w")

    for page in sorted_blobs:

        json_string = page.download_as_string()
        response = json.loads(json_string)
        #print ('json loaded')
        first_page_response = response['responses'][0]
        #print ('response redied')
        if 'fullTextAnnotation' in first_page_response:
          annotation = first_page_response['fullTextAnnotation']
        else:
          annotation = {'text':''}

        page_number = sorted_blobs.index(page)+1
        print (page_number, end = ",")
        text_file.write("\nPage %i****************************************************************************************\n" % page_number)
        text_file_iast.write("\nPage %i****************************************************************************************\n" % page_number)

        transliterated_text = transliterate.process('Devanagari', 'IAST', annotation['text'])
        text_file_iast.write(transliterated_text)
        #text_file.write(annotation.text)
        text_file.write(annotation['text'])
    text_file.close()
    text_file_iast.close()
    mark_as_processed(pdf_file_name+'.pdf')
    print (f'\nOCR done and saved of {os.path.basename(input_file_path)}')

    return ('OCR done.')

