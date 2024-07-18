from uuid import uuid4

import pytest

from jkclient import CreateKernelRequest


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
            {"name": "shared-vol", "mount_path": "/mnt/data"},
            {"name": "ipython-profile-vol", "mount_path": "/opt/startup"},
        ],
        "KERNEL_VOLUMES": [
            {
                "name": "shared-vol",
                "nfs": {"server": "10.0.0.29", "path": "/data"},
            },
            {
                "name": "ipython-profile-vol",
                "config_map": {"name": "ipython-startup-scripts"},
            },
        ],
        "KERNEL_STARTUP_SCRIPTS_PATH": "/opt/startup",
    }
    request = CreateKernelRequest(name=name, env=env)
    assert request.env is not None
    assert request.env["KERNEL_NAMESPACE"] == "default"


def test_create_kernel_request_env_error() -> None:
    name = f"kernel-{uuid4().hex}"
    env = {
        "KERNEL_USERNAME": "jovyan",
        "KERNEL_NAMESPACE": "default",
        "KERNEL_IMAGE": "weekenthralling/kernel-py:0.0.1",
        "KERNEL_WORKING_DIR": "/mnt/data",
        "KERNEL_VOLUME_MOUNTS": "foo-0",
        "KERNEL_VOLUMES": "bar-0",
        "KERNEL_STARTUP_SCRIPTS_PATH": "/opt/startup",
    }
    with pytest.raises(ValueError) as excinfo:
        CreateKernelRequest(name=name, env=env)
        assert str(excinfo.value) == "`KERNEL_VOLUME_MOUNTS` must be a json str"


def test_create_kernel_request_env_volumns() -> None:
    import json

    name = f"kernel-{uuid4().hex}"
    env = {
        "KERNEL_USERNAME": "jovyan",
        "KERNEL_NAMESPACE": "default",
        "KERNEL_IMAGE": "weekenthralling/kernel-py:0.0.1",
        "KERNEL_WORKING_DIR": "/mnt/data",
        "KERNEL_VOLUME_MOUNTS": '[{"name":"shared-vol","mount_path":"/mnt/data"},{"name":"ipython-profile-vol","mount_path":"/opt/startup"}]',
        "KERNEL_VOLUMES": '[{"name":"shared-vol","nfs":{"server":"10.0.0.29","path":"/data/tablegpt-slim-py/data"}},{"name":"ipython-profile-vol","config_map":{"name":"ipython-startup-scripts"}}]',
        "KERNEL_STARTUP_SCRIPTS_PATH": "/opt/startup",
    }
    request = CreateKernelRequest(name=name, env=env)
    assert isinstance(request.env["KERNEL_VOLUME_MOUNTS"], list)
    assert request.env["KERNEL_VOLUME_MOUNTS"] == json.loads(
        env["KERNEL_VOLUME_MOUNTS"]
    )
    assert isinstance(request.env["KERNEL_VOLUMES"], list)
    assert request.env["KERNEL_VOLUMES"] == json.loads(env["KERNEL_VOLUMES"])


if __name__ == "__main__":
    pytest.main()
