"""
File interface module with base class for making file handling configurable
for different storage backends.
"""

import logging
import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv

load_dotenv(".env")

# Interface type determined by environment variable, defaults to local
FILE_INTERFACE = os.environ.get("JIVAS_FILE_INTERFACE", "local")
DEFAULT_FILES_ROOT = os.environ.get("JIVAS_FILES_ROOT_PATH", ".files")


class FileInterface(ABC):
    """Abstract base class defining the interface for file storage operations."""

    __root_dir: str = ""
    LOGGER: logging.Logger = logging.getLogger(__name__)

    @abstractmethod
    def get_file(self, filename: str) -> bytes | None:
        """Retrieve a file from storage and return its contents as bytes."""
        pass

    @abstractmethod
    def save_file(self, filename: str, content: bytes) -> bool:
        """Save content to a file in storage."""
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage."""
        pass

    @abstractmethod
    def get_file_url(self, filename: str) -> str | None:
        """Get a URL to access the file."""
        pass


class LocalFileInterface(FileInterface):
    """Implementation of FileInterface for local filesystem storage."""

    def __init__(self, files_root: str = "") -> None:
        """Initialize local file interface with root directory."""
        self.__root_dir = files_root

    def get_file(self, filename: str) -> bytes | None:
        """Read and return contents of local file."""
        file_path = os.path.join(self.__root_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None

    def save_file(self, filename: str, content: bytes) -> bool:
        """Write content to a local file."""
        file_path = os.path.join(self.__root_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(content)
        return True

    def delete_file(self, filename: str) -> bool:
        """Delete local file."""
        file_path = os.path.join(self.__root_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def get_file_url(self, filename: str) -> str | None:
        """Get URL for accessing local file via HTTP."""
        file_path = os.path.join(self.__root_dir, filename)
        if os.path.exists(file_path):
            return f"{os.environ.get('JIVAS_FILES_URL', 'http://localhost:8000/files')}/{filename}"
        return None


class S3FileInterface(FileInterface):
    """Implementation of FileInterface for AWS S3 storage."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        endpoint_url: str | None = None,
        files_root: str = ".files",
    ) -> None:
        """Initialize S3 file interface."""
        import boto3
        from botocore.config import Config

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            endpoint_url=endpoint_url,
            config=Config(signature_version="v4"),
        )
        self.bucket_name = bucket_name
        self.__root_dir = files_root

        # Check for missing AWS credentials
        if not aws_access_key_id or not aws_secret_access_key or not region_name:
            FileInterface.LOGGER.warn(
                "Missing AWS credentials - S3 operations may fail"
            )

    def get_file(self, filename: str) -> bytes | None:
        """Get file contents from S3."""
        try:
            file_key = os.path.join(self.__root_dir, filename)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response["Body"].read()
        except Exception:
            return None

    def save_file(self, filename: str, content: bytes) -> bool:
        """Save file to S3 bucket."""
        try:
            file_key = os.path.join(self.__root_dir, filename)
            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=file_key, Body=content
            )
            return True
        except Exception:
            return False

    def delete_file(self, filename: str) -> bool:
        """Delete file from S3 bucket."""
        try:
            file_key = os.path.join(self.__root_dir, filename)
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except Exception:
            return False

    def get_file_url(self, filename: str) -> str | None:
        """Get pre-signed URL for S3 file access."""
        try:
            file_key = os.path.join(self.__root_dir, filename)
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_key},
                ExpiresIn=3600,
            )
            return url
        except Exception:
            return None


file_interface: FileInterface


def get_file_interface(files_root: str = DEFAULT_FILES_ROOT) -> FileInterface:
    """Returns a FileInterface instance based on the configured FILE_INTERFACE."""

    if FILE_INTERFACE == "s3":
        return S3FileInterface(
            bucket_name=os.environ.get("JIVAS_S3_BUCKET_NAME", ""),
            region_name=os.environ.get("JIVAS_S3_REGION_NAME", "us-east-1"),
            aws_access_key_id=os.environ.get("JIVAS_S3_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.environ.get("JIVAS_S3_SECRET_ACCESS_KEY", ""),
            endpoint_url=os.environ.get("JIVAS_S3_ENDPOINT_URL"),
            files_root=files_root,
        )
    else:
        return LocalFileInterface(files_root=files_root)


file_interface = get_file_interface()
