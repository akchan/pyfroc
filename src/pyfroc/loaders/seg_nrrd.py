#!/usr/bin/env python
# coding: UTF-8


from dataclasses import dataclass
import glob
import os
import re

import nrrd
import numpy as np
from skimage.measure import label

from pyfroc.loaders.base_loader import BaseLoader
from pyfroc.signals import Response


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
    origin: np.ndarray
    segmentations: tuple[SlicerSegmentation]
    mask: np.ndarray

    # Check attributes
    def __post_init__(self):
        assert self.space_directions.shape == (3, 3), f"Invalid shape of space_directions: {self.space_directions.shape}"
        assert self.origin.shape == (3,), f"Invalid shape of origin: {self.origin.shape}"
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

                res = Response.from_mask(name=seg.name,
                                         confidence=seg.confidence,
                                         mask=mask_i,
                                         space_directions=segnrrd.space_directions,
                                         origin=segnrrd.origin)

                responses.append(res)

        return responses

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
            origin=parsed_header["origin"],
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
            "origin": None,
            "n_layers": -1,
            "segmentations": [],
        }

        seg_dict = {}

        # Segmentations
        for key in header.keys():
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

        # voxel size
        volume_shape = header["sizes"]
        if len(volume_shape) == 3:
            ret["n_layers"] = 1
            ret["voxel_size"] = tuple(volume_shape)
        elif len(volume_shape) == 4:
            ret["n_layers"] = volume_shape[0]
            ret["voxel_size"] = tuple(volume_shape[1:])
        else:
            raise ValueError(f"Invalid len(sizes) = {len(volume_shape)}")

        ret["segmentations"] = tuple(seg_dict.values())

        ret["space_directions"] = np.array(header["space directions"][-3:], dtype=np.float32)

        ret["origin"] = np.array(header["space origin"][-3:], dtype=np.float32)

        return ret
