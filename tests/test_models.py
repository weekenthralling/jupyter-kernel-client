import pytest

from jkclient import V1Kernel


def test_kernel_model() -> None:
    kernel = {
        "api_version": "jupyter.org/v1beta1",
        "kind": "Kernel",
        "metadata": {
            "annotations": {"sidecar.istio.io/inject": "false"},
            "labels": {"app": "kernel"},
            "name": "kernel-7d25af7c-e687-46f6-98c3-0e7a0ce3a001",
            "namespace": "kubeflow-zc",
        },
        "spec": {
            "template": {
                "spec": {
                    "containers": [
                        {
                            "env": [
                                {
                                    "name": "KERNEL_ID",
                                    "value": "7d25af7c-e687-46f6-98c3-0e7a0ce3a001",
                                },
                                {"name": "KERNEL_USERNAME", "value": "jovyan"},
                                {"name": "KERNEL_LANGUAGE", "value": "python"},
                                {"name": "JPY_PARENT_PID", "value": "7"},
                                {"name": "LC_CTYPE", "value": "C.UTF-8"},
                                {"name": "KERNEL_IDLE_TIMEOUT", "value": "60"},
                            ],
                            "image": "weekenthralling/kernel-py:133fbe3",
                            "name": "kernel",
                            "volumeMounts": [
                                {"mountPath": "/mnt/shared", "name": "shared-vol"},
                            ],
                        }
                    ],
                    "restart_policy": "Never",
                    "volumes": [
                        {
                            "name": "shared-vol",
                            "nfs": {
                                "path": "/data/tablegpt-test/shared/",
                                "server": "10.0.0.29",
                            },
                        }
                    ],
                }
            }
        },
    }

    v1_kernel = V1Kernel(**kernel)
    assert v1_kernel.api_version == "jupyter.org/v1beta1"
    assert v1_kernel.kind == "Kernel"
    assert v1_kernel.status is None


if __name__ == "__main__":
    pytest.main()
