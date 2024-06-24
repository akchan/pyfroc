#!/usr/bin/env python
# coding: UTF-8

from bidict import bidict
from matching.algorithms import hospital_resident
from matching.players import Player, Hospital
from matching.games import HospitalResident
from matching.matchings import MultipleMatching

from pyfroc.raters import BaseRater
from pyfroc.signals import Response, Lesion, T_TruePositive, T_FalsePositive


class WithinLesionRater(BaseRater):
    @classmethod
    def evaluate_case_responses(cls, responses: list[Response], lesions: list[Lesion], check_players=False) -> tuple[T_TruePositive, T_FalsePositive]:
        """Evaluate the case responses and lesions to determine the true positive and false positive results.

        This function takes a list of responses and lesions as input and performs the evaluation process to determine the true positive and false positive results. It performs the matching process using the hospital-resident algorithm. The matching result is returned as true positive and false positive signals.

        Args:
            responses (list[Response]): A list of response objects representing the responses.
            lesions (list[Lesion]): A list of lesion objects representing the lesions.

        Returns:
            tuple[T_TruePositive, T_FalsePositive]: A tuple containing the true positive and false positive results.

        """
        responses_bidict, lesions_bidict = cls._build_bidict(responses, lesions)
        cls._set_prefs_of_players(responses_bidict, lesions_bidict)

        residents = list(responses_bidict.values())
        hospitals = list(lesions_bidict.values())

        if len(residents) > 0 and len(hospitals) > 0:
            # Set the residents and hospitals for validation
            if check_players:
                _ = HospitalResident(residents, hospitals)

            # Call hospital_resident() function directly to avoid deep copy of the players objects
            matching_result = MultipleMatching(hospital_resident(residents, hospitals, optimal="hospital"))

            true_positive, false_positive = cls._mathcing_result2signals(matching_result, responses_bidict, lesions_bidict)
        else:
            true_positive = []
            false_positive = list(responses_bidict.keys())

        return true_positive, false_positive

    @classmethod
    def _build_bidict(cls, responses: list[Response], lesions: list[Lesion]) -> tuple[bidict[Response, Player], bidict[Lesion, Hospital]]:
        responses_bidict = bidict({resp: Player(f"response{i:04d}") for i, resp in enumerate(responses)})

        lesions_bidict = bidict({lesion: Hospital(f"lesion{i:04d}", capacity=1) for i, lesion in enumerate(lesions)})

        return responses_bidict, lesions_bidict

    @classmethod
    def _set_prefs_of_players(cls, responses_bidict: bidict[Response, Player], lesions_bidict: bidict[Lesion, Hospital]) -> None:
        if len(responses_bidict) == 0:
            return

        # Set lesion preferences
        for lesion, hospital in lesions_bidict.items():
            hospital.capacity = 1

            selected_responses = []
            for response in responses_bidict.keys():
                if response.is_true_positive(lesion):
                    selected_responses.append(response)

            sorted_responses = sorted(selected_responses, key=lambda x: lesion.distance(x))
            pref = [responses_bidict[response] for response in sorted_responses]

            hospital.set_prefs(pref)

        # Set response preferences
        for response, player in responses_bidict.items():
            selected_lesions = []
            for lesion in lesions_bidict.keys():
                if response.is_true_positive(lesion):
                    selected_lesions.append(lesion)

            sorted_lesions = sorted(selected_lesions, key=lambda x: response.distance(x))
            pref = [lesions_bidict[lesion] for lesion in sorted_lesions]

            player.set_prefs(pref)

    @classmethod
    def _mathcing_result2signals(cls, matching_result: MultipleMatching,
                                 responses_bidict: bidict[Response, Player],
                                 lesions_bidict: bidict[Lesion, Hospital]) -> tuple[T_TruePositive, T_FalsePositive]:
        true_positive: T_TruePositive = []

        for hospital, residents in matching_result.items():
            lesion = lesions_bidict.inverse[hospital]

            for resident in residents:
                responses = responses_bidict.inverse[resident]
                true_positive.append((responses, lesion))

        false_positive: T_FalsePositive = list(set(responses_bidict.keys()) - set(map(lambda x: x[0], true_positive)))

        return true_positive, false_positive
