#!/usr/bin/env python
# coding: UTF-8


from dataclasses import dataclass
import glob
import os
import re

import nrrd
import numpy as np
from skimage.measure import label
from skimage.morphology import binary_erosion

from pyfroc.coords import SeriesCoordinates
from pyfroc.loaders.base_loader import BaseLoader
from pyfroc.signals import Response
from pyfroc.miniball_util import get_min_sphere


@dataclass
class SlicerSegmentation:
    id: int = -1
    layer: int = -1
    label_value: int = -1
    name: str = ""
    confidence: int = -1


@dataclass
class SegNRRD:
    space_directions: np.ndarray  # (3x3): (voxel_dir_xyz, xyz_spacing)
    segmentations: tuple[SlicerSegmentation]
    mask: np.ndarray

    # Check attributes
    def __post_init__(self):
        assert self.space_directions.shape == (3, 3), f"Invalid shape of space_directions: {self.space_directions.shape}"
        assert isinstance(self.segmentations, tuple), "segmentation should be a tuple"


class SegNRRDLoader(BaseLoader):
    def read_responses(self, case_dir_path: str) -> list[Response]:
        series_responses = []

        for segnrrd_path in self.list_segnrrd_path(case_dir_path):
            segnrrd = self.read_segnrrd(segnrrd_path)
            series_responses.extend(self.segnrrd2responses(segnrrd))

        return series_responses

    @staticmethod
    def segnrrd2responses(segnrrd: SegNRRD, mask_dtype=np.uint8) -> list[Response]:
        responses: list[Response] = []

        for seg in segnrrd.segmentations:
            layer_id = seg.layer
            label_value = seg.label_value

            mask = (segnrrd.mask[layer_id] == label_value).astype(mask_dtype)

            mask_labeled, label_max = label(mask, connectivity=1, return_num=True)  # type: ignore
            mask_labeled = mask_labeled.astype(mask_dtype)

            for label_i in range(1, label_max + 1):
                mask_i = (mask_labeled == label_i).astype(mask_dtype)

                c, r = SegNRRDLoader.mask2minisphere(mask_i, segnrrd.space_directions)
                assert r > 0.0, f"Invalid radius or {r} for {seg}"

                res = Response(coords=SeriesCoordinates(*c),
                               r=r,
                               name=seg.name,
                               confidence=seg.confidence)

                responses.append(res)

        return responses

    @staticmethod
    def mask2minisphere(mask: np.ndarray,
                        space_directions: np.ndarray,
                        mask_dtype=np.int8) -> tuple[np.ndarray, float]:
        # Consider only the edge points to reduce the computational cost
        mask = (mask > 0).astype(mask_dtype)

        assert mask.max() > 0, "mask should have at least one positive cell"

        mask_edge = mask - binary_erosion(mask).astype(mask_dtype)

        # Get series coordinates of the edge points
        xx, yy, zz = np.where(mask_edge > 0)
        edge_coords = xx[:, None] * space_directions[None, 0]\
            + yy[:, None] * space_directions[None, 1]\
            + zz[:, None] * space_directions[None, 2]

        if len(edge_coords) == 1:
            r = np.max(space_directions)
            return edge_coords[0], r

        c, r = get_min_sphere(edge_coords)

        return c, r

    @staticmethod
    def idx2coords(idx, space_directions, origin=np.zeros(3)):
        return np.dot(idx, space_directions) + origin

    @staticmethod
    def list_segnrrd_path(dir_path) -> list[str]:
        return glob.glob(os.path.join(dir_path, "*.seg.nrrd"))

    @staticmethod
    def read_segnrrd(segnrrd_path) -> SegNRRD:
        vol, header = nrrd.read(segnrrd_path)

        if vol.ndim == 3:
            vol = np.expand_dims(vol, axis=0)

        parsed_header = SegNRRDLoader.parse_seg_nrrd_header(header)

        segnrrd = SegNRRD(
            space_directions=parsed_header["space_directions"],
            segmentations=parsed_header["segmentations"],
            mask=vol
        )

        return segnrrd

    @staticmethod
    def parse_confidence_from_seg_name(name: str) -> int:
        """Take the confidence value from the segmentation name.
        The first integer included in the name is considered as the confidence value.

        Args:
            name (str): name of the segmentation

        Returns:
            int: confidence value
        """
        m = re.search(r"([0-9]+)", name)
        if m is not None:
            return int(m.group(1))
        return -1

    @staticmethod
    def parse_seg_nrrd_header(header: dict) -> dict:
        ret = {
            "space_directions": None,
            "n_layers": -1,
            "segmentations": [],
        }

        seg_dict = {}

        for key in header.keys():
            # voxel size
            if key == "sizes":
                ary = header[key]
                if len(ary) == 3:
                    ret["n_layers"] = 1
                    ret["voxel_size"] = tuple(ary)
                elif len(ary) == 4:
                    ret["n_layers"] = ary[0]
                    ret["voxel_size"] = tuple(ary[1:])
                else:
                    raise ValueError(f"Invalid len(sizes) = {len(ary)}")

            # Segmentations
            m = re.match(r"Segment([0-9])+_.*", key)

            if m is None:
                continue

            id = int(m.group(1))

            if id not in seg_dict:
                seg_dict[id] = SlicerSegmentation(id=id)

            if key.endswith("LabelValue"):
                seg_dict[id].label_value = int(header[key])
            elif key.endswith("Layer"):
                seg_dict[id].layer = int(header[key])
            elif key.endswith("Name"):
                name = header[key]
                seg_dict[id].name = name
                seg_dict[id].confidence = SegNRRDLoader.parse_confidence_from_seg_name(name)

        ret["segmentations"] = tuple(seg_dict.values())

        ret["space_directions"] = np.array(header["space directions"][-3:], dtype=np.float32)

        return ret
