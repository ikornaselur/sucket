import asyncio
import os
from typing import List

import aiobotocore  # type: ignore
import click

from .types import ListObjectsResultDict, ObjectDict
from .utils import sizeof_fmt


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

    async def _download_object(self, client, obj: ObjectDict, mode: str) -> int:
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
            with open(local_file, "wb") as fp:
                async with res["Body"] as stream:
                    fp.write(await stream.read())
            return obj["Size"]

    def secho(self, msg: str, fg: str):
        """ A helper function to print out but respecting quiet """
        if self.quiet:
            return
        click.secho(msg, fg=fg)

    async def download_all_objects(self, prefix: str, mode: str):
        self.secho("[*] Fetching object metadata...", fg="green")
        async with self.session.create_client("s3") as client:
            objects: List[ObjectDict] = []
            paginator = client.get_paginator("list_objects_v2")

            try:
                result: ListObjectsResultDict
                async for result in paginator.paginate(Bucket=self.name, Prefix=prefix):
                    objects.extend(result["Contents"])
            except client.exceptions.NoSuchBucket:
                self.secho("[-] Bucket doesn't exist", fg="red")
                return

            if not objects:
                self.secho("[-] No objects found", fg="red")
                return

            total_size = sum(o["Size"] for o in objects)
            self.secho(
                f"[*] Found {len(objects)} objects ({sizeof_fmt(total_size)})",
                fg="green",
            )

            if not self.skip_prompt and not click.confirm(
                click.style("[?] Do you want to download all the objects?", fg="yellow")
            ):
                self.secho("[-] Aborting...", fg="red")
                return

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
