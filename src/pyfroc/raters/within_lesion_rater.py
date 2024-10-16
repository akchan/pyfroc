#!/usr/bin/env python
# coding: UTF-8


from itertools import zip_longest

from bidict import bidict
from matching.algorithms import hospital_resident
from matching.players import Player, Hospital
from matching.games import HospitalResident
from matching.matchings import MultipleMatching

from pyfroc.raters import BaseRater
from pyfroc.signals import Response, Lesion, T_TruePositives, T_FalsePositives


class WithinLesionRater(BaseRater):
    def evaluate_case_responses(self, lesions: list[Lesion], responses: list[Response], check_players=False) -> tuple[T_TruePositives, T_FalsePositives]:
        """Evaluate the case responses and lesions to determine the true positive and false positive results.

        This function takes a list of responses and lesions as input and performs the evaluation process to determine the true positive and false positive results. It performs the matching process using the hospital-resident algorithm (Gale-Shapley algorithm). Each matched response and lesion pair is devided into the true positive or false positive results based on the  size of the lesion and the distance between the response and lesion.

        Args:
            responses (list[Response]): A list of response objects representing the responses.
            lesions (list[Lesion]): A list of lesion objects representing the lesions.

        Returns:
            tuple[T_TruePositive, T_FalsePositive]: A tuple containing the true positive and false positive results.

        """
        true_positive: T_TruePositives = []
        false_positive: T_FalsePositives = []

        algorithm = LesionResponseMatching(lesions, responses, check_players=check_players)
        paired_lesion_response = algorithm.match()

        for lesion, response in paired_lesion_response:
            if lesion is None and response is None:
                raise ValueError("Both lesion and response cannot be None.")
            elif lesion is None and response is not None:
                # False positive case
                false_positive.append(response)
            elif lesion is not None and response is None:
                # False negative case
                pass
            elif lesion is not None and response is not None:
                if response.is_true_positive(lesion):
                    true_positive.append((lesion, response))
                else:
                    false_positive.append(response)
            else:
                raise ValueError("Invalid combination of lesion and response.")

        return true_positive, false_positive


class LesionResponseMatching:
    def __init__(self, lesions: list[Lesion], responses: list[Response],
                 check_players=False):
        self.lesions = lesions
        self.responses = responses
        self.check_players = check_players

    @staticmethod
    def build_lesion_bidict(lesions: list[Lesion]) -> bidict[Lesion, Hospital]:
        return bidict({lesion: Hospital(f"lesion{i:04d}", capacity=1) for i, lesion in enumerate(lesions)})

    @staticmethod
    def build_response_bidict(responses: list[Response]) -> bidict[Response, Player]:
        return bidict({resp: Player(f"response{i:04d}") for i, resp in enumerate(responses)})

    @staticmethod
    def get_unmatched_responses(matching_result: MultipleMatching,
                                responses_bidict: bidict[Response, Player]) -> list[Response]:
        matched_responses: list[Response] = []
        for residents in matching_result.values():
            for resident in residents:
                matched_responses.append(responses_bidict.inverse[resident])

        unmatched_responses = list(set(responses_bidict.keys()) - set(matched_responses))

        return unmatched_responses

    @staticmethod
    def matching_result2signals(matching_result: MultipleMatching,
                                responses_bidict: bidict[Response, Player],
                                lesions_bidict: bidict[Lesion, Hospital]) -> list[tuple[Lesion, Response | None]]:
        ret = []

        for hospital, residents in matching_result.items():
            lesion = lesions_bidict.inverse[hospital]

            n_residents = len(residents)
            if n_residents == 0:
                ret.append((lesion, None))
            elif n_residents == 1:
                response = responses_bidict.inverse[residents[0]]
                ret.append((lesion, response))
            else:
                raise ValueError(f"Invalid number of residents: {n_residents}. It should be 0 or 1.")

        return ret

    def match(self) -> list[tuple[Lesion | None, Response | None]]:
        # Match the lesions and responses using the hospital-resident algorithm (Gale-Shapley algorithm)
        # Lesion = Hospital
        # Response = Player

        ret: list[tuple[Lesion | None, Response | None]] = []

        if len(self.lesions) > 0 and len(self.responses) > 0:
            # Prepare specific objects for the matching process
            lesions_bidict = LesionResponseMatching.build_lesion_bidict(self.lesions)
            responses_bidict = LesionResponseMatching.build_response_bidict(self.responses)

            # Set the preferences each other
            self.set_players_pref(lesions_bidict, responses_bidict)

            hospitals = list(lesions_bidict.values())
            residents = list(responses_bidict.values())

            # Use utility function to validate the residents and hospitals
            if self.check_players:
                _ = HospitalResident(residents, hospitals)

            # Call hospital_resident() function directly to avoid deep copy of the players objects
            # in the HospitalResident.__init__() method.
            matching_result = MultipleMatching(hospital_resident(residents, hospitals, optimal="hospital"))

            ret.extend(LesionResponseMatching.matching_result2signals(matching_result, responses_bidict, lesions_bidict))

            unmatched_responses = LesionResponseMatching.get_unmatched_responses(matching_result, responses_bidict)
            unmatched_responses = [(None, response) for response in unmatched_responses]

            ret.extend(unmatched_responses)
        else:
            ret.extend(list(zip_longest(self.lesions, self.responses)))

        return ret

    def set_players_pref(self,
                         lesions_bidict: bidict[Lesion, Hospital],
                         responses_bidict: bidict[Response, Player]) -> None:
        if len(responses_bidict) == 0:
            return

        # Set lesion preferences
        for lesion, hospital in lesions_bidict.items():
            responses = responses_bidict.keys()

            # Sort the responses based on the distance from the lesion
            sorted_responses = sorted(responses, key=lambda response: lesion.distance(response))

            # Convert the responses to players and set the preferences
            preference = [responses_bidict[response] for response in sorted_responses]
            hospital.set_prefs(preference)

        # Set response preferences
        for response, player in responses_bidict.items():
            lesions = lesions_bidict.keys()

            # Sort the lesions based on the distance from the response
            sorted_lesions = sorted(lesions, key=lambda lesion: response.distance(lesion))

            # Convert the responses to players and set the preferences
            preference = [lesions_bidict[lesion] for lesion in sorted_lesions]
            player.set_prefs(preference)

        self.is_pref_set = True
