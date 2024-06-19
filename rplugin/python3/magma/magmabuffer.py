from pynvim import Nvim
from pynvim.api import Buffer

from magma.utils import Span
from magma.runtime import JupyterRuntime


class MagmaBuffer:
    nvim: Nvim
    buffer: Buffer

    runtime: JupyterRuntime

    def __init__(
        self,
        nvim: Nvim,
        buffer: Buffer,
        kernel_name: str,
    ):
        self.nvim = nvim
        self.buffer = buffer

        self._doautocmd("MagmaInitPre")
        self.runtime = JupyterRuntime(kernel_name)
        self._doautocmd("MagmaInitPost")

    def _doautocmd(self, autocmd: str) -> None:
        assert " " not in autocmd
        self.nvim.command(f"doautocmd User {autocmd}")

    def deinit(self) -> None:
        self._doautocmd("MagmaDeinitPre")
        self.runtime.deinit()
        self._doautocmd("MagmaDeinitPost")

    def interrupt(self) -> None:
        self.runtime.interrupt()

    def restart(self) -> None:
        self.runtime.restart()

    def run_code(self, code: str, span: Span) -> None:
        self.runtime.run_code(code)
