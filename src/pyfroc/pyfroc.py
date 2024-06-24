#!/usr/bin/env python
# coding: UTF-8

from pyfroc.loaders import BaseLoader, SegNRRDLoader
from pyfroc.raters import NearestPairRater
from pyfroc.writers import RJAFROCWriter


def prepare(dcm_dir_path: str, tgt_dir_path, num_of_raters: int) -> None:
    BaseLoader.prepare(dcm_dir_path, tgt_dir_path, num_of_raters)


def evaluate(tgt_dir: str, loader_class_flag: str, rater_class_flag: str, out_path: str) -> None:
    if loader_class_flag == "SegNRRDLoader":
        loader_class = SegNRRDLoader
    else:
        raise ValueError(f"Unknown loader class flag: {loader_class_flag}")

    if rater_class_flag == "WithinLesionRater":
        rater_class = NearestPairRater
    else:
        raise ValueError(f"Unknown rater class flag: {rater_class_flag}")

    evaluation_input = loader_class.read(tgt_dir)
    evaluation_result = rater_class.evaluate(evaluation_input)

    RJAFROCWriter.write(out_path, evaluation_result)
