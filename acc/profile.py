# -*- coding: utf-8 -*-
from shapely.geometry import Polygon
from geographiclib.geodesic import Geodesic

_LARGE_BOX_WIDTH = 2000


def _get_box(latlon0, azimuth, length, width=_LARGE_BOX_WIDTH, offset=0):
    """Create a single box."""

    start = direct_geodetic(latlon0, azimuth, offset)
    azis = ((azimuth - 90) % 360, azimuth,
            (azimuth + 90) % 360, (azimuth + 180) % 360)
    dists = (width/2, length, width, length)
    latlon = start
    corners = []
    for a, d in zip(azis, dists):
        latlon = direct_geodetic(latlon, a, d)
        corners.append(latlon[::-1])
    box = {'poly': Polygon(corners),
           'length': length,
           'pos': offset + length/2,
           'latlon': direct_geodetic(start, azimuth, length/2)}
    return box


def direct_geodetic(latlon, azi, dist):
    """
    Solve direct geodetic problem with geographiclib.

    :param tuple latlon: coordinates of first point
    :param azi: azimuth of direction
    :param dist: distance in km

    :return: coordinates (lat, lon) of second point on a WGS84 globe
    """
    coords = Geodesic.WGS84.Direct(latlon[0], latlon[1], azi, dist * 1000)
    return coords['lat2'], coords['lon2']


def get_profile_boxes(latlon0, azimuth, bins, width=_LARGE_BOX_WIDTH):
    """
    Create 2D boxes for usage in `profile()` function.

    :param tuple latlon0: coordinates of starting point of profile
    :param azimuth: azimuth of profile direction
    :param tuple bins: Edges of the distance bins in km (e.g. (0, 10, 20, 30))
    :param width: width of the boxes in km (default: large)
    :return: List of box dicts. Each box has the entries
        'poly' (shapely polygon with lonlat corners),
        'length' (length in km),
        'pos' (midpoint of box in km from starting coordinates),
        'latlon' (midpoint of box as coordinates)
    """
    boxes = []
    for i in range(len(bins)-1):
        length = bins[i+1] - bins[i]
        box = _get_box(latlon0, azimuth, length, width, offset=bins[i])
        if i == 0:
            box['profile'] = {}
            box['profile']['latlon'] = latlon0
            box['profile']['azimuth'] = azimuth
            box['profile']['length'] = bins[-1] - bins[0]
            box['profile']['width'] = width
        boxes.append(box)
    return boxes


def _find_box(latlon, boxes, crs=None):
    """Return the box which encloses the coordinates."""
    import cartopy.crs as ccrs
    from shapely.geometry import Point
    if crs is None:
        latlons = [boxes[len(boxes)//2]['latlon']]
        latlon0 = np.median(latlons, axis=0)
        crs = ccrs.AzimuthalEquidistant(*latlon0[::-1])
    pc = ccrs.PlateCarree()
    p = crs.project_geometry(Point(*latlon[::-1]), pc)
    for box in boxes:
        poly = crs.project_geometry(box['poly'], pc)
        if p.within(poly):
            return box

