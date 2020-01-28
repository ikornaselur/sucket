import asyncio
import os
from typing import AsyncIterator, Dict, List

import aiobotocore
import click


def sizeof_fmt(num: float, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


async def _download(sem, client, bucket_name: str, obj: Dict):
    async with sem:
        os.makedirs(os.path.dirname(obj["Key"]), exist_ok=True)
        if obj["Key"].endswith("/"):
            # Directory has been created, nothing to download
            return

        res = await client.get_object(Bucket=bucket_name, Key=obj["Key"])
        with open(obj["Key"], "wb") as afp:
            afp.write(await res["Body"].read())


async def all_objects(
    client, bucket_name: str, prefix: str
) -> AsyncIterator[List[Dict]]:
    kwargs = {"Bucket": bucket_name, "Prefix": prefix}
    while True:
        response = await client.list_objects_v2(**kwargs)
        objects = response.get("Contents", [])
        yield objects

        if not response.get("IsTruncated"):
            break

        kwargs["ContinuationToken"] = response["NextContinuationToken"]


async def main(loop, bucket_name: str, prefix: str, skip_prompt: int, semaphores: int):
    session = aiobotocore.get_session(loop=loop)
    async with session.create_client("s3") as client:
        click.secho("[*] Fetching object metadata...", fg="green")

        objects = []
        async for page in all_objects(client, bucket_name, prefix):
            objects.extend(page)
        total_size = sum(o["Size"] for o in objects)

        if not objects:
            click.secho("[-] No objects found", fg="red")
            return

        click.secho(
            f"[+] Found {len(objects)} objects ({sizeof_fmt(total_size)})", fg="green"
        )

        if not skip_prompt and not click.confirm(
            click.style("[?] Do you want to download all the objects?", fg="yellow")
        ):
            click.secho("[-] Aborting...", fg="red")
            return

        sem = asyncio.Semaphore(semaphores)
        tasks = []
        with click.progressbar(
            objects, label=click.style("[*] Downloading...", fg="green"), show_pos=True
        ) as bar:
            for obj in bar:
                task = asyncio.ensure_future(_download(sem, client, bucket_name, obj))
                tasks.append(task)
        await asyncio.gather(*tasks)


@click.command()
@click.argument("bucket_name", type=str)
@click.argument(
    "prefix", required=False, default="", type=str,
)
@click.option(
    "-y", "--yes", is_flag=True, help="Don't prompt for continuing", type=bool
)
@click.option(
    "-s",
    "--semaphores",
    help="Max number of asynchronous requests to make. Default: 1000",
    type=int,
    default=1000,
)
def sucket(bucket_name: str, prefix: str, yes: bool, semaphores: int):
    """ Download all files from a S3 bucket

    By default, everything from a the bucket BUCKET_NAME is downloaded, with an
    optional key filter, specified with PREFIX
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        main(loop, bucket_name, prefix, skip_prompt=yes, semaphores=semaphores)
    )
