import dataclasses
from typing import List, Optional

from django.db import connection


@dataclasses.dataclass
class ImageAsset:
    id: int
    key: str
    bucket: str
    width: int
    height: int
    request_width: Optional[int]
    request_height: Optional[int]
    thumbs: List["ImageAsset"]

    @property
    def url(self):
        return f"https://{self.bucket}.s3.amazonaws.com/{self.key}"


@dataclasses.dataclass
class FeatureImage:
    caption: str
    image: ImageAsset


@dataclasses.dataclass
class Feature:
    id: int
    slug: str
    text: str
    title: str
    images: List[FeatureImage]


def _dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def _map_image(row) -> ImageAsset:
    return ImageAsset(
        id=row["id"],
        key=row["key"],
        bucket=row["bucket"],
        width=row["width"],
        height=row["height"],
        request_width=row.get("request_width"),
        request_height=row.get("request_height"),
        thumbs=list(map(_map_image, row.get("thumbs", [])))
    )


def _map_feature_image(row) -> FeatureImage:
    return FeatureImage(
        caption=row["caption"],
        image=_map_image(row)
    )


def _map_feature(row) -> Feature:
    return Feature(
        id=row["id"],
        slug=row["slug"],
        text=row["text"],
        title=row["title"],
        images=list(map(_map_feature_image, row["images"]))
    )


def get_features(app_id: int) -> List[Feature]:

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM features WHERE app_id = %s", [app_id])
        data = _dictfetchall(cursor)

        return list(map(_map_feature, data))