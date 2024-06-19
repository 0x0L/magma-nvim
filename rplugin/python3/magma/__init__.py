from typing import Any, Dict, List, Optional, Tuple

import pynvim
from magma.magmabuffer import MagmaBuffer
from magma.runtime import get_available_kernels
from magma.utils import DynamicPosition, MagmaException, Span, nvimui
from pynvim import Nvim


@pynvim.plugin
class Magma:
    nvim: Nvim
    initialized: bool

    highlight_namespace: int
    extmark_namespace: int

    buffers: Dict[int, MagmaBuffer]

    timer: Optional[int]

    def __init__(self, nvim: Nvim):
        self.nvim = nvim
        self.initialized = False

        self.buffers = {}
        self.timer = None

    def _initialize(self) -> None:
        assert not self.initialized

        self.highlight_namespace = self.nvim.funcs.nvim_create_namespace(
            "magma-highlights"
        )
        self.extmark_namespace = self.nvim.funcs.nvim_create_namespace("magma-extmarks")

        self._set_autocommands()

        self.initialized = True

    def _set_autocommands(self) -> None:
        self.nvim.command("augroup magma")
        self.nvim.command("  autocmd BufUnload    * call MagmaOnBufferUnload()")
        self.nvim.command("  autocmd ExitPre      * call MagmaOnExitPre()")
        self.nvim.command("augroup END")

    def _deinitialize(self) -> None:
        for magma in self.buffers.values():
            magma.deinit()
        if self.timer is not None:
            self.nvim.funcs.timer_stop(self.timer)

    def _initialize_if_necessary(self) -> None:
        if not self.initialized:
            self._initialize()

    def _get_magma(self, requires_instance: bool) -> Optional[MagmaBuffer]:
        maybe_magma = self.buffers.get(self.nvim.current.buffer.number)
        if requires_instance and maybe_magma is None:
            raise MagmaException(
                "Magma is not initialized; run `:MagmaInit <kernel_name>` to \
                initialize."
            )
        return maybe_magma

    def _ask_for_choice(self, preface: str, options: List[str]) -> Optional[str]:
        index: int = self.nvim.funcs.inputlist(
            [preface] + [f"{i+1}. {option}" for i, option in enumerate(options)]
        )
        if index == 0:
            return None
        else:
            return options[index - 1]

    def _initialize_buffer(self, kernel_name: str) -> MagmaBuffer:
        magma = MagmaBuffer(
            self.nvim,
            self.nvim.current.buffer,
            kernel_name,
        )

        self.buffers[self.nvim.current.buffer.number] = magma

        return magma

    @pynvim.command("MagmaInit", nargs="?", sync=True, complete="file")  # type: ignore
    @nvimui  # type: ignore
    def command_init(self, args: List[str]) -> None:
        self._initialize_if_necessary()

        if args:
            kernel_name = args[0]
            self._initialize_buffer(kernel_name)
        else:
            PROMPT = "Select the kernel to launch:"
            available_kernels = get_available_kernels()
            if self.nvim.exec_lua("return vim.ui.select ~= nil"):
                self.nvim.exec_lua(
                    """
                        vim.ui.select(
                            {%s},
                            {prompt = "%s"},
                            function(choice)
                                if choice ~= nil then
                                    vim.cmd("MagmaInit " .. choice)
                                end
                            end
                        )
                    """
                    % (
                        ", ".join(repr(x) for x in available_kernels),
                        PROMPT,
                    )
                )
            else:
                kernel_name = self._ask_for_choice(
                    PROMPT,
                    available_kernels,  # type: ignore
                )
                if kernel_name is not None:
                    self.command_init([kernel_name])

    def _deinit_buffer(self, magma: MagmaBuffer) -> None:
        magma.deinit()
        del self.buffers[magma.buffer.number]

    @pynvim.command("MagmaDeinit", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_deinit(self) -> None:
        self._initialize_if_necessary()

        magma = self._get_magma(True)
        assert magma is not None

        self._deinit_buffer(magma)

    def _do_evaluate(self, pos: Tuple[Tuple[int, int], Tuple[int, int]]) -> None:
        self._initialize_if_necessary()

        magma = self._get_magma(True)
        assert magma is not None

        bufno = self.nvim.current.buffer.number
        span = Span(
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, *pos[0]),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, *pos[1]),
        )

        code = span.get_text(self.nvim)

        magma.run_code(code, span)

    def _do_evaluate_expr(self, expr):
        self._initialize_if_necessary()

        magma = self._get_magma(True)
        assert magma is not None
        bufno = self.nvim.current.buffer.number
        span = Span(
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, 0, 0),
            DynamicPosition(self.nvim, self.extmark_namespace, bufno, 0, 0),
        )
        magma.run_code(expr, span)

    @pynvim.command("MagmaEvaluateArgument", nargs=1, sync=True)
    @nvimui
    def commnand_magma_evaluate_argument(self, expr) -> None:
        assert len(expr) == 1
        self._do_evaluate_expr(expr[0])

    @pynvim.command("MagmaEvaluateVisual", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_visual(self) -> None:
        _, lineno_begin, colno_begin, _ = self.nvim.funcs.getpos("'<")
        _, lineno_end, colno_end, _ = self.nvim.funcs.getpos("'>")
        span = (
            (
                lineno_begin - 1,
                min(colno_begin, len(self.nvim.funcs.getline(lineno_begin))) - 1,
            ),
            (
                lineno_end - 1,
                min(colno_end, len(self.nvim.funcs.getline(lineno_end))),
            ),
        )

        self._do_evaluate(span)

    @pynvim.command("MagmaEvaluateOperator", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_operator(self) -> None:
        self._initialize_if_necessary()

        self.nvim.options["operatorfunc"] = "MagmaOperatorfunc"
        self.nvim.out_write("g@\n")

    @pynvim.command("MagmaEvaluateLine", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_evaluate_line(self) -> None:
        _, lineno, _, _, _ = self.nvim.funcs.getcurpos()
        lineno -= 1

        span = ((lineno, 0), (lineno, -1))

        self._do_evaluate(span)

    @pynvim.command("MagmaInterrupt", nargs=0, sync=True)  # type: ignore
    @nvimui  # type: ignore
    def command_interrupt(self) -> None:
        magma = self._get_magma(True)
        assert magma is not None

        magma.interrupt()

    @pynvim.command("MagmaRestart", nargs=0, sync=True, bang=True)  # type: ignore # noqa
    @nvimui  # type: ignore
    def command(self) -> None:
        magma = self._get_magma(True)
        assert magma is not None

        magma.restart()

    # Internal functions which are exposed to VimScript

    @pynvim.function("MagmaOnBufferUnload", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_on_buffer_unload(self, _: Any) -> None:
        abuf_str = self.nvim.funcs.expand("<abuf>")
        if not abuf_str:
            return

        magma = self.buffers.get(int(abuf_str))
        if magma is None:
            return

        self._deinit_buffer(magma)

    @pynvim.function("MagmaOnExitPre", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_on_exit_pre(self, _: Any) -> None:
        self._deinitialize()

    @pynvim.function("MagmaOperatorfunc", sync=True)  # type: ignore
    @nvimui  # type: ignore
    def function_magma_operatorfunc(self, args: List[str]) -> None:
        if not args:
            return

        kind = args[0]

        _, lineno_begin, colno_begin, _ = self.nvim.funcs.getpos("'[")
        _, lineno_end, colno_end, _ = self.nvim.funcs.getpos("']")

        if kind == "line":
            colno_begin = 1
            colno_end = -1
        elif kind == "char":
            pass
        else:
            raise MagmaException(f"this kind of selection is not supported: '{kind}'")

        span = (
            (
                lineno_begin - 1,
                min(colno_begin, len(self.nvim.funcs.getline(lineno_begin))) - 1,
            ),
            (
                lineno_end - 1,
                min(colno_end, len(self.nvim.funcs.getline(lineno_end))),
            ),
        )

        self._do_evaluate(span)
