#!/usr/bin/env python
# coding: UTF-8

import glob
import os


import pydicom


def list_dcm_files(dir_path, recursive=True):
    if recursive:
        candidates = glob.glob(os.path.join(dir_path, "**"), recursive=True)
    else:
        candidates = glob.glob(os.path.join(dir_path, "*"))

    return [str(p) for p in candidates if os.path.isfile(p) and pydicom.misc.is_dicom(str(p))]
