import os
from datetime import datetime
from logging import Logger

import aioboto3
import aiofiles


class S3Storage:
    """
    Async S3 / MinIO storage adapter.
    Infrastructure layer.
    """

    def __init__(
        self,
        *,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        bucket_name: str,
        endpoint_url: str,
        region_name: str = "us-east-1",
        upload_folder: str = "",
        logger: Logger,
    ):
        self.logger = logger
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url.rstrip("/")
        self.region_name = region_name
        self.upload_folder = upload_folder.rstrip("/") + "/" if upload_folder else ""

        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    async def upload_file(self, file_path: str) -> str:
        if not os.path.exists(path=file_path):
            raise FileNotFoundError(file_path)

        date_str = datetime.utcnow().strftime(format="%Y-%m-%d")
        object_name = f"{self.upload_folder}{date_str}/{os.path.basename(file_path)}"

        async with self.session.client(
            service_name="s3",
            endpoint_url=self.endpoint_url,
        ) as s3: # type: ignore
            async with aiofiles.open(file=file_path, mode="rb") as file:
                await s3.upload_fileobj(file, self.bucket_name, object_name)

        self.logger.info(
            msg="Uploaded file to S3",
            extra={
                "bucket": self.bucket_name,
                "key": object_name,
            },
        )

        return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"