#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

import glob
import os
import re

import pydicom

from pyfroc.keys import CaseKey, RaterCaseKey, T_EvaluationInput
from pyfroc.signals import Response, Lesion, sort_signals
from pyfroc.utils import list_dcm_files


class BaseLoader(ABC):
    REFERENCE_ROOT_DIR_NAME = "reference"
    RESPONSE_ROOT_DIR_NAME = "responses"

    def __init__(self, root_dir_path: str, verbose=True):
        self.root_dir_path = root_dir_path
        self.verbose = verbose
        self.casekey_list: list[CaseKey] = []
        self.rater_list: list[str] = []

        self._init_casekey_list()
        self._init_rater_list()

    def __len__(self):
        return len(self.casekey_list)

    def __getitem__(self, index: int) -> T_EvaluationInput:
        if index >= len(self):
            raise IndexError("Index out of range")

        casekey = self.casekey_list[index]
        lesions_raw = self.read_lesions(self._lesion_dir_path(casekey))
        lesions = sort_signals(lesions_raw)

        rater_responses = {}

        for rater in self.rater_list:
            ratercasekey = casekey.to_ratercasekey(rater_name=rater)
            responses_raw = self.read_responses(self._response_dir_path(ratercasekey))
            rater_responses[ratercasekey] = sort_signals(responses_raw)

        return casekey, lesions, rater_responses

    @abstractmethod
    def read_responses(self, case_dir_path: str) -> list[Response]:
        raise NotImplementedError("This method should be implemented in the subclass.")

    def read_lesions(self, case_dir_path: str) -> list[Lesion]:
        responses = self.read_responses(case_dir_path)
        return [resp.to_lesion() for resp in responses]

    def prepare_dir(self, dcm_root_dir_path: str,
                    number_of_raters: int = 3,
                    number_of_modality_or_treatment=2,
                    verbose=True) -> None:
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

            for i in range(number_of_modality_or_treatment):
                key = CaseKey.from_dcm(dcm, modality_id=i)

                casekey_set.add(key)

        self.casekey_list = list(casekey_set)

        # Create a reference directory
        self._create_dirs(self._reference_root_dir_path())

        # Create response directories
        for i in range(number_of_raters):
            rater_dir_path = os.path.join(self._response_root_dir_path(), f"rater{i+1:02d}")
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

        for dir_path in glob.glob(os.path.join(self._reference_root_dir_path(), "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            key = CaseKey.from_path(dir_path)

            if key is None:
                continue

            casekey_set.add(key)

        self.casekey_list = list(casekey_set)

        assert len(self.casekey_list) == len(casekey_set), "Duplication found in the reference directory"

    def _init_rater_list(self) -> None:
        self.rater_list.clear()
        rater_set = set()

        for dir_path in glob.glob(os.path.join(self._response_root_dir_path(), "*")):
            if not os.path.isdir(dir_path):
                continue

            rater_set.add(os.path.basename(dir_path))

        self.rater_list = list(rater_set)

        assert len(self.rater_list) == len(rater_set), "Duplication is found in the response directory"

    @staticmethod
    def _casekey2path(casekey: CaseKey) -> str:
        return os.path.join(casekey.patient_id,
                            f"{casekey.study_date:>08s}_{casekey.modality.upper()}",
                            f"SE{casekey.se_num}")

    @staticmethod
    def _ratercasekey2path(ratercasekey: RaterCaseKey) -> str:
        return os.path.join(ratercasekey.rater_name,
                            BaseLoader._casekey2path(ratercasekey.to_casekey()))

    def _response_root_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.RESPONSE_ROOT_DIR_NAME)

    def _reference_root_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.REFERENCE_ROOT_DIR_NAME)

    def _lesion_dir_path(self, casekey: CaseKey) -> str:
        return os.path.join(self._reference_root_dir_path(), self._casekey2path(casekey))

    def _response_dir_path(self, ratercasekey: RaterCaseKey) -> str:
        return os.path.join(self._response_root_dir_path(), self._ratercasekey2path(ratercasekey))
