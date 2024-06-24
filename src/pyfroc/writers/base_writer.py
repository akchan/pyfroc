#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

from pyfroc.keys import T_EvaluationResult


class BaseWriter(ABC):
    @classmethod
    @abstractmethod
    def write(cls, path: str, evaluation_result: T_EvaluationResult) -> None:
        raise NotImplementedError()
