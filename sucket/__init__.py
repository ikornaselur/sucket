import argparse
import os
from typing import Optional

import boto3  # type: ignore
from mypy_boto3_s3 import S3ServiceResource


def sucket(bucket_name: str, prefix: str):
    s3: S3ServiceResource = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    for page in bucket.objects.filter(Prefix=prefix).pages():
        for summary in page:
            obj = summary.Object()
            os.makedirs(os.path.dirname(obj.key), exist_ok=True)
            with open(obj.key, "wb") as f:
                obj.download_fileobj(f)


def cli():
    parser = argparse.ArgumentParser(description="Download all files from a S3 bucket")
    parser.add_argument("bucket", type=str, help="The S3 bucket to download from")
    parser.add_argument(
        "prefix",
        type=str,
        default="",
        nargs="?",
        help="An optional prefix to apply on the bucket",
    )

    args = parser.parse_args()

    sucket(args.bucket, args.prefix)
