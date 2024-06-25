#!/usr/bin/env python
# coding: UTF-8

from dataclasses import dataclass

from pyfroc.signals import Response, Lesion, T_TruePositives, T_FalsePositives

T_EvaluationInput  = tuple["CaseKey", list[Lesion], dict["RaterCaseKey", list[Response]]]
T_EvaluationResult = tuple["CaseKey", list[Lesion], dict["RaterCaseKey", tuple[T_TruePositives, T_FalsePositives]]]


@dataclass(frozen=True)
class CaseKey:
    patient_id: str
    study_date: str
    modality: str
    se_num: str

    def to_ratercasekey(self, rater_name: str) -> "RaterCaseKey":
        return RaterCaseKey(rater_name=rater_name, patient_id=self.patient_id,
                            study_date=self.study_date, modality=self.modality, se_num=self.se_num)


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

