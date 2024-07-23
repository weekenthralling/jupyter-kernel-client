from __future__ import annotations

import datetime
import json
import logging
import os
import re
import tempfile
import time
from http import HTTPStatus
from typing import Any

import kubernetes.client.models
import six
from dateutil.parser import parse
from kubernetes import client, config, watch
from kubernetes.client import ApiException

import jkclient.models
from jkclient.models import V1Kernel
from jkclient.schema import CreateKernelRequest
from jkclient.schema import Kernel as KernelSchema

logger = logging.getLogger(__name__)

KERNEL_ID = "jupyter.org/kernel-id"
KERNEL_CONNECTION = "jupyter.org/kernel-connection-info"


class JupyterKernelClient:
    PRIMITIVE_TYPES = (float, bool, bytes, six.text_type) + six.integer_types
    NATIVE_TYPES_MAPPING = {
        "int": int,
        "long": int if six.PY3 else long,  # type: ignore # noqa: F821
        "float": float,
        "str": str,
        "bool": bool,
        "date": datetime.date,
        "datetime": datetime.datetime,
        "object": object,
    }

    def __init__(
        self,
        incluster: bool,
        group: str = "jupyter.org",
        version: str = "v1",
        kind: str = "Kernel",
        plural: str = "kernels",
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

    def create(self, request: CreateKernelRequest, **kwargs) -> KernelSchema:
        """Create kernel resource

        Args:
            request (CreateKernelRequest): create kernel request

        Returns:
            KernelSchema: kernel connection info
        """
        env = request.env
        logger.debug("Create kernel from env: %s", env)

        # Check kernel env
        if not env.get("KERNEL_IMAGE"):
            error_msg = "`KERNEL_IMAGE` must be not none"
            raise ValueError(error_msg)

        if not env.get("KERNEL_ID"):
            error_msg = "`KERNEL_ID` must be not none"
            raise ValueError(error_msg)

        kernel_id = env["KERNEL_ID"]
        kernel_user = env.get("KERNEL_USERNAME", "jovyan")
        kernel_name = request.name or f"{kernel_user}-{kernel_id}"

        kernel_namespace = env.get("KERNEL_NAMESPACE", "default")

        # pop kernel volumes and volume_mounts
        kernel_volumes = env.pop("KERNEL_VOLUMES", [])
        kernel_volume_mounts = env.pop("KERNEL_VOLUME_MOUNTS", [])

        # Generate kernel dict
        kernel_dict = {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": {
                "labels": {KERNEL_ID: kernel_id},
                "name": kernel_name,
                "namespace": kernel_namespace,
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {"name": name, "value": value}
                                    for name, value in env.items()
                                ],
                                "image": env["KERNEL_IMAGE"],
                                "name": "main",
                                "volumeMounts": kernel_volume_mounts,
                                "workingDir": env.get("KERNEL_WORKING_DIR"),
                            }
                        ],
                        "restartPolicy": "Never",
                        "volumes": kernel_volumes,
                    }
                }
            },
        }

        kernel = self._deserialize(kernel_dict, V1Kernel)

        try:
            response = self.api_instance.create_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=kernel_namespace,
                plural=self.plural,
                body=kernel,
                **kwargs,
            )
            logger.debug("Create response: %s", response)
        except ApiException as e:
            if e.status == HTTPStatus.CONFLICT.value:
                logger.debug("kernel %s already exists", kernel_name)
                return self.get(name=kernel_name, namespace=kernel_namespace)

            error_msg = f"Error create kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg)

        # Get kernel connection info from kernel label
        return self.get(name=kernel_name, namespace=kernel_namespace, **kwargs)

    async def acreate(self, request: CreateKernelRequest, **kwargs) -> KernelSchema:
        """Create kernel resource

        Args:
            request (CreateKernelRequest): create kernel request

        Returns:
            KernelSchema: kernel connection info
        """
        env = request.env
        logger.debug("Create kernel from env: %s", env)

        # Check kernel env
        if not env.get("KERNEL_IMAGE"):
            error_msg = "`KERNEL_IMAGE` must be not none"
            raise ValueError(error_msg)

        if not env.get("KERNEL_ID"):
            error_msg = "`KERNEL_ID` must be not none"
            raise ValueError(error_msg)

        kernel_id = env["KERNEL_ID"]
        kernel_user = env.get("KERNEL_USERNAME", "jovyan")
        kernel_name = request.name or f"{kernel_user}-{kernel_id}"

        kernel_namespace = env.get("KERNEL_NAMESPACE", "default")

        # pop kernel volumes and volume_mounts
        kernel_volumes = env.pop("KERNEL_VOLUMES", [])
        kernel_volume_mounts = env.pop("KERNEL_VOLUME_MOUNTS", [])

        # Generate kernel dict
        kernel_dict = {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": {
                "labels": {KERNEL_ID: kernel_id},
                "name": kernel_name,
                "namespace": kernel_namespace,
            },
            "spec": {
                "template": {
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {"name": name, "value": value}
                                    for name, value in env.items()
                                ],
                                "image": env["KERNEL_IMAGE"],
                                "name": "main",
                                "volumeMounts": kernel_volume_mounts,
                                "workingDir": env.get("KERNEL_WORKING_DIR"),
                            }
                        ],
                        "restartPolicy": "Never",
                        "volumes": kernel_volumes,
                    }
                }
            },
        }

        kernel = self._deserialize(kernel_dict, V1Kernel)

        try:
            response = self.api_instance.create_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=kernel_namespace,
                plural=self.plural,
                body=kernel,
                async_req=True,
                **kwargs,
            )
            logger.debug("Create response: %s", response.get())
        except ApiException as e:
            if e.status == HTTPStatus.CONFLICT.value:
                logger.debug("kernel %s already exists", kernel_name)
                return await self.aget(name=kernel_name, namespace=kernel_namespace)

            error_msg = f"Error create kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg)

        # Get kernel connection info from kernel label
        return await self.aget(name=kernel_name, namespace=kernel_namespace, **kwargs)

    def get(self, name: str, namespace: str = "default", **kwargs) -> KernelSchema:
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
                **kwargs,
            )
        except ApiException as e:
            error_msg = f"Error get kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg)

        # Check kernel if ready
        if kernel := self._wait_for_kernel_ready(
            name=name, namespace=namespace, **kwargs
        ):
            # Get kernel connection info from kernel label
            kernel_id = kernel["metadata"]["annotations"].get(KERNEL_ID, "")
            conn_info = kernel["metadata"]["annotations"].get(KERNEL_CONNECTION, None)

            return KernelSchema(
                name=name,
                kernel_id=kernel_id,
                conn_info=json.loads(conn_info) if conn_info else {},
            )

        error_msg = f"Kernel launch timeout due to: waited too long ({self.timeout}) to get connection info"
        raise RuntimeError(error_msg)

    async def aget(
        self, name: str, namespace: str = "default", **kwargs
    ) -> KernelSchema:
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
                async_req=True,
                **kwargs,
            )
        except ApiException as e:
            error_msg = f"Error get kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg)

        # Check kernel if ready
        if kernel := self._wait_for_kernel_ready(
            name=name, namespace=namespace, **kwargs
        ):
            # Get kernel connection info from kernel label
            kernel_id = kernel["metadata"]["annotations"].get(KERNEL_ID, "")
            conn_info = kernel["metadata"]["annotations"].get(KERNEL_CONNECTION, None)

            return KernelSchema(
                name=name,
                kernel_id=kernel_id,
                conn_info=json.loads(conn_info) if conn_info else {},
            )

        error_msg = f"Kernel launch timeout due to: waited too long ({self.timeout}) to get connection info"
        raise RuntimeError(error_msg)

    def delete(self, name: str, namespace: str = "default", **kwargs) -> None:
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
                **kwargs,
            )
        except ApiException as e:
            if e.status == HTTPStatus.NOT_FOUND.value:
                logger.warning("Kernel %s not found", name)
                return

            error_msg = f"Error delete kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg)

    async def adelete(self, name: str, namespace: str = "default", **kwargs) -> None:
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
                async_req=True,
                **kwargs,
            )
        except ApiException as e:
            if e.status == HTTPStatus.NOT_FOUND.value:
                logger.warning("Kernel %s not found", name)
                return

            error_msg = f"Error delete kernel: {e.status}\n{e.reason}"
            raise RuntimeError(error_msg)

    def delete_by_kernel_id(self, kerenl_id, **kwargs) -> None:
        """Delete kernel by kernel id

        Args:
            kerenl_id (_type_): kernel id
        """

        label_selector = f"{KERNEL_ID}={kerenl_id}"
        kernels = self.api_instance.list_cluster_custom_object(
            group=self.group,
            version=self.version,
            plural=self.plural,
            label_selector=label_selector,
            **kwargs,
        )
        logger.debug("List kernel response %s", kernels)
        if items := kernels.get("items", []):
            kernel_name = items[0]["metadata"]["name"]
            kernel_namespace = items[0]["metadata"]["namespace"]
            self.delete(name=kernel_name, namespace=kernel_namespace, **kwargs)

    async def adelete_by_kernel_id(self, kerenl_id, **kwargs) -> None:
        """Delete kernel by kernel id

        Args:
            kerenl_id (_type_): kernel id
        """

        label_selector = f"{KERNEL_ID}={kerenl_id}"
        response = self.api_instance.list_cluster_custom_object(
            group=self.group,
            version=self.version,
            plural=self.plural,
            label_selector=label_selector,
            async_req=True,
            **kwargs,
        )
        kernels = response.get()
        logger.debug("List kernel response %s", kernels)
        if items := kernels.get("items", []):
            kernel_name = items[0]["metadata"]["name"]
            kernel_namespace = items[0]["metadata"]["namespace"]
            await self.adelete(name=kernel_name, namespace=kernel_namespace, **kwargs)

    def _wait_for_kernel_ready(
        self, name: str, namespace: str, timeout=60, **kwargs
    ) -> Any | bool:
        """waitting for kernel ready

        Args:
            name (str): kernel name
            namespace (str): kernel namespaces
            timeout (int, optional): The maximum waiting time is reached;
                if it exceeds this time, stop watching and return false.. Defaults to 60.

        Returns:
            bool: Retuen kernel CR if kernel ready, otherwise, return false.
        """
        w = watch.Watch()
        start_time = time.time()
        logger.debug("Waiting for kernel %s to be created", name)
        try:
            for event in w.stream(
                self.api_instance.list_namespaced_custom_object,
                group=self.group,
                version=self.version,
                namespace=namespace,
                plural=self.plural,
                timeout_seconds=timeout,
                **kwargs,
            ):
                if event["type"] == "ADDED" or event["type"] == "MODIFIED":  # noqa: SIM102
                    if event["object"]["metadata"]["name"] == name and event[
                        "object"
                    ].get("status"):
                        logger.debug(
                            "Kernel %s created with event: %s", name, namespace
                        )
                        conditions = event["object"]["status"].get("conditions", [])
                        available_condition = next(
                            (c for c in conditions if c.get("type", None) == "Ready"),
                            None,
                        )
                        if (
                            available_condition
                            and available_condition.get("status", None) == "True"
                        ):
                            return event["object"]
                if time.time() - start_time > timeout:
                    logger.warning(
                        "Timeout waiting for kernel %s to be ready, delete it", name
                    )
                    self.delete(name=name, namespace=namespace, **kwargs)
                    return False
        finally:
            w.stop()

        return False

    def _deserialize(self, data, klass):
        """Deserializes dict, list, str into an object.

        :param data: dict, list or str.
        :param klass: class literal, or string of class name.

        :return: object.
        """
        if data is None:
            return None

        if klass == "file":
            return self.__deserialize_file(data)

        if type(klass) == str:  # noqa: E721
            if klass.startswith("list["):
                sub_kls = re.match(r"list\[(.*)\]", klass).group(1)
                return [self._deserialize(sub_data, sub_kls) for sub_data in data]

            if klass.startswith("dict("):
                sub_kls = re.match(r"dict\(([^,]*), (.*)\)", klass).group(2)
                return {
                    k: self._deserialize(v, sub_kls) for k, v in six.iteritems(data)
                }

            # convert str to class
            if klass in self.NATIVE_TYPES_MAPPING:
                klass = self.NATIVE_TYPES_MAPPING[klass]
            else:
                try:
                    klass = getattr(jkclient.models, klass)
                except AttributeError:
                    klass = getattr(kubernetes.client.models, klass)

        if klass in self.PRIMITIVE_TYPES:
            return self.__deserialize_primitive(data, klass)
        elif klass == object:  # noqa: E721
            return self.__deserialize_object(data)
        elif klass == datetime.date:
            return self.__deserialize_date(data)
        elif klass == datetime.datetime:
            return self.__deserialize_datetime(data)
        else:
            return self.__deserialize_model(data, klass)

    def __deserialize_file(self, response):
        """Deserializes body to file

        Saves response body into a file in a temporary folder,
        using the filename from the `Content-Disposition` header if provided.

        :param response:  RESTResponse.
        :return: file path.
        """
        fd, path = tempfile.mkstemp(dir=self.configuration.temp_folder_path)
        os.close(fd)
        os.remove(path)

        content_disposition = response.getheader("Content-Disposition")
        if content_disposition:
            filename = re.search(
                r'filename=[\'"]?([^\'"\s]+)[\'"]?', content_disposition
            ).group(1)
            path = os.path.join(os.path.dirname(path), filename)

        with open(path, "wb") as f:
            f.write(response.data)

        return path

    def __deserialize_primitive(self, data, klass):
        """Deserializes string to primitive type.

        :param data: str.
        :param klass: class literal.

        :return: int, long, float, str, bool.
        """
        try:
            return klass(data)
        except UnicodeEncodeError:
            return six.text_type(data)
        except TypeError:
            return data

    def __deserialize_object(self, value):
        """Return an original value.

        :return: object.
        """
        return value

    def __deserialize_date(self, string):
        """Deserializes string to date.

        :param string: str.
        :return: date.
        """
        try:
            return parse(string).date()
        except ImportError:
            return string
        except ValueError:
            raise ValueError("Failed to parse `{0}` as date object".format(string))

    def __deserialize_datetime(self, string):
        """Deserializes string to datetime.

        The string should be in iso8601 datetime format.

        :param string: str.
        :return: datetime.
        """
        try:
            return parse(string)
        except ImportError:
            return string
        except ValueError:
            error_msg = "Failed to parse `{0}` as datetime object".format(string)
            raise ValueError(error_msg)

    def __deserialize_model(self, data, klass):
        """Deserializes list or dict to model.

        :param data: dict, list.
        :param klass: class literal.
        :return: model object.
        """

        if not klass.openapi_types and not hasattr(klass, "get_real_child_model"):
            return data

        kwargs = {}
        if (
            data is not None
            and klass.openapi_types is not None
            and isinstance(data, (list, dict))
        ):
            for attr, attr_type in six.iteritems(klass.openapi_types):
                if klass.attribute_map[attr] in data:
                    value = data[klass.attribute_map[attr]]
                    kwargs[attr] = self._deserialize(value, attr_type)

        instance = klass(**kwargs)

        if hasattr(instance, "get_real_child_model"):
            klass_name = instance.get_real_child_model(data)
            if klass_name:
                instance = self._deserialize(data, klass_name)
        return instance
