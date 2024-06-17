from typing import Optional, Dict
from queue import Queue
import hashlib

import pynvim
from pynvim import Nvim
from pynvim.api import Buffer

from magma.options import MagmaOptions
from magma.utils import MagmaException, Position, Span
from magma.runtime import JupyterRuntime


class MagmaBuffer:
    nvim: Nvim
    highlight_namespace: int
    extmark_namespace: int
    buffer: Buffer

    runtime: JupyterRuntime

    options: MagmaOptions

    def __init__(
        self,
        nvim: Nvim,
        highlight_namespace: int,
        extmark_namespace: int,
        buffer: Buffer,
        options: MagmaOptions,
        kernel_name: str,
    ):
        self.nvim = nvim
        self.highlight_namespace = highlight_namespace
        self.extmark_namespace = extmark_namespace
        self.buffer = buffer

        self._doautocmd("MagmaInitPre")

        self.runtime = JupyterRuntime(kernel_name, options)

        self.options = options

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

    def restart(self, delete_outputs: bool = False) -> None:
        self.runtime.restart()

    def run_code(self, code: str, span: Span) -> None:
        self.runtime.run_code(code)

    def tick(self) -> None:
        was_ready = self.runtime.is_ready()
        if not was_ready and self.runtime.is_ready():
            self.nvim.api.notify(
                "Kernel '%s' is ready." % self.runtime.kernel_name,
                pynvim.logging.INFO,
                {"title": "Magma"},
            )

    def _get_cursor_position(self) -> Position:
        _, lineno, colno, _, _ = self.nvim.funcs.getcurpos()
        return Position(self.nvim.current.buffer.number, lineno - 1, colno - 1)

    def _get_selected_span(self) -> Optional[Span]:
        current_position = self._get_cursor_position()
        selected = None
        for span in reversed(self.outputs.keys()):
            if current_position in span:
                selected = span
                break

        return selected

    def _get_content_checksum(self) -> str:
        return hashlib.md5(
            "\n".join(self.nvim.current.buffer.api.get_lines(0, -1, True)).encode(
                "utf-8"
            )
        ).hexdigest()
