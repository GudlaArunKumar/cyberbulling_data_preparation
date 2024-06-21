import os

from typing import Any

import yaml

from fsspec import AbstractFileSystem, filesystem  #  provides an abstract file-system interface

GCS_PREFIX = "gs://"
GCS_FILE_SYSTEM_NAME = "gcs"
LOCAL_FILE_SYSTEM_NAME = "file"
TMP_FILE_PATH = "/tmp/"   # inside docker container


def choose_file_system(path: str) -> AbstractFileSystem:
    return filesystem(GCS_FILE_SYSTEM_NAME) if path.startswith(GCS_PREFIX) else filesystem(LOCAL_FILE_SYSTEM_NAME)


# To open/save the file either in gcp or local file system
def open_file(path: str, mode: str = "r") -> Any:
    file_system = choose_file_system(path)
    return file_system.open(path, mode)


def write_yaml_file(yaml_file_path: str, yaml_file_content: dict[Any, Any]) -> None:
    with open_file(yaml_file_path, "w") as yaml_file:
        yaml.dump(yaml_file_content, yaml_file)