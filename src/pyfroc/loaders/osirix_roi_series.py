#!/usr/bin/env python
# coding: UTF-8


import dataclasses
import re
import sys


import numpy as np
from numpy.typing import ArrayLike
import smallestenclosingcircle
from skimage.draw import polygon
from skimage.measure import label, regionprops
import typedstream


from pyfroc.signals import Lesion, Response
from pyfroc.loaders.base_loader import BaseLoader


@dataclasses.dataclass
class ROI:
    """
    # type

    - 5.0: line
    - 9.0: circle
    - 11.0: polygon
    - 19:0: point

    # Reference

    https://github.com/horosproject/horos/blob/af3595a5c7b0ef025be0154825efc1ce17114de3/Horos/Sources/ROI.m#L1017
    """
    points: list[tuple[float, float]] = []
    rect: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    type: int = 0
    thickness: float = 0.0
    opacity: float = 0.0
    color_rgb: tuple[float, float, float] = (0.0, 0.0, 0.0)
    name: str = ""
    pixel_spacing: tuple[float, float] = (0.0, 0.0)
    image_origin: tuple[float, float] = (0.0, 0.0)
    text_box: str = ""

    type_str: str = ""
    type_dict = {5: "line", 9: "circle", 11: "polygon", 19: "point"}


@dataclasses.dataclass
class ROIsInSeries:
    slices: list[list[ROI]] = []


def parse_nsstring_num(nsstr) -> list[float]:
    return list(map(float, re.sub(r"[{}\s]", "", nsstr).split(",")))


def parse_nsroi(nsroi) -> ROI:
    roi = ROI()

    points_list = []
    for ns_point in nsroi.contents[0].elements:
        x, y = parse_nsstring_num(ns_point.value.value)
        points_list.append((x, y))
    roi.points = points_list

    x, y, width, height = parse_nsstring_num(nsroi.contents[1].value.value)
    roi.rect = (x, y, width, height)

    roi.type = int(nsroi.contents[2].value.value)
    roi.thickness = nsroi.contents[4].value.value
    roi.opacity = nsroi.contents[6].value.value
    roi.color_rgb = (nsroi.contents[7].value.value,
                     nsroi.contents[8].value.value,
                     nsroi.contents[9].value.value)
    roi.name = nsroi.contents[10].value.value
    roi.pixel_spacing = (nsroi.contents[12].value.value, nsroi.contents[12].value.value)

    img_origin_x, img_origin_y = parse_nsstring_num(nsroi.contents[13].value.value)
    roi.image_origin = (img_origin_x, img_origin_y)

    roi.text_box = ""
    for i in range(5):
        line = nsroi.contents[21+i]
        if line is not None:
            roi.text_box += line.value.value + "\n"
    roi.text_box = roi.text_box.strip()

    roi.type_str = roi.type_dict.get(roi.type, "unknown")

    return roi


def read_rois_series(filepath) -> ROIsInSeries:
    ns_array = typedstream.unarchive_from_file(filepath)

    rois_in_series = ROIsInSeries()

    for nsrois_on_slice in ns_array.elements[0].elements:
        rois_on_slice = []

        for nsroi in nsrois_on_slice.elements:
            rois_on_slice.append(parse_nsroi(nsroi))

        rois_in_series.slices.append(rois_on_slice)

    return rois_in_series


def roisinseries_to_lesions(rois_in_series: ROIsInSeries,
                            slice_thickness: float = 0.0) -> list[Lesion]:
    lesions = []

    for i_slice, rois_on_slice in enumerate(rois_in_series.slices):
        for roi in rois_on_slice:
            if roi.type == 9:  # circle
                x, y, r_x, r_y = roi.rect
                r = (r_x + r_y) / 2

                lesion = Lesion(coords=(x, y, i_slice * slice_thickness),
                                r=r,
                                name=roi.name)
                lesions.append(lesion)

            elif roi.type == 11:  # polygon
                ret = smallestenclosingcircle.make_circle(roi.points)
                if ret is None:
                    continue
                center_x, center_y, r = ret

                lesion = Lesion(coords=(center_x, center_y, i_slice * slice_thickness),
                                r=r,
                                name=roi.name)
                lesions.append(lesion)
            else:
                print(f"Unsupported ROI type: {roi.type_str}", file=sys.stderr)

    return lesions


class OsirixROISeriesHandler(BaseLoader):
    def prepare(cls, dcm_root_dir_path: str, tgt_dir_path: str) -> None:
        raise NotImplementedError()

    def read_lesions(cls, dir_path: str) -> list[Lesion]:
        rois_in_series = read_rois_series(dir_path)
        return roisinseries_to_lesions(rois_in_series)

    def read_responses(cls, dir_path: str) -> list[Response]:
        raise NotImplementedError()
