"""
Self-check for the Bytecode Virtual Machine project.

Run it from your language's project folder (the one with language.json and
src/), and give it the module number you just finished:

    python3 check.py 3
    python3 check.py 3 path/to/my-language

(Use 0 right after setup, in Module 00.)

It checks that module and every module before it, so you know nothing broke.

It also tests the practice problems in each lesson:

    python3 check.py practice 2               # tests practice_02.c
    python3 check.py practice 2 my_file.c

How it works: the checker compiles every .c file in src/ itself, twice.

  * A checked build, with AddressSanitizer and UndefinedBehaviorSanitizer,
    runs the test programs. Any memory error, leak or undefined behaviour
    is reported, even if the output looked right.
  * A fast build (-O2) is used for the speed and memory checks in Module 08.

Both builds must compile without a single warning. Then it runs your VM the
way a user would (yourvm file) and compares what comes out with the spec in
the lessons. Every test program is written in YOUR keyword spellings, read
from language.json.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

# How long one program may run, in seconds, before we assume it's stuck.
TIMEOUT = 10

# The keyword token types every language needs, and their usual spellings.
# Test programs below are written with these spellings; the checker swaps in
# yours before running them.
CANONICAL = {
    "let": "LET", "fn": "FN", "if": "IF", "else": "ELSE", "while": "WHILE",
    "return": "RETURN", "print": "PRINT", "true": "TRUE", "false": "FALSE",
    "nil": "NIL", "and": "AND", "or": "OR",
}
KEYWORD_TYPES = list(CANONICAL.values())

# Names of the built-in functions from Module 06. Keywords can't use them.
NATIVES = ["clock", "len", "str"]

# Exit codes from the spec.
COMPILE_ERROR, RUNTIME_ERROR, NO_FILE = 65, 70, 66

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Flags every build uses. -Wno-unused-parameter because C has no other way
# to say "this callback ignores an argument" without (void) casts everywhere.
COMMON_FLAGS = ["-std=c11", "-Wall", "-Wextra", "-Wno-unused-parameter"]
SANITIZE_FLAGS = ["-g", "-O1", "-fno-omit-frame-pointer",
                  "-fsanitize=address,undefined", "-fno-sanitize-recover=undefined"]
FAST_FLAGS = ["-O2", "-DNDEBUG"]

LINUX = sys.platform.startswith("linux")

# The learner's project folder, set in main(). Error messages show paths
# relative to it, which are much easier to read.
PROJECT = ""


class CheckFailed(Exception):
    """Raised when one of the checks finds a problem."""


def fail(message):
    raise CheckFailed(message)


def shorten(text):
    """Show paths inside the project folder relative to it."""
    return text.replace(PROJECT + os.sep, "") if PROJECT else text


def indent(text, by="      "):
    """Indent every line of text, for showing programs and output."""
    lines = text.rstrip("\n").split("\n") if text.strip() else ["(nothing)"]
    if len(lines) > 30:
        lines = lines[:25] + [f"... ({len(lines) - 25} more lines)"]
    return "\n".join(by + line[:200] for line in lines)


def sanitizer_env():
    """Environment for running a sanitized binary."""
    asan = ["exitcode=99", "abort_on_error=0", "allocator_may_return_null=1"]
    if LINUX:
        asan.append("detect_leaks=1")   # LeakSanitizer only works on Linux
    return dict(os.environ,
                ASAN_OPTIONS=":".join(asan),
                UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1:exitcode=98",
                LSAN_OPTIONS="exitcode=97")


def sanitizer_report(stderr, mine="src/"):
    """
    If a sanitizer found a problem, return a short summary of it. `mine` is
    how to recognise stack frames in the learner's own code.
    """
    markers = ("ERROR: AddressSanitizer", "ERROR: LeakSanitizer", "runtime error:")
    if not any(marker in stderr for marker in markers):
        return None
    lines = shorten(stderr).strip().splitlines()
    keep = []
    frames = 0
    for line in lines:
        # The headline, the summary, and stack frames inside the learner's code.
        if line.lstrip().startswith("#") and (mine in line or "src/" in line):
            frames += 1
            if frames > 8:
                continue
        elif not (any(m in line for m in markers) or line.startswith("SUMMARY:") or
                  "leak of" in line or "is located" in line or "freed by" in line or
                  "previously allocated" in line):
            continue
        else:
            frames = 0  # a new section of the report starts its own frame count
        # Drop the "#3 0x55fea5a2402a" address part of stack frames.
        keep.append(re.sub(r"^(#\d+) 0x[0-9a-f]+ ", r"\1 ", line.strip()))
    return "\n".join(keep[:24])


def describe_crash(code, stderr, mine="src/", where="your src/ files"):
    """Explain a crash: a signal, or a sanitizer report. None if it didn't crash."""
    report = sanitizer_report(stderr, mine)
    if report:
        return ("The sanitizers found a memory or undefined-behaviour bug:\n"
                f"{indent(report)}\n"
                f"    Read the first line, then look at the lines in {where} "
                "(file:line).")
    if code < 0:
        try:
            name = signal.Signals(-code).name
        except ValueError:
            name = f"signal {-code}"
        return f"Your VM crashed with {name}."
    return None


# ---------------------------------------------------------------------------
# Building the learner's VM
# ---------------------------------------------------------------------------
def find_compilers():
    """C compilers to try, best first: $CC, then cc, clang and gcc."""
    names = []
    if os.environ.get("CC"):
        names.append(os.environ["CC"])
    names += ["cc", "clang", "gcc"]
    found = []
    for name in names:
        path = shutil.which(name)
        if path and path not in found:
            found.append(path)
    return found


def can_sanitize(compiler, temp):
    """True if this compiler can build and run a sanitized program here."""
    source = os.path.join(temp, "probe.c")
    binary = os.path.join(temp, "probe")
    with open(source, "w") as file:
        file.write("#include <stdlib.h>\nint main(void) { free(malloc(4)); return 0; }\n")
    result = subprocess.run([compiler, *SANITIZE_FLAGS, source, "-o", binary],
                            capture_output=True, text=True)
    if result.returncode != 0:
        return False
    run = subprocess.run([binary], capture_output=True, text=True, env=sanitizer_env())
    return run.returncode == 0


class Build:
    """Compiles src/*.c and remembers where the binaries are."""

    def __init__(self, folder, temp):
        self.folder = folder
        self.temp = temp
        self.src = os.path.join(folder, "src")
        compilers = find_compilers()
        if not compilers:
            fail("Couldn't find a C compiler (cc, clang or gcc). See the guide "
                 "Installing a C compiler, then open a new terminal.")
        self.compiler = compilers[0]
        self.sanitize = None
        for compiler in compilers:
            if can_sanitize(compiler, temp):
                self.sanitize = compiler
                break
        self.binaries = {}

    def sources(self):
        if not os.path.isdir(self.src):
            fail(f"Couldn't find a src/ folder in {self.folder}.\n"
                 "Your C files go in src/, like src/main.c.")
        files = sorted(f for f in os.listdir(self.src) if f.endswith(".c"))
        if not files:
            fail(f"There are no .c files in {self.src}.")
        return [os.path.join(self.src, f) for f in files]

    def compile(self, kind, extra=()):
        """Build one kind of binary: 'checked', 'fast' or 'stress'."""
        if kind in self.binaries:
            return self.binaries[kind]
        binary = os.path.join(self.temp, f"vm-{kind}")
        if kind == "fast":
            compiler, flags = self.compiler, FAST_FLAGS
        else:
            compiler = self.sanitize or self.compiler
            flags = SANITIZE_FLAGS if self.sanitize else ["-g"]
        command = [compiler, *COMMON_FLAGS, *flags, *extra, "-I", self.src,
                   *self.sources(), "-o", binary, "-lm"]
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        output = shorten(result.stdout + result.stderr).strip()
        shown = " ".join(os.path.basename(c) if c.endswith(".c") else
                         f"vm-{kind}" if c == binary else shorten(c) for c in command[1:])
        if result.returncode != 0:
            fail(f"Your VM didn't compile ({kind} build):\n{indent(output)}\n\n"
                 f"    The command was:\n      {os.path.basename(compiler)} {shown}")
        if "warning:" in output:
            fail(f"Your VM compiled, but with warnings ({kind} build):\n{indent(output)}\n\n"
                 "    Fix every warning: in C, most warnings are bugs that haven't "
                 "happened yet.")
        self.binaries[kind] = binary
        return binary


# ---------------------------------------------------------------------------
# Reading the learner's project
# ---------------------------------------------------------------------------
class Language:
    """Everything the checker knows about the learner's language."""

    def __init__(self, folder, temp):
        self.folder = folder
        self.temp = temp
        config_path = os.path.join(folder, "language.json")
        if not os.path.isfile(config_path):
            fail(f"Couldn't find language.json in {folder}.\n"
                 "Run this from your language's folder, or pass the folder's path.")
        try:
            with open(config_path, encoding="utf-8") as file:
                config = json.load(file)
        except ValueError as error:
            fail(f"language.json isn't valid JSON: {error}\n"
                 "Check for missing quotes or commas, and no comma after the last entry.")
        if not isinstance(config, dict):
            fail('language.json should hold one object, like {"name": "Glim", ...}.')

        self.name = config.get("name")
        if not isinstance(self.name, str) or not self.name.strip():
            fail('language.json needs a "name" for your language.')
        self.extension = config.get("extension")
        if not isinstance(self.extension, str) or not re.match(r"^\.[A-Za-z0-9_]+$", self.extension):
            fail('language.json needs an "extension" for program files, like ".glim" '
                 "(a dot, then letters or digits).")
        if self.extension.lower() in (".c", ".h", ".o", ".py", ".json"):
            fail(f'Pick an "extension" of your own. "{self.extension}" is already taken.')
        self.read_keywords(config.get("keywords"))
        self.build = Build(folder, temp)

    def read_keywords(self, keywords):
        """Check the "keywords" object, and work out each keyword's spelling."""
        if not isinstance(keywords, dict):
            fail('language.json needs "keywords": an object mapping each spelling to its '
                 'token type, like {"let": "LET", "fn": "FN", ...}.')
        self.spell = {}
        for word, kind in keywords.items():
            if kind not in KEYWORD_TYPES:
                fail(f'"keywords" maps "{word}" to {kind!r}, which isn\'t a keyword type. '
                     f"The types are: {', '.join(KEYWORD_TYPES)}.")
            if not IDENTIFIER.match(word):
                fail(f'The keyword "{word}" must look like a name: letters, digits and '
                     "underscores, not starting with a digit.")
            if word in NATIVES:
                fail(f'"{word}" is the name of a built-in function in Module 06. '
                     "Pick another spelling for your keyword.")
            self.spell.setdefault(kind, word)  # the first spelling wins
        missing = [kind for kind in KEYWORD_TYPES if kind not in self.spell]
        if missing:
            fail(f'"keywords" needs a spelling for every keyword type. Missing: {", ".join(missing)}.')
        self.spellings = set(keywords)

    # --- Translating the checker's test programs into the learner's spelling ---
    def rename(self, word):
        """A test program's own variable name, changed if it clashes with a keyword."""
        while word in self.spellings:
            word += "_"
        return word

    def translate(self, source):
        """
        Swap the usual keyword spellings for the learner's in a test program.
        Strings and // comments are left alone.
        """
        out, i = [], 0
        while i < len(source):
            c = source[i]
            if c == '"':
                end = i + 1
                while end < len(source) and source[end] not in '"\n':
                    end += 2 if source[end] == "\\" else 1
                out.append(source[i:end + 1])
                i = end + 1
            elif source.startswith("//", i):
                end = source.find("\n", i)
                end = len(source) if end == -1 else end
                out.append(source[i:end])
                i = end
            elif c.isalpha() or c == "_":
                end = i
                while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                    end += 1
                word = source[i:end]
                out.append(self.spell[CANONICAL[word]] if word in CANONICAL else self.rename(word))
                i = end
            elif c.isdigit():
                # Skip whole numbers so "1x" isn't treated as a word.
                end = i
                while end < len(source) and (source[end].isalnum() or source[end] in "._"):
                    end += 1
                out.append(source[i:end])
                i = end
            else:
                out.append(c)
                i += 1
        return "".join(out)

    def output(self, lines):
        """Expected output lines, with {true}/{false}/{nil} in the learner's spelling."""
        text = "\n".join(lines)
        for kind in ("TRUE", "FALSE", "NIL"):
            text = text.replace("{" + kind.lower() + "}", self.spell[kind])
        text = re.sub(r"<fn (\w+)>", lambda m: f"<fn {self.rename(m.group(1))}>", text)
        return text.split("\n") if lines else []

    # --- Running the VM ---
    def run(self, source, flag=None, stdin=None, file_name=None, kind="checked",
            extra=(), timeout=TIMEOUT):
        """
        Save `source` as a program file, run the VM on it, and return
        (exit code, stdout, stderr). With source=None, run with no file at all.
        """
        binary = self.build.compile(kind, extra)
        folder = tempfile.mkdtemp(dir=self.temp)
        command = [binary]
        if flag:
            command.append(flag)
        if source is not None:
            path = os.path.join(folder, file_name or "test" + self.extension)
            with open(path, "w", encoding="utf-8", newline="\n") as file:
                file.write(source)
            command.append(path)
        elif file_name:
            command.append(os.path.join(folder, file_name))
        env = sanitizer_env() if kind != "fast" else dict(os.environ)
        try:
            result = subprocess.run(
                command, input=(stdin if stdin is not None else "").encode(),
                capture_output=True, timeout=timeout, cwd=folder, env=env,
            )
        except subprocess.TimeoutExpired:
            shown = f"this program:\n{indent(source)}" if source is not None else \
                f"this input:\n{indent(stdin or '')}"
            fail(f"Your VM was still running {timeout} seconds after starting "
                 f"{shown}\nIs there a loop that never ends, or is it waiting for input?")
        finally:
            shutil.rmtree(folder, ignore_errors=True)
        out = result.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        err = result.stderr.decode("utf-8", "replace")
        return result.returncode, out, err


def lines_of(text):
    """Output as a list of lines, ignoring trailing spaces and blank lines at the end."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def stage(kind):
    return "" if kind == "checked" else f" (in the {kind} build)"


# ---------------------------------------------------------------------------
# Generic test runners
# ---------------------------------------------------------------------------
def expect_output(lang, source, want, flag=None, what="this program", kind="checked",
                  extra=(), translated=False):
    """Run a program that should succeed, and compare its output line by line."""
    program = source if translated else lang.translate(source)
    want = lang.output(want)
    code, out, err = lang.run(program, flag, kind=kind, extra=extra)
    crash = describe_crash(code, err)
    if crash:
        fail(f"Problem running {what}{stage(kind)}:\n{indent(program)}\n\n{crash}")
    got = lines_of(out)
    if code != 0 or got != want:
        message = (f"Wrong result for {what}{stage(kind)}:\n{indent(program)}\n\n"
                   f"    Expected output:\n{indent(chr(10).join(want))}\n"
                   f"    Your output:\n{indent(chr(10).join(got))}")
        if code != 0:
            message += f"\n    It exited with code {code}, and printed this error:\n{indent(err)}"
        fail(message)


def expect_error(lang, source, kind, line, before=(), flag=None, check_output=True):
    """
    Run a program that should stop with an error, and check the exit code, that
    the error mentions the right line, and the output printed before the error.
    """
    program = lang.translate(source)
    code, out, err = lang.run(program, flag)
    want_code = COMPILE_ERROR if kind == "compile" else RUNTIME_ERROR
    crash = describe_crash(code, err)
    if crash:
        fail(f"This program should give a {kind} error, but your VM crashed "
             f"instead:\n{indent(program)}\n\n{crash}")
    if code != want_code:
        fail(f"This program has a {kind} error on line {line}:\n{indent(program)}\n\n"
             f"    It should exit with code {want_code}, but exited with {code}.\n"
             f"    Output:\n{indent(out)}\n    Errors:\n{indent(err)}")
    if not re.search(rf"(?i)\bline\W*{line}\b", err):
        fail(f"This program has a {kind} error on line {line}:\n{indent(program)}\n\n"
             f"    Your error message (on stderr) should say \"line {line}\", but it "
             f"was:\n{indent(err)}")
    if not check_output:
        return
    want = lang.output(list(before))
    got = lines_of(out)
    if got != want:
        if kind == "compile":
            fail(f"This program has a compile error, so none of it should run:\n"
                 f"{indent(program)}\n\n    But it printed:\n{indent(out)}\n"
                 "Compile the whole program before running any of it.")
        fail(f"Wrong output before the runtime error in:\n{indent(program)}\n\n"
             f"    Expected output:\n{indent(chr(10).join(want))}\n"
             f"    Your output:\n{indent(chr(10).join(got))}")


def expect_tokens(lang, source, tokens):
    """Run --tokens and compare with the expected (TYPE, lexeme) list."""
    want = []
    for kind, lexeme in tokens + [("EOF", "")]:
        if kind in KEYWORD_TYPES:
            lexeme = lang.spell[kind]
        elif kind == "IDENTIFIER":
            lexeme = lang.rename(lexeme)
        want.append(f"{kind} {lexeme}" if lexeme else kind)
    program = lang.translate(source)
    code, out, err = lang.run(program, "--tokens")
    crash = describe_crash(code, err)
    if crash:
        fail(f"Problem scanning:\n{indent(program)}\n\n{crash}")
    got = lines_of(out)
    if code != 0 or got != want:
        detail = ""
        for number, (a, b) in enumerate(zip(want, got + [""] * len(want))):
            if a != b:
                detail = f"\n    Token {number + 1} should be  {a[:80]}  but was  {b[:80] or '(missing)'}"
                break
        if not detail and len(got) > len(want):
            detail = f"\n    There are extra tokens after EOF: {got[len(want):][:5]}"
        message = (f"Wrong tokens for:\n{indent(program)}\n\n"
                   f"    Expected:\n{indent(chr(10).join(want))}\n"
                   f"    Yours:\n{indent(chr(10).join(got))}{detail}")
        if code != 0:
            message += f"\n    It exited with code {code}:\n{indent(err)}"
        fail(message)


def expect_repl(lang, typed, want_in_output):
    """Type lines into the REPL and check that each expected line was printed."""
    typed = lang.translate(typed)
    code, out, err = lang.run(None, stdin=typed)
    crash = describe_crash(code, err)
    if crash:
        fail(f"Your REPL crashed after typing:\n{indent(typed)}\n\n{crash}")
    if code != 0:
        fail(f"Your REPL exited with code {code} after typing:\n{indent(typed)}\n"
             "When the input runs out (EOF), it should stop with exit code 0.")
    # Prompts like "> " come before output on the same line, so look at the
    # end of each line.
    for want in lang.output(want_in_output):
        if not any(line.rstrip().endswith(want) for line in out.split("\n")):
            fail(f"After typing this into your REPL:\n{indent(typed)}\n\n"
                 f"    the output should include the line  {want}\n"
                 f"    Your output:\n{indent(out)}")


def expect_disassembly(lang, source, must_contain, must_not_contain=(), min_lines=1):
    """Run --disassemble: it must succeed, show some things, and not run the program."""
    program = lang.translate(source)
    code, out, err = lang.run(program, "--disassemble")
    crash = describe_crash(code, err)
    if crash:
        fail(f"Problem with --disassemble on:\n{indent(program)}\n\n{crash}")
    if code != 0:
        fail(f"--disassemble should exit with code 0 for this program:\n{indent(program)}\n\n"
             f"    It exited with {code}:\n{indent(err)}")
    lines = lines_of(out)
    if len(lines) < min_lines:
        fail(f"--disassemble printed {len(lines)} lines for this program:\n{indent(program)}\n\n"
             f"{indent(out)}\n    It should print at least one line per instruction "
             f"(at least {min_lines} here).")
    for text in must_contain:
        text = lang.rename(text) if IDENTIFIER.match(text) else text
        if text not in out:
            fail(f"--disassemble output for this program should mention {text}:\n"
                 f"{indent(program)}\n\n    Your output:\n{indent(out)}")
    for text in must_not_contain:
        if any(line.strip() == text for line in lines):
            fail(f"--disassemble should only show the bytecode, not run the program, but "
                 f"the output has the line {text}:\n{indent(out)}")


# ---------------------------------------------------------------------------
# Test programs
# ---------------------------------------------------------------------------
# Kept at the top level so Module 08 can run them all again with the
# stress-test garbage collector.

ARITHMETIC = [
    ("print 1 + 2 * 3;\nprint (1 + 2) * 3;\nprint 10 - 4 - 3;", ["7", "9", "3"]),
    ("print 10 / 4;\nprint 7 / 7;\nprint 7 % 3;\nprint -(2 * 3);\nprint 1.5 * 2;",
     ["2.5", "1", "1", "-6", "3"]),
    ("print 12345678;\nprint 0.5;\nprint 100 - 0.25;\nprint 0.1 + 0.2;\nprint 1 / 3;",
     ["12345678", "0.5", "99.75", "0.30000000000000004", "0.3333333333333333"]),
    ("print 8 / 4 / 2;\nprint 2 * 3 % 4;\nprint - -5;\nprint -2 * -3;\nprint 007 + 1;",
     ["1", "2", "5", "6", "8"]),
    ("print ((((((((((1 + 2))))))))));\nprint 1 + (2 * (3 + (4 * (5 + 6))));",
     ["3", "95"]),
    ("// comments and blank lines are fine\n\nprint 1; // here too\n\n", ["1"]),
    ("print 1; print 2;  print 3;\n1 + 2;\nprint 4;", ["1", "2", "3", "4"]),
]

VALUES = [
    ('print "hello" + " " + "world";', ["hello world"]),
    ('print "a\\"b\\\\c";\nprint "two\\nlines";\nprint "tab\\there";',
     ['a"b\\c', "two", "lines", "tab\there"]),
    ("print true;\nprint false;\nprint nil;", ["{true}", "{false}", "{nil}"]),
    ('print !nil;\nprint !0;\nprint !"";\nprint !!true;',
     ["{true}", "{false}", "{false}", "{true}"]),
    ('print 1 == 1;\nprint 1 == true;\nprint nil == false;\nprint "a" == "a";\n'
     'print 1 != 2;\nprint nil == nil;\nprint "1" == 1;\nprint 0 == false;',
     ["{true}", "{false}", "{false}", "{true}", "{true}", "{true}", "{false}", "{false}"]),
    ('print "ab" + "c" == "a" + "bc";\nprint "abc" != "abd";\nprint "" == "";',
     ["{true}", "{true}", "{true}"]),
    ("print 3 > 2;\nprint 2 >= 3;\nprint 1 <= 1;\nprint 1 < 1;",
     ["{true}", "{false}", "{true}", "{false}"]),
    ('"just an expression";\nprint "after";', ["after"]),
]

GLOBALS = [
    ("let a = 1;\nlet b = 2;\nprint a + b;", ["3"]),
    ("let x;\nprint x;", ["{nil}"]),
    ("let a = 1;\na = 2;\nprint a;", ["2"]),
    ("let a;\nlet b;\na = b = 3;\nprint a;\nprint b;", ["3", "3"]),
    ("let c = 1;\nprint c = 5;\nprint c;", ["5", "5"]),
    ('let s = "a";\ns = s + "b";\ns = s + s;\nprint s;', ["abab"]),
    ("let a = 1;\nlet a = a + 1;\nprint a;", ["2"]),
    ('let greeting = "hel" + "lo";\nprint greeting == "hello";\nlet t = greeting;\n'
     'greeting = "bye";\nprint t;', ["{true}", "hello"]),
]

BLOCKS = [
    ('let a = "global";\n{\n  let a = "outer";\n  {\n    let a = "inner";\n'
     "    print a;\n  }\n  print a;\n}\nprint a;", ["inner", "outer", "global"]),
    ("let n = 1;\n{\n  n = n + 1;\n  let m = 10;\n  n = n + m;\n}\nprint n;", ["12"]),
    ("let a = 1;\n{\n  let b = a + 1;\n  {\n    let c = b + 1;\n    print a + b + c;\n"
     "  }\n}", ["6"]),
    ("{}\n{ { } }\nprint \"empty blocks are fine\";", ["empty blocks are fine"]),
    ("{\n  let a = 1;\n  let b = 2;\n  a = b = a + b;\n  print a;\n  print b;\n}", ["3", "3"]),
    ("{\n  let a = 1;\n  {\n    let b = a;\n    a = 5;\n    print b;\n  }\n  print a;\n}",
     ["1", "5"]),
]

CONTROL = [
    ('if (1 < 2) print "yes"; else print "no";\n'
     'if (nil) print "bad"; else print "nil is falsy";\n'
     'if (0) print "0 is truthy";\n'
     'if ("") print "empty strings are truthy";\n'
     'if (false) print "never";',
     ["yes", "nil is falsy", "0 is truthy", "empty strings are truthy"]),
    ('if (true) if (false) print "a"; else print "b";', ["b"]),
    ("let n = 9;\nif (n % 15 == 0) {\n  print \"FizzBuzz\";\n} else if (n % 3 == 0) {\n"
     "  print \"Fizz\";\n} else {\n  print n;\n}", ["Fizz"]),
    ("let i = 1;\nlet total = 0;\nwhile (i <= 100) {\n  total = total + i;\n"
     "  i = i + 1;\n}\nprint total;", ["5050"]),
    ("{\n  let i = 0;\n  while (i < 3) {\n    let sq = i * i;\n    print sq;\n"
     "    i = i + 1;\n  }\n}", ["0", "1", "4"]),
    ("let i = 1;\nwhile (i <= 15) {\n  if (i % 15 == 0) print \"FizzBuzz\";\n"
     "  else if (i % 3 == 0) print \"Fizz\";\n  else if (i % 5 == 0) print \"Buzz\";\n"
     "  else print i;\n  i = i + 1;\n}",
     ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz",
      "13", "14", "FizzBuzz"]),
    ("let row = 1;\nwhile (row <= 3) {\n  let line = \"\";\n  let col = 1;\n"
     "  while (col <= row) {\n    line = line + \"*\";\n    col = col + 1;\n  }\n"
     "  print line;\n  row = row + 1;\n}", ["*", "**", "***"]),
    ('print nil or "default";\nprint "first" or "second";\nprint 1 and 2;\n'
     "print false and 1;\nprint nil and nil;\nprint false or nil;",
     ["default", "first", "2", "{false}", "{nil}", "{nil}"]),
    ("let a = 0;\nfalse and (a = 1);\ntrue or (a = 2);\nprint a;\n"
     "true and (a = 3);\nprint a;\nnil or (a = 4);\nprint a;", ["0", "3", "4"]),
    ("print true or false and false;\nprint false and true or true;",
     ["{true}", "{true}"]),
    ("{\n  let x = 5;\n  if (x > 1 and x < 10) print \"between\";\n"
     "  if (x < 1 or x > 3) print \"outside 1 to 3\";\n}", ["between", "outside 1 to 3"]),
    ("let i = 0;\nwhile (i < 3) {\n  let j = 0;\n  while (j < 2) {\n    let k = i * 10 + j;\n"
     "    print k;\n    j = j + 1;\n  }\n  i = i + 1;\n}", ["0", "1", "10", "11", "20", "21"]),
]

FUNCTIONS = [
    ("fn add(a, b) {\n  return a + b;\n}\nprint add(1, 2);", ["3"]),
    ('fn hi() {\n  print "hi";\n}\nprint hi();', ["hi", "{nil}"]),
    ('fn early() {\n  return;\n  print "never";\n}\nprint early();', ["{nil}"]),
    ("fn fib(n) {\n  if (n < 2) return n;\n  return fib(n - 1) + fib(n - 2);\n}\n"
     "print fib(15);", ["610"]),
    ("fn twice(f, x) {\n  return f(f(x));\n}\nfn inc(n) {\n  return n + 1;\n}\n"
     "print twice(inc, 5);", ["7"]),
    ("fn add(a, b) {\n  return a + b;\n}\nprint add;\nprint clock;",
     ["<fn add>", "<native fn>"]),
    ('print len("hello");\nprint len("");\nprint str(3) + "!";\nprint str(2.5);\n'
     "print str(true);\nprint str(nil);\nlet t = clock();\nprint t >= 0;",
     ["5", "0", "3!", "2.5", "{true}", "{nil}", "{true}"]),
    ("fn firstOver(limit) {\n  let i = 0;\n  while (true) {\n"
     "    if (i * i > limit) return i;\n    i = i + 1;\n  }\n}\nprint firstOver(50);",
     ["8"]),
    ('let x = "global";\nfn show(x) {\n  print x;\n}\nshow("param");\nprint x;',
     ["param", "global"]),
    ("let a = 1;\nfn getA() {\n  return a;\n}\na = 2;\nprint getA();", ["2"]),
    ("fn isEven(n) {\n  if (n == 0) return true;\n  return isOdd(n - 1);\n}\n"
     "fn isOdd(n) {\n  if (n == 0) return false;\n  return isEven(n - 1);\n}\n"
     "print isEven(10);\nprint isOdd(7);", ["{true}", "{true}"]),
    ("let calls = 0;\nfn count() {\n  calls = calls + 1;\n  return true;\n}\n"
     "false and count();\ntrue or count();\nprint calls;", ["0"]),
    ("fn depth(n) {\n  if (n == 0) return 0;\n  return 1 + depth(n - 1);\n}\n"
     "print depth(60);", ["60"]),
    ("fn sum(a, b, c, d) {\n  let total = a + b;\n  {\n    let more = c + d;\n"
     "    total = total + more;\n  }\n  return total;\n}\nprint sum(1, 2, 3, 4) * 2;", ["20"]),
    ('fn label(n) {\n  if (n > 0) return "positive";\n  if (n < 0) return "negative";\n'
     '  return "zero";\n}\nprint label(3) + " " + label(-1) + " " + label(0);',
     ["positive negative zero"]),
]

CLOSURES = [
    ("fn makeCounter() {\n  let count = 0;\n  fn counter() {\n    count = count + 1;\n"
     "    return count;\n  }\n  return counter;\n}\nlet c1 = makeCounter();\n"
     "let c2 = makeCounter();\nprint c1();\nprint c1();\nprint c2();\nprint c1();",
     ["1", "2", "1", "3"]),
    ("fn adder(a) {\n  fn add(b) {\n    return a + b;\n  }\n  return add;\n}\n"
     "print adder(2)(3);", ["5"]),
    ("fn outer() {\n  let x = \"outer x\";\n  fn inner() {\n    print x;\n  }\n"
     "  inner();\n}\nouter();", ["outer x"]),
    ("fn f() {\n  let x = 1;\n  fn g() {\n    return x;\n  }\n  x = 2;\n  return g;\n}\n"
     "print f()();", ["2"]),
    ("let inc;\nlet get;\nfn make() {\n  let n = 0;\n  fn i() {\n    n = n + 1;\n  }\n"
     "  fn g() {\n    return n;\n  }\n  inc = i;\n  get = g;\n}\nmake();\ninc();\ninc();\n"
     "print get();", ["2"]),
    ("let a;\nlet b;\nlet c;\nlet i = 0;\nwhile (i < 3) {\n  let j = i;\n"
     "  fn show() {\n    return j;\n  }\n  if (i == 0) a = show;\n  if (i == 1) b = show;\n"
     "  if (i == 2) c = show;\n  i = i + 1;\n}\nprint a();\nprint b();\nprint c();",
     ["0", "1", "2"]),
    ("fn outer() {\n  let x = \"x\";\n  fn middle() {\n    fn inner() {\n"
     "      return x + \"!\";\n    }\n    return inner;\n  }\n  return middle;\n}\n"
     "print outer()()();", ["x!"]),
    ("fn keep(v) {\n  fn get() {\n    return v;\n  }\n  return get;\n}\n"
     "let k = keep(\"kept\");\nfn noise(a, b, c) {\n  let d = a + b + c;\n  return d;\n}\n"
     "noise(1, 2, 3);\nprint k();", ["kept"]),
    ("{\n  let shared = 0;\n  fn bump() {\n    shared = shared + 10;\n  }\n  bump();\n"
     "  bump();\n  print shared;\n}", ["20"]),
    ("fn counterFrom(start) {\n  fn next() {\n    start = start + 1;\n    return start;\n"
     "  }\n  return next;\n}\nlet n = counterFrom(41);\nprint n();\nprint n();",
     ["42", "43"]),
]


def big_program_constants(count):
    """A program with `count` print statements, each with its own number."""
    lines = [f"print {i} + 0.5;" for i in range(count)]
    return "\n".join(lines), [f"{i}.5" for i in range(count)]


# ---------------------------------------------------------------------------
# The checks, one function per module
# ---------------------------------------------------------------------------
def check_00(lang, target):
    print(f"  - language.json describes {lang.name} ({lang.extension} files)")
    print("  - keywords: " + " ".join(lang.spell[k] for k in KEYWORD_TYPES))
    build = lang.build
    print(f"  - compiler: {build.compiler}")
    if build.sanitize and build.sanitize != build.compiler:
        print(f"  - checked build: {build.sanitize} ({os.path.basename(build.compiler)} "
              "can't use the sanitizers here)")
    if build.sanitize is None:
        print("  [WARN] Couldn't build with -fsanitize=address,undefined here, so memory "
              "bugs won't be caught.\n         See the guide Installing a C compiler. "
              "(On Linux, try gcc.)")
    elif not LINUX:
        print("  [NOTE] Leak checks need Linux or WSL (LeakSanitizer doesn't run on macOS). "
              "Everything else is checked.")
    build.compile("checked")
    build.compile("fast")
    print("  - src/*.c compiles with no warnings, in both the checked and fast builds")

    # An empty program is fine in every module.
    code, out, err = lang.run("")
    crash = describe_crash(code, err)
    if crash or code != 0:
        fail(f"Running an empty {lang.extension} file should work and exit with code 0, "
             f"but it exited with code {code}:\n{indent(err)}\n{crash or ''}")

    # A file that doesn't exist: a message, and exit code 66.
    code, out, err = lang.run(None, file_name="missing" + lang.extension)
    crash = describe_crash(code, err)
    if crash:
        fail(f"Running a file that doesn't exist crashed:\n{crash}")
    if code != NO_FILE:
        fail(f"Running a file that doesn't exist should print a message and exit with "
             f"code {NO_FILE}, but it exited with code {code}.")
    if not err.strip():
        fail("Running a file that doesn't exist should print a message to stderr, "
             "saying which file couldn't be opened.")
    print(f"  - runs a file, and exits with {NO_FILE} for a missing file")

    # The REPL must stop cleanly when the input runs out.
    code, out, err = lang.run(None, stdin="")
    crash = describe_crash(code, err)
    if crash or code != 0:
        fail("With no file, your VM should start a REPL that stops with exit code 0 "
             f"when the input runs out (EOF). It exited with code {code}:\n{indent(err)}\n"
             f"{crash or ''}")

    if target == 0:
        # In Module 00 only, the VM just prints files back.
        text = f"Hello from {lang.name}!\n  This is line two.\n\nAnd 4.\n"
        code, out, err = lang.run(text)
        crash = describe_crash(code, err)
        if crash:
            fail(f"Problem printing a file back:\n{crash}")
        if lines_of(out) != lines_of(text):
            fail(f"Running a file should print it back, for now. For this file:\n"
                 f"{indent(text)}\n    Your output:\n{indent(out)}")
        big = "".join(f"line {i} " + "x" * (i % 70) + "\n" for i in range(3000))
        code, out, err = lang.run(big)
        if describe_crash(code, err) or lines_of(out) != lines_of(big):
            fail("Printing back a 3000-line file didn't work. Read the whole file, "
                 f"however big it is.\n{describe_crash(code, err) or ''}")
        code, out, err = lang.run(None, stdin="echo me\nand me\n")
        crash = describe_crash(code, err)
        if crash or "echo me" not in out or "and me" not in out:
            fail(f"Your REPL should print each line back, for now. After typing 'echo me' "
                 f"and 'and me' the output was:\n{indent(out)}\n{crash or ''}")
        print("  - prints files and REPL lines back")
    print("  - the REPL stops cleanly at the end of the input")


def check_01(lang, target):
    cases = [
        ("let x = 12.5;", [("LET", ""), ("IDENTIFIER", "x"), ("EQUAL", "="),
                           ("NUMBER", "12.5"), ("SEMICOLON", ";")]),
        ("( ) { } , ; + - * / %",
         [("LEFT_PAREN", "("), ("RIGHT_PAREN", ")"), ("LEFT_BRACE", "{"),
          ("RIGHT_BRACE", "}"), ("COMMA", ","), ("SEMICOLON", ";"), ("PLUS", "+"),
          ("MINUS", "-"), ("STAR", "*"), ("SLASH", "/"), ("PERCENT", "%")]),
        ("! != = == < <= > >=",
         [("BANG", "!"), ("BANG_EQUAL", "!="), ("EQUAL", "="), ("EQUAL_EQUAL", "=="),
          ("LESS", "<"), ("LESS_EQUAL", "<="), ("GREATER", ">"), ("GREATER_EQUAL", ">=")]),
        ("x>=1==!y<=-2", [("IDENTIFIER", "x"), ("GREATER_EQUAL", ">="), ("NUMBER", "1"),
                          ("EQUAL_EQUAL", "=="), ("BANG", "!"), ("IDENTIFIER", "y"),
                          ("LESS_EQUAL", "<="), ("MINUS", "-"), ("NUMBER", "2")]),
        ("let fn if else while return\nprint true false nil and or",
         [(kind, "") for kind in KEYWORD_TYPES]),
        ("iffy _under score2 x_1", [("IDENTIFIER", "iffy"), ("IDENTIFIER", "_under"),
                                    ("IDENTIFIER", "score2"), ("IDENTIFIER", "x_1")]),
        ("0 7 3.14 10.0 007", [("NUMBER", "0"), ("NUMBER", "7"), ("NUMBER", "3.14"),
                               ("NUMBER", "10.0"), ("NUMBER", "007")]),
        ('print "hi"; // a comment, ignored\n"a\\"b" "back\\\\slash" "two\\nlines" ""',
         [("PRINT", ""), ("STRING", '"hi"'), ("SEMICOLON", ";"), ("STRING", '"a\\"b"'),
          ("STRING", '"back\\\\slash"'), ("STRING", '"two\\nlines"'), ("STRING", '""')]),
        ('"// not a comment" 1 / 2 // a comment', [("STRING", '"// not a comment"'),
                                                   ("NUMBER", "1"), ("SLASH", "/"),
                                                   ("NUMBER", "2")]),
        ("", []),
        ("// only a comment\n\n   \t\r\n", []),
    ]
    for source, tokens in cases:
        expect_tokens(lang, source, tokens)

    # Long names and strings: no fixed-size buffers.
    long_name = "n" * 5000
    long_string = '"' + "s" * 20000 + '"'
    expect_tokens(lang, f"{long_name} = {long_string};",
                  [("IDENTIFIER", long_name), ("EQUAL", "="), ("STRING", long_string),
                   ("SEMICOLON", ";")])
    many = "x + 1;\n" * 4000
    code, out, err = lang.run(lang.translate(many), "--tokens")
    if describe_crash(code, err) or code != 0 or len(lines_of(out)) != 4 * 4000 + 1:
        fail("--tokens on a 4000-line program should print 16001 tokens and exit 0, "
             f"but it printed {len(lines_of(out))} lines and exited with {code}.\n"
             f"{describe_crash(code, err) or indent(err)}")
    print(f"  - --tokens scans {len(cases) + 2} programs correctly: symbols, keywords, "
          "names, numbers, strings, comments, and very long ones")

    errors = [
        ("let a = 1;\nlet b = @;", 2),
        ('print "ok";\n\nprint "never closed;', 3),
        ('"line one\nline two"', 1),
        ('print "bad \\q escape";', 1),
        ("let x = 1;\n#", 2),
        ("\n\n\n\n$", 5),
    ]
    for source, line in errors:
        expect_error(lang, source, "compile", line, flag="--tokens", check_output=False)
    print("  - scan errors (bad characters, unclosed strings, unknown escapes) "
          "exit with code 65 and give the line")


def check_02(lang, target):
    for source, want in ARITHMETIC:
        expect_output(lang, source, want)
    print(f"  - runs {len(ARITHMETIC)} programs: arithmetic, precedence, grouping and "
          "number formatting")

    # Many constants and lots of code: the arrays must grow, and constant
    # indexes must go past 255.
    program, want = big_program_constants(1000)
    expect_output(lang, program, want, what="a program with 1000 print statements "
                  "(2000 constants)", translated=False)
    deep = "print " + "(" * 200 + "1" + ")" * 200 + ";"
    expect_output(lang, deep, ["1"], what="an expression nested 200 deep")
    print("  - handles 2000 constants in one chunk, and deeply nested expressions")

    expect_disassembly(lang, "print 1234 * 1000;\nprint -(5 - 2);",
                       must_contain=["<script>"], must_not_contain=["1234000", "-3"],
                       min_lines=8)
    print("  - --disassemble shows the bytecode without running it")

    runtime = [
        ('print 1;\nprint 2;\nprint 5 / 0;', 3, ["1", "2"]),
        ("print 5 % 0;", 1, []),
        ("print 1;\n\nprint (10 - 10) / (5 - 5);", 3, ["1"]),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    print("  - dividing by zero is a runtime error: exit code 70, with the line")

    compile_errors = [
        ("print 1;\nprint 2", 2),
        ("print 1;\nprint (;\n", 2),
        ("print;", 1),
        ("print 1 +;", 1),
        ("print (1 + 2;", 1),
        ("print 1 2;", 1),
        ("print 1;\n\n\nprint * 3;", 4),
        ("print 1 +\n\n);", 3),
    ]
    for source, line in compile_errors:
        expect_error(lang, source, "compile", line)
    print("  - compile errors exit with code 65, give the line, and nothing runs")


def check_03(lang, target):
    for source, want in VALUES:
        expect_output(lang, source, want)
    print(f"  - runs {len(VALUES)} programs: strings, booleans, nil, truthiness, "
          "equality and comparisons")

    chain = " + ".join(f'"{chr(97 + i % 26)}"' for i in range(500))
    expect_output(lang, f"print {chain};", ["".join(chr(97 + i % 26) for i in range(500))],
                  what="a chain of 500 joined strings")
    long_text = "z" * 30000
    expect_output(lang, f'print "{long_text}" + "{long_text}" == "{long_text}{long_text}";',
                  ["{true}"], what="joining two 30000-character strings")
    print("  - joins long strings and long chains of strings, freeing everything")

    runtime = [
        ('print "before";\nprint 1 + "a";', 2, ["before"]),
        ('print -"x";', 1, []),
        ('print 1 < "2";', 1, []),
        ('print "ok";\nprint "ok";\nprint "a" * 3;', 3, ["ok", "ok"]),
        ("print true + 1;", 1, []),
        ("print nil - nil;", 1, []),
        ('print 1;\nprint "a" >= "b";', 2, ["1"]),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    print("  - type errors are runtime errors: exit code 70, the line, earlier output kept")

    expect_repl(lang, 'print "a" + "b";\nprint 1 +;\nprint -nil;\nprint 5;\n', ["ab", "5"])
    print("  - the REPL runs each line, and keeps going after an error")


def check_04(lang, target):
    for source, want in GLOBALS:
        expect_output(lang, source, want)
    print(f"  - runs {len(GLOBALS)} programs with global variables and assignment")

    # A thousand globals: the hash table must grow, and keep every one.
    count = 1000
    names = [f"v{i}" for i in range(count)]
    program = "\n".join(f"let {name} = {i};" for i, name in enumerate(names))
    program += "\n" + "\n".join(f"{name} = {name} * 2;" for name in names[::7])
    total = sum(i * 2 if i % 7 == 0 else i for i in range(count))
    program += "\nprint " + " + ".join(names) + ";"
    expect_output(lang, program, [str(total)], what=f"a program with {count} global variables")
    strings = "\n".join(f'let s{i} = "word" + "{i}";' for i in range(600))
    strings += "\nprint s599 == \"word599\";\nprint s0 + s1 + s2;"
    expect_output(lang, strings, ["{true}", "word0word1word2"],
                  what="a program with 600 distinct strings")
    print(f"  - keeps {count} globals and 600 strings in your hash tables")

    runtime = [
        ("print y;", 1, []),
        ('print "start";\n\nz = 1;', 3, ["start"]),
        ('let a = 1;\nprint a;\nprint a + b;', 3, ["1"]),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    compile_errors = [
        ("let = 3;", 1),
        ("let 1x = 2;", 1),
        ("let a = 1;\n1 = 2;", 2),
        ("let a = 1;\n(a) = 2;", 2),
        ("let a = 1;\nlet b = 2;\na + b = 3;", 3),
        ("let a = 1 + = 2;", 1),
        ("let a = 1", 1),
    ]
    for source, line in compile_errors:
        expect_error(lang, source, "compile", line)
    print("  - undefined variables are runtime errors; bad declarations and "
          "assignments are compile errors")

    expect_repl(lang, "let a = 2;\nprint a * 3;\nprint nope;\na = a + 1;\nprint a;\n",
                ["6", "3"])
    print("  - globals in the REPL last from one line to the next, even after an error")


def check_05(lang, target):
    for source, want in BLOCKS + CONTROL:
        expect_output(lang, source, want)
    print(f"  - runs {len(BLOCKS) + len(CONTROL)} programs with blocks, local variables, "
          "if/else, while and and/or")

    # Lots of locals, and long jumps.
    locals_ok = "{\n" + "\n".join(f"  let l{i} = {i};" for i in range(200)) + \
        "\n  print l0 + l199;\n}"
    expect_output(lang, locals_ok, ["199"], what="a block with 200 local variables")
    body = "\n".join("  x = x + 1;" for _ in range(3000))
    expect_output(lang, f"let x = 0;\nif (true) {{\n{body}\n}}\nprint x;", ["3000"],
                  what="an if with 3000 statements in its body")
    expect_output(lang, f"let x = 0;\nlet n = 0;\nwhile (n < 3) {{\n{body}\n  n = n + 1;\n}}\n"
                  "print x;", ["9000"], what="a while loop with 3000 statements in its body")
    print("  - handles 200 locals, and jumps over thousands of instructions")

    compile_errors = [
        ("let x = 1;\n{\n  let x = x + 10;\n}", 3),
        ("{\n  let a = a;\n}", 2),
        ("{\n" + "\n".join(f"  let t{i} = {i};" for i in range(300)) + "\n}", None),
        ("let x = 0;\nif (true) {\n" + "\n".join("  x = x + 1;" for _ in range(9000)) +
         "\n}", None),
        ("if 1 < 2 print 1;", 1),
        ("let ok = true;\nwhile (ok print 1;", 2),
        ("if (true) print 1;\nelse;", 2),
        ("{\n  print 1;\n", 3),
    ]
    for source, line in compile_errors:
        if line is None:
            # Too many locals, or too much code to jump over: any line is fine.
            program = lang.translate(source)
            code, out, err = lang.run(program)
            crash = describe_crash(code, err)
            what = "300 locals in one block" if "t299" in source else \
                "an if body too big for a 16-bit jump (over 65535 bytes)"
            if crash:
                fail(f"Compiling a program with {what} crashed your VM:\n{crash}\n"
                     "This must be a compile error (exit code 65) instead.")
            if code != COMPILE_ERROR:
                fail(f"A program with {what} should be a compile error (exit code 65), "
                     f"but it exited with {code}.\n    Output (first lines):\n{indent(out)}")
            continue
        expect_error(lang, source, "compile", line)
    print("  - reading a local in its own initializer, too many locals, too-long jumps "
          "and broken if/while are compile errors")

    expect_error(lang, "let i = 0;\nwhile (i < 5) {\n  print i;\n  i = i + 1;\n"
                 "  if (i == 3) print i + \"x\";\n}", "runtime", 5, ["0", "1", "2"])
    expect_error(lang, "{\n  let a = 1;\n  {\n    print a + nil;\n  }\n}", "runtime", 4)
    print("  - runtime errors inside loops and blocks give the right line")


def check_06(lang, target):
    for source, want in FUNCTIONS:
        expect_output(lang, source, want)
    print(f"  - runs {len(FUNCTIONS)} programs with functions, recursion and built-ins")

    expect_disassembly(lang, "fn helper(a) {\n  return a * 2;\n}\nprint helper(21);",
                       must_contain=["<script>", "helper"], must_not_contain=["42"],
                       min_lines=8)
    print("  - --disassemble shows every function, by name")

    runtime = [
        ("fn f(a) {\n  return a;\n}\nprint f(1, 2);", 4, []),
        ("fn f(a, b) {\n  return a;\n}\nprint f(1);", 4, []),
        ("let x = 1;\nx();", 2, []),
        ('"not a function"();', 1, []),
        ("print len(5);", 1, []),
        ("print len();", 1, []),
        ('print str(1, 2);', 1, []),
        ('fn bad() {\n  return 1 + nil;\n}\nprint "start";\nbad();', 2, ["start"]),
        ("fn forever(n) {\n  return forever(n + 1);\n}\nforever(0);", 2, []),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    code, out, err = lang.run(lang.translate(
        "fn forever(n) {\n  return forever(n + 1);\n}\nforever(0);"))
    if "overflow" not in err.lower():
        fail("Endless recursion should stop with a runtime error saying \"Stack overflow\", "
             f"but the error was:\n{indent(err)}")
    print("  - wrong argument counts, calling non-functions, bad built-in calls and "
          "endless recursion are runtime errors")

    compile_errors = [
        ("return 1;", 1),
        ("print 1;\n{\n  return;\n}", 3),
        ("fn f( {\n}", 1),
        ("fn (a) {\n  return a;\n}", 1),
        ("print f(1, 2;", 1),
        ("fn f(a, b {\n}", 1),
    ]
    for source, line in compile_errors:
        expect_error(lang, source, "compile", line)
    print("  - return outside a function, and broken function syntax, are compile errors")

    expect_repl(lang, "fn sq(n) { return n * n; }\nprint sq(9);\nsq(1, 2);\nprint sq(3);\n",
                ["81", "9"])
    print("  - functions defined in the REPL can be called on later lines")


def check_07(lang, target):
    for source, want in CLOSURES:
        expect_output(lang, source, want)
    print(f"  - runs {len(CLOSURES)} programs with closures: counters, adders, shared and "
          "loop-captured variables")

    many = ("fn makeAll(n) {\n  let total = 0;\n  let i = 0;\n  while (i < n) {\n"
            "    let x = i;\n    fn add() {\n      total = total + x;\n    }\n"
            "    add();\n    i = i + 1;\n  }\n  return total;\n}\nprint makeAll(1000);")
    expect_output(lang, many, ["499500"], what="a loop that makes 1000 closures")
    print("  - closes over a new variable on every pass through a loop")


def peak_memory_mb(lang, source):
    """Run the fast build on a program and return (exit code, output, peak memory in MB)."""
    binary = lang.build.compile("fast")
    folder = tempfile.mkdtemp(dir=lang.temp)
    path = os.path.join(folder, "memory" + lang.extension)
    with open(path, "w", encoding="utf-8", newline="\n") as file:
        file.write(source)
    # A tiny Python helper runs the VM as its only child, so the peak memory
    # it reports is the VM's alone.
    helper = (
        "import resource, subprocess, sys, json\n"
        "r = subprocess.run(sys.argv[1:], capture_output=True)\n"
        "peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss\n"
        "scale = 1024 * 1024 if sys.platform == 'darwin' else 1024\n"
        "print(json.dumps({'code': r.returncode, 'out': r.stdout.decode('utf-8', 'replace'),"
        " 'mb': peak / scale}))\n"
    )
    try:
        result = subprocess.run([sys.executable, "-c", helper, binary, path],
                                capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        fail(f"This program was still running after 60 seconds:\n{indent(source)}")
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    data = json.loads(result.stdout)
    return data["code"], data["out"], data["mb"]


def timed(lang, source, want, limit, what):
    """Run a program in the fast build, check its output, and return the time taken."""
    program = lang.translate(source)
    start = time.perf_counter()
    try:
        code, out, err = lang.run(program, kind="fast", timeout=limit)
    except CheckFailed:
        fail(f"{what} took longer than {limit} seconds in the fast build:\n{indent(program)}\n\n"
             "    A bytecode VM should finish this in about a second. Look for slow spots in "
             "the run loop:\n    a lookup that scans a list, a table that never grows, or "
             "an allocation on every instruction.")
    seconds = time.perf_counter() - start
    if code != 0 or lines_of(out) != lang.output(want):
        fail(f"Wrong result for {what} (in the fast build):\n{indent(program)}\n\n"
             f"    Expected:\n{indent(chr(10).join(lang.output(want)))}\n"
             f"    Yours (exit code {code}):\n{indent(out)}\n{indent(err)}")
    return seconds


def check_08(lang, target):
    # 1. Run every earlier program again with a collection on every allocation.
    stress = ["-DSTRESS_GC"]
    programs = ARITHMETIC + VALUES + GLOBALS + BLOCKS + CONTROL + FUNCTIONS + CLOSURES
    for source, want in programs:
        expect_output(lang, source, want, kind="stress", extra=stress)
    small_garbage = ('let i = 0;\nlet kept = "";\nwhile (i < 300) {\n  let s = "item " + str(i);\n'
                     '  if (i % 100 == 0) kept = kept + s + ";";\n  i = i + 1;\n}\nprint kept;')
    expect_output(lang, small_garbage, ["item 0;item 100;item 200;"], kind="stress",
                  extra=stress, what="a loop that makes lots of garbage")
    print(f"  - all {len(programs) + 1} earlier programs still work when compiled with "
          "-DSTRESS_GC (a collection before every allocation)")

    # 2. Garbage really is collected: peak memory stays small.
    limit_mb = 64
    for what, source in [
        ("300,000 strings of 1 KB each", (
            'let big = "x";\nlet n = 0;\nwhile (n < 10) {\n  big = big + big;\n  n = n + 1;\n}\n'
            'let i = 0;\nwhile (i < 300000) {\n  let s = big + str(i);\n  i = i + 1;\n}\n'
            'print "done";')),
        ("200,000 closures", (
            "let i = 0;\nlet total = 0;\nwhile (i < 200000) {\n  fn make() {\n"
            "    let a = i;\n    fn get() {\n      return a;\n    }\n    return get;\n  }\n"
            "  let g = make();\n  total = total + g();\n  i = i + 1;\n}\n"
            'print "done";')),
    ]:
        code, out, mb = peak_memory_mb(lang, lang.translate(source))
        if code != 0 or lines_of(out) != ["done"]:
            fail(f"A program that makes {what} didn't finish properly (exit code {code}).\n"
                 f"    Output:\n{indent(out)}")
        if mb > limit_mb:
            fail(f"A program that makes {what} (all garbage) peaked at {mb:.0f} MB of "
                 f"memory. With a working collector it stays under {limit_mb} MB.\n"
                 "    Is the collector running? Are dead strings removed from your "
                 "string table, so it doesn't keep them alive?")
        print(f"  - {what} of garbage: peak memory {mb:.0f} MB (limit {limit_mb} MB)")

    # 3. Speed, in the fast build. Generous limits, for slow laptops.
    benchmarks = [
        ("fib(30)", "fn fib(n) {\n  if (n < 2) return n;\n  return fib(n - 1) + fib(n - 2);\n}\n"
         "print fib(30);", ["832040"], 8),
        ("a 10-million-step loop", "let i = 0;\nlet total = 0;\nwhile (i < 10000000) {\n"
         "  total = total + i;\n  i = i + 1;\n}\nprint total;", ["49999995000000"], 8),
        ("a million string joins", 'let i = 0;\nlet s = "";\nwhile (i < 1000000) {\n'
         '  s = "ab" + str(i % 10);\n  i = i + 1;\n}\nprint s;', ["ab9"], 8),
    ]
    for what, source, want, limit in benchmarks:
        seconds = timed(lang, source, want, limit, what)
        print(f"  - {what}: {seconds:.2f} s (limit {limit} s)")
    print("    (A tree-walking interpreter written in Python takes minutes for these.)")


CHECKS = [check_00, check_01, check_02, check_03, check_04, check_05, check_06,
          check_07, check_08]


# ---------------------------------------------------------------------------
# Practice problems
# ---------------------------------------------------------------------------
# Each lesson has a practice_NN.c file of small functions to fill in. The
# checker writes a test program that #includes it, compiles that with the
# sanitizers, and runs each problem's test in its own process with a time
# limit, so one that crashes or loops forever doesn't stop the rest.

PRACTICE_TIMEOUT = 5
MARKER = "Your code here"

# The test helpers every practice test program starts with.
TEST_PRELUDE = r"""
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

static void fail(const char *format, ...) {
  va_list args;
  va_start(args, format);
  printf("FAIL: ");
  vprintf(format, args);
  printf("\n");
  va_end(args);
  fflush(stdout);
  exit(1);
}

#define EXPECT_INT(call, want) do { long long got_ = (long long)(call); \
  if (got_ != (long long)(want)) fail("%s should give %lld, but gave %lld.", #call, \
  (long long)(want), got_); } while (0)
#define EXPECT_TRUE(cond, ...) do { if (!(cond)) fail(__VA_ARGS__); } while (0)
#define EXPECT_STR(got, want, what) do { const char *g_ = (got); \
  if (g_ == NULL || strcmp(g_, (want)) != 0) fail("%s should be \"%s\", but was \"%s\".", \
  what, (want), g_ ? g_ : "(NULL)"); } while (0)
"""

# For each module: (function names, test body) per problem, in the order they
# appear in the practice file. A problem is "not started" while every one of
# its functions still contains the "Your code here" marker.
PRACTICE = {
    1: [
        (["identifier_length"], r"""
  EXPECT_INT(identifier_length("score = 1"), 5);
  EXPECT_INT(identifier_length("_x2+y"), 3);
  EXPECT_INT(identifier_length("my_var"), 6);
  EXPECT_INT(identifier_length("2x"), 0);
  EXPECT_INT(identifier_length(""), 0);
  EXPECT_INT(identifier_length("a-b"), 1);
  EXPECT_INT(identifier_length("(x)"), 0);
"""),
        (["scan_number"], r"""
  double v = -1;
  EXPECT_INT(scan_number("12.5x", &v), 4);
  EXPECT_TRUE(v == 12.5, "scan_number(\"12.5x\", &v) should set v to 12.5, not %g.", v);
  EXPECT_INT(scan_number("7.", &v), 1);
  EXPECT_TRUE(v == 7, "scan_number(\"7.\", &v) should set v to 7, not %g.", v);
  EXPECT_INT(scan_number("3.14.15", &v), 4);
  EXPECT_TRUE(v == 3.14, "scan_number(\"3.14.15\", &v) should set v to 3.14, not %g.", v);
  EXPECT_INT(scan_number("007;", &v), 3);
  EXPECT_TRUE(v == 7, "scan_number(\"007;\", &v) should set v to 7, not %g.", v);
  v = 99;
  EXPECT_INT(scan_number(".5", &v), 0);
  EXPECT_INT(scan_number("x1", &v), 0);
  EXPECT_TRUE(v == 99, "scan_number() shouldn't change *value when there's no number.");
"""),
        (["skip_space"], r"""
  int line = 1;
  const char *text = "  \t x";
  const char *at = skip_space(text, &line);
  EXPECT_TRUE(at == text + 4, "skip_space(\"  \\t x\") should return a pointer to the x.");
  EXPECT_INT(line, 1);
  text = " // comment\n\n\r  y // more";
  at = skip_space(text, &line);
  EXPECT_TRUE(at == strchr(text, 'y'), "skip_space() should skip // comments and newlines, "
              "and return a pointer to the y in \" // comment\\n\\n\\r  y // more\".");
  EXPECT_TRUE(line == 3, "After skipping two newlines, *line should go from 1 to 3, not %d.", line);
  at = skip_space("// only a comment", &line);
  EXPECT_TRUE(*at == '\0', "skip_space(\"// only a comment\") should return a pointer to "
              "the end of the string.");
  text = "a / b";
  EXPECT_TRUE(skip_space(text + 1, &line) == text + 2,
              "A single / isn't a comment: skip_space(\" / b\") should stop at the /.");
"""),
        (["copy_lexeme"], r"""
  const char *source = "let total = 10;";
  char *copy = copy_lexeme(source + 4, 5);
  EXPECT_STR(copy, "total", "copy_lexeme(source + 4, 5)");
  free(copy);
  copy = copy_lexeme(source, 0);
  EXPECT_STR(copy, "", "copy_lexeme(source, 0)");
  free(copy);
"""),
    ],
    2: [
        (["int_array_push"], r"""
  IntArray a;
  int_array_init(&a);
  for (int i = 0; i < 1000; i++) int_array_push(&a, i * 3);
  EXPECT_INT(a.count, 1000);
  EXPECT_TRUE(a.capacity >= 1000, "After 1000 pushes, capacity should be at least 1000, not %d.", a.capacity);
  EXPECT_TRUE(a.capacity == 1024, "Starting at 8 and doubling, capacity after 1000 pushes "
              "should be 1024, not %d.", a.capacity);
  for (int i = 0; i < 1000; i++) {
    EXPECT_TRUE(a.values[i] == i * 3, "values[%d] should be %d, not %d.", i, i * 3, a.values[i]);
  }
  free(a.values);
"""),
        (["int_array_free"], r"""
  IntArray a;
  int_array_init(&a);
  a.values = malloc(sizeof(int) * 8);
  a.capacity = 8;
  a.count = 3;
  int_array_free(&a);
  EXPECT_TRUE(a.values == NULL && a.count == 0 && a.capacity == 0,
              "After int_array_free(), the array should be empty again: values NULL, "
              "count 0, capacity 0.");
  int_array_free(&a);  // freeing an empty array must be safe too
"""),
        (["run_bytes"], r"""
  double constants[] = {1, 2, 3, 10};
  uint8_t add_mul[] = {OP_PUSH, 0, OP_PUSH, 1, OP_PUSH, 2, OP_MUL, OP_ADD, OP_RETURN};
  EXPECT_TRUE(run_bytes(add_mul, constants) == 7, "1 + 2 * 3 should give 7, not %g.",
              run_bytes(add_mul, constants));
  uint8_t sub[] = {OP_PUSH, 3, OP_PUSH, 1, OP_SUB, OP_RETURN};
  EXPECT_TRUE(run_bytes(sub, constants) == 8, "PUSH 10, PUSH 2, SUB should give 10 - 2 = 8, "
              "not %g. (The first value pushed is the left operand.)", run_bytes(sub, constants));
  uint8_t neg[] = {OP_PUSH, 2, OP_NEG, OP_PUSH, 0, OP_SUB, OP_RETURN};
  EXPECT_TRUE(run_bytes(neg, constants) == -4, "-3 - 1 should give -4, not %g.",
              run_bytes(neg, constants));
  uint8_t just[] = {OP_PUSH, 3, OP_RETURN};
  EXPECT_TRUE(run_bytes(just, constants) == 10, "PUSH 10, RETURN should give 10.");
"""),
        (["double_array_push"], r"""
  DoubleArray a = {0, 0, NULL};
  for (int i = 0; i < 100; i++) double_array_push(&a, i + 0.5);
  EXPECT_INT(a.count, 100);
  for (int i = 0; i < 100; i++) {
    EXPECT_TRUE(a.values[i] == i + 0.5, "values[%d] should be %g.", i, i + 0.5);
  }
  free(a.values);
"""),
    ],
    3: [
        (["values_equal"], r"""
  Val n1 = {V_NUMBER, {.number = 1}}, n1b = {V_NUMBER, {.number = 1}}, n2 = {V_NUMBER, {.number = 2}};
  Val t = {V_BOOL, {.boolean = true}}, f = {V_BOOL, {.boolean = false}}, nil = {V_NIL, {.number = 0}};
  char a1[] = "abc", a2[] = "abc";
  Val s1 = {V_STRING, {.string = a1}}, s2 = {V_STRING, {.string = a2}}, s3 = {V_STRING, {.string = "abd"}};
  EXPECT_TRUE(values_equal(n1, n1b), "1 should equal 1.");
  EXPECT_TRUE(!values_equal(n1, n2), "1 shouldn't equal 2.");
  EXPECT_TRUE(!values_equal(n1, t), "1 shouldn't equal true: different types are never equal.");
  EXPECT_TRUE(values_equal(nil, nil), "nil should equal nil.");
  EXPECT_TRUE(!values_equal(nil, f), "nil shouldn't equal false.");
  EXPECT_TRUE(values_equal(t, t) && !values_equal(t, f), "true == true, true != false.");
  EXPECT_TRUE(values_equal(s1, s2), "Two strings with the same text should be equal, even "
              "at different addresses. Compare the characters, not the pointers.");
  EXPECT_TRUE(!values_equal(s1, s3), "\"abc\" shouldn't equal \"abd\".");
"""),
        (["format_number"], r"""
  char buffer[64];
  struct { double n; const char *want; } cases[] = {
    {3, "3"}, {-6, "-6"}, {2.5, "2.5"}, {12345678, "12345678"}, {0.1 + 0.2, "0.30000000000000004"},
    {1.0 / 3, "0.3333333333333333"}, {100 - 0.25, "99.75"}, {0.5, "0.5"},
  };
  for (size_t i = 0; i < sizeof cases / sizeof cases[0]; i++) {
    memset(buffer, '#', sizeof buffer);
    format_number(cases[i].n, buffer, sizeof buffer);
    char what[64];
    snprintf(what, sizeof what, "format_number(%.17g)", cases[i].n);
    EXPECT_STR(buffer, cases[i].want, what);
  }
"""),
        (["concat"], r"""
  char *joined = concat("hello", " world");
  EXPECT_STR(joined, "hello world", "concat(\"hello\", \" world\")");
  free(joined);
  joined = concat("", "");
  EXPECT_STR(joined, "", "concat(\"\", \"\")");
  free(joined);
  char big[5001];
  memset(big, 'q', 5000);
  big[5000] = '\0';
  joined = concat(big, big);
  EXPECT_TRUE(joined != NULL && strlen(joined) == 10000, "concat() of two 5000-character "
              "strings should give 10000 characters.");
  free(joined);
"""),
        (["repeat"], r"""
  char *r = repeat("ab", 3);
  EXPECT_STR(r, "ababab", "repeat(\"ab\", 3)");
  free(r);
  r = repeat("x", 0);
  EXPECT_STR(r, "", "repeat(\"x\", 0)");
  free(r);
"""),
    ],
    4: [
        (["fnv1a"], r"""
  EXPECT_TRUE(fnv1a("", 0) == 2166136261u, "fnv1a(\"\", 0) should be 2166136261, not %u.", fnv1a("", 0));
  EXPECT_TRUE(fnv1a("a", 1) == 0xe40c292cu, "fnv1a(\"a\", 1) should be 3826002220, not %u.", fnv1a("a", 1));
  EXPECT_TRUE(fnv1a("hello", 5) == 0x4f9f2cabu, "fnv1a(\"hello\", 5) should be 1335831723, not %u.", fnv1a("hello", 5));
  EXPECT_TRUE(fnv1a("hello world", 5) == 0x4f9f2cabu, "fnv1a() should only hash the first "
              "`length` characters.");
  const char high[] = {(char)0xE9, 0};
  EXPECT_TRUE(fnv1a(high, 1) == 1812687940u, "fnv1a() should treat each byte as unsigned "
              "(0 to 255). For the byte 0xE9 the hash is 1812687940, not %u.", fnv1a(high, 1));
"""),
        (["find_entry"], r"""
  Entry entries[8];
  memset(entries, 0, sizeof entries);
  int home = (int)(fnv1a("cat", 3) & 7);
  Entry *e = find_entry(entries, 8, "cat");
  EXPECT_TRUE(e == &entries[home], "In an empty table, find_entry() should return the "
              "key's home slot, fnv1a(key) & (capacity - 1) = %d.", home);
  // Put "dog" in cat's home slot, so cat has to probe one further.
  entries[home].key = "dog";
  e = find_entry(entries, 8, "cat");
  EXPECT_TRUE(e == &entries[(home + 1) & 7], "When the home slot holds another key, "
              "find_entry() should move on to the next slot, wrapping around at the end.");
  entries[(home + 1) & 7].key = "cat";
  entries[(home + 1) & 7].value = 42;
  e = find_entry(entries, 8, "cat");
  EXPECT_TRUE(e == &entries[(home + 1) & 7] && e->value == 42, "find_entry() should find "
              "\"cat\" one slot past its home.");
  // A tombstone in the way must not stop the search...
  entries[home].key = NULL;
  entries[home].tombstone = true;
  e = find_entry(entries, 8, "cat");
  EXPECT_TRUE(e == &entries[(home + 1) & 7], "A tombstone isn't empty: find_entry() should "
              "keep probing past it, and find \"cat\".");
  // ...but a missing key should reuse the first tombstone.
  char key[] = "cat";  // same text at a different address: compare with strcmp
  e = find_entry(entries, 8, key);
  EXPECT_TRUE(e == &entries[(home + 1) & 7], "Compare keys by their text (strcmp), not by pointer.");
  entries[(home + 1) & 7].key = NULL;  // now: tombstone, then empty
  e = find_entry(entries, 8, "cat");
  EXPECT_TRUE(e == &entries[home], "For a key that isn't there, find_entry() should "
              "return the first tombstone it passed, so the slot gets reused.");
"""),
        (["table_delete"], r"""
  Entry entries[8];
  memset(entries, 0, sizeof entries);
  int home = (int)(fnv1a("owl", 3) & 7);
  entries[home].key = "owl";
  entries[home].value = 1;
  EXPECT_TRUE(table_delete(entries, 8, "owl"), "table_delete() should return true when the key was there.");
  EXPECT_TRUE(entries[home].key == NULL && entries[home].tombstone,
              "table_delete() should leave a tombstone: key NULL, tombstone true.");
  EXPECT_TRUE(!table_delete(entries, 8, "owl"), "Deleting \"owl\" again should return false.");
  EXPECT_TRUE(!table_delete(entries, 8, "bat"), "Deleting a key that was never there should return false.");
"""),
        (["slot_of"], r"""
  const char *keys[8] = {NULL};
  keys[6] = "a";
  keys[7] = "b";
  EXPECT_INT(slot_of(keys, 8, 6, "b"), 7);
  keys[0] = "c";
  keys[1] = "d";
  EXPECT_INT(slot_of(keys, 8, 7, "d"), 1);
  EXPECT_INT(slot_of(keys, 8, 6, "zzz"), -1);
"""),
    ],
    5: [
        (["write_u16", "read_u16"], r"""
  uint8_t code[4] = {0, 0, 0, 0};
  write_u16(code, 1, 0x1234);
  EXPECT_TRUE(code[1] == 0x12 && code[2] == 0x34, "write_u16(code, 1, 0x1234) should store "
              "0x12 then 0x34 (high byte first), not 0x%02x 0x%02x.", code[1], code[2]);
  EXPECT_TRUE(code[0] == 0 && code[3] == 0, "write_u16() should only change two bytes.");
  EXPECT_INT(read_u16(code, 1), 0x1234);
  write_u16(code, 0, 65535);
  EXPECT_INT(read_u16(code, 0), 65535);
  write_u16(code, 2, 300);
  EXPECT_INT(read_u16(code, 2), 300);
"""),
        (["patch_jump"], r"""
  uint8_t code[70000];
  memset(code, 0, sizeof code);
  EXPECT_TRUE(patch_jump(code, 1, 10), "patch_jump(code, 1, 10) should succeed.");
  EXPECT_INT(read_u16(code, 1), 7);
  EXPECT_TRUE(patch_jump(code, 5, 7), "A jump to just after its operand should work.");
  EXPECT_INT(read_u16(code, 5), 0);
  EXPECT_TRUE(patch_jump(code, 0, 65537), "A jump of exactly 65535 should work.");
  EXPECT_INT(read_u16(code, 0), 65535);
  EXPECT_TRUE(!patch_jump(code, 0, 65538), "A jump of 65536 doesn't fit in 16 bits: "
              "patch_jump() should return false.");
"""),
        (["run_counter"], r"""
  // INC, then LOOP_IF_LESS 5 back to the INC, then END.
  uint8_t loop[] = {OP_INC, OP_LOOP_IF_LESS, 5, 0, 5, OP_END};
  EXPECT_INT(run_counter(loop), 5);
  // JUMP over two INCs, then one INC.
  uint8_t skip[] = {OP_JUMP, 0, 2, OP_INC, OP_INC, OP_INC, OP_END};
  EXPECT_INT(run_counter(skip), 1);
  uint8_t none[] = {OP_END};
  EXPECT_INT(run_counter(none), 0);
  // Two nested-looking loops in a row: 3, then up to 7.
  uint8_t two[] = {OP_INC, OP_LOOP_IF_LESS, 3, 0, 5, OP_INC, OP_LOOP_IF_LESS, 7, 0, 5, OP_END};
  EXPECT_INT(run_counter(two), 7);
"""),
        (["loop_distance"], r"""
  EXPECT_INT(loop_distance(0, 10), 13);
  EXPECT_INT(loop_distance(4, 4), 3);
  EXPECT_INT(loop_distance(100, 250), 153);
"""),
    ],
    6: [
        (["push_frame", "pop_frame"], r"""
  CallStack s = {.count = 0};
  Frame f;
  EXPECT_TRUE(!pop_frame(&s, &f), "pop_frame() on an empty stack should return false.");
  EXPECT_TRUE(push_frame(&s, "main", 0, 0), "push_frame() should work on an empty stack.");
  EXPECT_TRUE(push_frame(&s, "helper", 12, 3), "push_frame() should work.");
  EXPECT_INT(s.count, 2);
  EXPECT_TRUE(pop_frame(&s, &f) && strcmp(f.name, "helper") == 0 && f.return_ip == 12 &&
              f.slot_base == 3, "pop_frame() should give back the last frame pushed.");
  EXPECT_INT(s.count, 1);
  while (s.count < FRAMES_MAX) push_frame(&s, "deep", 0, 0);
  EXPECT_TRUE(!push_frame(&s, "too deep", 0, 0), "push_frame() on a full stack should "
              "return false: that's a stack overflow.");
  EXPECT_INT(s.count, FRAMES_MAX);
"""),
        (["format_trace"], r"""
  CallStack s = {.count = 0};
  s.frames[0] = (Frame){NULL, 0, 0};
  s.frames[1] = (Frame){"outer", 5, 1};
  s.frames[2] = (Frame){"inner", 9, 4};
  s.count = 3;
  char buffer[100];
  format_trace(&s, buffer, sizeof buffer);
  EXPECT_STR(buffer, "in inner()\nin outer()\nin script\n", "The trace");
  char small[12];
  memset(small, '#', sizeof small);
  format_trace(&s, small, sizeof small);
  EXPECT_STR(small, "in inner()\n", "The trace in a 12-byte buffer");
  char tiny[5];
  format_trace(&s, tiny, sizeof tiny);
  EXPECT_STR(tiny, "in i", "The trace in a 5-byte buffer");
  s.count = 0;
  format_trace(&s, buffer, sizeof buffer);
  EXPECT_STR(buffer, "", "The trace of an empty stack");
"""),
        (["arity_message"], r"""
  char buffer[40];
  arity_message(buffer, sizeof buffer, "add", 2, 3);
  EXPECT_STR(buffer, "add() expected 2 arguments but got 3.", "The message");
  char small[16];
  arity_message(small, sizeof small, "a_very_long_function_name", 1, 0);
  EXPECT_STR(small, "a_very_long_fun", "The message in a 16-byte buffer");
"""),
    ],
    7: [
        (["capture"], r"""
  double slots[4] = {0, 1, 2, 3};
  Upvalue *open = NULL;
  Upvalue *a = capture(&open, &slots[1]);
  EXPECT_TRUE(a != NULL && a->location == &slots[1], "capture() should return an upvalue "
              "pointing at the slot.");
  Upvalue *b = capture(&open, &slots[3]);
  Upvalue *c = capture(&open, &slots[2]);
  EXPECT_TRUE(open == b && b->next == c && c->next == a && a->next == NULL,
              "The open list should be sorted by slot address, highest first: slots 3, 2, 1.");
  EXPECT_TRUE(capture(&open, &slots[2]) == c, "Capturing the same slot again should "
              "return the same upvalue, so closures share the variable.");
  EXPECT_TRUE(open == b && b->next == c && c->next == a && a->next == NULL,
              "Capturing a slot twice shouldn't add it to the list again.");
  free(a); free(b); free(c);
"""),
        (["close_upvalues"], r"""
  double slots[3] = {10, 20, 30};
  Upvalue *u0 = calloc(1, sizeof(Upvalue)), *u1 = calloc(1, sizeof(Upvalue)), *u2 = calloc(1, sizeof(Upvalue));
  u2->location = &slots[2]; u1->location = &slots[1]; u0->location = &slots[0];
  u2->next = u1; u1->next = u0; u0->next = NULL;
  Upvalue *open = u2;
  close_upvalues(&open, &slots[1]);
  EXPECT_TRUE(open == u0, "close_upvalues(&open, &slots[1]) should close the upvalues for "
              "slots 2 and 1, leaving only slot 0's open.");
  EXPECT_TRUE(u1->location == &u1->closed && u1->closed == 20, "A closed upvalue should "
              "copy the value into `closed`, and point `location` at it.");
  EXPECT_TRUE(u2->location == &u2->closed && u2->closed == 30, "Slot 2's upvalue should be closed too.");
  slots[1] = -1;
  EXPECT_TRUE(*u1->location == 20, "After closing, changing the old slot shouldn't change the upvalue.");
  EXPECT_TRUE(u0->location == &slots[0], "Slot 0's upvalue should still be open.");
  close_upvalues(&open, &slots[0]);
  EXPECT_TRUE(open == NULL && u0->closed == 10, "Closing from slot 0 should close the last one.");
  free(u0); free(u1); free(u2);
"""),
        (["free_upvalues"], r"""
  Upvalue *head = NULL;
  for (int i = 0; i < 5; i++) {
    Upvalue *u = calloc(1, sizeof(Upvalue));
    u->next = head;
    head = u;
  }
  free_upvalues(head);
"""),
    ],
    8: [
        (["mark"], r"""
  Obj a = {0}, b = {0};
  GrayStack gray = {.count = 0};
  mark(&a, &gray);
  EXPECT_TRUE(a.marked && gray.count == 1 && gray.items[0] == &a, "mark() should set "
              "`marked` and push the object onto the gray stack.");
  mark(&a, &gray);
  EXPECT_TRUE(gray.count == 1, "Marking an object that's already marked shouldn't push it again.");
  mark(NULL, &gray);
  EXPECT_TRUE(gray.count == 1, "mark(NULL) should do nothing.");
  mark(&b, &gray);
  EXPECT_TRUE(gray.count == 2 && b.marked, "mark() should push a second object.");
"""),
        (["trace"], r"""
  // a -> b -> c, c -> a (a cycle), and d unreachable.
  Obj a = {0}, b = {0}, c = {0}, d = {0};
  a.refs[0] = &b; b.refs[1] = &c; c.refs[2] = &a; d.refs[0] = &a;
  GrayStack gray = {.count = 0};
  mark(&a, &gray);
  trace(&gray);
  EXPECT_TRUE(gray.count == 0, "trace() should keep going until the gray stack is empty.");
  EXPECT_TRUE(a.marked && b.marked && c.marked, "Everything reachable from a should be "
              "marked: a, b and c.");
  EXPECT_TRUE(!d.marked, "d isn't reachable from a, so it shouldn't be marked.");
"""),
        (["sweep"], r"""
  Obj *objects = NULL;
  Obj *made[6];
  for (int i = 0; i < 6; i++) {
    made[i] = calloc(1, sizeof(Obj));
    made[i]->id = i;
    made[i]->next = objects;
    objects = made[i];
  }
  made[1]->marked = true; made[4]->marked = true; made[5]->marked = true;
  EXPECT_INT(sweep(&objects), 3);
  int ids[6], count = 0;
  for (Obj *o = objects; o != NULL; o = o->next) {
    EXPECT_TRUE(!o->marked, "sweep() should unmark the objects it keeps, ready for the next collection.");
    if (count < 6) ids[count++] = o->id;
  }
  EXPECT_TRUE(count == 3 && ids[0] == 5 && ids[1] == 4 && ids[2] == 1, "After sweeping, the "
              "list should hold objects 5, 4 and 1, in that order.");
  EXPECT_INT(sweep(&objects), 3);  // nothing marked now: everything goes
  EXPECT_TRUE(objects == NULL, "Sweeping with nothing marked should empty the list.");
"""),
        (["collect_simple"], r"""
  Obj *objects = NULL;
  Obj *made[4];
  for (int i = 0; i < 4; i++) {
    made[i] = calloc(1, sizeof(Obj));
    made[i]->id = i;
    made[i]->next = objects;
    objects = made[i];
  }
  made[0]->refs[0] = made[1];          // 0 -> 1
  Obj *roots[] = {made[0], made[2]};   // roots: 0 and 2; 3 is garbage
  EXPECT_INT(collect_simple(&objects, roots, 2), 1);
  EXPECT_TRUE(made[0]->refs[0]->id == 1, "Object 0 is a root, so it and object 1 must survive.");
  while (objects != NULL) {
    Obj *next = objects->next;
    free(objects);
    objects = next;
  }
"""),
    ],
}


def function_body(source, name):
    """The text of a function's body in C source, or None if it isn't there."""
    for match in re.finditer(rf"\b{re.escape(name)}\s*\(", source):
        # Skip calls and prototypes: a definition's ) is followed by {.
        depth, i = 1, match.end()
        while i < len(source) and depth:
            depth += {"(": 1, ")": -1}.get(source[i], 0)
            i += 1
        rest = source[i:]
        stripped = rest.lstrip()
        if not stripped.startswith("{"):
            continue
        start = i + (len(rest) - len(stripped))
        depth, j = 0, start
        while j < len(source):
            if source[j] == "{":
                depth += 1
            elif source[j] == "}":
                depth -= 1
                if depth == 0:
                    return source[start:j + 1]
            j += 1
    return None


def run_practice(module, path):
    """Test every practice problem for a module and print a short report."""
    problems = PRACTICE[module]
    with open(path, encoding="utf-8") as file:
        source = file.read()
    compilers = find_compilers()
    if not compilers:
        print("Couldn't find a C compiler (cc, clang or gcc). See the guide Installing a C compiler.")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as temp:
        sanitize = next((c for c in compilers if can_sanitize(c, temp)), None)
        driver = os.path.join(temp, "practice_test.c")
        binary = os.path.join(temp, "practice_test")
        tests = []
        for index, (names, body) in enumerate(problems):
            tests.append(f"static void test_{index}(void) {{{body}}}\n")
        cases = "".join(f"    case {i}: test_{i}(); break;\n" for i in range(len(problems)))
        with open(driver, "w", encoding="utf-8") as file:
            file.write(f'#include "{os.path.abspath(path)}"\n')
            file.write(TEST_PRELUDE)
            file.write("".join(tests))
            file.write("int main(int argc, char **argv) {\n  (void)argc;\n"
                       f"  switch (atoi(argv[1])) {{\n{cases}  }}\n"
                       '  printf("PASS\\n");\n  return 0;\n}\n')
        compiler = sanitize or compilers[0]
        flags = SANITIZE_FLAGS if sanitize else ["-g"]
        result = subprocess.run([compiler, *COMMON_FLAGS, *flags, driver, "-o", binary, "-lm"],
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        output = shorten(result.stdout + result.stderr).strip()
        if result.returncode != 0:
            # Show only the errors about the learner's file.
            name = os.path.basename(path)
            lines = [line for line in output.splitlines() if name in line or "error" in line]
            print(f"[NOT YET] {os.path.basename(path)} doesn't compile:\n"
                  f"{indent(chr(10).join(lines[:20]) or output)}")
            sys.exit(1)
        if "warning:" in output:
            shown = "\n".join(line for line in output.splitlines()
                              if not line.startswith("In file included"))
            print(f"[NOTE] Compiler warnings (fix these too):\n"
                  f"{indent(chr(10).join(shown.splitlines()[:12]))}\n")
        if sanitize is None:
            print("[WARN] No sanitizers here, so memory bugs won't be caught.\n")

        passed = 0
        for index, (names, body) in enumerate(problems):
            label = f"{index + 1}. " + " and ".join(f"{n}()" for n in names)
            bodies = [function_body(source, name) for name in names]
            if any(b is None for b in bodies):
                missing = [n for n, b in zip(names, bodies) if b is None]
                print(f"[NOT YET] {label}\n          Couldn't find {', '.join(missing)}() in "
                      "the file. Keep the function names from the practice file.")
                continue
            if all(MARKER in b for b in bodies):
                print(f"[TODO]    {label}  (not started yet)")
                continue
            try:
                run = subprocess.run([binary, str(index)], capture_output=True,
                                     timeout=PRACTICE_TIMEOUT, env=sanitizer_env())
                out = run.stdout.decode("utf-8", "replace")
                err = run.stderr.decode("utf-8", "replace")
                if run.returncode == 0 and "PASS" in out:
                    passed += 1
                    print(f"[PASS]    {label}")
                    continue
                message = next((line[6:] for line in out.splitlines() if line.startswith("FAIL: ")),
                               None)
                if message is None:
                    name = os.path.basename(path)
                    message = describe_crash(run.returncode, err, mine=name,
                                             where=name) or \
                        f"exited with code {run.returncode}\n{indent(err)}"
            except subprocess.TimeoutExpired:
                message = (f"Still running after {PRACTICE_TIMEOUT} seconds. Is there a "
                           "loop that never ends?")
            print(f"[NOT YET] {label}\n          {message}")

    print(f"\n{passed} of {len(problems)} practice problems solved.")
    if passed == len(problems):
        print("All done. On to the steps!")
    sys.exit(0 if passed == len(problems) else 1)


def main():
    global PROJECT
    args = sys.argv[1:]
    if os.name == "nt":
        print("This checker needs Linux, macOS, or WSL on Windows (for the sanitizers and\n"
              "memory checks). See the guide Installing a C compiler for setting up WSL.")
        sys.exit(1)
    if sys.version_info < (3, 9):
        print(f"You're using Python {sys.version.split()[0]}. The checker needs 3.9 or newer.")
        sys.exit(1)

    # python3 check.py practice N [file]
    if args[:1] == ["practice"]:
        if len(args) < 2 or not args[1].isdigit() or int(args[1]) not in PRACTICE:
            print(f"Usage: python3 check.py practice N  (N is 1 to {len(PRACTICE)})")
            sys.exit(1)
        module = int(args[1])
        path = os.path.abspath(args[2] if len(args) > 2 else f"practice_{module:02d}.c")
        if not os.path.isfile(path):
            print(f"Couldn't find {path}.")
            print(f"Copy practice_{module:02d}.c from the module's folder into this folder first.")
            sys.exit(1)
        PROJECT = os.path.dirname(path)
        run_practice(module, path)
        return

    if not args or not args[0].isdigit() or not 0 <= int(args[0]) < len(CHECKS):
        print(__doc__)
        sys.exit(1)
    module = int(args[0])
    folder = os.path.abspath(args[1] if len(args) > 1 else ".")
    PROJECT = folder

    with tempfile.TemporaryDirectory() as temp:
        try:
            lang = Language(folder, temp)
        except CheckFailed as problem:
            print(f"[NOT YET] {problem}")
            sys.exit(1)

        # Run every module's checks up to the one asked for.
        for number in range(module + 1):
            print(f"Module {number:02d}:")
            try:
                CHECKS[number](lang, module)
            except CheckFailed as problem:
                print(f"\n[NOT YET] {problem}")
                sys.exit(1)
    print(f"\n[PASS] Everything up to module {module:02d} works. {lang.name} is coming along!")


if __name__ == "__main__":
    main()
