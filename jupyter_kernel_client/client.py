from __future__ import annotations

import logging
import time
import json
from uuid import uuid4
from kubernetes import config, client, watch
from kubernetes.client import (
    V1ObjectMeta,
    V1PodTemplateSpec,
    V1PodSpec,
    V1Container,
    V1VolumeMount,
    V1Volume,
    V1EnvVar,
)
from jupyter_kernel_client.models import (
    V1Kernel,
    V1KernelSpec,
)
from jupyter_kernel_client.schema import CreateKernelRequest, Kernel as KernelSchema

logger = logging.getLogger(__name__)


class JupyterKernelClient:

    def __init__(
        self,
        group: str = "jupyter.org",
        version: str = "v1",
        kind: str = "Kernel",
        plural: str = "kernels",
        incluster: bool = True,
    ) -> None:
        if incluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()

        self.api_instance = client.CustomObjectsApi()

        self.kind = kind
        self.plural = plural
        self.group = group
        self.version = version
        self.api_version = f"{group}/{version}"

    def create(self, request: CreateKernelRequest) -> KernelSchema | None:
        """Create kernel resource

        Args:
            request (CreateKernelRequest): create kernel request

        Returns:
            KernelSchema: kernel connection info
        """
        env = request.env
        logger.debug(f"Create kernel from env: {env}")

        kernel_id = env.get("KERNEL_ID", uuid4().hex)
        kernel_name = request.name or f"jovyan-{uuid4().hex}"
        kernel_namespace = env.get("KERNEL_NAMESPACE", "default")

        # Set kernel volume mounts
        volume_mounts = []
        kernel_volume_mounts = env.pop("KERNEL_VOLUME_MOUNTS", None)
        if kernel_volume_mounts and isinstance(kernel_volume_mounts, list):
            volume_mounts = [
                V1VolumeMount(**volume_mount) for volume_mount in volume_mounts
            ]

        # Set kernel volumes
        volumes = []
        kernel_volumes = env.pop("KERNEL_VOLUMES", None)
        if kernel_volumes and isinstance(kernel_volumes, list):
            volumes = [V1Volume(**volume) for volume in kernel_volumes]

        # TODO: Set kernel env, value_from is not considered
        container_env = [
            V1EnvVar(name=name, value=value) for name, value in env.items()
        ]

        kernel = V1Kernel(
            api_version=self.api_version,
            kind=self.kind,
            metadata=V1ObjectMeta(
                name=kernel_name,
                namespace=kernel_namespace,
                labels={"kernel-id": kernel_id},
            ),
            spec=V1KernelSpec(
                template=V1PodTemplateSpec(
                    spec=V1PodSpec(
                        containers=[
                            V1Container(
                                name="main",
                                image=env["KERNEL_IMAGE"],
                                env=container_env,
                                volume_mounts=volume_mounts,
                            )
                        ],
                        restart_policy="Never",
                        volumes=volumes,
                    ),
                ),
            ),
        )

        response = self.api_instance.create_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=kernel_namespace,
            plural=self.plural,
            body=kernel,
        )
        logger.debug(f"Create response: {response}")

        return KernelSchema(
            kernel_id=kernel_id,
            name=kernel_name,
            conn_info={},
        )

    def _wait_for_kernel_creation(self, name, namespace, timeout=60):
        w = watch.Watch()
        start_time = time.time()
        logger.debug(f"Waiting for kernel {name} to be created")
        for event in w.stream(
            self.api_instance.list_namespaced_custom_object,
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural=self.plural,
            timeout_seconds=timeout,
        ):
            if event["type"] == "ADDED" or event["type"] == "MODIFIED":
                if event["object"]["metadata"]["name"] == name:
                    logger.debug(f"Kernel {name} created with event: {event}")
                    w.stop()
                    return event["object"]
            if time.time() - start_time > timeout:
                logger.error(f"Timeout waiting for kernel {name} to be created")
                w.stop()
                return None

    def get(self, name: str, namespace: str = "default") -> KernelSchema | None:
        """Get kernel connection info by name and namespace

        Args:
            name (str): kernel name
            namespace (str, optional): kernel namespace. Defaults to "default".

        Returns:
            KernelSchema: kernel connection info
        """

        try:
            kernel = self.api_instance.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=namespace,
                plural=self.plural,
                name=name,
            )
        except Exception as e:
            logger.error(f"Failed get kernel {name} namespace: {namespace}", e)
            return None

        # Get kernel connection info from kernel label
        kernel_id = kernel["metadata"]["labels"].get("kernel-id", "")
        conn_info = kernel["metadata"]["labels"].get("kernel-conn-info", None)

        return KernelSchema(
            name=name,
            kernel_id=kernel_id,
            conn_info=json.loads(conn_info) if conn_info else {},
        )

    def delete(self, name: str, namespace: str = "default") -> None:
        """Delete kernel by name and namespaces

        Args:
            name (str): kernel name
            namespace (str, optional): kernel namespace. Defaults to "default".
        """
        self.api_instance.delete_namespaced_custom_object(
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural=self.plural,
            name=name,
        )
