#!/usr/bin/env python
# coding: UTF-8

from collections.abc import MutableMapping
from dataclasses import dataclass, field
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pydicom
from pydicom.pixels.processing import apply_modality_lut, apply_windowing

from pyfroc.coords import ScannerCoordinates
from pyfroc.keys import CaseKey, RaterCaseKey
from pyfroc.signals import BaseLesion, BaseResponse
from pyfroc.raters import BaseRater
from pyfroc.utils import get_spacing_directions, list_dcm_files, normalize
from .base_writer import BaseWriter


@dataclass
class DcmSeriesInfo:
    dcm_path_list: list[str] = field(default_factory=list)
    shape: tuple[int, int, int] = (0, 0, 0)
    spacing_directions: np.ndarray = field(default_factory=lambda: np.zeros([3, 3]))
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def __post_init__(self):
        assert len(self.shape) == 3
        assert self.spacing_directions.shape == (3, 3)
        assert self.origin.shape == (3,)

    def __repr__(self):
        text = ""

        text += f"{self.__class__.__name__}(\n"
        text += f"    dcm_path_list={self.dcm_path_list},\n"
        text += f"    shape={self.shape},\n"
        text += f"    spacing_directions={self.spacing_directions},\n"
        text += f"    origin={self.origin})"

        return text

    def coordinates_to_idx(self, coords: ScannerCoordinates) -> tuple[int, int, int]:
        return coords.to_idx(spacing_direction=self.spacing_directions, origin=self.origin)

    def get_image(self, slice_idx: int) -> Image.Image:
        return Image.fromarray(pydicom.dcmread(self.dcm_path_list[slice_idx]).pixel_array)

    def read_dcm_and_set_attrs(self):
        # Sort dcm_path_list in ascending order of slice coordinate
        self.dcm_path_list.sort(key=lambda dcm_path: self.get_sliceposition(pydicom.dcmread(dcm_path)))

        dcm = pydicom.dcmread(self.dcm_path_list[0])
        nx, ny = dcm.pixel_array.shape
        nz = len(self.dcm_path_list)
        self.shape = (nx, ny, nz)

        # Set voxel spacing
        self.spacing_directions = get_spacing_directions(dcm)

        # Set origin of this series (the origin of the first slice)
        self.origin = np.array(dcm.ImagePositionPatient)

    @staticmethod
    def get_sliceposition(dcm: pydicom.Dataset) -> float:
        if "ImagePositionPatient" in dcm:
            return float(dcm.ImagePositionPatient[2])
        else:
            raise ValueError("Cannot find ImagePositionPatient in DICOM file.")


class DcmSeriesDB(MutableMapping):
    def __init__(self, **kwargs):
        self.store: dict[CaseKey, DcmSeriesInfo] = dict()
        self.update(**kwargs)

    def __setitem__(self, key: CaseKey, value: DcmSeriesInfo) -> None:
        assert isinstance(key, CaseKey)
        assert isinstance(value, DcmSeriesInfo)
        self.store[key] = value

    def __getitem__(self, key: CaseKey) -> DcmSeriesInfo:
        return self.store[key]

    def __delitem__(self, key: CaseKey) -> None:
        del self.store[key]

    def __iter__(self):
        return iter(self.store)

    def __len__(self) -> int:
        return len(self.store)

    def __contains__(self, key: CaseKey) -> bool:
        return key in self.store

    def __repr__(self):
        return f'{self.__class__.__name__}({self.store})'

    @classmethod
    def from_dcm_dir(cls, dcm_root_dir_path: str) -> "DcmSeriesDB":
        db = cls()

        # Search dicom files and set them to DcmSeriesInfo
        for dcm_path in list_dcm_files(dcm_root_dir_path):
            dcm = pydicom.dcmread(dcm_path)
            casekey = CaseKey.from_dcm(dcm)

            if casekey not in db:
                db[casekey] = DcmSeriesInfo()

            db[casekey].dcm_path_list.append(dcm_path)

        # Set all attributes of DcmSeriesInfo
        for dcm_series_info in db.values():
            dcm_series_info.read_dcm_and_set_attrs()

        return db


@dataclass
class ImageObj:
    img: Image.Image
    slice_i: int
    z: float


class ResponseLesionImagesWriter(BaseWriter):
    IMAGE_ROOT_DIR_NAME = "responses_img"

    @classmethod
    def write(cls, rater: BaseRater,
              dcm_root_dir_path: str,
              out_path: str) -> None:
        db = DcmSeriesDB.from_dcm_dir(dcm_root_dir_path)

        # out_root_dir_path = cls.get_uniq_dir_path(os.path.join(rater.loader.root_dir_path, cls.IMAGE_ROOT_DIR_NAME))
        out_root_dir_path = cls.get_uniq_dir_path(out_path)

        for ratercasekey, lesions, tp, fp in rater:
            i_counter = 1
            casekey = ratercasekey.to_casekey()

            for lesion, response in tp:
                if casekey not in db.keys():
                    print(f"[Error] Dicom not found: {casekey}", file=sys.stderr)
                    continue

                dcm_series_info = db[casekey]

                img = cls.create_response_lesion_image(ratercasekey, dcm_series_info, lesion, response)

                img_path = cls.build_img_path(out_root_dir_path, ratercasekey, i_counter, "true_positive")
                i_counter += 1

                print(f" writing {img_path}")
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img.save(img_path)

            for response in fp:
                dcm_series_info = db[casekey]

                img = cls.create_response_lesion_image(ratercasekey, dcm_series_info, None, response)

                img_path = cls.build_img_path(out_root_dir_path, ratercasekey, i_counter, "false_positive")
                i_counter += 1

                print(f" writing {img_path}")
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img.save(img_path)

        print("")

    @classmethod
    def get_uniq_dir_path(cls, dir_path: str) -> str:
        dir_path = str(dir_path).rstrip("/")

        if not os.path.exists(dir_path):
            return dir_path

        i = 2
        while True:
            new_dir_path = f"{dir_path}_{i}"
            if not os.path.exists(new_dir_path):
                return new_dir_path
            i += 1

    @classmethod
    def build_img_path(cls, root_dir_path: str, ratercasekey: RaterCaseKey, i_counter: int, postfix: str = "") -> str:
        dir_path = os.path.join(root_dir_path, ratercasekey.to_path())
        img_filename = f"{i_counter:03d}_{postfix}.png"
        return os.path.join(dir_path, img_filename)

    @classmethod
    def read_dcm_image(cls, signal: BaseLesion | BaseResponse,
                       dcm_series_info: DcmSeriesInfo,
                       img_size=(512, 512)) -> ImageObj:
        """_summary_

        Args:
            signal (BaseLesion | BaseResponse): a lesion or response
            dcm_series_info (DcmSeriesInfo): a DcmSeriesInfo object
            img_size (tuple, optional): width x height. Defaults to (512, 512).

        Returns:
            ImageObj: an ImageObj object
        """
        signal_idx = signal.coords.to_idx(dcm_series_info.spacing_directions, dcm_series_info.origin)
        slice_i = signal_idx[2]

        dcm = pydicom.dcmread(dcm_series_info.dcm_path_list[slice_i])

        # Read pixel data and convert to uint8
        img = dcm.pixel_array
        img = apply_modality_lut(img, dcm)
        img = apply_windowing(img, dcm)  # Normalized to 0.0-1.0
        img = (normalize(img) * 255).astype(np.uint8)
        img = Image.fromarray(img).convert("RGB")

        img_resized = cls.resize(img, img_size)

        img_padded = Image.new("RGB", img_size, color="black")
        img_padded = cls.paste_center(img_resized, img_padded)

        return ImageObj(img_padded, slice_i, signal.coords.z)

    @staticmethod
    def resize(img: Image.Image, img_size: tuple[int, int]) -> Image.Image:
        """Resize the given image while preserving its aspect ratio.
        Parameters:
            img (Image.Image): The image to be resized.
            img_size (tuple[int, int]): The target size as a tuple (width, height).
        Returns:
            Image.Image: The resized image.
        """
        img_aspect_ratio = img.height / img.width
        tgt_aspect_ratio = img_size[1] / img_size[0]

        if img_aspect_ratio >= tgt_aspect_ratio:
            # The constraint is the height
            new_height = img_size[1]
            new_width = int(new_height / img_aspect_ratio)
        else:
            # The constraint is the width
            new_width = img_size[0]
            new_height = int(new_width * img_aspect_ratio)

        return img.resize((new_width, new_height), resample=Image.Resampling.LANCZOS)

    @staticmethod
    def paste_center(img: Image.Image, tgt_img: Image.Image) -> Image.Image:
        """Paste the given image at the center of the target image.
        Parameters:
            img (Image.Image): The image to be pasted.
            tgt_img (Image.Image): The target image.
        Returns:
            Image.Image: The target image with the image pasted at the center.
        """
        tgt_width, tgt_height = tgt_img.size
        img_width, img_height = img.size

        x = (tgt_width - img_width) // 2
        y = (tgt_height - img_height) // 2

        tgt_img.paste(img, (x, y))

        return tgt_img

    @classmethod
    def apply_signal_to_image(cls, img: ImageObj, signal: BaseLesion | BaseResponse,
                              dcm_series_info: DcmSeriesInfo,
                              center_indicator_size=5,
                              line_width=1,
                              signal_color="orange",
                              eps_z=1.0e-1) -> ImageObj:
        # Check if the signal is out of the slice
        z_diff = np.abs(signal.coords.z - img.z)
        r = getattr(signal, "r", 0.0)
        if z_diff >= r:
            return img

        # Calculate the radius of the signal in pixels assuming the aspect
        # ratio of the pixel is 1:1
        vec_x = dcm_series_info.spacing_directions[0, :]
        spacing_x = np.linalg.norm(vec_x)
        r_on_slice = np.sqrt(r ** 2 - z_diff ** 2)
        r_in_px = np.round(r_on_slice / spacing_x)

        # Prepare the drawing object
        draw = ImageDraw.Draw(img.img)

        # Draw a signal circle and center point
        signal_idx = signal.coords.to_idx(dcm_series_info.spacing_directions, dcm_series_info.origin)
        x, y = signal_idx[0], signal_idx[1]
        top_left_point = (x - r_in_px, y - r_in_px)
        bottom_right_point = (x + r_in_px, y + r_in_px)
        draw.ellipse([top_left_point, bottom_right_point], outline=signal_color, width=line_width)

        # Draw cross line
        if z_diff <= eps_z:
            draw.line([(x - center_indicator_size//2, y), (x + center_indicator_size//2, y)],
                      fill=signal_color,
                      width=line_width)
            draw.line([(x, y - center_indicator_size//2), (x, y + center_indicator_size//2)],
                      fill=signal_color,
                      width=line_width)

        return img

    @classmethod
    def apply_text_to_image(cls, img: ImageObj, text: str,
                            text_size=24,
                            position=(5, 5),
                            color="orange") -> ImageObj:
        try:
            font = ImageFont.truetype("Arial.ttf", text_size)
        except IOError:
            font = ImageFont.load_default()

        draw = ImageDraw.Draw(img.img)
        draw.text(position, text, fill=color, font=font)

        return img

    @classmethod
    def apply_signal_text_to_image(cls, img: ImageObj, signal: BaseLesion | BaseResponse,
                                   position=(5, 5),
                                   text_size=24,
                                   color="orange") -> ImageObj:
        r = getattr(signal, "r", 0.0)

        text = f"{signal.__class__.__name__}"
        text += f" (x={signal.coords.x:.2f}, y={signal.coords.y:.2f}, z={signal.coords.z:.2f}, r={r:.2f})"
        return cls.apply_text_to_image(img, text, text_size, position, color)

    @classmethod
    def create_response_lesion_image(cls, ratercasekey: RaterCaseKey,
                                     dcm_series_info: DcmSeriesInfo,
                                     lesion: BaseLesion | None,
                                     response: BaseResponse,
                                     text_size=20,
                                     text_position=(5, 5),
                                     img_size=(512, 512),
                                     response_color="orange",
                                     lesion_color="lime") -> Image.Image:
        # Prepare a header image based on the ratercasekey
        header_size = (img_size[0] * 2, int(text_size * 1.5))
        img_header = ImageObj(Image.new("RGB", header_size), -1, -1)
        header_text = ratercasekey.to_path()
        img_header = cls.apply_text_to_image(img_header, header_text, text_size, text_position, color="white")

        # Read DICOM image and apply signal to it
        # Response
        img_res = cls.read_dcm_image(response, dcm_series_info, img_size)
        img_res = cls.apply_signal_text_to_image(img_res, response, position=text_position, text_size=text_size, color=response_color)

        # Lesion
        if lesion is None:
            img_lesion = ImageObj(Image.new("RGB", img_size), -1, -1)
            img_lesion = cls.apply_text_to_image(img_lesion, "No lesion", text_size, text_position, color=lesion_color)
        else:
            img_res = cls.apply_signal_to_image(img_res, lesion, dcm_series_info, signal_color=lesion_color)

            img_lesion = cls.read_dcm_image(lesion, dcm_series_info, img_size)
            img_lesion = cls.apply_signal_to_image(img_lesion, lesion, dcm_series_info, signal_color=lesion_color)
            img_lesion = cls.apply_signal_text_to_image(img_lesion, lesion, position=text_position, text_size=text_size, color=lesion_color)

        img_res = cls.apply_signal_to_image(img_res, response, dcm_series_info, signal_color=response_color)

        # Concatenate the two iamges horizontally
        img = Image.fromarray(np.hstack([np.array(img_res.img), np.array(img_lesion.img)]))
        img = Image.fromarray(np.vstack([np.array(img_header.img), np.array(img)]))

        return img
