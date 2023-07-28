# OCRathon: OCR Pipeline Using Google Vision

* Python script to perform OCR using the Google Cloud Vision API. 
* Files are stored on Google Cloud Storage bucket, and jobs are sent concurrently to speed up the process.
* I upload files to Google Cloud by dropping them into a folder on my Synology NAS (using its Cloud Sync tool).
 
## Prerequisites

Ensure the following before you proceed:

- Python installed on your machine.
- Google Cloud Storage bucket containing the PDF files to be processed.
- Google Cloud Vision API and Google Cloud Storage API enabled on your Google Cloud project.

## Dependencies

The following Python packages are necessary dependencies for this project:

- `aksharamukha`
- `google-cloud-vision`
- `google-cloud-storage`
- `protobuf`

You can install them using the following command:

```bash
pip install aksharamukha google-cloud-vision google-cloud-storage protobuf
```

## Configuration

To start using this script, please configure the following details:

1. Place your PDF files in your Google Cloud Storage bucket.
2. Ensure you have the Google Cloud Vision and Storage APIs enabled and set up on your Google Cloud project.
3. Update the bucket_name variable with the name of your bucket.
4. Generate a JSON key file for your Google Cloud project and update the key_path variable with the path to this file.

## Functionality

The main script, main.py, is responsible for setting up the Google Vision client and ensuring necessary directories and log files exist. It fetches a list of all PDF files in the bucket and filters out files that have already been processed or errored out, and prints out the paths of the remaining files.

The script then uses the Google Vision API to perform OCR on each PDF, storing the text output and a version transliterated to the International Alphabet of Sanskrit Transliteration (IAST) in text files.

This pipeline is built for robustness, logging errors and ensuring files are not reprocessed. It takes advantage of Python's native concurrency features to process multiple files simultaneously for improved efficiency.

Note: This repository is a starting point and might need adjustments to fit your specific use case.

