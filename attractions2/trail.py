import csv
import dataclasses
import gzip
import math
import statistics
from typing import List

# Avoid giving significant weight to individual point in
# elevation gain calculation, because, from experience, altitude is
# much less accurate than latitude or longitude
ALTITUDE_COMPARE_POINTS = 30


class FileEmpty(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class SinglePoint:
    latitude: float
    longitude: float
    altitude: float


@dataclasses.dataclass(frozen=True)
class TrailAnalysis:
    center_latitude: float
    center_longitude: float
    elevation_gain: float
    distance: float


def _get_distance(point1, point2):
    r = 6370 * 1000  # In meters
    lat1 = math.radians(point1[0])
    lon1 = math.radians(point1[1])
    lat2 = math.radians(point2[0])
    lon2 = math.radians(point2[1])

    d_lon = lon2 - lon1
    d_lat = lat2 - lat1

    a = math.sin(d_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = r * c
    return distance


def _calculate_gain(points: List[SinglePoint]) -> float:
    elv_gain = 0
    last_elv_points = []  # type: List[float]
    last_elv_avg = None

    for point in points:
        if len(last_elv_points) > ALTITUDE_COMPARE_POINTS / 2:
            elv_avg = statistics.mean(last_elv_points)

            if last_elv_avg is not None and elv_avg > last_elv_avg:
                elv_gain += elv_avg - last_elv_avg

            last_elv_avg = elv_avg

        last_elv_points.append(point.altitude)

        if len(last_elv_points) > ALTITUDE_COMPARE_POINTS:
            del last_elv_points[0]

    return elv_gain


def analyze_trail(fh) -> TrailAnalysis:
    data = []  # type: List[SinglePoint]

    with gzip.open(fh, "rt") as gh:
        reader = csv.reader(gh)
        header = {}
        index = 0

        for col in next(reader):
            header[col] = index
            index += 1

        for row in reader:
            data.append(SinglePoint(
                latitude=float(row[header["Latitude"]]),
                longitude=float(row[header["Longitude"]]),
                altitude=float(row[header["Altitude"]])
            ))

    if len(data) == 0:
        raise FileEmpty()

    lat = statistics.mean(map(lambda x: x.latitude, data))
    long = statistics.mean(map(lambda x: x.longitude, data))

    distance = 0.0

    last_point = data[0]
    for point in data[1:]:
        distance += _get_distance(
            (last_point.latitude, last_point.longitude),
            (point.latitude, point.longitude)
        )

        last_point = point

    return TrailAnalysis(
        center_longitude=long,
        center_latitude=lat,
        elevation_gain=_calculate_gain(data),
        distance=distance
    )
