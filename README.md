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

- [Use case](#use-case)
- [Installation](#instalation)
- [Tutorial](#tutorial)
- [Author](#author)
- [License](#license)

## Use case

pyfroc is designed for specific scenarios of FROC/AFROC analysis. pyfroc itself supports only one modality for reference lesions. If you want to compare two modality using two reference modality, run pyfroc for each reference modality, write .xlsx files for RJafroc, and combine the two .xlsx file manually.

### Example scenario #1

- Compare detection performance between radiologists with and without AI
- The responses will be recored on the same series of DICOM image for radiologists with and without AI.

### Example scenario #2

- Compare a standard MRI protocol with an abbreviated protocol.
- The responses will be recored on the same series of DICOM image for both protocols.

### Example scenario #3

- Compare images reconstructed using an advanced method with images reconstructed using conventional method in terms of the lesion detectability.
- Using either series to record responses.

## Instalation

Run the command below in your terminal.

```bash
pip install pyfroc
```

## Tutorial

Use pyfroc with 3D Slicer

## Author

Satoshi Funayama (@akchan)

Department of Radiology, Hamamatsu University School of Medicine, Shizuoka, Japan

## License

GPLv3
