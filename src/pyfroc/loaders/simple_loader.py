from dataclasses import dataclass

from pyfroc.coords import ScannerCoordinates
from pyfroc.loaders import BaseLoader
from pyfroc.keys import RaterCaseKey, T_RatorInput
from pyfroc.signals import Lesion, Response


@dataclass
class SignalRaw:
    name: str
    x: float
    y: float
    z: float
    r: float
    confidence: float


@dataclass
class ReferenceRaw:
    case_id: str
    modality_id: str
    signals: list[SignalRaw]


@dataclass
class ResponseRaw:
    rater_id: str
    case_id: str
    modality_id: str
    signals: list[SignalRaw]


T_case_list = list[tuple[ReferenceRaw, ResponseRaw]]


class SimpleLoader(BaseLoader):
    def __init__(self, case_list: T_case_list):
        self.case_list = case_list

    def __len__(self):
        return len(self.case_list)

    def __getitem__(self, index: int) -> T_RatorInput:
        if index < 0 or index >= len(self):
            raise IndexError("Index out of range")

        reference_raw, response_raw = self.case_list[index]

        # Convert the signal objects to the pyfroc objects
        responses = self.read_responses(response_raw)
        lesions = self.read_lesions(reference_raw)  # type: ignore
        ratercasekey = self.build_ratercasekey(response_raw)

        return ratercasekey, lesions, responses

    def read_responses(self, raw_data: ReferenceRaw | ResponseRaw) -> list[Response]:
        ret = []

        for i, signal in enumerate(raw_data.signals):
            signal_name = f"C{raw_data.case_id}"
            if isinstance(raw_data, ResponseRaw):
                signal_name += f"_R{raw_data.rater_id}"
            signal_name += f"_{i:03d}"

            coords = ScannerCoordinates(signal.x, signal.y, signal.z)
            response = Response(coords, signal.confidence, signal.r, signal_name)

            ret.append(response)

        return ret

    def read_lesions(self, reference_raw: ReferenceRaw):
        return [response.to_lesion() for response in self.read_responses(reference_raw)]

    def build_ratercasekey(self, response_raw: ResponseRaw):
        rater_name = response_raw.rater_id
        patient_id = response_raw.case_id
        study_date = ""
        modality = response_raw.modality_id
        modality_id = int(response_raw.modality_id)
        se_num = ""

        return RaterCaseKey(rater_name, patient_id, study_date, modality, modality_id, se_num)
