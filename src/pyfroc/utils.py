#!/usr/bin/env python
# coding: UTF-8

import glob
import os

import numpy as np
import pydicom


def count_directories(path):
    try:
        return len([entry for entry in os.listdir(path) if os.path.isdir(os.path.join(path, entry))])
    except FileNotFoundError:
        return "The specified path does not exist."
    except PermissionError:
        return "You do not have permission to access this path."


def list_dcm_files(dir_path, recursive=True):
    if recursive:
        candidates = glob.glob(os.path.join(dir_path, "**"), recursive=True)
    else:
        candidates = glob.glob(os.path.join(dir_path, "*"))

    return [str(p) for p in candidates if os.path.isfile(p) and pydicom.misc.is_dicom(str(p))]


def get_spacing_directions(dcm: pydicom.Dataset) -> np.ndarray:
    """Calculate 3 basis vectors of voxel spacing
    This function assumes that the slices are ordered in ascending order of slice coordinate.

    Args:
        dcm (pydicom.Dataset): pydicom.Dataset object of a DICOM file

    Returns:
        np.ndarray: 3x3 matrix of voxel spacing directions. Each row represents a basis vector.
    """
    # Calculate voxel spacing
    vec_x = np.array(dcm.ImageOrientationPatient[:3])
    vec_y = np.array(dcm.ImageOrientationPatient[3:6])
    perpendicular_vec = np.cross(vec_x, vec_y)

    # Normalize vectors
    vec_x = vec_x / np.linalg.norm(vec_x) * dcm.PixelSpacing[0]
    vec_y = vec_y / np.linalg.norm(vec_y) * dcm.PixelSpacing[1]
    perpendicular_vec = perpendicular_vec / np.linalg.norm(perpendicular_vec) * dcm.SliceThickness

    # Force perpendicular_vec to be positive along z axis
    if rad_between_vectors(perpendicular_vec, np.array([0.0, 0.0, 1.0])) > np.pi / 2.0:
        perpendicular_vec *= -1.0

    return np.array([vec_x, vec_y, perpendicular_vec])


def rad_between_vectors(vec1: np.ndarray, vec2: np.ndarray) -> float:
    cos_theta = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return np.arccos(cos_theta)


def normalize(img, vlim=(0.0, 1.0)):
    lim_lower, lim_upper = vlim

    val_min = np.min(img[:])
    val_max = np.max(img[:])

    return (img - val_min) / (val_max - val_min) * (lim_upper - lim_lower) + lim_lower
