#!/usr/bin/env python
# coding: UTF-8

from typing import Type

from pyfroc.loaders import BaseLoader, DirectorySetup
from pyfroc.raters import BaseRater
from pyfroc.writers import BaseWriter


def prepare(dcm_dir_path: str, tgt_dir_path, num_of_raters: int, num_of_modalities: int) -> None:
    direcotry_setup = DirectorySetup(tgt_dir_path)
    direcotry_setup.prepare_dir(dcm_dir_path, num_of_raters, num_of_modalities)


def evaluate(tgt_dir: str,
             loader_class: Type["BaseLoader"],
             rater_class: Type["BaseRater"],
             writer_class: Type["BaseWriter"], out_path: str) -> None:
    loader = loader_class(tgt_dir)
    rater = rater_class(loader)
    writer_class.write(out_path, rater)
