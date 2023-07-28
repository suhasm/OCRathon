import os
import concurrent.futures

from funcs import ensure_dir, list_blobs, parse_input_txt, OCR, create_log_file_if_not_exists, is_processed
from funcs import create_error_log_if_not_exists, mark_as_errored, has_errored

key_name = 'key.json'
txt_file_path = '/txt_files'
bucket = 'suhasocr'

# Load in the Google Vision Key
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_name

# Make sure the txt_files folder exists. This is where the OCR files will be written to.
ensure_dir(txt_file_path)
# Make sure the processed files log file exists
create_log_file_if_not_exists()
# Make sure the errored log file exists
create_error_log_if_not_exists()

print("reached here")

# Recursively list all pdfs in the bucket
pdf_list, txt_list = list_blobs(bucket)
print(f"There are {len(pdf_list)} pdfs in the bucket {bucket}")

#Make list of paths of all pdfs in bucket
pdf_path_list = ['gs://' + bucket + '/' + filename for filename in pdf_list]

#Get those that are not OCRed AND have not errored.
filtered_pdf_path_list = [path for path in pdf_path_list
                          if not is_processed(os.path.basename(path)) and not has_errored(os.path.basename(path))]

for x in filtered_pdf_path_list:
    print (x)
input()

#OCR(smaller_list[3], txt_file_path)

import concurrent.futures

# Initialize the executor
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Submit the tasks and create a dictionary to map futures to args
    futures_to_args = {executor.submit(OCR, arg, txt_file_path): arg for arg in filtered_pdf_path_list}

    # Collect the results as they become available
    results = []
    errors = []
    for future in concurrent.futures.as_completed(futures_to_args):
        try:
            result = future.result()  # Get the result (this will block until the result is ready)
            results.append(result)
        except Exception as e:
            # Catch all exceptions raised while fetching the result or inside the OCR function
            # Get the arg that caused this error using our map
            arg_that_caused_error = futures_to_args[future]
            # Append a tuple of the exception and the arg that caused it to the errors list
            errors.append((str(e), arg_that_caused_error))

# Print errors along with the arg that caused them
for error, arg in errors:
    print(f"Error occurred in arg {arg}: ", error)
    mark_as_errored(os.path.basename(arg))


