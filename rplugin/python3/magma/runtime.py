from typing import Tuple, List, Generator, IO
from enum import Enum
from contextlib import contextmanager
import os
import tempfile
import json

import jupyter_client


class RuntimeState(Enum):
    STARTING = 0
    IDLE = 1
    RUNNING = 2


class JupyterRuntime:
    state: RuntimeState
    kernel_name: str

    kernel_manager: jupyter_client.KernelManager
    kernel_client: jupyter_client.KernelClient

    allocated_files: List[str]

    def __init__(self, kernel_name: str):
        self.state = RuntimeState.STARTING
        self.kernel_name = kernel_name

        if ".json" not in self.kernel_name:
            self.external_kernel = True
            self.kernel_manager = jupyter_client.manager.KernelManager(
                kernel_name=kernel_name
            )
            self.kernel_manager.start_kernel()
            self.kernel_client = self.kernel_manager.client()
            assert isinstance(
                self.kernel_client,
                jupyter_client.blocking.client.BlockingKernelClient,
            )
            self.kernel_client.start_channels()

            self.allocated_files = []

        else:
            kernel_file = kernel_name
            self.external_kernel = True
            # Opening JSON file
            kernel_json = json.load(open(kernel_file))
            # we have a kernel json
            self.kernel_manager = jupyter_client.manager.KernelManager(
                kernel_name=kernel_json["kernel_name"]
            )
            self.kernel_client = self.kernel_manager.client()

            self.kernel_client.load_connection_file(connection_file=kernel_file)

            self.allocated_files = []

    def is_ready(self) -> bool:
        return self.state.value > RuntimeState.STARTING.value

    def deinit(self) -> None:
        for path in self.allocated_files:
            if os.path.exists(path):
                os.remove(path)

        if self.external_kernel is False:
            self.kernel_client.shutdown()

    def interrupt(self) -> None:
        self.kernel_manager.interrupt_kernel()

    def restart(self) -> None:
        self.state = RuntimeState.STARTING
        self.kernel_manager.restart_kernel()

    def run_code(self, code: str) -> None:
        self.kernel_client.execute(code, store_history=False, allow_stdin=False)

    @contextmanager
    def _alloc_file(
        self, extension: str, mode: str
    ) -> Generator[Tuple[str, IO[bytes]], None, None]:
        with tempfile.NamedTemporaryFile(
            suffix="." + extension, mode=mode, delete=False
        ) as file:
            path = file.name
            yield path, file
        self.allocated_files.append(path)


def get_available_kernels() -> List[str]:
    return list(jupyter_client.kernelspec.find_kernel_specs().keys())
