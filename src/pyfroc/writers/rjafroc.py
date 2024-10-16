#!/usr/bin/env python
# coding: UTF-8


from typing import Generic, TypeVar

import pandas as pd
from tqdm import tqdm


from pyfroc.keys import CaseKey, RaterCaseKey
from pyfroc.raters.base_rater import BaseRater
from pyfroc.signals import BaseLesion
from .base_writer import BaseWriter


T = TypeVar("T")


class ObjIDDatabase(Generic[T]):
    def __init__(self, idx_start=1):
        self.dict: dict[T, int] = {}
        self.idx_start = int(idx_start)

    def get_id(self, obj: T) -> int:
        if obj not in self.dict:
            self.dict[obj] = len(self.dict) + self.idx_start

        return self.dict[obj]


class CaseIDDB(ObjIDDatabase):
    def get_id(self, casekey: CaseKey | RaterCaseKey) -> int:
        if isinstance(casekey, RaterCaseKey):
            casekey = casekey.to_casekey()

        return super().get_id(casekey)


class RaterIDDB(ObjIDDatabase):
    def get_id(self, ratercasekey: RaterCaseKey) -> int:
        return super().get_id(ratercasekey.rater_name)


class LesionIDDB:
    def __init__(self, idx_start=1) -> None:
        self.idx_start = int(idx_start)
        self.dict: dict[CaseKey, ObjIDDatabase[BaseLesion | None]] = {}

    def get_id(self, casekey: CaseKey | RaterCaseKey, lesion: BaseLesion | None) -> int:
        if isinstance(casekey, RaterCaseKey):
            casekey = casekey.to_casekey()

        if casekey not in self.dict:
            if lesion is None:
                self.dict[casekey] = ObjIDDatabase(idx_start=0)
            else:
                self.dict[casekey] = ObjIDDatabase(idx_start=self.idx_start)

        return self.dict[casekey].get_id(lesion)


class RJAFROCWriter(BaseWriter):
    @classmethod
    def write(cls, xlsx_path: str, rater: BaseRater, verbose=False) -> None:
        """
        Reference
        ---------

        - [Chapter 3 FROC data format | The RJafroc Quick Start Book](https://dpc10ster.github.io/RJafrocQuickStart/quick-start-froc-data-format.html#quick-start-froc-data-intro)
        """
        # Prepare dataframes
        tp_list = []
        fp_list = []
        truth_set = set()
        response_list = []

        # Prepare a conversion dictionary
        #   rater_id, modality_id should start with 0.
        #   case_id, lesion_id should start with 1.
        #   The lesion_id of cases having no lesion should be 0.
        raterid_db = RaterIDDB(idx_start=0)
        caseid_db = CaseIDDB(idx_start=1)
        lesionid_db = LesionIDDB(idx_start=1)

        modalityid_set = set()

        # Read evaluation results
        for ratercasekey, lesions, tp, fp in tqdm(rater, desc="Evaluating and writing responses..."):
            if verbose:
                print(f"{ratercasekey = }")
                print(f"{lesions = }")
                print(f"{tp = }")
                print(f"{fp = }")
                print("")
            
            # TRUTH sheet
            n_lesions = len(lesions)
            if n_lesions == 0:
                truth_set.add((caseid_db.get_id(ratercasekey),
                               lesionid_db.get_id(ratercasekey, None),
                               0.0,
                               "",
                               "",
                               "",
                               ))
            else:
                lesion_weight = 1.0 / n_lesions

                for lesion in lesions:
                    truth_set.add((caseid_db.get_id(ratercasekey),
                                   lesionid_db.get_id(ratercasekey, lesion),
                                   lesion_weight,
                                   "",
                                   "",
                                   "",
                                   ))

            modalityid_set.add(ratercasekey.modality_id)

            # TP sheet
            for lesion, response in tp:
                tp_list.append({
                    "ReaderID": raterid_db.get_id(ratercasekey),
                    "ModalityID": ratercasekey.modality_id,
                    "CaseID": caseid_db.get_id(ratercasekey),
                    "LesionID": lesionid_db.get_id(ratercasekey, lesion),
                    "TP_Rating": response.confidence,
                })

                response_list.append({
                    "modality": ratercasekey.modality,
                    "modalityID": ratercasekey.modality_id,
                    "CaseID": caseid_db.get_id(ratercasekey),
                    "patient_id": ratercasekey.patient_id,
                    "study_date": ratercasekey.study_date,
                    "RateName": ratercasekey.rater_name,
                    "RaterID": raterid_db.get_id(ratercasekey),
                    "se_num": ratercasekey.se_num,
                    "Response": lesionid_db.get_id(ratercasekey, lesion),
                    "x": response.coords.x,
                    "y": response.coords.y,
                    "z": response.coords.z,
                    "diameter": getattr(response, "r", ""),
                    "Rating": response.confidence,
                    "Judge": "TruePositive",
                })

            # FP sheet
            for response in fp:
                fp_list.append({
                    "ReaderID": raterid_db.get_id(ratercasekey),
                    "ModalityID": ratercasekey.modality_id,
                    "CaseID": caseid_db.get_id(ratercasekey),
                    "FP_Rating": response.confidence,
                })

                response_list.append({
                    "modality": ratercasekey.modality,
                    "modalityID": ratercasekey.modality_id,
                    "CaseID": caseid_db.get_id(ratercasekey),
                    "patient_id": ratercasekey.patient_id,
                    "study_date": ratercasekey.study_date,
                    "RateName": ratercasekey.rater_name,
                    "RaterID": raterid_db.get_id(ratercasekey),
                    "se_num": ratercasekey.se_num,
                    "Response": lesionid_db.get_id(ratercasekey, lesion),
                    "x": response.coords.x,
                    "y": response.coords.y,
                    "z": response.coords.z,
                    "diameter": getattr(response, "r", ""),
                    "Rating": response.confidence,
                    "Judge": "FalsePositive",
                })

        # Convert truth_set to a list
        truth_list = []
        for row in truth_set:
            truth_list.append({
                "CaseID": row[0],
                "LesionID": row[1],
                "Weight": row[2],
                "ReaderID": row[3],
                "ModalityID": row[4],
                "Paradigm": row[5],
            })
        truth_list = sorted(truth_list, key=lambda x: (x["CaseID"], x["LesionID"]))

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

        # Set reader_ids and modality_ids in the TRUTH sheet
        readerids_str = ",".join(map(str, sorted(set(raterid_db.dict.values()))))
        modality_ids = ",".join(map(str, sorted(modalityid_set)))
        for row in truth_list:
            row["ReaderID"] = readerids_str
            row["ModalityID"] = modality_ids

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

        # Create dataframes from lists of dictionaries
        columns_df_tp = ["ReaderID", "ModalityID", "CaseID", "LesionID", "TP_Rating"]
        df_tp = pd.DataFrame(tp_list, columns=columns_df_tp)

        columns_df_fp = ["ReaderID", "ModalityID", "CaseID", "FP_Rating"]
        df_fp = pd.DataFrame(fp_list, columns=columns_df_fp)

        columns_df_truth = ["CaseID", "LesionID", "Weight", "ReaderID", "ModalityID", "Paradigm"]
        df_truth = pd.DataFrame(truth_list, columns=columns_df_truth)

        columns_df_response = ["modality", "modalityID", "CaseID", "patient_id", "study_date",
                               "RateName", "RaterID", "se_num", "Response", "x", "y", "z", "diameter", "Rating", "Judge",]
        df_response = pd.DataFrame(response_list, columns=columns_df_response)

        # Write data
        with pd.ExcelWriter(xlsx_path, engine='openpyxl', mode='w') as writer:
            # Sheets for Rjafroc
            df_tp.to_excel(writer, sheet_name='TP', index=False)
            df_fp.to_excel(writer, sheet_name='FP', index=False)
            df_truth.to_excel(writer, sheet_name='Truth', index=False)
            df_response.to_excel(writer, sheet_name='Suppl_Responses', index=False)

            cls.write_supporting_information(writer, caseid_db, lesionid_db, raterid_db)

    @ staticmethod
    def write_supporting_information(writer: pd.ExcelWriter,
                                     caseid_db: CaseIDDB,
                                     lesionid_db: LesionIDDB,
                                     raterid_db: RaterIDDB) -> None:
        """Write supporting information
        """
        # Suppl_Lesions sheet
        lesions_list = []

        for casekey, lesionid_dict in lesionid_db.dict.items():
            for lesion, lesion_id in lesionid_dict.dict.items():
                if lesion is None:
                    x, y, z, r = ("", "", "", "")
                else:
                    if hasattr(lesion, "r"):
                        r = lesion.r  # type: ignore
                    else:
                        r = ""
                    x, y, z, r = (lesion.coords.x, lesion.coords.y, lesion.coords.z, r)

                lesions_list.append({
                    "modality": casekey.modality,
                    "CaseID": caseid_db.get_id(casekey),
                    "patient_id": casekey.patient_id,
                    "study_date": casekey.study_date,
                    "se_num": casekey.se_num,
                    "LesionID": lesion_id,
                    "x": x,
                    "y": y,
                    "z": z,
                    "diameter": r,
                })

        pd.DataFrame(lesions_list).to_excel(writer, sheet_name='Suppl_Lesions', index=False)

        # Suppl_Raters sheet
        ratername_list = []
        for rater_name, reader_id in raterid_db.dict.items():
            ratername_list.append({
                "ReaderID": reader_id,
                "Rater": rater_name,
            })

        pd.DataFrame(ratername_list).to_excel(writer, sheet_name='Suppl_Raters', index=False)
