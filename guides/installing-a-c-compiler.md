# Installing a C compiler

C programs have to be **compiled**, turned into a program your computer runs directly, before you can run them. This guide installs a C compiler (`gcc` or `clang`), `make`, and Python 3 (which the vault's C self-checks use), on Linux, macOS or Windows.

| You have | Do this |
| --- | --- |
| Linux (Ubuntu, Debian, Mint, ...) | [Linux](#linux) |
| A Mac | [macOS](#macos) |
| Windows | [Windows: install WSL](#windows-install-wsl), then follow the Linux steps inside it |

## Linux

Open a terminal and run:

```sh
sudo apt update
sudo apt install build-essential python3
```

`build-essential` is `gcc`, `make` and the standard C library headers. (On Fedora: `sudo dnf install gcc make python3`. On Arch: `sudo pacman -S base-devel python`.)

Then [check it works](#check-it-works).

## macOS

Install Apple's **Command Line Tools**. In Terminal:

```sh
xcode-select --install
```

A window pops up; click **Install** and wait (it can take a while). You don't need the full Xcode app. This gives you `clang` (also available as `cc` and `gcc`), `make` and `python3`.

Then [check it works](#check-it-works).

> **One difference on macOS:** the memory-leak checker (LeakSanitizer) doesn't run on macOS, so the self-checks skip leak checks there and tell you so. Every other memory check works. If you want leak checks too, use a Linux machine or a Linux virtual machine.

## Windows: install WSL

The vault's C projects use tools that only work on Linux and macOS: the **sanitizers**, which catch memory bugs while your program runs, and Unix-style memory limits. So on Windows you'll use **WSL** (Windows Subsystem for Linux), which runs a real Ubuntu Linux inside Windows. It's free, made by Microsoft, and what most developers on Windows use for C.

1. Open **PowerShell as administrator**: press the Windows key, type `PowerShell`, right-click it and choose **Run as administrator**.
2. Run:
   ```powershell
   wsl --install
   ```
   This installs WSL and Ubuntu. **Restart your computer** when it asks.
3. After the restart, an **Ubuntu** window opens (or open **Ubuntu** from the Start menu). Choose a Linux username and password. The password doesn't show as you type; that's normal. Remember it: `sudo` asks for it.
4. In the Ubuntu window, follow the [Linux](#linux) steps above.

From now on, do your C projects **in the Ubuntu terminal**, not PowerShell.

**Where are my files?** WSL has its own Linux file system. Keep your projects there (in your Linux home folder, `~`), not under `/mnt/c/`: it's much faster, and avoids Windows/Linux line-ending trouble.

- To get the vault inside WSL, run `git clone` in the Ubuntu terminal (`sudo apt install git` first if you need it).
- To see your WSL files in Windows Explorer, run `explorer.exe .` in the Ubuntu terminal.

**Editing in VS Code:** install the **WSL** extension in VS Code. Then, in the Ubuntu terminal, go to your project folder and run `code .`. VS Code opens connected to WSL, and its terminal is a Linux terminal. Install the **C/C++** extension when VS Code suggests it.

> **Why not a Windows compiler?** You *can* compile C on Windows with MSVC or MinGW, but the sanitizers the self-checks rely on are missing or incomplete there. WSL gives you the same tools as Linux and macOS, so every check works.

## Check it works

In your terminal (the Ubuntu terminal on Windows):

```sh
cc --version
make --version
python3 --version
```

Each should print a version. Python needs to be **3.9 or newer**.

Now compile and run a tiny program. Make a file called `hello.c`:

```c
#include <stdio.h>

int main(void) {
  printf("Hello from C!\n");
  return 0;
}
```

Then:

```sh
cc -std=c11 -Wall -Wextra hello.c -o hello
./hello
```

You should see `Hello from C!`. The `./` means "the program in this folder": unlike Windows, Linux and macOS don't look in the current folder for programs unless you say so.

Finally, check the sanitizers work:

```sh
cc -fsanitize=address,undefined -g hello.c -o hello
./hello
```

It should print the same thing. If you get a linker error mentioning `asan` or `libclang_rt` (this happens with some Linux clang installs), use `gcc` instead: `sudo apt install gcc`. The self-checks pick a compiler that supports the sanitizers by themselves.

## Troubleshooting

- **`cc: command not found`**: the install didn't finish. On macOS, run `xcode-select --install` again. On Linux/WSL, `sudo apt install build-essential`.
- **`xcrun: error: invalid active developer path`** (macOS, often after a system update): run `xcode-select --install` again.
- **`wsl --install` does nothing, or says virtualization is off**: virtualization may be turned off in your computer's firmware (BIOS/UEFI). Search for your laptop model plus "enable virtualization". On school-managed laptops you may not be allowed to; ask whoever manages it, or use a different computer.
- **`Permission denied` running `./hello`**: you're probably under `/mnt/c/` in WSL. Work in your Linux home folder instead (`cd ~`).

## Learn more

- [Microsoft: Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install): the official guide, if anything above goes differently for you.
- [Beej's Guide to C Programming](https://beej.us/guide/bgc/): a free, friendly guide to C, including pointers and memory.
