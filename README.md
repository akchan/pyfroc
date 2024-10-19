# pyfroc

Python framework for FROC/AFROC analysis

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

## Table of contents

- [pyfroc](#pyfroc)
  - [About](#about)
    - [What pyfroc does](#what-pyfroc-does)
    - [What pyfroc doesn't](#what-pyfroc-doesnt)
  - [Table of contents](#table-of-contents)
  - [Use case](#use-case)
    - [Scenario #1](#scenario-1)
    - [Scenario #2](#scenario-2)
    - [Scenario #3](#scenario-3)
  - [Instalation](#instalation)
  - [Tutorials](#tutorials)
    - [1. Demonstration](#1-demonstration)
    - [2. Perform an AFROC experiment](#2-perform-an-afroc-experiment)
    - [3. How to modify behavior in pyfroc](#3-how-to-modify-behavior-in-pyfroc)
  - [Author](#author)
  - [License](#license)

## Use case

pyfroc is designed for specific scenarios of FROC/AFROC analysis. pyfroc itself supports only one modality for reference lesions. If you want to compare two modality using two reference modality, run pyfroc for each reference modality, write .xlsx files for RJafroc, and combine the two .xlsx file manually.

Here are the sample scenarios.

### Scenario #1

- Compare detection performance between radiologists with and without AI
- The responses will be recored on the same series of DICOM images for radiologists with and without AI.

### Scenario #2

- Compare a standard MRI protocol with an abbreviated protocol in terms of lesion detection.
- The responses will be recored on the same series of DICOM images for both protocols.

### Scenario #3

- Compare images reconstructed using an advanced method with images reconstructed using conventional method in terms of the lesion detectability.
- Using either series to record responses.

## Instalation

Run the command below in your terminal.

```bash
pip install pyfroc
```

## Tutorials

### 1. Demonstration

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
