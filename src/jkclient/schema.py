from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class CreateKernelRequest(BaseModel):
    name: str | None = None
    """Kernel spec name (defaults to default kernel spec for server)."""
    env: dict[str, Any] = {}
    """A dictionary of environment variables and values to include in the kernel process - subject to filtering."""

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
