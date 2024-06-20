# My micro fork of Magma

Magma is a NeoVim plugin for running code interactively with Jupyter.

This is a slimmed down version of Magama.
It only provides the ability to launch/connect to a kernel and to send commands.
It is meant to be used in conjunction with [jupyter-watch](https://github.com/0x0L/jupyter_watch).

## Requirements

- NeoVim 0.5+
- Python 3.8+
- Required Python packages:
  - [`pynvim`](https://github.com/neovim/pynvim) (for the Remote Plugin API)
  - [`jupyter_client`](https://github.com/jupyter/jupyter_client) (for interacting with Jupyter)

You can do a `:checkhealth` to see if you are ready to go.

## Installation

Use your favourite package/plugin manager.

If you use `packer.nvim`,

```lua
use { '0x0L/magma-nvim', run = ':UpdateRemotePlugins' }
```

If you use `vim-plug`,

```vim
Plug '0x0L/magma-nvim', { 'do': ':UpdateRemotePlugins' }
```

Note that you will still need to configure keymappings -- see [Keybindings](#keybindings).

## Suggested settings

If you want a quickstart, these are the author's suggestions of mappings and options (beware of potential conflicts of these mappings with your own!):

```vim
nnoremap <silent><expr> <LocalLeader>r  :MagmaEvaluateOperator<CR>
nnoremap <silent>       <LocalLeader>rr :MagmaEvaluateLine<CR>
xnoremap <silent>       <LocalLeader>r  :<C-u>MagmaEvaluateVisual<CR>
```

## Usage

### Commands

#### MagmaInit

This command initializes a runtime for the current buffer.

It can take a single argument, a connection file to an existing kernel or the Jupyter kernel's name to launch.
For example,

```vim
:MagamInit /Users/xav/Library/Jupyter/runtime/kernel-2c91528a-a8f7-437a-83ba-94c0af8c5228.json
```

or 

```vim
:MagmaInit python3
```

will initialize the current buffer with a `python3` kernel.

It can also be called with no arguments, as such:

```vim
:MagmaInit
```

This will prompt you for which kernel you want to launch (from the list of available kernels).

#### MagmaDeinit

This command deinitializes the current buffer's runtime and magma instance.

```vim
:MagmaDeinit
```

**Note** You don't need to run this, as deinitialization will happen automatically upon closing Vim or the buffer being unloaded. This command exists in case you just want to make Magma stop running.

#### MagmaEvaluateLine

Evaluate the current line.

Example usage:

```vim
:MagmaEvaluateLine
```

#### MagmaEvaluateVisual

Evaluate the selected text.

Example usage (after having selected some text):

```vim
:MagmaEvaluateVisual
```

#### MagmaEvaluateOperator

Evaluate the text given by some operator.

This won't do much outside of an `<expr>` mapping. Example usage:

```vim
nnoremap <expr> <LocalLeader>r nvim_exec('MagmaEvaluateOperator', v:true)
```

Upon using this mapping, you will enter operator mode, with which you will be able to select text you want to execute. You can, of course, hit ESC to cancel, as usual with operator mode.

#### MagmaEvaluateArgument

Evaluate the text following this command. Could be used for some automation (e. g. run something on initialization of a kernel).

```vim
:MagmaEvaluateArgument a=5;
```

#### MagmaInterrupt

Send a keyboard interrupt to the kernel. Interrupts the currently running cell and does nothing if not
cell is running.

Example usage:

```vim
:MagmaInterrupt
```

#### MagmaRestart

Shuts down and restarts the current kernel.

Optionally deletes all output if used with a bang.

Example usage:

```vim
:MagmaRestart
```

Example usage (also deleting outputs):

```vim
:MagmaRestart!
```

## Autocommands

We provide some `User` autocommands (see `:help User`) for further customization. They are:

- `MagmaInitPre`: runs right before `MagmaInit` initialization happens for a buffer
- `MagmaInitPost`: runs right after `MagmaInit` initialization happens for a buffer
- `MagmaDeinitPre`: runs right before `MagmaDeinit` deinitialization happens for a buffer
- `MagmaDeinitPost`: runs right after `MagmaDeinit` deinitialization happens for a buffer

## Extras

### Notifications

We use the `vim.notify` API. This means that you can use plugins such as [rcarriga/nvim-notify](https://github.com/rcarriga/nvim-notify) for pretty notifications.
