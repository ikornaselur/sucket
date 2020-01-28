import asyncio

import click

from .bucket import Bucket


async def main(
    loop,
    bucket_name: str,
    prefix: str,
    quiet: bool,
    skip_prompt: bool,
    semaphores: int,
    mode: str,
):
    bucket = Bucket(
        bucket_name=bucket_name,
        semaphores=semaphores,
        loop=loop,
        quiet=quiet,
        skip_prompt=skip_prompt,
    )
    await bucket.download_all_objects(prefix, mode)


@click.command()
@click.argument("bucket_name", type=str)
@click.argument(
    "prefix", required=False, default="", type=str,
)
@click.option(
    "-m",
    "--mode",
    help="The structure to download the objects in.",
    type=click.Choice(["folder", "flat", "keys-only"], case_sensitive=False),
    default="folder",
)
@click.option(
    "-y", "--yes", is_flag=True, help="Don't prompt for continuing", type=bool
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Don't print out any info, assumes --yes",
    type=bool,
)
@click.option(
    "-s",
    "--semaphores",
    help="Max number of asynchronous requests to make. Default: 1000",
    type=int,
    default=1000,
)
def sucket(
    bucket_name: str, prefix: str, yes: bool, quiet: bool, semaphores: int, mode: str
):
    """ Download all files from a S3 bucket

    Everything from the bucket BUCKET_NAME is downloaded, with an optional key
    filter, specified with PREFIX

    By default the "folder" mode is used, which will keep the bucket "folder
    structure" when downloading.

    The "flat" mode will download all objects into the current folder by adding
    the folder structure into the key name.

    The "keys-only" will completely disregard the folders and put all files in
    the current folder.
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        main(
            loop,
            bucket_name,
            prefix,
            quiet=quiet,
            skip_prompt=yes or quiet,
            semaphores=semaphores,
            mode=mode,
        )
    )
