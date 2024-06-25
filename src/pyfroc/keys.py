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
    def from_dcm(cls, dcm: pydicom.Dataset, modality_id: int | None = None) -> "CaseKey":
        if modality_id is None:
            modality = dcm.Modality
        else:
            modality = f"{dcm.Modality}{int(modality_id):d}"

        return CaseKey(patient_id=dcm.PatientID,
                       study_date=dcm.StudyDate,
                       modality=modality,
                       se_num=dcm.SeriesNumber)

    @classmethod
    def from_path(cls, dir_path: str) -> "CaseKey" | None:
        # Search case directories
        dirpath_pattern = r".*?([^\/]+)\/([0-9]{8})_([A-Z]{2}\d*)\/SE([0-9]+)"
        m = re.match(dirpath_pattern, dir_path)

        if m is None:
            return None
        else:
            return CaseKey(patient_id=m.group(1),
                           study_date=m.group(2),
                           modality=m.group(3),
                           se_num=m.group(4))

    def to_ratercasekey(self, rater_name: str) -> "RaterCaseKey":
        return RaterCaseKey(rater_name=rater_name, patient_id=self.patient_id,
                            study_date=self.study_date, modality=self.modality, se_num=self.se_num)

    def without_modalityid(self) -> "CaseKey":
        pattern = r'\d+$'
        modality = re.sub(pattern, '', self.modality)

        return CaseKey(patient_id=self.patient_id,
                       study_date=self.study_date,
                       modality=modality,
                       se_num=self.se_num)


@dataclass(frozen=True)
class RaterCaseKey:
    rater_name: str
    patient_id: str
    study_date: str
    modality: str
    se_num: str

    def to_casekey(self) -> CaseKey:
        return CaseKey(patient_id=self.patient_id,
                       study_date=self.study_date,
                       modality=self.modality,
                       se_num=self.se_num)
