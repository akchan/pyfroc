#!/usr/bin/env python
# coding: UTF-8

from dataclasses import dataclass

import pandas as pd


from pyfroc.raters.base_rater import T_EvaluationResult
from .base_writer import BaseWriter


@dataclass(frozen=True)
class LesionInfo:
    lesion_id: int
    weight: float


class RJAFROCWriter(BaseWriter):
    @classmethod
    def write(cls, xlsx_path: str,
              evaluation_result: T_EvaluationResult) -> None:
        # Prepare dataframes
        columns_df_tp = ["ReaderID", "ModalityID", "CaseID", "LesionID", "TP_Rating"]
        df_tp = pd.DataFrame(columns=columns_df_tp)
        tp_list = []

        columns_df_fp = ["ReaderID", "ModalityID", "CaseID", "FP_Rating"]
        df_fp = pd.DataFrame(columns=columns_df_fp)
        fp_list = []

        columns_df_truth = ["CaseID", "LesionID", "Weight", "ReaderID", "ModalityID", "Paradigm"]
        df_truth = pd.DataFrame(columns=columns_df_truth)
        truth_list = []

        # Prepare a conversion dictionary
        casekey2caseid = cls._build_casekey2caseid_dict(evaluation_result)
        casekey2modalityid = cls._build_casekey2modalityid_dict(evaluation_result)
        ratercasekey2readerid = cls._build_ratercasekey2readerid_dict(evaluation_result)
        lesion2lesionid = cls._build_lesion2lesionid_dict(evaluation_result)

        # Write to dataframes (TRUTH sheet)
        readerids_str = ",".join(map(str, sorted(set(ratercasekey2readerid.values()))))
        modalityids_str = ",".join(map(str, sorted(set(casekey2modalityid.values()))))
        for casekey, (lesions, rater_result_dict) in evaluation_result.items():
            case_id = casekey2caseid[casekey]

            n_lesions = len(lesions)

            if n_lesions == 0:
                truth_list.append({
                    "CaseID": case_id,
                    "LesionID": 0,
                    "Weight": 0,
                    "ReaderID": readerids_str,
                    "ModalityID": modalityids_str,
                    "Paradigm": "",
                })
                continue

            lesion_weight = 1.0 / n_lesions

            for lesion in lesions:
                truth_list.append({
                    "CaseID": case_id,
                    "LesionID": lesion2lesionid[(casekey, lesion)],
                    "Weight": lesion_weight,
                    "ReaderID": readerids_str,
                    "ModalityID": modalityids_str,
                    "Paradigm": "",
                })

        # Set paradigm cells
        if len(truth_list) < 2:
            for _ in range(2 - len(truth_list)):
                truth_list.append({
                    "CaseID": "",
                    "LesionID": "",
                    "Weight": "",
                    "ReaderID": "",
                    "ModalityID": "",
                    "Paradigm": "",
                })
        truth_list[0]["Paradigm"] = "FROC"
        truth_list[1]["Paradigm"] = "FCTRL"

        # Write to dataframes (TP and FP sheets)
        for casekey, (lesions, rater_result_dict) in evaluation_result.items():
            case_id = casekey2caseid[casekey]

            for ratercasekey, (tp, fp) in rater_result_dict.items():
                case_id = casekey2caseid[casekey]
                reader_id = ratercasekey2readerid[ratercasekey]
                modality_id = casekey2modalityid[casekey]

                for response, lesion in tp:
                    lesion_id = lesion2lesionid[(casekey, lesion)]
                    tp_list.append({
                        "ReaderID": reader_id,
                        "ModalityID": modality_id,
                        "CaseID": case_id,
                        "LesionID": lesion_id,
                        "TP_Rating": response.confidence,
                    })

                for response in fp:
                    fp_list.append({
                        "ReaderID": reader_id,
                        "ModalityID": modality_id,
                        "CaseID": case_id,
                        "FP_Rating": response.confidence,
                    })

        # Check empty
        if len(tp_list) == 0:
            tp_list.append({
                "ReaderID": "",
                "ModalityID": "",
                "CaseID": "",
                "LesionID": "",
                "TP_Rating": "",
            })
        if len(fp_list) == 0:
            fp_list.append({
                "ReaderID": "",
                "ModalityID": "",
                "CaseID": "",
                "FP_Rating": "",
            })
        if len(truth_list) == 0:
            truth_list.append({
                "CaseID": "",
                "LesionID": "",
                "Weight": "",
                "ReaderID": "",
                "ModalityID": "",
                "Paradigm": "",
            })

        # Create dataframes from dictionaries
        df_tp = pd.DataFrame(tp_list)
        df_fp = pd.DataFrame(fp_list)
        df_truth = pd.DataFrame(truth_list)

        # Write data
        with pd.ExcelWriter(xlsx_path, engine='openpyxl', mode='w') as writer:
            # Sheets for Rjafroc
            df_tp.to_excel(writer, sheet_name='TP', index=False)
            df_fp.to_excel(writer, sheet_name='FP', index=False)
            df_truth.to_excel(writer, sheet_name='TRUTH', index=False)

            cls._write_supporting_information(writer, casekey2caseid, casekey2modalityid, lesion2lesionid, ratercasekey2readerid)

    @classmethod
    def _build_casekey2caseid_dict(cls, evaluation_result: T_EvaluationResult) -> dict:
        patientid_set = set([casekey.patient_id for casekey in evaluation_result.keys()])
        patientid2caseid = {patient_id: i+1 for i, patient_id in enumerate(patientid_set)}
        casekey2caseid = {casekey: patientid2caseid[casekey.patient_id] for casekey in evaluation_result.keys()}
        return casekey2caseid

    @classmethod
    def _build_casekey2modalityid_dict(cls, evaluation_result: T_EvaluationResult) -> dict:
        modality_set = set([casekey.modality for casekey in evaluation_result.keys()])
        modality2modalityid = {modality: i for i, modality in enumerate(modality_set)}
        casekey2modalityid = {casekey: modality2modalityid[casekey.modality] for casekey in evaluation_result.keys()}
        return casekey2modalityid

    @classmethod
    def _build_ratercasekey2readerid_dict(cls, evaluation_result: T_EvaluationResult) -> dict:
        ratercasekey_list = []
        for lesions, rater_result_dict in evaluation_result.values():
            ratercasekey_list.extend(rater_result_dict.keys())

        rater_name_set = set([ratercasekey.rater_id for ratercasekey in ratercasekey_list])
        ratername2readerid = {rater_name: i for i, rater_name in enumerate(rater_name_set)}

        ratercasekey2readerid = {ratercasekey: ratername2readerid[ratercasekey.rater_id] for ratercasekey in ratercasekey_list}

        return ratercasekey2readerid

    @classmethod
    def _build_lesion2lesionid_dict(cls, evaluation_result: T_EvaluationResult) -> dict:
        lesion2lesionid = {}

        for casekey, (lesions, rater_result_dict) in evaluation_result.items():
            for i, lesion in enumerate(lesions):
                key = (casekey, lesion)
                lesion2lesionid[key] = i + 1

        return lesion2lesionid

    @classmethod
    def _write_supporting_information(cls, writer: pd.ExcelWriter,
                                      casekey2caseid: dict,
                                      casekey2modalityid: dict,
                                      lesion2lesionid: dict,
                                      ratercasekey2readerid: dict) -> None:
        # Write supporting information
        lesions_list = []

        for (casekey, lesion), lesion_id in lesion2lesionid.items():
            lesions_list.append({
                "LesionID": lesion_id,
                "CaseID": casekey2caseid[casekey],
                "ModalityID": casekey2modalityid[casekey],
                "patient_id": casekey.patient_id,
                "study_date": casekey.study_date,
                "modality": casekey.modality,
                "se_num": casekey.se_num,
                "x": lesion.coords.x,
                "y": lesion.coords.y,
                "z": lesion.coords.z,
                "diameter": lesion.r,
            })

        pd.DataFrame(lesions_list).to_excel(writer, sheet_name='Suppl_Lesions', index=False)

        # Prepare reader_id to rater_name
        readerid2ratername_dict = {}
        for ratercasekey, reader_id in ratercasekey2readerid.items():
            readerid2ratername_dict[reader_id] = ratercasekey.rater_id
        ratername_list = []
        for reader_id, rater_name in readerid2ratername_dict.items():
            ratername_list.append({
                "ReaderID": reader_id,
                "Rater": rater_name,
            })

        pd.DataFrame(ratername_list).to_excel(writer, sheet_name='Suppl_Raters', index=False)
