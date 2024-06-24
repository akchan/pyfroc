#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

import glob
import os
import re

import pydicom

from pyfroc.keys import CaseKey, RaterCaseKey, T_EvaluationInput
from pyfroc.signals import Response, Lesion
from pyfroc.utils import list_dcm_files


class BaseLoader(ABC):
    REFERENCE_DIR_NAME = "reference"
    RESPONSE_DIR_NAME = "responses"

    def __init__(self, root_dir_path: str, verbose=True):
        self.root_dir_path = root_dir_path
        self.verbose = verbose
        self.casekey_list: list[CaseKey] = []
        self.rater_list: list[str] = []

        self._init_casekey_list()
        self._init_rater_list()

    def __len__(self):
        return len(self.casekey_list)

    def __getitem__(self, index) -> T_EvaluationInput:
        if index >= len(self):
            raise IndexError("Index out of range")

        casekey = self.casekey_list[index]
        lesions = self.read_lesions(self._casekey2path(casekey))

        responses = {}

        for rater_id in self.rater_list:
            ratercasekey = casekey.to_ratercasekey(rater_id=rater_id)
            responses[ratercasekey] = self.read_responses(self._ratercasekey2path(ratercasekey))

        return casekey, lesions, responses

    @abstractmethod
    def read_responses(self, case_dir_path: str) -> list[Response]:
        raise NotImplementedError("This method should be implemented in the subclass.")

    def read_lesions(self, case_dir_path: str) -> list[Lesion]:
        responses = self.read_responses(case_dir_path)
        return [resp.to_lesion() for resp in responses]

    def prepare_dir(self, dcm_root_dir_path: str, number_of_raters: int = 3, verbose=True) -> None:
        """Prepare the directories to store the reference lesion and response files.

        This method prepares the necessary directories to store the files for further processing.
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

        dcm_path_list = list_dcm_files(dcm_root_dir_path, recursive=True)

        if len(dcm_path_list) == 0:
            return None

        # Set casekey_list from dicom files
        casekey_set = set()

        for dcm_path in dcm_path_list:
            dcm = pydicom.dcmread(dcm_path)

            key = CaseKey(patient_id=str(dcm.PatientID),
                          study_date=str(dcm.StudyDate),
                          modality=str(dcm.Modality),
                          se_num=str(dcm.SeriesNumber))

            casekey_set.add(key)

        self.casekey_list = list(casekey_set)

        # Create a reference directory
        self._create_dirs(self._reference_dir_path())

        # Create response directories
        for i in range(number_of_raters):
            rater_dir_path = os.path.join(self._response_dir_path(), f"rater{i+1:02d}")
            self._create_dirs(rater_dir_path)

        if verbose:
            n_cases = len(set(map(lambda c: c.patient_id, self.casekey_list)))
            n_series = len(self.casekey_list)
            print(f"Prepared: {n_cases} cases, {n_series} series")

    def _create_dirs(self, tgt_dir_path: str) -> None:
        for casekey in self.casekey_list:
            se_dir_path = os.path.join(tgt_dir_path, self._casekey2path(casekey))
            os.makedirs(se_dir_path, exist_ok=True)

    def _init_casekey_list(self) -> None:
        self.casekey_list.clear()
        casekey_set = set()

        for dir_path in glob.glob(os.path.join(self._reference_dir_path(), "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            key = self._path2casekey(dir_path)

            if key is None:
                continue

            casekey_set.add(key)

        self.casekey_list = list(casekey_set)

        assert len(self.casekey_list) == len(casekey_set), "Duplication found in the reference directory"

    def _init_rater_list(self) -> None:
        self.rater_list.clear()
        rater_set = set()

        for dir_path in glob.glob(os.path.join(self._response_dir_path(), "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            key = self._path2casekey(dir_path)

            if key is None:
                continue

            rater_set.add(key)

        self.rater_list = list(rater_set)

        assert len(self.rater_list) == len(rater_set), "Duplication is found in the response directory"

    @staticmethod
    def _path2casekey(dir_path: str) -> CaseKey | None:
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

    @staticmethod
    def _path2ratercasekey(dir_path: str) -> RaterCaseKey | None:
        # Search case directories
        dirpath_pattern = r".*?([^\/]+)\/([^\/]+)\/([0-9]{8})_([A-Z]{2})\/SE([0-9]+)"
        m = re.match(dirpath_pattern, dir_path)

        if m is None:
            return None
        else:
            return RaterCaseKey(rater_id=m.group(1),
                                patient_id=m.group(2),
                                study_date=m.group(3),
                                modality=m.group(4),
                                se_num=m.group(5))

    @staticmethod
    def _casekey2path(casekey: CaseKey) -> str:
        return os.path.join(casekey.patient_id, f"{casekey.study_date:>08s}_{casekey.modality.upper()}", f"SE{casekey.se_num}")

    @staticmethod
    def _ratercasekey2path(ratercakey: RaterCaseKey) -> str:
        return os.path.join(ratercakey.rater_id, ratercakey.patient_id, f"{ratercakey.study_date:>08s}_{ratercakey.modality.upper()}", f"SE{ratercakey.se_num}")

    def _response_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.RESPONSE_DIR_NAME)

    def _reference_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.REFERENCE_DIR_NAME)
