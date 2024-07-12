import pytest

from uuid import uuid4

from jupyter_kernel_client.schema import CreateKernelRequest
from jupyter_kernel_client.client import JupyterKernelClient


def test_create_kernel() -> None:
    client = JupyterKernelClient(incluster=False)

    request = CreateKernelRequest(
        name="foo-0",
        env={
            "KERNEL_ID": uuid4().hex,
            "KERNEL_NAME": f"kernel-{uuid4().hex}",
            "KERNEL_USERNAME": "jovyan",
            "KERNEL_NAMESPACE": "default",
            "KERNEL_IMAGE": "weekenthralling/kernel-py:133fbe3",
            "KERNEL_WORKING_DIR": "/mnt/data",
            "KERNEL_VOLUME_MOUNTS": [
                {"name": "shared-vol", "mountPath": "/mnt/data"},
            ],
            "KERNEL_VOLUMES": [
                {
                    "name": "shared-vol",
                    "nfs": {"server": "10.0.0.29", "path": "/data"},
                },
            ],
            "KERNEL_STARTUP_SCRIPTS_PATH": "/opt/startup",
            "KERNEL_IDLE_TIMEOUT": "1800",
        },
    )
    response = client.create(request=request)
    assert response is not None


def test_get_kernel() -> None:
    client = JupyterKernelClient(incluster=False)
    kernel = client.get(name="foo-0", namespace="default")

    assert kernel is not None


def test_get_kernel_none() -> None:
    client = JupyterKernelClient(incluster=False)
    kernel = client.get(name="foo-1")

    assert kernel is None


def test_delete_kernel() -> None:
    client = JupyterKernelClient(incluster=False)
    client.delete(name="foo-1", namespace="default")


if __name__ == "__main__":
    pytest.main()
