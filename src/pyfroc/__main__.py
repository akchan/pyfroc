#!/usr/bin/env python
# coding: UTF-8

import argparse

from pyfroc import prepare, evaluate
from pyfroc.loaders import SegNRRDLoader
from pyfroc.raters import NearestPairRater
from pyfroc.writers import RJAFROCWriter


def main():
    # Parsers for the main command and subcommands
    usage_text = "Usage: python -m pyfroc [command] [options]"
    parser = argparse.ArgumentParser(description="pyfroc: A Python package for FROC/JAFROC analysis.",usage=usage_text, formatter_class=argparse.HelpFormatter)
    subparsers = parser.add_subparsers(dest='command')

    # 'prepare' subcommand parser
    parser_prepare = subparsers.add_parser('prepare', help='Prepare directories for image interpretation experiment based on DICOM files.')
    parser_prepare.add_argument('--dicom-dir', type=str, required=True, help='Path to the root directory of DICOM files used in the experiment')
    parser_prepare.add_argument('--target-dir', type=str, required=True, help='Path to the target directory where the prepared files will be stored')
    parser_prepare.add_argument('--num-of-raters', type=int, default=3, help='Number of raters in the experiment. Default is 3.')
    parser_prepare.add_argument('--num-of-modalities', type=int, default=2,
                                help='Number of modalities (or treatments) in the experiment. Default is 2.')

    # 'evaluate' subcommand parser
    parser_eval = subparsers.add_parser('evaluate', help='Evaluate the responses of the raters and generate a xlsx file for the RJAFROC analysis.')
    parser_eval.add_argument('--eval-dir', type=str, required=True,
                             help='Path to the root directory of the evaluation results. Typically, this is the target direcotry created with "prepare" subcommand.')
    parser_eval.add_argument('--out-path', type=str, default="./rjafroc_froccr.xlsx",
                             help='Path to the root directory of the evaluation results. Typically, this is the target direcotry created with "prepare" subcommand.')
    parser_eval.add_argument('--filetype', choices=["segnrrd"], default="segnrrd",
                             help='File type of the evaluation results.')
    parser_eval.add_argument('--criteria', choices=["within_lesion"], default="within_lesion",
                             help='Criteria for positive responses.')
    parser_eval.add_argument('--out-format', choices=["rjafroc_xlsx"], default="rjafroc_xlsx",
                             help='Output file format')

    args = parser.parse_args()

    if args.command == 'prepare':
        print(args.dicom_dir)
        prepare(args.dicom_dir, args.target_dir, args.num_of_raters, args.num_of_modalities)

    elif args.command == 'evaluate':
        if args.filetype == "segnrrd":
            loader_class = SegNRRDLoader
        else:
            raise ValueError(f"Unknown loader class flag: {args.filetype}")

        if args.criteria == "WithinLesionRater":
            rater_class = NearestPairRater
        else:
            raise ValueError(f"Unknown rater class flag: {args.criteria}")

        if args.out_format == "rjafroc_xlsx":
            writer_class = RJAFROCWriter
        else:
            raise ValueError(f"Unknown writer class flag: {args.out_format}")

        evaluate(args.out_path, args.out_path, loader_class, rater_class, writer_class)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
