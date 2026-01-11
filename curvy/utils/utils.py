import random
import socket
from typing import Union
import math

import numpy as np


def internet(host="8.8.8.8", port=53, timeout=3):
    """ Function that returns True if an internet connection is available, False if otherwise

    Based on https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python

    Parameters
    ----------
    host: str
        IP of the host, which should be used for checking the internet connections
    port: int
        Port that should be used
    timeout: int
        Timeout in seconds

    Returns
    -------
    bool
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False


def generate_random_color(color_format: str = "RGB") -> Union[list, str]:
    """
    Parameters
    ----------
    color_format: str
        Color format of the generated color, either "RGB" or "HEX". RGB values range from 0 to 255
    """

    if color_format == "RGB":
        return list(np.random.choice(range(256), size=3))
    elif color_format == "HEX":
        return "#" + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
    else:
        raise ValueError("Format %s is not valid, must be 'RGB' or 'HEX' " % color_format)


def poly_quadratic(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """ Evaluates quadratric

    Parameters
    ----------
    x
    a
    b

    Returns
    -------

    """
    return a * x ** 2 + b * x

def convert_wgs_to_utm(lon: float, lat: float):
    """Based on lat and lng, return best utm epsg-code"""
    utm_band = str((math.floor((lon + 180) / 6 ) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if lat >= 0:
        epsg_code = 'EPSG:326' + utm_band
        return epsg_code
    epsg_code = 'EPSG:327' + utm_band
    return epsg_code

