from uuid import uuid4

import pytest

from jkclient import CreateKernelRequest, JupyterKernelClient


@pytest.mark.skip(reason="Create kernel with kubernetes config")
def test_create_kernel() -> None:
    client = JupyterKernelClient(incluster=False)

    request = CreateKernelRequest(
        name="foo-0",
        env={
            "KERNEL_ID": str(uuid4()),
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


@pytest.mark.skip(reason="Create kernel with kubernetes config")
def test_create_kernel_without_name() -> None:
    client = JupyterKernelClient(incluster=False)
    request = CreateKernelRequest(
        env={
            "KERNEL_ID": str(uuid4()),
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


@pytest.mark.skip(reason="Create kernel with kubernetes config")
def test_create_kernel_with_work_dir() -> None:
    client = JupyterKernelClient(incluster=False)
    request = CreateKernelRequest(
        env={
            "KERNEL_ID": str(uuid4()),
            "KERNEL_USERNAME": "tablegpt",
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
    response = client.create(request)
    assert response is not None


@pytest.mark.skip(reason="Get kernel with kubernetes config")
def test_get_kernel() -> None:
    client = JupyterKernelClient(incluster=False)
    kernel = client.get(name="foo-0", namespace="default")

    assert kernel is not None


@pytest.mark.skip(reason="Get kernel with kubernetes config")
def test_get_kernel_none() -> None:
    client = JupyterKernelClient(incluster=False)
    kernel = client.get(name="foo-1")

    assert kernel is None


@pytest.mark.skip(reason="Delete kernel with kubernetes config")
def test_delete_kernel() -> None:
    client = JupyterKernelClient(incluster=False)
    client.delete(name="foo-1", namespace="default")


@pytest.mark.skip(reason="Delete kernel with kubernetes config")
def test_delete_kernel_by_kernel_id() -> None:
    client = JupyterKernelClient(incluster=False)
    client.delete_by_kernel_id(kerenl_id="968183bb-13ef-4faf-b7d8-30fe8d20e6a3")


@pytest.mark.skip(reason="Delete kernel with kubernetes config")
def test_delete_kernel_none() -> None:
    client = JupyterKernelClient(incluster=False)
    client.delete_by_kernel_id(kerenl_id=str(uuid4()))


if __name__ == "__main__":
    pytest.main()
