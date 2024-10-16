#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod
from collections.abc import Sequence

from pyfroc.loaders.base_loader import BaseLoader
from pyfroc.keys import T_RatorInput, T_WriterInput
from pyfroc.signals import BaseResponse, BaseLesion, T_TruePositives, T_FalsePositives


class BaseRater(ABC):
    def __init__(self, loader: BaseLoader, use_cache=True):
        self.loader = loader
        self.use_cache = use_cache
        self.cache = {}

    def __len__(self):
        return len(self.loader)

    def __getitem__(self, index: int) -> T_WriterInput:
        if self.use_cache and index in self.cache:
            return self.cache[index]

        evaluation_input: T_RatorInput = self.loader[index]
        ratercasekey, lesions, responses = evaluation_input
        tp, fp = self.evaluate_case_responses(lesions, responses)

        writer_input: T_WriterInput = (ratercasekey, lesions, tp, fp)

        if self.use_cache:
            self.cache[index] = writer_input

        return writer_input

    def __iter__(self):
        for key in range(len(self)):
            yield self[key]

    def clear_cache(self):
        self.cache = {}

    @abstractmethod
    def evaluate_case_responses(self, lesions: Sequence[BaseLesion], responses: Sequence[BaseResponse]) -> tuple[T_TruePositives, T_FalsePositives]:
        """Evaluate the responses of a specific case and devide them into true positive and false positive.

        Args:
            responses (list[Response]): list of Response objects
            lesions (list[Lesion]): list of Lesion objects

        Returns:
            True positive (list[tuple[Response, Lesion]]): list of tuples of Response and Lesion objects
            False positive (list[Response]): list of Response objects
        """
        raise NotImplementedError()
