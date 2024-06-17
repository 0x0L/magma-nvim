import os

from pynvim import Nvim


class MagmaOptions:
    cell_highlight_group: str
    save_path: str

    def __init__(self, nvim: Nvim):
        self.cell_highlight_group = nvim.vars.get(
            "magma_cell_highlight_group", "CursorLine"
        )
        self.save_path = nvim.vars.get(
            "magma_save_cell",
            os.path.join(nvim.funcs.stdpath("data"), "magma"),
        )
