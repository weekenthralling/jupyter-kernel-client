from __future__ import annotations

import json
import logging
import time
from http import HTTPStatus
from uuid import uuid4

from kubernetes import client, config, watch
from kubernetes.client import (
    ApiException,
    V1Container,
    V1EnvVar,
    V1ObjectMeta,
    V1PodSpec,
    V1PodTemplateSpec,
    V1Volume,
    V1VolumeMount,
)

from jkclient.models import V1Kernel, V1KernelSpec
from jkclient.schema import CreateKernelRequest
from jkclient.schema import Kernel as KernelSchema

logger = logging.getLogger(__name__)

KERNEL_ID = "jupyter.org/kernel-id"
KERNEL_CONNECTION = "jupyter.org/kernel-connection-info"


class JupyterKernelClient:
    def __init__(
        self,
        group: str = "jupyter.org",
        version: str = "v1",
        kind: str = "Kernel",
        plural: str = "kernels",
        incluster: bool = True,  # noqa: FBT001, FBT002
        timeout: int = 60,
    ) -> None:
        if incluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()

        self.kind = kind
        self.plural = plural
        self.group = group
        self.version = version
        self.timeout = timeout

        self.api_version = f"{group}/{version}"
        self.api_instance = client.CustomObjectsApi()

    def create(self, request: CreateKernelRequest) -> KernelSchema | None:
        """Create kernel resource

        Args:
            request (CreateKernelRequest): create kernel request

        Returns:
            KernelSchema: kernel connection info
        """
        env = request.env
        logger.debug("Create kernel from env: %s", env)

        kernel_id = env.get("KERNEL_ID", uuid4().hex)
        kernel_name = request.name or f"jovyan-{uuid4().hex}"
        kernel_namespace = env.get("KERNEL_NAMESPACE", "default")

        # Set kernel volume mounts
        volume_mounts = []
        kernel_volume_mounts = env.pop("KERNEL_VOLUME_MOUNTS", None)
        if kernel_volume_mounts and isinstance(kernel_volume_mounts, list):
            volume_mounts = [
                V1VolumeMount(**volume_mount) for volume_mount in kernel_volume_mounts
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

        try:
            response = self.api_instance.create_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=kernel_namespace,
                plural=self.plural,
                body=kernel,
            )
            logger.debug("Create response: %s", response)
        except ApiException as e:
            if e.status == HTTPStatus.CONFLICT.value:
                logger.debug("kernel %s already exists", kernel_name)
                return self.get(name=kernel_name, namespace=kernel_namespace)

            error_msg = f"Error create kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg) from None

        # Get kernel connection info from kernel label
        resource = self._wait_for_kernel_ready(
            name=kernel_name, namespace=kernel_namespace
        )
        if resource and (
            conn_info := resource["metadata"]["annotations"].get(KERNEL_CONNECTION)
        ):
            return KernelSchema(
                kernel_id=kernel_id, name=kernel_name, conn_info=json.loads(conn_info)
            )

        error_msg = f"Kernel launch timeout due to: waited too long ({self.timeout}) to get connection info"
        raise RuntimeError(error_msg) from None

    def _wait_for_kernel_ready(self, name, namespace, timeout=60):
        w = watch.Watch()
        start_time = time.time()
        logger.debug("Waiting for kernel %s to be created", name)
        for event in w.stream(
            self.api_instance.list_namespaced_custom_object,
            group=self.group,
            version=self.version,
            namespace=namespace,
            plural=self.plural,
            timeout_seconds=timeout,
        ):
            if event["type"] == "ADDED" or event["type"] == "MODIFIED":  # noqa: SIM102
                if event["object"]["metadata"]["name"] == name and event["object"].get(
                    "status"
                ):
                    logger.debug("Kernel %s created with event: %s", name, namespace)
                    conditions = event["object"]["status"].get("conditions", [])
                    available_condition = next(
                        (c for c in conditions if c.get("type", None) == "Ready"), None
                    )
                    if (
                        available_condition
                        and available_condition.get("status", None) == "True"
                    ):
                        w.stop()
                        return event["object"]
            if time.time() - start_time > timeout:
                logger.warning(
                    "Timeout waiting for kernel %s to be ready, delete it", name
                )
                self.delete(name=name, namespace=namespace)
                w.stop()
                return None
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
        except ApiException as e:
            if e.status == HTTPStatus.NOT_FOUND.value:
                return None

            error_msg = f"Error get kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg) from None

        # TODO: Check kernel if ready

        # Get kernel connection info from kernel label
        kernel_id = kernel["metadata"]["annotations"].get(KERNEL_ID, "")
        conn_info = kernel["metadata"]["annotations"].get(KERNEL_CONNECTION, None)

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
        try:
            self.api_instance.delete_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=namespace,
                plural=self.plural,
                name=name,
            )
        except ApiException as e:
            if e.status == HTTPStatus.NOT_FOUND.value:
                logger.warning("Kernel %s not found", name)
                return

            error_msg = f"Error delete kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg) from None
