import os

import boto3  # type: ignore
import click
from mypy_boto3_s3 import S3ServiceResource


def _download(obj):
    os.makedirs(os.path.dirname(obj.key), exist_ok=True)
    if obj.content_type == "application/x-directory":
        # Directory has been created, nothing to download
        return

    with open(obj.key, "wb") as f:
        obj.download_fileobj(f)


@click.command()
@click.argument("bucket_name", type=str)
@click.argument(
    "prefix", required=False, default="", type=str,
)
def sucket(bucket_name: str, prefix: str):
    """ Download all files from a S3 bucket

    By default, everything from a the bucket BUCKET_NAME is downloaded, with an
    optional key filter, specified with PREFIX
    """
    s3: S3ServiceResource = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    click.secho("[*] Fetching object metadata...", fg="green")
    objects = [
        summary.Object() for summary in bucket.objects.filter(Prefix=prefix).all()
    ]
    click.secho(f"[+] Found {len(objects)} objects", fg="green")
    if not click.confirm(click.style("[?] Continue?", fg="yellow")):
        click.secho("[-] Aborting...", fg="red")
        return

    with click.progressbar(
        objects, label=click.style("[*] Downloading...", fg="green"), show_pos=True
    ) as bar:
        for obj in bar:
            _download(obj)
