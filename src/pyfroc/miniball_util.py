#!/usr/bin/env python
# coding: UTF-8


import numpy as np
import miniball


def get_min_sphere(coords: np.ndarray) -> tuple[np.ndarray, float]:
    """Get the minimum bounding sphere of the edge coordinates.

    Args:
        coords (np.ndarray): The edge coordinates. It should have a shape of (m, 3),
            where m is the number of coordinates and 3 represents the x, y, and z coordinates respectively.

    Returns:
        tuple[np.ndarray, float]: A tuple containing the center and radius of the minimum bounding sphere.
            The center is represented as a numpy array of shape (3,) and the radius is a float value.
    """
    assert coords.ndim == 2 and coords.shape[1] == 3, f"Invalid shape of coords: {coords.shape}"
    assert np.isnan(coords).sum() == 0, "coords should not contain NaN"

    coords = np.unique(coords, axis=0)

    assert len(coords) > 1, "coords should have at least two unique coordinates"

    ret = miniball.Miniball(coords)

    center = np.array(ret.center())
    r2 = ret.squared_radius()
    r = np.sqrt(r2)

    return center, r
