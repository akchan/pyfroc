#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod
from collections.abc import Sequence
from itertools import product

import glob
import os
import sys

import pydicom

from pyfroc.keys import CaseKey, RaterCaseKey, T_RatorInput
from pyfroc.signals import BaseResponse, BaseLesion, sort_signals
from pyfroc.utils import list_dcm_files


class BaseLoader(ABC):
    REFERENCE_ROOT_DIR_NAME = "reference"
    RESPONSE_ROOT_DIR_NAME = "responses"

    def __init__(self, root_dir_path: str, verbose=True):
        self.root_dir_path = root_dir_path
        self.verbose = verbose
        self.casekey_ratercasekey_dict: dict[CaseKey, list[RaterCaseKey]] = {}

        self._init_casekey_ratercasekey_dict()

    def __len__(self):
        return len(self.casekey_ratercasekey_dict)

    def __getitem__(self, index: int) -> T_RatorInput:
        if index >= len(self):
            raise IndexError("Index out of range")

        casekey = list(self.casekey_ratercasekey_dict.keys())[index]
        lesions_raw = self.read_lesions(self._lesion_dir_path(casekey))
        lesions = sort_signals(lesions_raw)

        rater_responses = {}

        for ratercasekey in self.casekey_ratercasekey_dict[casekey]:
            responses_raw = self.read_responses(self._response_dir_path(ratercasekey))
            rater_responses[ratercasekey] = sort_signals(responses_raw)

        return casekey, lesions, rater_responses

    @abstractmethod
    def read_responses(self, case_dir_path: str) -> Sequence[BaseResponse]:
        """
        Reads and returns a list of Response objects from the specified case directory path.
        This abstract method should be implemented in the subclass.

        Args:
            case_dir_path (str): The path to the case directory.

        Returns:
            list[Response]: A list of Response objects.
        """
        raise NotImplementedError("This method should be implemented in the subclass.")

    def read_lesions(self, case_dir_path: str) -> Sequence[BaseLesion]:
        responses = self.read_responses(case_dir_path)
        return [resp.to_lesion() for resp in responses]

    def prepare_dir(self, dcm_root_dir_path: str,
                    number_of_raters: int = 3,
                    number_of_modality_or_treatment=2) -> None:
        """Prepare the directories to store the reference lesion and response files.

        This method prepares the required directories to store the files for further processing.
        It creates a reference directory and multiple rater directories based on the specified parameters.

        Args:
            dcm_root_dir_path (str): The root directory path containing the DICOM files.
            tgt_dir_path (str): The target directory path where the directories will be created.
            number_of_raters (int, optional): The number of rater directories to create. Defaults to 3.

        Returns:
            None
        """
        if self.verbose:
            print("Preparing directories...")

        assert number_of_raters > 0, "number_of_raters should be greater than 0."

        dcm_path_list = list_dcm_files(dcm_root_dir_path, recursive=True)

        if len(dcm_path_list) == 0:
            print("No DICOM files found.", file=sys.stderr)
            return None

        # Set casekey_list from dicom files
        casekey_set = set()

        for dcm_path in dcm_path_list:
            dcm = pydicom.dcmread(dcm_path)

            for i in range(number_of_modality_or_treatment):
                key = CaseKey.from_dcm(dcm)

                casekey_set.add(key)

        # Set self.casekey_ratercasekey_dict using casekey_set
        self.casekey_ratercasekey_dict.clear()
        for casekey in list(casekey_set):
            self.casekey_ratercasekey_dict[casekey] = []

            # Set ratercasekey based on self.casekey_list
            for rater_id, modality_id in product(range(number_of_raters),
                                                 range(number_of_modality_or_treatment)):
                rater_name = f"rater{rater_id+1:02d}"
                ratercasekey = casekey.to_ratercasekey(rater_name=rater_name, modality_id=modality_id)

                self.casekey_ratercasekey_dict[casekey].append(ratercasekey)

        if self.verbose:
            n_cases = len(set(map(lambda c: c.patient_id, self.casekey_ratercasekey_dict.keys())))
            n_series = len(self.casekey_ratercasekey_dict.keys())

            print("Detected dicom:")
            print(f"  Number of dicom files: {len(dcm_path_list)}")
            print(f"  Number of cases: {n_cases}")
            print(f"  Number of series: {n_series}")

        # Create a reference directory
        self._create_dirs()

    def _create_dirs(self) -> None:
        # Create reference directories
        for casekey, ratercasekey_list in self.casekey_ratercasekey_dict.items():
            dir_path = os.path.join(self._reference_root_dir_path(), casekey.to_path())

            if self.verbose:
                print(f"Creating directory: {dir_path}")

            os.makedirs(dir_path, exist_ok=True)

            # Create response directories
            for ratercasekey in ratercasekey_list:
                dir_path = os.path.join(self._response_root_dir_path(), ratercasekey.to_path())

                if self.verbose:
                    print(f"Creating directory: {dir_path}")

                os.makedirs(dir_path, exist_ok=True)

    def _init_casekey_ratercasekey_dict(self) -> None:
        self.casekey_ratercasekey_dict.clear()

        # Search reference directories
        for dir_path in glob.glob(os.path.join(self._reference_root_dir_path(), "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            ratercasekey = CaseKey.from_path(dir_path)

            if ratercasekey is None:
                if self.verbose:
                    print(f"Invalid directory: {dir_path}", file=sys.stderr)
                continue

            self.casekey_ratercasekey_dict[ratercasekey] = []

        # Search response directories
        for dir_path in glob.glob(os.path.join(self._response_root_dir_path(), "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            ratercasekey = RaterCaseKey.from_path(dir_path)

            if ratercasekey is None:
                if self.verbose:
                    print(f"Invalid directory: {dir_path}", file=sys.stderr)
                continue

            casekey = ratercasekey.to_casekey()

            dir_path = os.path.join(self._reference_root_dir_path(), casekey.to_path())
            assert casekey in self.casekey_ratercasekey_dict, f"Directory {dir_path} not found in the reference directory, but found in the response directory."

            self.casekey_ratercasekey_dict[casekey].append(ratercasekey)

    def _response_root_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.RESPONSE_ROOT_DIR_NAME)

    def _reference_root_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.REFERENCE_ROOT_DIR_NAME)

    def _lesion_dir_path(self, casekey: CaseKey) -> str:
        return os.path.join(self._reference_root_dir_path(), casekey.to_path())

    def _response_dir_path(self, ratercasekey: RaterCaseKey) -> str:
        return os.path.join(self._response_root_dir_path(), ratercasekey.to_path())


class DirectorySetup(BaseLoader):
    def read_responses(self, case_dir_path: str) -> Sequence[BaseResponse]:
        return []
