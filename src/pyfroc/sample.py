#!/usr/bin/env python
# coding: UTF-8

import os
import tempfile
import zipfile


from tcia_utils import nbia
import requests


def download_dicom_from_nbia(target_path="./sample_data/dicom"):
    os.makedirs(target_path, exist_ok=True)

    # A list of Series UID of LIDC-IDRI
    # Using 2 cases (#1, 3) of 10 cases (#1-10)
    #
    se_uid_list = [
        "1.3.6.1.4.1.14519.5.2.1.6279.6001.179049373636438705059720603192",
        "1.3.6.1.4.1.14519.5.2.1.6279.6001.619372068417051974713149104919",
        "1.3.6.1.4.1.14519.5.2.1.6279.6001.170706757615202213033480003264",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.323541312620128092852212458228",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.129007566048223160327836686225",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.132817748896065918417924920957",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.272348349298439120568330857680",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.774060103415303828812229821954",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.286061375572911414226912429210",
        # "1.3.6.1.4.1.14519.5.2.1.6279.6001.416701701108520592702405866796",
    ]

    nbia.downloadSeries(se_uid_list, input_type="list", path=target_path)


def download_experiment_data(target_dir="./sample_data"):
    # github release url
    release_url = "https://github.com/akchan/pyfroc/releases/download/sample_data/sample_experiment.zip"

    # Create a temporary file to store the downloaded zip file
    with tempfile.NamedTemporaryFile() as temp_file:
        # Download the zip file
        response = requests.get(release_url)
        temp_file.write(response.content)

        # Extract the contents of the zip file
        with zipfile.ZipFile(temp_file.name, 'r') as zip_ref:
            zip_ref.extractall(target_dir)


def download_sample_data(target_dir="./sample_data"):
    # Download experiment data from github release
    download_experiment_data(target_dir)

    # Download dicom files from NBIA
    dicom_path = os.path.join(target_dir, "dicom")
    download_dicom_from_nbia(target_path=dicom_path)
