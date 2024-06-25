#!/usr/bin/env python
# coding: UTF-8


from dataclasses import dataclass
from collections import defaultdict

from bidict import bidict
import pandas as pd
from tqdm import tqdm


from pyfroc.keys import CaseKey
from pyfroc.raters.base_rater import BaseRater
from pyfroc.signals import Lesion
from .base_writer import BaseWriter


T_rjafroc_casekey_lesion_dict = dict[tuple[CaseKey, Lesion | None], "RJAFROC_IDs"]


class ObjIDbidict:
    def __init__(self, idx_start=1):
        self.dict = bidict()
        self.idx_start = int(idx_start)

    def get_id_from(self, obj):
        if obj not in self.dict:
            self.dict[obj] = len(self.dict) + self.idx_start
        return self.dict[obj]

    def get_obj_from(self, id: int):
        return self.dict.inv[id]

    def keys(self):
        return self.dict.keys()

    def values(self):
        return self.dict.values()

    def items(self):
        return self.dict.items()


@dataclass(frozen=True)
class RJAFROC_IDs:
    case_id: int
    lesion_id: int
    modality_id: int


class RJAFROCWriter(BaseWriter):
    @classmethod
    def write(cls, xlsx_path: str, rater: BaseRater) -> None:
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
        modality2modalityid = ObjIDbidict(idx_start=0)
        raterid2readerid = ObjIDbidict(idx_start=0)
        lesionid_modalityid_set = defaultdict(set)

        rjafroc_casekey_lesion_dict: T_rjafroc_casekey_lesion_dict = {}

        # Prepare progress bar
        progress_bar = tqdm(desc="Processing ...", total=len(rater)+1)

        # Read evaluation results
        for case_id, (casekey, lesions, rater_result_dict) in enumerate(rater):
            modality_id = modality2modalityid.get_id_from(casekey.modality)

            # TRUTH sheet
            n_lesions = len(lesions)
            if n_lesions == 0:
                lesion_id = 0

                rjafroc_casekey_lesion_dict[(casekey, None)] = RJAFROC_IDs(case_id, lesion_id, modality_id)

                lesionid_modalityid_set[(case_id, lesion_id)].add(modality_id)

                truth_list.append({
                    "CaseID": case_id,
                    "LesionID": lesion_id,
                    "Weight": 0.0,
                    "ReaderID": "",
                    "ModalityID": "",
                    "Paradigm": "",
                })
            else:
                lesion_weight = 1.0 / n_lesions

                for lesion_id, lesion in zip(range(1, n_lesions+1), lesions):
                    rjafroc_casekey_lesion_dict[(casekey, lesion)] = RJAFROC_IDs(case_id, lesion_id, modality_id)

                    lesionid_modalityid_set[(case_id, lesion_id)].add(modality_id)

                    truth_list.append({
                        "CaseID": case_id,
                        "LesionID": lesion_id,
                        "Weight": lesion_weight,
                        "ReaderID": "",
                        "ModalityID": "",
                        "Paradigm": "",
                    })

            # TP and FP sheet
            for ratercasekey, (tp, fp) in rater_result_dict.items():
                reader_id = raterid2readerid.get_id_from(ratercasekey.rater_name)

                for response, lesion in tp:
                    lesion_id = rjafroc_casekey_lesion_dict[(casekey, lesion)].lesion_id

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

            progress_bar.update(1)

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
        readerids_str = ",".join(map(str, sorted(set(raterid2readerid.values()))))
        for row in truth_list:
            row["ReaderID"] = readerids_str

            modalities = lesionid_modalityid_set[(row["CaseID"], row["LesionID"])]
            modality_ids = ",".join(map(str, sorted(modalities)))
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

            cls._write_supporting_information(writer, rjafroc_casekey_lesion_dict, raterid2readerid)

        progress_bar.update(1)
        progress_bar.close()

    @classmethod
    def _write_supporting_information(cls, writer: pd.ExcelWriter,
                                      rjafroc_casekey_lesion_dict: T_rjafroc_casekey_lesion_dict,
                                      ratername2readerid: ObjIDbidict) -> None:
        # Write supporting information
        lesions_list = []

        for (casekey, lesion), rjafroc_id in rjafroc_casekey_lesion_dict.items():
            if lesion is None:
                x, y, z, r = ("", "", "", "")
            else:
                x, y, z, r = (lesion.coords.x, lesion.coords.y, lesion.coords.z, lesion.r)

            lesions_list.append({
                "ModalityID": rjafroc_id.modality_id,
                "modality": casekey.modality,
                "CaseID": rjafroc_id.case_id,
                "patient_id": casekey.patient_id,
                "study_date": casekey.study_date,
                "se_num": casekey.se_num,
                "LesionID": rjafroc_id.lesion_id,
                "x": x,
                "y": y,
                "z": z,
                "diameter": r,
            })

        pd.DataFrame(lesions_list).to_excel(writer, sheet_name='Suppl_Lesions', index=False)

        # Prepare reader_id to rater_name
        ratername_list = []
        for rater_name, reader_id in ratername2readerid.items():
            ratername_list.append({
                "ReaderID": reader_id,
                "Rater": rater_name,
            })

        pd.DataFrame(ratername_list).to_excel(writer, sheet_name='Suppl_Raters', index=False)
