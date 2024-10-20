# pyfroc

Python framework for FROC/AFROC analysis

## Table of contents

- [pyfroc](#pyfroc)
  - [Table of contents](#table-of-contents)
  - [About](#about)
    - [What pyfroc does](#what-pyfroc-does)
    - [What pyfroc doesn't](#what-pyfroc-doesnt)
    - [Use case](#use-case)
      - [Scenario #1](#scenario-1)
      - [Scenario #2](#scenario-2)
      - [Scenario #3](#scenario-3)
  - [Instalation](#instalation)
  - [Sample code (CLI)](#sample-code-cli)
  - [Sample code (Python)](#sample-code-python)
  - [Tutorials](#tutorials)
    - [1. Demonstration using sample data](#1-demonstration-using-sample-data)
    - [2. Perform an AFROC experiment](#2-perform-an-afroc-experiment)
    - [3. How to modify behavior in pyfroc](#3-how-to-modify-behavior-in-pyfroc)
  - [Author](#author)
  - [License](#license)

## About

### What pyfroc does

- Improve the FROC/AFROC analysis process.
- Manage responses of raters.
  - The responses can be made using segmentation tools (e.g., [3D Slicer](https://www.slicer.org/)).
  - You can use your tool if you write a loader class inheriting BaseLoader class.
- Evaluate responses and devide them into true positive or false positive automatically.
  - Using built-in module, the responses within the paired lesion approximated as a sphere is regarded as true positive, otherwise false positive.
- Build a .xlsx file for the [RJafroc](https://github.com/dpc10ster/RJafroc), a R library which runs statistical tests of AFROC (alternative Free-response receiver operating characteristic) analysis.
- Write images of responses with paired lesions (if exists).

### What pyfroc doesn't

- Statistical analysis of JAFROC. This is out of scope of pyfroc. Use [RJafroc](https://github.com/dpc10ster/RJafroc) for statistical analysis.
- FROC/AFROC analysis including multi-modality references because pyfroc doesn't implement an algorithm to match intermodality lesions.

### Use case

pyfroc is designed for specific scenarios of FROC/AFROC analysis. pyfroc itself supports only one modality for reference lesions. If you want to compare two modality using two reference modality, run pyfroc for each reference modality, write .xlsx files for RJafroc, and combine the two .xlsx file manually.

Here are the sample scenarios.

#### Scenario #1

- Compare detection performance between radiologists with and without AI
- The responses will be recored on the same series of DICOM images for radiologists with and without AI.

#### Scenario #2

- Compare a standard MRI protocol with an abbreviated protocol in terms of lesion detection.
- The responses will be recored on the same series of DICOM images for both protocols.

#### Scenario #3

- Compare images reconstructed using an advanced method with images reconstructed using conventional method in terms of the lesion detectability.
- Using either series to record responses.

## Instalation

Run the command below in your terminal.

```bash
pip install pyfroc
```

## Sample code (CLI)

```bash
# Install pyfroc
pip install pyfroc

# Prepare dicrectories for an experiment
pyfroc prepare --dicom-dir ./dicom --num-of-raters 2 --num-of-modalities 2

# Record responses of the raters using 3D Slicer
# See the turorial 2 for details

# Read the responses and create rjafroc_input.xlsx file for RJafroc analysis
pyfroc evaluate --out-format rjafroc_xlsx --write-img --dicom-dir •/dicom

# Run AFROC statistical analysis using the RJafroc
RScript samples/afroc_analysis.R
```

## Sample code (Python)

```python
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


class SampleLoader:
    def __init__(self):
        self.case_list: T_case_list = []

    def __len__(self):
        return len(self.case_list)

    def __getitem__(self, index: int) -> T_RatorInput:
        if index < 0 or index >= len(self):
            raise IndexError("Index out of range")

        reference_raw, response_raw = self.case_list[index]

        # Convert the signal objects to the pyfroc objects
        responses = self.read_signals(reference_raw)
        lesions = self.read_signals(response_raw)
        ratercasekey = self.build_ratercasekey(response_raw)

        return ratercasekey, lesions, responses

    def read_signals(self, raw_data: ReferenceRaw | ResponseRaw):
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

    def build_ratercasekey(self, response_raw: ResponseRaw):
        rater_name = response_raw.rater_id
        patient_id = response_raw.case_id
        study_date = ""
        modality = response_raw.modality_id
        modality_id = int(response_raw.modality_id)
        se_num = ""

        return RaterCaseKey(rater_name, patient_id, study_date, modality, modality_id, se_num)

```

## Tutorials

### 1. Demonstration using sample data

This tutorial demostrates a walkthrough of AFROC analysis using the pyfroc framework.

See [./samples/tutorial1.ipynb](./samples/tutorial1.ipynb)

### 2. Perform an AFROC experiment

In this tutorial, you will perform an AFROC analysis using the pyfroc framework with your DICOM images.

See [./samples/tutorial2.ipynb](./samples/tutorial2.ipynb)

### 3. How to modify behavior in pyfroc

If you want to modify behavior in pyfroc other than CLI options, you can write your own class inheriting base class to make new behavior.

See [./samples/tutorial3.ipynb](./samples/tutorial3.ipynb)

## Author

Satoshi Funayama (@akchan)

Department of Radiology, Hamamatsu University School of Medicine, Shizuoka, Japan

## License

GPLv3
