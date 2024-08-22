from uuid import uuid4

import pytest

from jkclient import CreateKernelRequest, JupyterKernelClient
from jkclient.schema import KernelCreationForbiddenError


@pytest.fixture(scope="module")
def kernel_client() -> JupyterKernelClient:
    return JupyterKernelClient()


@pytest.fixture(scope="module")
def create_kernel_request() -> CreateKernelRequest:
    return CreateKernelRequest(
        env={
            "KERNEL_ID": "968183bb-13ef-4faf-b7d8-30fe8d20e6a3",
            "KERNEL_USERNAME": "dev",
            "KERNEL_NAMESPACE": "default",
            "KERNEL_IMAGE": "zjuici/tablegpt-kernel:0.1.1",
            "KERNEL_WORKING_DIR": "/mnt/data",
            "KERNEL_VOLUME_MOUNTS": [
                {"name": "shared-vol", "mountPath": "/mnt/data"},
                {"name": "ipython-profile-vol", "mountPath": "/opt/startup"},
                {
                    "name": "kernel-launch-vol",
                    "mountPath": "/usr/local/bin/bootstrap-kernel.sh",
                    "subPath": "bootstrap-kernel.sh",
                },
                {
                    "name": "kernel-launch-vol",
                    "mountPath": "/usr/local/bin/kernel-launchers/python/scripts/launch_ipykernel.py",
                    "subPath": "launch_ipykernel.py",
                },
            ],
            "KERNEL_VOLUMES": [
                {
                    "name": "shared-vol",
                    "nfs": {
                        "server": "10.0.0.29",
                        "path": "/data/tablegpt-slim-py/data",
                    },
                },
                {
                    "name": "ipython-profile-vol",
                    "configMap": {"name": "ipython-startup-scripts"},
                },
                {
                    "name": "kernel-launch-vol",
                    "configMap": {
                        "defaultMode": 0o755,
                        "name": "kernel-launch-scripts",
                    },
                },
            ],
            "KERNEL_STARTUP_SCRIPTS_PATH": "/opt/startup",
            "KERNEL_IDLE_TIMEOUT": "1800",
        },
    )


@pytest.mark.skip(reason="Create kernel with kubernetes config")
def test_create_kernel(
    kernel_client: JupyterKernelClient, create_kernel_request: CreateKernelRequest
) -> None:
    create_kernel_request.name = "foo-0"
    response = kernel_client.create(request=create_kernel_request)
    assert response is not None


@pytest.mark.skip(reason="Get kernel with kubernetes config")
def test_get_kernel(kernel_client: JupyterKernelClient) -> None:
    kernel = kernel_client.get(name="foo-0", namespace="default")
    assert kernel is not None


@pytest.mark.skip(reason="Get kernel with kubernetes config")
def test_get_kernel_none(kernel_client: JupyterKernelClient) -> None:
    with pytest.raises(RuntimeError):
        kernel_client.get(name="foo-1")


@pytest.mark.skip(reason="Delete kernel with kubernetes config")
def test_delete_kernel(kernel_client: JupyterKernelClient) -> None:
    kernel_client.delete(name="foo-1", namespace="default")


@pytest.mark.skip(reason="Delete kernel with kubernetes config")
def test_delete_kernel_by_kernel_id(kernel_client: JupyterKernelClient) -> None:
    kernel_client.delete_by_kernel_id(kerenl_id="968183bb-13ef-4faf-b7d8-30fe8d20e6a3")


@pytest.mark.skip(reason="Delete kernel with kubernetes config")
def test_delete_kernel_none(kernel_client: JupyterKernelClient) -> None:
    kernel_client.delete_by_kernel_id(kerenl_id=str(uuid4()))


@pytest.mark.asyncio
@pytest.mark.skip(reason="Create kernel with kubernetes config")
async def test_acreate_kernel(
    kernel_client: JupyterKernelClient, create_kernel_request: CreateKernelRequest
) -> None:
    create_kernel_request.name = "foo-0"
    response = await kernel_client.acreate(create_kernel_request)
    assert response is not None


@pytest.mark.asyncio
@pytest.mark.skip(reason="Create kernel with kubernetes config and resourcequota limit")
async def test_acreate_kernel_w_err(
    kernel_client: JupyterKernelClient, create_kernel_request: CreateKernelRequest
) -> None:
    with pytest.raises(KernelCreationForbiddenError):
        await kernel_client.acreate(create_kernel_request)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Get kernel with kubernetes config")
async def test_aget_kernel(kernel_client: JupyterKernelClient) -> None:
    response = await kernel_client.aget(name="foo-0", namespace="default")
    assert response is not None


@pytest.mark.asyncio
@pytest.mark.skip(reason="Delete kernel with kubernetes config")
async def test_adelete_kernel(kernel_client: JupyterKernelClient) -> None:
    await kernel_client.adelete(name="foo-0", namespace="default")


@pytest.mark.asyncio
@pytest.mark.skip(reason="Delete kernel with kubernetes config")
async def test_adelete_kernel_w_kid(kernel_client: JupyterKernelClient) -> None:
    await kernel_client.adelete_by_kernel_id(
        kerenl_id="968183bb-13ef-4faf-b7d8-30fe8d20e6a3"
    )


if __name__ == "__main__":
    pytest.main()
