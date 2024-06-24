#!/usr/bin/env python
# coding: UTF-8

from bidict import bidict
from matching.algorithms import hospital_resident
from matching.players import Player, Hospital
from matching.games import HospitalResident
from matching.matchings import MultipleMatching

from pyfroc.raters import BaseRater
from pyfroc.signals import Response, Lesion, T_TruePositive, T_FalsePositive


    def evaluate_case_responses(self, responses: list[Response], lesions: list[Lesion], check_players=False) -> tuple[T_TruePositives, T_FalsePositives]:
        """Evaluate the case responses and lesions to determine the true positive and false positive results.

        This function takes a list of responses and lesions as input and performs the evaluation process to determine the true positive and false positive results. It performs the matching process using the hospital-resident algorithm. The matching result is returned as true positive and false positive signals.

        Args:
            responses (list[Response]): A list of response objects representing the responses.
            lesions (list[Lesion]): A list of lesion objects representing the lesions.

        Returns:
            tuple[T_TruePositive, T_FalsePositive]: A tuple containing the true positive and false positive results.

        """
        responses_bidict, lesions_bidict = self.build_bidict(responses, lesions)
        self.set_prefs_of_players(responses_bidict, lesions_bidict)

        residents = list(responses_bidict.values())
        hospitals = list(lesions_bidict.values())

        if len(residents) > 0 and len(hospitals) > 0:
            # Set the residents and hospitals for validation
            if check_players:
                _ = HospitalResident(residents, hospitals)

            # Call hospital_resident() function directly to avoid deep copy of the players objects
            # in the HospitalResident.__init__() method.
            matching_result = MultipleMatching(hospital_resident(residents, hospitals, optimal="hospital"))

            true_positive, false_positive = self.mathcing_result2signals(matching_result, responses_bidict, lesions_bidict)
        else:
            true_positive = []
            false_positive = list(responses_bidict.keys())

        return true_positive, false_positive

    @staticmethod
    def build_bidict(responses: list[Response], lesions: list[Lesion]) -> tuple[bidict[Response, Player], bidict[Lesion, Hospital]]:
        responses_bidict = bidict({resp: Player(f"response{i:04d}") for i, resp in enumerate(responses)})

        lesions_bidict = bidict({lesion: Hospital(f"lesion{i:04d}", capacity=1) for i, lesion in enumerate(lesions)})

        return responses_bidict, lesions_bidict

    @staticmethod
    def set_prefs_of_players(responses_bidict: bidict[Response, Player], lesions_bidict: bidict[Lesion, Hospital]) -> None:
        if len(responses_bidict) == 0:
            return

        # Set lesion preferences
        for lesion, hospital in lesions_bidict.items():
            hospital.capacity = 1

            responses = responses_bidict.keys()
            sorted_responses = sorted(responses, key=lambda response: lesion.distance(response))

            # Convert the responses to players and set the preferences
            pref = [responses_bidict[response] for response in sorted_responses]
            hospital.set_prefs(pref)

        # Set response preferences
        for response, player in responses_bidict.items():
            lesions = lesions_bidict.keys()

            sorted_lesions = sorted(lesions, key=lambda lesion: response.distance(lesion))

            # Convert the responses to players and set the preferences
            pref = [lesions_bidict[lesion] for lesion in sorted_lesions]
            player.set_prefs(pref)

    @staticmethod
    def mathcing_result2signals(matching_result: MultipleMatching,
                                responses_bidict: bidict[Response, Player],
                                lesions_bidict: bidict[Lesion, Hospital]) -> tuple[T_TruePositives, T_FalsePositives]:
        true_positives: T_TruePositives = []

        for hospital, residents in matching_result.items():
            assert len(residents) in [0, 1], "Each hospital (lesion) should have at most one resident (response)."

            lesion = lesions_bidict.inverse[hospital]

            # Use for loop to handle the both cases of 0 and 1 resident
            for resident in residents:
                response = responses_bidict.inverse[resident]

                if response.is_true_positive(lesion):
                    true_positives.append((response, lesion))

        false_positive: T_FalsePositives = list(set(responses_bidict.keys()) - set(map(lambda t: t[0], true_positives)))

        return true_positives, false_positive
