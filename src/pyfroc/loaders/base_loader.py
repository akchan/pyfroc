#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

import glob
import os
import re

from tqdm import tqdm
import pydicom

from pyfroc.keys import CaseKey, T_EvaluationInput
from pyfroc.signals import Response, Lesion
from pyfroc.utils import list_dcm_files


class BaseLoader(ABC):
    REFERENCE_DIR_NAME = "reference"
    RATERS_DIR_NAME = "raters"

    @classmethod
    @abstractmethod
    def read_responses(cls, case_dir_path: str) -> list[Response]:
        raise NotImplementedError()

    @classmethod
    def read_lesions(cls, case_dir_path: str) -> list[Lesion]:
        responses = cls.read_responses(case_dir_path)
        return [resp.to_lesion() for resp in responses]

    @classmethod
    def prepare(cls, dcm_root_dir_path: str, tgt_dir_path: str, number_of_raters: int = 3, verbose=True) -> None:
        """Prepare the directories to store the .seg.nrrd files.

        This method prepares the necessary directories to store the .seg.nrrd files for further processing.
        It creates a reference directory and multiple rater directories based on the specified parameters.

        Args:
            dcm_root_dir_path (str): The root directory path containing the DICOM files.
            tgt_dir_path (str): The target directory path where the directories will be created.
            number_of_raters (int, optional): The number of rater directories to create. Defaults to 3.
            verbose (bool, optional): If True, print the number of directories prepared. Defaults to True.

        Returns:
            None
        """
        assert number_of_raters > 0, "number_of_raters should be greater than 0."

        dcm_path_list = list_dcm_files(dcm_root_dir_path)

        if len(dcm_path_list) == 0:
            return None

        casekey_set = set()

        for dcm_path in dcm_path_list:
            dcm = pydicom.dcmread(dcm_path)

            key = CaseKey(patient_id=str(dcm.PatientID),
                          study_date=str(dcm.StudyDate),
                          modality=str(dcm.Modality),
                          se_num=str(dcm.SeriesNumber))

            casekey_set.add(key)

        # prepare a reference directory
        ref_dir_path = cls._reference_dir_path(tgt_dir_path)
        cls._create_dir(ref_dir_path, casekey_set)

        for i in range(number_of_raters):
            rater_dir_path = os.path.join(cls._raters_dir_path(tgt_dir_path), f"rater{i+1:02d}")
            cls._create_dir(rater_dir_path, casekey_set)

        if verbose:
            print(f"A total of {len(casekey_set)} serieses was found.")

    @classmethod
    def read(cls, dir_path: str) -> T_EvaluationInput:
        evaluation_input: T_EvaluationInput = {}

        # List rater dir paths
        rater_dir_paths = [p for p in glob.glob(os.path.join(cls._raters_dir_path(dir_path), "*")) if os.path.isdir(p)]

        # Prepare a progress bar
        len_bar = len(rater_dir_paths) + 1
        bar = tqdm(total=len_bar, desc="Reading reference", leave=True)

        # Read the reference lesions
        ref_dir_path = cls._reference_dir_path(dir_path)
        for casekey, case_dir_path in cls._list_case_dirs(ref_dir_path).items():
            evaluation_input[casekey] = (cls.read_lesions(case_dir_path), {})
        bar.update(1)

        # Read the responses of each rater
        for rater_dir_path in glob.glob(os.path.join(cls._raters_dir_path(dir_path), "*")):
            if not os.path.isdir(rater_dir_path):
                continue

            rater_dir_name = os.path.basename(rater_dir_path)
            bar.set_description(f"Reading {rater_dir_name:9s}")

            for casekey, case_dir_path in cls._list_case_dirs(rater_dir_path).items():
                responses = cls.read_responses(case_dir_path)
                ratercasekey = casekey.to_ratercasekey(rater_id=rater_dir_name)
                evaluation_input[casekey][1][ratercasekey] = responses

            bar.update(1)
        bar.close()

        return evaluation_input

    @classmethod
    def _casekey2path(cls, casekey: CaseKey) -> str:
        return os.path.join(casekey.patient_id, f"{casekey.study_date}_{casekey.modality.upper()}", f"SE{casekey.se_num}")

    @classmethod
    def _create_dir(cls, tgt_dir_path: str, casekey_set: set[CaseKey]) -> None:
        for casekey in casekey_set:
            se_dir_path = os.path.join(tgt_dir_path, cls._casekey2path(casekey))
            os.makedirs(se_dir_path, exist_ok=True)

    @classmethod
    def _list_case_dirs(cls, root_dir_path) -> dict[CaseKey, str]:
        case_dir_dict = {}

        for dir_path in glob.glob(os.path.join(root_dir_path, "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            key = cls._path2casekey(dir_path)

            if key is None:
                continue

            case_dir_dict[key] = dir_path

        return case_dir_dict

    @classmethod
    def _path2casekey(cls, dir_path: str) -> CaseKey | None:
        # Search case directories
        dirpath_pattern = r".*?([^\/]+)\/([0-9]{8})_([A-Z]{2})\/SE([0-9]+)"
        m = re.match(dirpath_pattern, dir_path)

        if m is None:
            return None
        else:
            return CaseKey(patient_id=m.group(1),
                           study_date=m.group(2),
                           modality=m.group(3),
                           se_num=m.group(4))

    @classmethod
    def _raters_dir_path(cls, tgt_dir_path: str) -> str:
        return os.path.join(tgt_dir_path, cls.RATERS_DIR_NAME)

    @classmethod
    def _reference_dir_path(cls, tgt_dir_path: str) -> str:
        return os.path.join(tgt_dir_path, cls.REFERENCE_DIR_NAME)
