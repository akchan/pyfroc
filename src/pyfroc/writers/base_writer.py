#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

from pyfroc.raters import BaseRater


class BaseWriter(ABC):
    @classmethod
    @abstractmethod
    def write(cls, path: str, rater: BaseRater) -> None:
        raise NotImplementedError()
