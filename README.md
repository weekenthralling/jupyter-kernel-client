# Jupyter-Kernel-Client

The Jupyter Kernel Client provides you with the ability to create, query, and delete Kubernetes kernel custom resources. It uses the [Jupyter Kernel Controller](https://github.com/weekenthralling/jupyter-kernel-controller) to create the necessary [pod](https://kubernetes.io/docs/concepts/workloads/pods/) and [service](https://kubernetes.io/docs/concepts/services-networking/service/) resources for the kernel custom resources. Finally, you can connect to the created remote kernel using the [jupyter-client](https://github.com/jupyter/jupyter_client).

## Installation and Basic usage

To install the latest release locally, make sure you have
[pip installed](https://pip.readthedocs.io/en/stable/installing/) and run:

```console
pip install jkclient
```

## Usage - Running Jupyter Kernel Client

**Create kernel**

```python
from uuid import uuid4
from jkclient import CreateKernelRequest, JupyterKernelClient

client = JupyterKernelClient(incluster=False)
request = CreateKernelRequest(
    name="foo",
    env={
        "KERNEL_ID": str(uuid4()),
        "KERNEL_USERNAME": "jovyan",
        "KERNEL_NAMESPACE": "default",
        "KERNEL_IMAGE": "weekenthralling/kernel-py:480d2f5",
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

client.create(request=request)
```

**And return the kernel connection info**

```json
{
    "kernel_id" : "968183bb-13ef-4faf-b7d8-30fe8d20e6a3",
    "kernel_name": "foo-0",
    "conn_info": {
        "shell_port": 52317,
        "stdin_port": 52321,
        "iopub_port": 52318,
        "control_port": 52320,
        "hb_port": 52319,
        "ip": "foo.default.svc.cluster.local",
        "key": "968183bb-13ef-4faf-b7d8-30fe8d20e6a3",
        "transport": "tcp",
        "signature_scheme": "hmac-sha256",
        "kernel_name": "",
    }
}
```

**Use kernel connection info**

```python
import queue
from jupyter_client.blocking import BlockingKernelClient

client = BlockingKernelClient()
client.load_connection_info(
    info={
        "shell_port": 52317,
        "stdin_port": 52321,
        "iopub_port": 52318,
        "control_port": 52320,
        "hb_port": 52319,
        "ip": "foo.default.svc.cluster.local",
        "key": "968183bb-13ef-4faf-b7d8-30fe8d20e6a3",
        "transport": "tcp",
        "signature_scheme": "hmac-sha256",
        "kernel_name": "",
    }
)

client.start_channels()

code = """
import math
result = math.sqrt(16)
result
"""
client.execute(code)

shell_msg = None
while True:
    try:
        shell_msg = client.get_shell_msg(timeout=30)
        if shell_msg["msg_type"] == "execute_reply":
            break
    except queue.Empty:
        print(f"Get shell msg is empty.")
        break

iopub_msg = None
while True:
    # Poll the message
    try:
        io_msg_content = client.get_iopub_msg(timeout=30)["content"]
        print(f"io_msg_content: {io_msg_content}")
        if (
            "execution_state" in io_msg_content
            and io_msg_content["execution_state"] == "idle"
        ):
            break
        iopub_msg = io_msg_content
    except queue.Empty:
        print(f"Get iopub msg is empty.")
        break

print(f"Got kernel output, shell_msg: {shell_msg} iopub_msg: {iopub_msg}")
```

**Get exec code log**

```console
Got kernel output, shell_msg: {'header': {'msg_id': 'cf9f0c39-b0fbb1595399f44b68f893ab_9_39', 'msg_type': 'execute_reply', 'username': 'username', 'session': 'cf9f0c39-b0fbb1595399f44b68f893ab', 'date': datetime.datetime(2024, 7, 9, 8, 31, 56, 856558, tzinfo=tzlocal()), 'version': '5.3'}, 'msg_id': 'cf9f0c39-b0fbb1595399f44b68f893ab_9_39', 'msg_type': 'execute_reply', 'parent_header': {'msg_id': 'c65b2c1d-b8dca8ea83672d1f56b1a79d_86_3', 'msg_type': 'execute_request', 'username': 'username', 'session': 'c65b2c1d-b8dca8ea83672d1f56b1a79d', 'date': datetime.datetime(2024, 7, 9, 8, 31, 56, 846349, tzinfo=tzlocal()), 'version': '5.3'}, 'metadata': {'started': '2024-07-09T08:31:56.847191Z', 'dependencies_met': True, 'engine': 'a6d2191d-b438-44f0-a413-d8db6af4cebe', 'status': 'ok'}, 'content': {'status': 'ok', 'execution_count': 8, 'user_expressions': {}, 'payload': []}, 'buffers': []} iopub_msg: {'data': {'text/plain': '4.0'}, 'metadata': {}, 'execution_count': 1}
```

## License

`Jupyter-Kernel-Client` is distributed under the terms of the [Apache 2.0](https://spdx.org/licenses/Apache-2.0.html) license.
