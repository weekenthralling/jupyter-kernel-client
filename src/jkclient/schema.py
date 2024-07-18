from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, field_validator


class CreateKernelRequest(BaseModel):
    name: str | None = None
    """Kernel spec name (defaults to default kernel spec for server)."""
    env: dict[str, Any] = {}
    """A dictionary of environment variables and values to include in the kernel process - subject to filtering."""

    @field_validator("env")
    @classmethod
    def convert_env_value_to_list(cls, v: dict[str, Any]) -> dict[str, str]:
        if "KERNEL_VOLUME_MOUNTS" in v:
            kernel_volume_mounts = v["KERNEL_VOLUME_MOUNTS"]
            if isinstance(kernel_volume_mounts, str):
                try:
                    kernel_volume_mounts = json.loads(kernel_volume_mounts)
                except ValueError:
                    err_msg = "`KERNEL_VOLUME_MOUNTS` must be a json str"
                    raise ValueError(err_msg)
            if not isinstance(kernel_volume_mounts, list):
                err_msg = "`KERNEL_VOLUME_MOUNTS` must be a list or json list str"
                raise ValueError(err_msg)
            v["KERNEL_VOLUME_MOUNTS"] = kernel_volume_mounts

        if "KERNEL_VOLUMES" in v:
            kernel_volumes = v["KERNEL_VOLUMES"]
            if isinstance(v["KERNEL_VOLUMES"], str):
                try:
                    kernel_volumes = json.loads(kernel_volumes)
                except ValueError:
                    err_msg = "`KERNEL_VOLUMES` must be a json str"
                    raise ValueError(err_msg)
            if not isinstance(kernel_volumes, list):
                err_msg = "`KERNEL_VOLUME` must be a list or json list str"
                raise ValueError(err_msg)
            v["KERNEL_VOLUMES"] = kernel_volumes

        return v

    def model_dump(self):
        return super().model_dump(by_alias=True, exclude_none=True)

    def model_dump_json(self):
        return super().model_dump_json(by_alias=True, exclude_none=True)


class Kernel(BaseModel):
    """Kernel info"""

    name: str
    """Kernel spec name (defaults to default kernel spec for server)."""
    kernel_id: str
    """Indicates the id associated with the launched kernel."""
    conn_info: dict[str, Any] = {}
    """Kernel connection info, include kernel shell_port, service and other"""
