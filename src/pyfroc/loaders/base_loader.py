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
from pyfroc.utils import list_dcm_files, count_directories


class BaseLoader(ABC):
    REFERENCE_ROOT_DIR_NAME = "reference"
    RESPONSE_ROOT_DIR_NAME = "responses"

    def __init__(self, root_dir_path: str, verbose=True):
        self.root_dir_path = root_dir_path
        self.verbose = verbose

        self.ratercasekey_list: list[RaterCaseKey] = []

        self.init_ratercasekey_list_by_dirs()

    def __len__(self):
        return len(self.ratercasekey_list)

    def __getitem__(self, index: int) -> T_RatorInput:
        if index >= len(self):
            raise IndexError("Index out of range")

        ratercasekey = self.ratercasekey_list[index]

        # Read lesions
        lesions_raw = self.read_lesions(self.lesion_dir_path(ratercasekey.to_casekey()))
        lesions = sort_signals(lesions_raw)

        # Read responses
        responses_raw = self.read_responses(self.response_dir_path(ratercasekey))
        responses = sort_signals(responses_raw)

        return ratercasekey, lesions, responses

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
                    number_of_modality_or_treatment: int = 2) -> None:
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
            print("[Error]No DICOM files found.", file=sys.stderr)
            return None

        # Set casekey_list from dicom files
        casekey_set = set()
        for dcm_path in dcm_path_list:
            dcm = pydicom.dcmread(dcm_path)
            casekey_set.add(CaseKey.from_dcm(dcm))
        self.casekey_list = list(casekey_set)

        # Set self.ratercasekey_list using casekey_set
        self.ratercasekey_list.clear()
        for casekey in self.casekey_list:
            for rater_id, modality_id in product(range(number_of_raters),
                                                 range(number_of_modality_or_treatment)):
                rater_name = f"rater{rater_id+1:02d}"
                ratercasekey = casekey.to_ratercasekey(rater_name=rater_name, modality_id=modality_id)

                self.ratercasekey_list.append(ratercasekey)

        self.sort_casekey_list()
        self.sort_ratercasekey_list()

        if self.verbose:
            n_cases = len(set(map(lambda c: c.patient_id, self.casekey_list)))
            n_series = len(self.casekey_list)

            print("Detected dicom:")
            print(f"  Dicom files: {len(dcm_path_list)}")
            print(f"  Cases : {n_cases}")
            print(f"  Series: {n_series}")

        # Create a reference directory
        self._create_dirs()

    def _create_dirs(self) -> None:
        # Create reference directories
        for casekey in self.casekey_list:
            dir_path = os.path.join(self.response_root_dir_path(), casekey.to_path())

            if self.verbose:
                print(f"Creating: {dir_path}")

            os.makedirs(dir_path, exist_ok=True)

        # Create response directories
        for ratercasekey in self.ratercasekey_list:
            dir_path = os.path.join(self.response_root_dir_path(), ratercasekey.to_path())

            if self.verbose:
                print(f"Creating: {dir_path}")

            os.makedirs(dir_path, exist_ok=True)

    def init_ratercasekey_list_by_dirs(self) -> None:
        self.ratercasekey_list.clear()

        # Search response directories
        for dir_path in glob.glob(os.path.join(self.response_root_dir_path(), "**"), recursive=True):
            if not os.path.isdir(dir_path):
                continue

            ratercasekey = RaterCaseKey.from_path(dir_path)

            if ratercasekey is None:
                continue

            self.ratercasekey_list.append(ratercasekey)
        self.sort_ratercasekey_list()

        self.casekey_list = list(set([ratercasekey.to_casekey() for ratercasekey in self.ratercasekey_list]))
        self.sort_casekey_list()

    def sort_casekey_list(self) -> None:
        # Sort self.casekey_list
        self.casekey_list = sorted(self.casekey_list, key=lambda ck: ck.study_date)
        self.casekey_list = sorted(self.casekey_list, key=lambda ck: ck.patient_id)
        self.casekey_list = sorted(self.casekey_list, key=lambda ck: ck.modality)

    def sort_ratercasekey_list(self) -> None:
        # Sort self.ratercasekey_list
        self.ratercasekey_list = sorted(self.ratercasekey_list, key=lambda rck: rck.patient_id)
        self.ratercasekey_list = sorted(self.ratercasekey_list, key=lambda rck: rck.rater_name)
        self.ratercasekey_list = sorted(self.ratercasekey_list, key=lambda rck: rck.modality_id)

    def validate_dirs(self) -> bool:
        """This method needs documentation and some tests.
        """
        ret_flag = True

        # Validate reference directories
        ref_dir_list = []
        casekey_list = []

        for dir_path in glob.glob(os.path.join(self.reference_root_dir_path(), "**"), recursive=True):
            if not (os.path.isdir(dir_path) and count_directories(dir_path) == 0):
                continue
            ref_dir_list.append(dir_path)

            casekey = CaseKey.from_path(dir_path)

            if casekey is None:
                ret_flag = False
                if self.verbose:
                    print(f"Invalid directory: {dir_path}")
                continue
            casekey_list.append(casekey)

        # Validate response directories
        res_dir_list = []
        ratercasekey_list = []

        for dir_path in glob.glob(os.path.join(self.response_root_dir_path(), "**"), recursive=True):
            if not (os.path.isdir(dir_path) and count_directories(dir_path) == 0):
                continue
            res_dir_list.append(dir_path)

            ratercasekey = RaterCaseKey.from_path(dir_path)

            if ratercasekey is None:
                ret_flag = False
                if self.verbose:
                    print(f"Invalid directory: {dir_path}")
                continue

            ratercasekey_list.append(ratercasekey)

        # Print detected directories
        if self.verbose:
            print("Reference directory:")
            for dir_path in sorted(map(self.lesion_dir_path, casekey_list)):
                print("  ", dir_path)
            print("Response directory:")
            for dir_path in sorted(map(self.response_dir_path, ratercasekey_list)):
                print("  ", dir_path)
            print(f"Valid reference directory: {len(casekey_list)} / {len(ref_dir_list)}")
            print(f"Valid response directory : {len(ratercasekey_list)} / {len(res_dir_list)}")

        return ret_flag

    def response_root_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.RESPONSE_ROOT_DIR_NAME)

    def reference_root_dir_path(self) -> str:
        return os.path.join(self.root_dir_path, self.REFERENCE_ROOT_DIR_NAME)

    def lesion_dir_path(self, casekey: CaseKey) -> str:
        return os.path.join(self.reference_root_dir_path(), casekey.to_path())

    def response_dir_path(self, ratercasekey: RaterCaseKey) -> str:
        return os.path.join(self.response_root_dir_path(), ratercasekey.to_path())


class DirectorySetup(BaseLoader):
    def __init__(self, root_dir_path: str, verbose=True):
        self.root_dir_path = root_dir_path
        self.verbose = verbose

        self.ratercasekey_list: list[RaterCaseKey] = []

    def read_responses(self, case_dir_path: str) -> Sequence[BaseResponse]:
        return []
