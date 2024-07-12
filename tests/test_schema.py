import pytest

from uuid import uuid4
from jupyter_kernel_client.schema import CreateKernelRequest


def test_create_kernel_request() -> None:
    name = f"kernel-{uuid4().hex}"
    request = CreateKernelRequest(name=name)

    assert request.name == name
    assert request.env == {}


def test_create_kernel_request_env() -> None:
    name = f"kernel-{uuid4().hex}"

    env = {
        "KERNEL_USERNAME": "jovyan",
        "KERNEL_NAMESPACE": "default",
        "KERNEL_IMAGE": "weekenthralling/kernel-py:0.0.1",
        "KERNEL_WORKING_DIR": "/mnt/data",
        "KERNEL_VOLUME_MOUNTS": [
            {"name": "shared-vol", "mountPath": "/mnt/data"},
            {"name": "ipython-profile-vol", "mountPath": "/opt/startup"},
        ],
        "KERNEL_VOLUMES": [
            {
                "name": "shared-vol",
                "nfs": {"server": "10.0.0.29", "path": "/data"},
            },
            {
                "name": "ipython-profile-vol",
                "configMap": {"name": "ipython-startup-scripts"},
            },
        ],
        "KERNEL_STARTUP_SCRIPTS_PATH": "/opt/startup",
    }
    request = CreateKernelRequest(name=name, env=env)
    assert request.env is not None
    assert request.env["KERNEL_NAMESPACE"] == "default"
    assert isinstance(request.env["KERNEL_VOLUME_MOUNTS"], str)
    assert isinstance(request.env["KERNEL_VOLUMES"], str)


if __name__ == "__main__":
    pytest.main()
