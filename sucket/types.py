import datetime as dt
from typing import Dict, List

from typing_extensions import TypedDict


class ObjectDict(TypedDict):
    Key: str
    LastModified: dt.datetime
    ETag: str
    Size: int
    StorageClass: str


class ListObjectsResultDict(TypedDict):
    ResponseMetadata: Dict
    IsTruncated: bool
    Contents: List[ObjectDict]
    Name: str
    Prefix: str
    MaxKeys: int
    EncodingType: str
    KeyCount: int
