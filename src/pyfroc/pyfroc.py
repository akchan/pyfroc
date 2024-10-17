#!/usr/bin/env python
# coding: UTF-8

import argparse
import os
import sys

from pyfroc.loaders import DirectorySetup, SegNRRDLoader
from pyfroc.raters import BaseRater, WithinLesionRater
from pyfroc.writers import RJAFROCWriter, ResponseLesionImagesWriter


def prepare(dcm_dir_path: str, tgt_dir_path, num_of_raters: int, num_of_modalities: int) -> None:
    direcotry_setup = DirectorySetup(tgt_dir_path)
    direcotry_setup.prepare_dir(dcm_dir_path, num_of_raters, num_of_modalities)


def evaluate(args, def_param: dict) -> None:
    # Prepare the loader
    if args.filetype == "segnrrd":
        loader_class = SegNRRDLoader
    else:
        raise ValueError(f"Unknown loader class flag: {args.filetype}")

    loader = loader_class(args.eval_dir)
    loader.validate_dirs()

    # Prepare the rater
    if args.criteria == "within_lesion":
        rater_class = WithinLesionRater
    else:
        raise ValueError(f"Unknown rater class flag: {args.criteria}")

    rater = rater_class(loader)

    # Evaluate the responses and write the results
    if args.out_format == "rjafroc_xlsx":
        # Evaluate the responses
        rjafrox_xlsx_path = os.path.join(args.out_path, def_param['out_filename'])

        RJAFROCWriter.write(xlsx_path=rjafrox_xlsx_path, rater=rater)
    elif args.out_format == "signal_img":
        write_response_lesion_images(args, def_param, rater)
    else:
        raise ValueError(f"Unknown writer class flag: {args.out_format}")

    if args.write_img:
        write_response_lesion_images(args, def_param, rater)


def write_response_lesion_images(args, def_param: dict, rater: BaseRater) -> None:
    write_img_out_dir_path = os.path.join(args.out_path, def_param['out_write_img_dirname'])
    ResponseLesionImagesWriter.write(rater=rater,
                                     dcm_root_dir_path=args.dicom_dir,
                                     out_path=write_img_out_dir_path)


def main():
    # Default parameters
    def_param = {
        'target_dir': "./experiment",
        "out_filename": "rjafroc_input.xlsx",
        "out_write_img_dirname": "lesion_response_images"
    }

    # Parsers for the main command and subcommands
    usage_text = "Usage: pyfroc [subcommand] [options]"
    parser = argparse.ArgumentParser(description="pyfroc: A Python package for FROC/JAFROC analysis.",
                                     usage=usage_text, formatter_class=argparse.HelpFormatter)
    subparsers = parser.add_subparsers(dest='subcommand',
                                       title="subcommand",
                                       description="See 'pyfroc [subcommand] --help' for more information on a specific subcommand.",)

    # 'prepare' subcommand parser
    parser_prepare = subparsers.add_parser('prepare', help='Prepare directories for image interpretation experiment based on DICOM files.')
    parser_prepare.add_argument('--dicom-dir',
                                type=str,
                                required=True,
                                help='Path to the root directory of DICOM files used in the experiment.')
    parser_prepare.add_argument('--target-dir',
                                type=str,
                                default=def_param['target_dir'],
                                help=f'Path to the target directory where the prepared files will be stored. The responses of the raters and the reference files should be stored in this directory. The default is {def_param["target_dir"]}.')
    parser_prepare.add_argument('--num-of-raters',
                                type=int,
                                default=3,
                                help='Number of raters in the experiment. Default is 3.')
    parser_prepare.add_argument('--num-of-modalities',
                                type=int,
                                default=2,
                                help='Number of modalities (or treatments) in the experiment. Default is 2.')

    # 'evaluate' subcommand parser
    parser_eval = subparsers.add_parser('evaluate',
                                        help='Evaluate the responses of the raters and generate a xlsx file for the RJAFROC analysis.')
    parser_eval.add_argument('--eval-dir',
                             type=str,
                             default=def_param['target_dir'],
                             help=f'Path to the root directory of the evaluation results. Basically, this is the target direcotry created with "prepare" subcommand. The default is {def_param["target_dir"]}.')
    parser_eval.add_argument('--out-path',
                             type=str,
                             help=f'Path to the output file of the evaluation results. The defult path is the [--eval-dir]/{def_param["out_filename"]}.')
    parser_eval.add_argument('--filetype',
                             choices=["segnrrd"],
                             default="segnrrd",
                             help='File type of the evaluation results.')
    parser_eval.add_argument('--criteria',
                             choices=["within_lesion"],
                             default="within_lesion",
                             help='Criteria for positive responses.')
    parser_eval.add_argument('--out-format',
                             choices=["rjafroc_xlsx", "signal_img"],
                             default="rjafroc_xlsx",
                             help='Output file format')
    parser_eval.add_argument('--write-img',
                             action='store_true',
                             help='Same as --out-format signal_img. This option can be used with the other type of output file format and save the processing time.')
    parser_eval.add_argument('--dicom-dir',
                             type=str,
                             help='Path to the root directory of DICOM files used in this experiment. This option is required if --out-format signal_img or --write-img flag is used.')

    args = parser.parse_args()

    # Call the appropriate function based on the subcommand
    if args.subcommand == 'prepare':
        print(args.dicom_dir)
        prepare(args.dicom_dir,
                args.target_dir,
                args.num_of_raters,
                args.num_of_modalities)

    elif args.subcommand == 'evaluate':
        # Custom validation for the 'evaluate' subcommand

        # Check the arguments and set the appropriate variables
        if args.out_path is None:
            args.out_path = args.eval_dir

        # Check the dicom_dir option when the out_format is signal_img
        if args.out_format == "signal_img":
            if args.dicom_dir is None:
                print("The --dicom-dir option is required when --out-format is signal_img.", file=sys.stderr)
                sys.exit(1)

            if args.write_img:
                args.write_img = False

        evaluate(args, def_param)
    else:
        parser.print_help()
