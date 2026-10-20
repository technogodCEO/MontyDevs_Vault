# Ideas

Plans and ideas for the vault that aren't built yet. Anything here is open for discussion: if you want to take one on, open an issue first so we can agree on the shape of it.

When an idea is done, remove it from this file.

## New courses

### C compiler: native and LLVM back ends (Advanced)

One large course that compiles **a subset of C** to native code, the way gcc does. This is a real compiler, unlike LANG 301, which builds an interpreter.

- **Why C as the source language:** the checker can compile every test program with `gcc` and with the learner's compiler and compare the output and exit codes, so it gets an answer key for free. Learners coming from LANG 301 already know C and have written a scanner and a parser.
- **Part 1, front end:** scanner and parser for a C subset (`int`, `char`, pointers, arrays, `if`/`while`/`for`, functions, maybe `struct`), and a type checker.
- **Part 2, native back end:** emit assembly directly. Expressions on a stack, locals in the stack frame, labels and jumps, the platform calling convention, pointers and arrays. The system assembler and linker turn it into an executable.
- **Part 3, LLVM back end:** the same front end emits textual LLVM IR (`.ll` files) and `clang` builds it. Covers SSA and basic blocks, `alloca` plus the `mem2reg` pass, and running `opt -O2`. Compare speed against their own back end and `gcc -O0`/`-O2`.
- **Extension:** compile their own language from LANG 201/301. Its dynamic typing needs a small runtime written in C.
- **Target:** probably x86-64. It runs natively on Linux and WSL, and on Apple-silicon Macs through Rosetta (`clang -arch x86_64`), with small symbol-naming differences on macOS.
- **Emit LLVM IR as text rather than linking LLVM's C++ API:** it avoids version mismatches and hard installs, and only needs `clang`.
- **Outside resources:** Nora Sandler's *Writing a C Compiler*, Rui Ueyama's chibicc, and the LLVM Language Reference.
- **Place:** after LANG 301 (e.g. `LANG 310`), recommending LANG 201 or 301 for the front end.

## Reading experience

### Website

Markdown reads poorly in most editors, and VS Code's preview uses proportional fonts and odd highlighting. Publish the vault as a website with **MkDocs Material on GitHub Pages**: proper code blocks, search, collapsible hints, and light and dark themes, built from the same Markdown files.
