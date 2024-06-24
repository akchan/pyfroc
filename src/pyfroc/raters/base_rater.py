#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

from pyfroc.loaders.base_loader import BaseLoader
from pyfroc.signals import Response, Lesion, T_TruePositives, T_FalsePositives
from pyfroc.keys import T_EvaluationResult


class BaseRater(ABC):
    def __init__(self, loader: BaseLoader):
        self.loader = loader

    def __len__(self):
        return len(self.loader)

    def __getitem__(self, key: int) -> T_EvaluationResult:
        evaluation_input = self.loader[key]
        casekey, lesions, responses_dict = evaluation_input

        evaluation_result: T_EvaluationResult = (casekey, lesions, {})

        for ratercasekey, responses in responses_dict.items():
            tp, fp = self.evaluate_case_responses(responses, lesions)
            evaluation_result[2][ratercasekey] = (tp, fp)

        return evaluation_result

    @abstractmethod
    def evaluate_case_responses(self, responses: list[Response], lesions: list[Lesion]) -> tuple[T_TruePositives, T_FalsePositives]:
        """Evaluate the responses of a specific case and devide them into true positive and false positive.

        Args:
            responses (list[Response]): list of Response objects
            lesions (list[Lesion]): list of Lesion objects

        Returns:
            True positive (list[tuple[Response, Lesion]]): list of tuples of Response and Lesion objects
            False positive (list[Response]): list of Response objects
        """
        raise NotImplementedError()
