import asyncio
import os
from typing import AsyncIterator, Dict, List

import aiobotocore  # type: ignore
import click

from .utils import sizeof_fmt


class BucketException(Exception):
    pass


class Bucket:
    name: str
    session: aiobotocore.AioSession
    semaphore: asyncio.Semaphore
    skip_prompt: bool
    quiet: bool

    def __init__(
        self, bucket_name: str, semaphores: int, loop, skip_prompt: bool, quiet: bool
    ):
        self.name = bucket_name
        self.session = aiobotocore.get_session(loop=loop)
        self.semaphore = asyncio.Semaphore(semaphores)
        self.skip_prompt = skip_prompt
        self.quiet = quiet

    async def all_objects_paginator(self, prefix: str) -> AsyncIterator[List[Dict]]:
        kwargs = {"Bucket": self.name, "Prefix": prefix}
        async with self.session.create_client("s3") as client:
            while True:
                try:
                    response = await client.list_objects_v2(**kwargs)
                except client.exceptions.NoSuchBucket as e:
                    raise BucketException("Bucket not found") from e

                objects = response.get("Contents", [])
                yield objects

                if not response.get("IsTruncated"):
                    break

                kwargs["ContinuationToken"] = response["NextContinuationToken"]

    async def _download_object(self, client, obj: Dict, mode: str) -> int:
        async with self.semaphore:
            if mode == "folder":
                os.makedirs(os.path.dirname(obj["Key"]), exist_ok=True)

            if obj["Key"].endswith("/"):
                # Directory has been created, nothing to download
                return obj["Size"]

            if mode == "flat":
                local_file = obj["Key"].replace("/", "-")
            elif mode == "keys-only":
                local_file = obj["Key"].rsplit("/", maxsplit=1)[-1]
            else:
                local_file = obj["Key"]

            res = await client.get_object(Bucket=self.name, Key=obj["Key"])
            with open(local_file, "wb") as afp:
                afp.write(await res["Body"].read())
            return obj["Size"]

    def secho(self, msg: str, fg: str):
        """ A helper function to print out but respecting quiet """
        if self.quiet:
            return
        click.secho(msg, fg=fg)

    async def download_all_objects(self, prefix: str, mode: str):
        self.secho("[*] Fetching object metadata...", fg="green")
        objects = []
        try:
            async for page in self.all_objects_paginator(prefix):
                objects.extend(page)
        except BucketException as e:
            self.secho(f"[-] {e}", fg="red")
            return

        total_size = sum(o["Size"] for o in objects)

        if not objects:
            self.secho("[-] No objects found", fg="red")
            return

        self.secho(
            f"[*] Found {len(objects)} objects ({sizeof_fmt(total_size)})", fg="green"
        )

        if not self.skip_prompt and not click.confirm(
            click.style("[?] Do you want to download all the objects?", fg="yellow")
        ):
            self.secho("[-] Aborting...", fg="red")
            return

        async with self.session.create_client("s3") as client:
            tasks = []
            for obj in objects:
                task = asyncio.ensure_future(self._download_object(client, obj, mode))
                tasks.append(task)

            if self.quiet:
                for task in asyncio.as_completed(tasks):
                    await task
            else:
                with click.progressbar(
                    length=total_size,
                    label=click.style("[*] Downloading...", fg="green"),
                ) as bar:
                    for task in asyncio.as_completed(tasks):
                        bar.update(await task)
        self.secho("[*] All done!", fg="green")
