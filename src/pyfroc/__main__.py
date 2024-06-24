#!/usr/bin/env python
# coding: UTF-8

import argparse

from pyfroc import prepare, evaluate


def main():
    # Parsers for the main command and subcommands
    parser = argparse.ArgumentParser(description="pyfroc: A Python package for FROC/JAFROC analysis.")
    subparsers = parser.add_subparsers(dest='command')

    # 'prepare' subcommand parser
    parser_prepare = subparsers.add_parser('prepare', help='Prepare directories for image interpretation experiment based on DICOM files.')
    parser_prepare.add_argument('--dicom-dir', type=str, required=True, help='Path to the root directory of DICOM files used in the experiment')
    parser_prepare.add_argument('--target-dir', type=str, required=True, help='Path to the target directory where the prepared files will be stored')
    parser_prepare.add_argument('--num-of-raters', type=int, default=3, help='Number of raters in the experiment. Default is 3.')

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

    args = parser.parse_args()

    if args.command == 'prepare':
        prepare(args.dicom_dir, args.target_dir, args.num_of_raters)
    elif args.command == 'evaluate':
        evaluate(args.out_path, args.filetype, args.criteria, args.out_path)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
