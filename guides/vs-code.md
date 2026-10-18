# Setting up VS Code

[Visual Studio Code](https://code.visualstudio.com/) is a free code editor that works on Windows, macOS and Linux. You can use any editor you like, but the tutorials assume VS Code.

## Install it

1. Download it from [code.visualstudio.com](https://code.visualstudio.com/) and install it.
2. On Windows, tick **"Add to PATH"** during setup. It lets you open folders from the terminal with `code .`.

## Add the Python extension

1. Open VS Code and click the **Extensions** icon in the left sidebar (four small squares), or press Ctrl+Shift+X (Cmd+Shift+X on macOS).
2. Search for **Python** and install the one published by **Microsoft**.

This gives you colour-coding, error underlines, auto-complete and a Run button for Python files.

## Open your project folder

Use *File → Open Folder...* and pick your project's folder (for example `my-adventure`). Always open the **folder**, not just a single file: the sidebar shows all your files and the terminal starts in the right place.

## Use the built-in terminal

*Terminal → New Terminal* opens a terminal at the bottom of the window, already inside your project folder. Run your programs and checks from there. See [Terminal basics](terminal-basics.md).

## Settings worth knowing

- **Auto save:** *File → Auto Save* saves your files as you type, so you never run an old version by mistake.
- **Spaces, not tabs:** VS Code uses 4 spaces for Python by default. The status bar at the bottom shows "Spaces: 4". If it says "Tab Size", click it and choose *Indent Using Spaces*.
- **Python version:** if the status bar shows the wrong Python, click it and choose the one you installed.
