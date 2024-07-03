#!/usr/bin/env python
# coding: UTF-8

import pytest


@pytest.fixture(scope="session")
def resources():
    return {
        "dcm_dir_path": "/path/to/dcm",
        "tgt_dir_path": "/path/to/tgt",
        "num_of_raters": 2,
        "num_of_modalities": 2,
        "tgt_dir": "/path/to/tgt",
        "out_path": "/path/to/out",
    }
