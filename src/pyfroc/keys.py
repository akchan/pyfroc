#!/usr/bin/env python
# coding: UTF-8

from dataclasses import dataclass
import re

import pydicom

from pyfroc.signals import Response, Lesion, T_TruePositives, T_FalsePositives

T_EvaluationInput = tuple["CaseKey", list[Lesion], dict["RaterCaseKey", list[Response]]]
T_EvaluationResult = tuple["CaseKey", list[Lesion], dict["RaterCaseKey", tuple[T_TruePositives, T_FalsePositives]]]


@dataclass(frozen=True)
class CaseKey:
    patient_id: str
    study_date: str
    modality: str
    se_num: str

    @classmethod
    def from_dcm(cls, dcm: pydicom.Dataset) -> "CaseKey":
        return CaseKey(patient_id=dcm.PatientID,
                       study_date=dcm.StudyDate,
                       modality=dcm.Modality,
                       se_num=dcm.SeriesNumber)

    @classmethod
    def from_path(cls, dir_path: str) -> "CaseKey | None":
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

    def to_path(self) -> str:
        return f"{self.patient_id}/{self.study_date}_{self.modality}/SE{self.se_num}"

    def to_ratercasekey(self, rater_name: str, modality_id: int) -> "RaterCaseKey":
        return RaterCaseKey(rater_name=rater_name,
                            patient_id=self.patient_id,
                            study_date=self.study_date,
                            modality=self.modality,
                            modality_id=modality_id,
                            se_num=self.se_num)


@dataclass(frozen=True)
class RaterCaseKey:
    rater_name: str
    patient_id: str
    study_date: str
    modality: str
    modality_id: int
    se_num: str

    @classmethod
    def from_path(cls, dir_path: str) -> "RaterCaseKey | None":
        # Search case directories
        dirpath_pattern = r".*?([^\/]+)\/([^\/]+)\/([0-9]{8})_([A-Z]{2})([0-9]+)\/SE([0-9]+)"
        m = re.match(dirpath_pattern, dir_path)

        if m is None:
            return None
        else:
            return RaterCaseKey(rater_name=m.group(1),
                                patient_id=m.group(2),
                                study_date=m.group(3),
                                modality=m.group(4),
                                modality_id=int(m.group(5)),
                                se_num=m.group(6))

    def to_casekey(self) -> CaseKey:
        return CaseKey(patient_id=self.patient_id,
                       study_date=self.study_date,
                       modality=self.modality,
                       se_num=self.se_num)

    def to_path(self) -> str:
        return f"{self.rater_name}/{self.patient_id}/{self.study_date}_{self.modality}{self.modality_id}/SE{self.se_num}"
