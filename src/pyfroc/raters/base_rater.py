#!/usr/bin/env python
# coding: UTF-8


from abc import ABC, abstractmethod

from pyfroc.loaders.base_loader import BaseLoader
from pyfroc.signals import Response, Lesion, T_TruePositive, T_FalsePositive
from pyfroc.keys import CaseKey, RaterCaseKey, T_EvaluationInput, T_EvaluationResult


class BaseRater(ABC):
    def __init__(self, loader: BaseLoader) -> None:
        self.loader = loader

    def __len__(self) -> int:
        return len(self.loader)
        
    def __getitem__(self, key: int) -> tuple[list[Lesion], dict[RaterCaseKey, list[Response]]]:
        return self.loader[key]
    
    @classmethod
    @abstractmethod
    def evaluate_case_responses(cls, responses: list[Response], lesions: list[Lesion]) -> tuple[T_TruePositive, T_FalsePositive]:
        """Evaluate the responses of a specific case and devide them into true positive and false positive.

        Args:
            responses (list[Response]): list of Response objects
            lesions (list[Lesion]): list of Lesion objects

        Returns:
            True positive (list[tuple[Response, Lesion]]): list of tuples of Response and Lesion objects
            False positive (list[Response]): list of Response objects
        """
        raise NotImplementedError()

    @classmethod
    def evaluate(cls, input: T_EvaluationInput) -> T_EvaluationResult:
        evaluation_result: T_EvaluationResult = {}

        for casekey, (lesions, responses_dict) in input.items():
            evaluation_result[casekey] = (lesions, {})

            for ratercasekey, responses in responses_dict.items():
                tp, fp = cls.evaluate_case_responses(responses, lesions)
                evaluation_result[casekey][1][ratercasekey] = (tp, fp)

        return evaluation_result
