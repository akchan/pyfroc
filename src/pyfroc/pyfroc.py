#!/usr/bin/env python
# coding: UTF-8

from typing import Type

from pyfroc.loaders import BaseLoader, DirectorySetup, SegNRRDLoader
from pyfroc.raters import BaseRater, NearestPairRater
from pyfroc.writers import BaseWriter, RJAFROCWriter


def prepare(dcm_dir_path: str, tgt_dir_path, num_of_raters: int, num_of_modalities: int) -> None:
    direcotry_setup = DirectorySetup(tgt_dir_path)
    direcotry_setup.prepare_dir(dcm_dir_path, num_of_raters, num_of_modalities)


def evaluate(tgt_dir: str,
             out_path: str,
             loader_class: Type["BaseLoader"] = SegNRRDLoader,
             rater_class: Type["BaseRater"] = NearestPairRater,
             writer_class: Type["BaseWriter"] = RJAFROCWriter) -> None:
    loader = loader_class(tgt_dir)
    rater = rater_class(loader)
    writer_class.write(out_path, rater)
