#!/usr/bin/env python
# coding: UTF-8

from dataclasses import dataclass

from pyfroc.signals import Response, Lesion, T_TruePositive, T_FalsePositive

T_EvaluationInput = dict["CaseKey", tuple[list[Lesion], dict["RaterCaseKey", list[Response]]]]
T_EvaluationResult = dict["CaseKey", tuple[list[Lesion], dict["RaterCaseKey", tuple[T_TruePositive, T_FalsePositive]]]]


@dataclass(frozen=True)
class CaseKey:
    patient_id: str
    study_date: str
    modality: str
    se_num: str

    def to_ratercasekey(self, rater_id: str) -> "RaterCaseKey":
        return RaterCaseKey(rater_id=rater_id, patient_id=self.patient_id,
                            study_date=self.study_date, modality=self.modality, se_num=self.se_num)


@dataclass(frozen=True)
class RaterCaseKey:
    rater_id: str
    patient_id: str
    study_date: str
    modality: str
    se_num: str

    def to_casekey(self) -> CaseKey:
        return CaseKey(patient_id=self.patient_id,
                       study_date=self.study_date,
                       modality=self.modality,
                       se_num=self.se_num)
