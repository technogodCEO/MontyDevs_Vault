"""
Self-check for the Build Your Own Language project.

Run it from your language's project folder (the one with language.json), and
give it the module number you just finished:

    python check.py 3
    python check.py 3 path/to/my-language

(Use 0 right after setup, in Module 00.)

It checks that module and every module before it, so you know nothing broke.

It also tests the practice problems in each lesson:

    python check.py practice 2               # tests practice_02.py
    python check.py practice 2 my_file.py

This is an acceptance test: it only runs your interpreter the way a user
would (python yourlang.py file) and compares what comes out with the spec in
the lessons. How you write the interpreter is up to you. It reads your
KEYWORDS, so every test program is written in YOUR keyword spellings.
"""

import ast
import contextlib
import importlib.util
import inspect
import io
import json
import os
import re
import subprocess
import sys
import tempfile

# How long one program may run, in seconds, before we assume it's stuck.
TIMEOUT = 5

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
SYNTAX_ERROR, RUNTIME_ERROR = 65, 70

IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class CheckFailed(Exception):
    """Raised when one of the checks finds a problem."""


def fail(message):
    raise CheckFailed(message)


def indent(text, by="      "):
    """Indent every line of text, for showing programs and output."""
    lines = text.rstrip("\n").split("\n") if text.strip() else ["(nothing)"]
    return "\n".join(by + line for line in lines)


# ---------------------------------------------------------------------------
# Reading the learner's project
# ---------------------------------------------------------------------------
# This little program runs in a separate Python process. It loads the main
# file WITHOUT running it, and prints the KEYWORDS dictionary as JSON.
LOADER = r"""
import contextlib, importlib.util, io, json, os, sys
path = sys.argv[1]
sys.path.insert(0, os.path.dirname(path))   # so `import lexer` etc. work
printed = io.StringIO()
with contextlib.redirect_stdout(printed):
    spec = importlib.util.spec_from_file_location("language_main", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
keywords = getattr(module, "KEYWORDS", None)
if isinstance(keywords, dict):
    # Values may be strings or Enum members; either way, use the name.
    keywords = {str(k): str(getattr(v, "name", v)) for k, v in keywords.items()}
else:
    keywords = repr(keywords)
print("\n" + json.dumps({"printed": printed.getvalue(), "keywords": keywords}))
"""


class Language:
    """Everything the checker knows about the learner's language."""

    def __init__(self, folder):
        self.folder = folder
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
        main = config.get("main")
        if not isinstance(main, str) or not main.endswith(".py"):
            fail('language.json needs "main": the Python file that runs your '
                 'language, like "glim.py".')
        self.main = os.path.join(folder, main)
        if not os.path.isfile(self.main):
            fail(f'language.json says "main" is {main}, but there\'s no such file in {folder}.')
        self.extension = config.get("extension")
        if not isinstance(self.extension, str) or not re.match(r"^\.[A-Za-z0-9_]+$", self.extension):
            fail('language.json needs an "extension" for program files, like ".glim" '
                 "(a dot, then letters or digits).")
        if self.extension.lower() == ".py":
            fail('Pick an "extension" of your own. ".py" is taken by Python.')

        self.load_keywords()

    def load_keywords(self):
        """Read KEYWORDS from the main file, and work out each keyword's spelling."""
        try:
            result = subprocess.run(
                [sys.executable, "-B", "-c", LOADER, self.main],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=TIMEOUT, cwd=self.folder,
            )
        except subprocess.TimeoutExpired:
            fail("Loading your main file took too long. Make sure your interpreter only "
                 "starts inside the  if __name__ == \"__main__\":  block at the bottom.")
        if result.returncode != 0:
            fail(f"Python couldn't load {os.path.basename(self.main)}:\n\n{result.stderr}")
        data = json.loads(result.stdout.strip().splitlines()[-1])
        if data["printed"].strip():
            fail(f"{os.path.basename(self.main)} printed something as soon as it was loaded:\n"
                 f"{indent(data['printed'])}\n"
                 "Keep the\n    if __name__ == \"__main__\":\n        main()\n"
                 "lines at the bottom, and put the code that runs things inside main().")

        keywords = data["keywords"]
        if not isinstance(keywords, dict):
            fail("Couldn't find a dictionary called KEYWORDS in your main file. It maps "
                 'each spelling to its token type, like {"let": "LET", ...}. '
                 "(It's fine to import it from another file.)")
        self.spell = {}
        for word, kind in keywords.items():
            if kind not in KEYWORD_TYPES:
                fail(f'KEYWORDS maps "{word}" to {kind!r}, which isn\'t a keyword type. '
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
            fail(f"KEYWORDS needs a spelling for every keyword type. Missing: {', '.join(missing)}.")
        self.spellings = set(keywords)

    # --- Translating the checker's test programs into the learner's spelling ---
    def rename(self, word):
        """A test program's own variable name, changed if it clashes with a keyword."""
        while word in self.spellings:
            word += "_"
        return word

    def translate(self, source):
        """
        Swap the usual keyword spellings for the learner's in a test program
        (or an expected --ast line). Strings and // comments are left alone.
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

    # --- Running the interpreter ---
    def run(self, source, flag=None, stdin=None, file_name=None):
        """
        Save `source` as a program file, run the interpreter on it, and return
        (exit code, stdout, stderr). With source=None, run with no file at all.
        """
        with tempfile.TemporaryDirectory() as temp:
            command = [sys.executable, "-B", self.main]
            if flag:
                command.append(flag)
            if source is not None:
                path = os.path.join(temp, file_name or "test" + self.extension)
                with open(path, "w", encoding="utf-8", newline="\n") as file:
                    file.write(source)
                command.append(path)
            elif file_name:
                command.append(os.path.join(temp, file_name))
            try:
                result = subprocess.run(
                    command, input=stdin if stdin is not None else "",
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    timeout=TIMEOUT, cwd=self.folder,
                    env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                )
            except subprocess.TimeoutExpired:
                shown = f"this program:\n{indent(source)}" if source is not None else \
                    f"this input:\n{indent(stdin or '')}"
                fail(f"Your interpreter was still running {TIMEOUT} seconds after starting "
                     f"{shown}\nIs there a loop that never ends, or is it waiting for input?")
        out = result.stdout.replace("\r\n", "\n")
        return result.returncode, out, result.stderr


def lines_of(text):
    """Output as a list of lines, ignoring trailing spaces and blank lines at the end."""
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def crash_report(stderr):
    """If Python itself crashed, return the end of its traceback."""
    if "Traceback (most recent call last)" not in stderr:
        return None
    return "\n".join(stderr.strip().splitlines()[-4:])


# ---------------------------------------------------------------------------
# Generic test runners
# ---------------------------------------------------------------------------
def expect_output(lang, source, want, flag=None, what="this program"):
    """Run a program that should succeed, and compare its output line by line."""
    program = lang.translate(source)
    want = lang.output(want)
    code, out, err = lang.run(program, flag)
    crash = crash_report(err)
    if crash:
        fail(f"Your interpreter crashed with a Python error on {what}:\n{indent(program)}\n\n"
             f"{indent(crash)}")
    got = lines_of(out)
    if code != 0 or got != want:
        message = (f"Wrong result for {what}:\n{indent(program)}\n\n"
                   f"    Expected output:\n{indent(chr(10).join(want))}\n"
                   f"    Your output:\n{indent(chr(10).join(got))}")
        if code != 0:
            message += f"\n    It exited with code {code}, and printed this error:\n{indent(err)}"
        fail(message)


def expect_error(lang, source, kind, line, before=(), flag=None):
    """
    Run a program that should stop with an error, and check the exit code, that
    the error mentions the right line, and the output printed before the error.
    """
    program = lang.translate(source)
    code, out, err = lang.run(program, flag)
    want_code = SYNTAX_ERROR if kind == "syntax" else RUNTIME_ERROR
    crash = crash_report(err)
    if crash:
        fail(f"This program should give a {kind} error, but your interpreter crashed "
             f"with a Python error instead:\n{indent(program)}\n\n{indent(crash)}\n"
             f"Catch the problem and report it as a {kind} error (exit code {want_code}).")
    if code != want_code:
        fail(f"This program has a {kind} error on line {line}:\n{indent(program)}\n\n"
             f"    It should exit with code {want_code}, but exited with {code}.\n"
             f"    Output:\n{indent(out)}\n    Errors:\n{indent(err)}")
    if not re.search(rf"(?i)\bline\W*{line}\b", err):
        fail(f"This program has a {kind} error on line {line}:\n{indent(program)}\n\n"
             f"    Your error message should say \"line {line}\", but it was:\n{indent(err)}")
    want = lang.output(list(before))
    got = lines_of(out)
    if got != want:
        if kind == "syntax":
            fail(f"This program has a syntax error, so none of it should run:\n"
                 f"{indent(program)}\n\n    But it printed:\n{indent(out)}\n"
                 "Parse the whole program before running any of it.")
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
    crash = crash_report(err)
    if crash:
        fail(f"Your scanner crashed with a Python error on:\n{indent(program)}\n\n{indent(crash)}")
    got = lines_of(out)
    if code != 0 or got != want:
        detail = ""
        for number, (a, b) in enumerate(zip(want, got + [""] * len(want))):
            if a != b:
                detail = f"\n    Token {number + 1} should be  {a}  but was  {b or '(missing)'}"
                break
        if not detail and len(got) > len(want):
            detail = f"\n    There are extra tokens after EOF: {got[len(want):]}"
        message = (f"Wrong tokens for:\n{indent(program)}\n\n"
                   f"    Expected:\n{indent(chr(10).join(want))}\n"
                   f"    Yours:\n{indent(chr(10).join(got))}{detail}")
        if code != 0:
            message += f"\n    It exited with code {code}:\n{indent(err)}"
        fail(message)


def expect_ast(lang, source, want):
    expect_output(lang, source, [lang.translate(want)], flag="--ast",
                  what="this expression (with --ast)")


def expect_repl(lang, typed, want_in_output):
    """Type lines into the REPL and check that each expected line was printed."""
    typed = lang.translate(typed)
    code, out, err = lang.run(None, stdin=typed)
    crash = crash_report(err)
    if crash:
        fail(f"Your REPL crashed with a Python error after typing:\n{indent(typed)}\n\n"
             f"{indent(crash)}\nIn the REPL, report errors and keep going.")
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


# ---------------------------------------------------------------------------
# The checks, one function per module
# ---------------------------------------------------------------------------
def check_00(lang, target):
    # The checker runs your interpreter with the same Python you ran it with.
    if sys.version_info < (3, 9):
        fail(f"You're using Python {sys.version.split()[0]}. This project needs 3.9 or newer.")
    print(f"  - Python {sys.version.split()[0]} works")
    print(f"  - language.json describes {lang.name} ({lang.extension} files, "
          f"run by {os.path.basename(lang.main)})")
    print("  - KEYWORDS has a spelling for every keyword: "
          + " ".join(lang.spell[k] for k in KEYWORD_TYPES))

    # An empty program is fine in every module.
    code, out, err = lang.run("")
    if code != 0 or crash_report(err):
        fail(f"Running an empty {lang.extension} file should work and exit with code 0, "
             f"but it exited with code {code}:\n{indent(err)}")

    # A file that doesn't exist: a friendly message, not a Python traceback.
    code, out, err = lang.run(None, file_name="missing" + lang.extension)
    if crash_report(err):
        fail("Running a file that doesn't exist crashed with a Python error:\n"
             f"{indent(crash_report(err))}\nCatch the error and print a friendly message instead.")
    if code == 0:
        fail("Running a file that doesn't exist should exit with an error code "
             "(the spec uses 66), not 0.")
    print("  - runs a file, and handles a missing file without crashing")

    # The REPL must stop cleanly when the input runs out.
    code, out, err = lang.run(None, stdin="")
    if code != 0 or crash_report(err):
        fail("With no file, your interpreter should start a REPL that stops with exit "
             f"code 0 when the input runs out (EOF). It exited with code {code}:\n{indent(err)}")

    if target == 0:
        # In Module 00 only, the interpreter just prints files back.
        text = f"Hello from {lang.name}!\n  This is line two.\n"
        code, out, err = lang.run(text)
        if lines_of(out) != lines_of(text):
            fail(f"Running a file should print it back, for now. For this file:\n"
                 f"{indent(text)}\n    Your output:\n{indent(out)}")
        code, out, err = lang.run(None, stdin="echo me\n")
        if "echo me" not in out:
            fail(f"Your REPL should print each line back, for now. After typing 'echo me' "
                 f"the output was:\n{indent(out)}")
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
        ("// only a comment\n\n   \t\n", []),
    ]
    for source, tokens in cases:
        expect_tokens(lang, source, tokens)
    print(f"  - --tokens scans {len(cases)} programs correctly: symbols, keywords, "
          "names, numbers, strings and comments")

    errors = [
        ("let a = 1;\nlet b = @;", 2),
        ('print "ok";\n\nprint "never closed;', 3),
        ('"line one\nline two"', 1),
        ('print "bad \\q escape";', 1),
        ("let x = 1;\n#", 2),
    ]
    for source, line in errors:
        expect_error(lang, source, "syntax", line, flag="--tokens")
    print("  - scan errors (bad characters, unclosed strings, unknown escapes) "
          "exit with code 65 and give the line")


def check_02(lang, target):
    cases = [
        ("1 + 2 * 3", "(+ 1 (* 2 3))"),
        ("(1 + 2) * 3", "(* (group (+ 1 2)) 3)"),
        ("10 - 4 - 3", "(- (- 10 4) 3)"),
        ("8 / 4 / 2 % 3", "(% (/ (/ 8 4) 2) 3)"),
        ("-x * !true", "(* (- x) (! true))"),
        ("- -5", "(- (- 5))"),
        ("!!false", "(! (! false))"),
        ("1 < 2 == 3 >= 4", "(== (< 1 2) (>= 3 4))"),
        ("a != b == c", "(== (!= a b) c)"),
        ("1 + 2 < 3 * 4 - 5", "(< (+ 1 2) (- (* 3 4) 5))"),
        ('"hi" + "there"', '(+ "hi" "there")'),
        ("2.50 + 10.0", "(+ 2.5 10)"),
        ("nil == false", "(== nil false)"),
        ("((x))", "(group (group x))"),
        ("// a comment first\n  42\n", "42"),
    ]
    for source, want in cases:
        expect_ast(lang, source, want)
    print(f"  - --ast parses {len(cases)} expressions with the right precedence "
          "and grouping")

    errors = [
        ("1 +", 1),
        ("(1 + 2", 1),
        ("1 2", 1),
        ("* 3", 1),
        ("1 +\n\n)", 3),
        ("()", 1),
    ]
    for source, line in errors:
        expect_error(lang, source, "syntax", line, flag="--ast")
    print("  - syntax errors exit with code 65 and give the line")


def check_03(lang, target):
    programs = [
        ("print 1 + 2 * 3;\nprint (1 + 2) * 3;\nprint 10 - 4 - 3;", ["7", "9", "3"]),
        ("print 10 / 4;\nprint 7 / 7;\nprint 7 % 3;\nprint -(2 * 3);\nprint 1.5 * 2;",
         ["2.5", "1", "1", "-6", "3"]),
        ("print 12345678;\nprint 0.5;\nprint 100 - 0.25;", ["12345678", "0.5", "99.75"]),
        ('print "hello" + " " + "world";', ["hello world"]),
        ('print "a\\"b\\\\c";\nprint "two\\nlines";', ['a"b\\c', "two", "lines"]),
        ("print true;\nprint false;\nprint nil;", ["{true}", "{false}", "{nil}"]),
        ('print !nil;\nprint !0;\nprint !"";\nprint !!true;',
         ["{true}", "{false}", "{false}", "{true}"]),
        ('print 1 == 1;\nprint 1 == true;\nprint nil == false;\nprint "a" == "a";\n'
         'print 1 != 2;\nprint nil == nil;\nprint "1" == 1;\nprint 0 == false;',
         ["{true}", "{false}", "{false}", "{true}", "{true}", "{true}", "{false}", "{false}"]),
        ("print 3 > 2;\nprint 2 >= 3;\nprint 1 <= 1;\nprint 1 < 1;",
         ["{true}", "{false}", "{true}", "{false}"]),
        ('1 + 2;\n"just an expression";\nprint "after";', ["after"]),
        ("// comments and blank lines are fine\n\nprint 1; // here too\n\n", ["1"]),
        ("print 1; print 2;  print 3;", ["1", "2", "3"]),
    ]
    for source, want in programs:
        expect_output(lang, source, want)
    print(f"  - runs {len(programs)} programs: arithmetic, strings, truthiness, "
          "equality and comparisons")

    runtime = [
        ('print "before";\nprint 1 + "a";', 2, ["before"]),
        ('print -"x";', 1, []),
        ('print 1 < "2";', 1, []),
        ("print 5 / 0;", 1, []),
        ("print 5 % 0;", 1, []),
        ('print "ok";\nprint "ok";\nprint "a" * 3;', 3, ["ok", "ok"]),
        ("print true + 1;", 1, []),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    print("  - runtime errors exit with code 70, give the line, and keep earlier output")

    syntax = [
        ("print 1;\nprint 2", 2),
        ("print 1;\nprint (;\n", 2),
        ("print;", 1),
    ]
    for source, line in syntax:
        expect_error(lang, source, "syntax", line)
    print("  - syntax errors stop the program before anything runs")

    expect_repl(lang, "print 1 + 2;\nprint 1 +;\nprint 5;\n", ["3", "5"])
    print("  - the REPL runs each line, and keeps going after an error")


def check_04(lang, target):
    programs = [
        ("let a = 1;\nlet b = 2;\nprint a + b;", ["3"]),
        ("let x;\nprint x;", ["{nil}"]),
        ("let a = 1;\na = 2;\nprint a;", ["2"]),
        ("let a;\nlet b;\na = b = 3;\nprint a;\nprint b;", ["3", "3"]),
        ("let c = 1;\nprint c = 5;\nprint c;", ["5", "5"]),
        ('let s = "a";\ns = s + "b";\ns = s + s;\nprint s;', ["abab"]),
        ("let a = 1;\nlet a = a + 1;\nprint a;", ["2"]),
        ('let a = "global";\n{\n  let a = "outer";\n  {\n    let a = "inner";\n'
         "    print a;\n  }\n  print a;\n}\nprint a;", ["inner", "outer", "global"]),
        ("let n = 1;\n{\n  n = n + 1;\n  let m = 10;\n  n = n + m;\n}\nprint n;", ["12"]),
        ("let a = 1;\n{\n  let b = a + 1;\n  {\n    let c = b + 1;\n    print a + b + c;\n"
         "  }\n}", ["6"]),
        ("{}\n{ { } }\nprint \"empty blocks are fine\";", ["empty blocks are fine"]),
        ("let x = 1;\n{\n  let x = x + 10;\n  print x;\n}\nprint x;", ["11", "1"]),
    ]
    for source, want in programs:
        expect_output(lang, source, want)
    print(f"  - runs {len(programs)} programs with variables, assignment, blocks "
          "and shadowing")

    expect_ast(lang, "a = b = 1", "(= a (= b 1))")
    expect_ast(lang, "x = 1 + 2", "(= x (+ 1 2))")
    print("  - --ast shows assignment as (= name value)")

    runtime = [
        ("print y;", 1, []),
        ('print "start";\n\nz = 1;', 3, ["start"]),
        ("{\n  let inner = 1;\n}\nprint inner;", 4, []),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    syntax = [
        ("let = 3;", 1),
        ("let 1x = 2;", 1),
        ("let a = 1;\n1 = 2;", 2),
        ("let a = 1;\n(a) = 2;", 2),
        ("let a = 1 + = 2;", 1),
        ("{\n  print 1;\n", 3),
    ]
    for source, line in syntax:
        expect_error(lang, source, "syntax", line)
    expect_error(lang, "1 = 2", "syntax", 1, flag="--ast")
    print("  - undefined variables are runtime errors; bad declarations and "
          "assignments are syntax errors")

    expect_repl(lang, "let a = 2;\nprint a * 3;\n", ["6"])
    print("  - variables in the REPL last from one line to the next")


def check_05(lang, target):
    programs = [
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
        ("let i = 0;\nwhile (i < 3) {\n  let sq = i * i;\n  print sq;\n  i = i + 1;\n}",
         ["0", "1", "4"]),
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
        ("let x = 5;\nif (x > 1 and x < 10) print \"between\";\n"
         "if (x < 1 or x > 3) print \"outside 1 to 3\";", ["between", "outside 1 to 3"]),
    ]
    for source, want in programs:
        expect_output(lang, source, want)
    print(f"  - runs {len(programs)} programs with if/else, while loops, and and/or")

    expect_ast(lang, "a or b and c", "(or a (and b c))")
    expect_ast(lang, "a = b or c", "(= a (or b c))")
    expect_ast(lang, "x == 1 or !y", "(or (== x 1) (! y))")
    print("  - --ast shows and/or with the right precedence")

    expect_error(lang, "let i = 0;\nwhile (i < 5) {\n  print i;\n  i = i + 1;\n"
                 "  if (i == 3) print i + \"x\";\n}", "runtime", 5, ["0", "1", "2"])
    syntax = [
        ("if 1 < 2 print 1;", 1),
        ("let ok = true;\nwhile (ok print 1;", 2),
        ("if (true) print 1;\nelse;", 2),
    ]
    for source, line in syntax:
        expect_error(lang, source, "syntax", line)
    print("  - errors inside loops, and broken if/while syntax, are reported")


def check_06(lang, target):
    programs = [
        ("fn add(a, b) {\n  return a + b;\n}\nprint add(1, 2);", ["3"]),
        ('fn hi() {\n  print "hi";\n}\nprint hi();', ["hi", "{nil}"]),
        ('fn early() {\n  return;\n  print "never";\n}\nprint early();', ["{nil}"]),
        ("fn fib(n) {\n  if (n < 2) return n;\n  return fib(n - 1) + fib(n - 2);\n}\n"
         "print fib(15);", ["610"]),
        ("fn makeCounter() {\n  let count = 0;\n  fn counter() {\n    count = count + 1;\n"
         "    return count;\n  }\n  return counter;\n}\nlet c1 = makeCounter();\n"
         "let c2 = makeCounter();\nprint c1();\nprint c1();\nprint c2();\nprint c1();",
         ["1", "2", "1", "3"]),
        ("fn twice(f, x) {\n  return f(f(x));\n}\nfn inc(n) {\n  return n + 1;\n}\n"
         "print twice(inc, 5);", ["7"]),
        ("fn adder(a) {\n  fn add(b) {\n    return a + b;\n  }\n  return add;\n}\n"
         "print adder(2)(3);", ["5"]),
        ("fn add(a, b) {\n  return a + b;\n}\nprint add;\nprint clock;",
         ["<fn add>", "<native fn>"]),
        ('print len("hello");\nprint len("");\nprint str(3) + "!";\nprint str(2.5);\n'
         "print str(true);\nprint str(nil);\nlet t = clock();\nprint t > 0;",
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
        ("fn outer() {\n  let x = \"outer x\";\n  fn inner() {\n    print x;\n  }\n"
         "  inner();\n}\nouter();", ["outer x"]),
        ("let calls = 0;\nfn count() {\n  calls = calls + 1;\n  return true;\n}\n"
         "false and count();\ntrue or count();\nprint calls;", ["0"]),
    ]
    for source, want in programs:
        expect_output(lang, source, want)
    print(f"  - runs {len(programs)} programs with functions, recursion, closures "
          "and built-ins")

    expect_ast(lang, "f(1, 2 + 3)", "(call f 1 (+ 2 3))")
    expect_ast(lang, "f()", "(call f)")
    expect_ast(lang, "f(1)(2)", "(call (call f 1) 2)")
    expect_ast(lang, "-f(x) * 2", "(* (- (call f x)) 2)")
    print("  - --ast shows calls as (call callee args...)")

    runtime = [
        ("fn f(a) {\n  return a;\n}\nprint f(1, 2);", 4, []),
        ("fn f(a, b) {\n  return a;\n}\nprint f(1);", 4, []),
        ("let x = 1;\nx();", 2, []),
        ('"not a function"();', 1, []),
        ("print len(5);", 1, []),
        ('fn bad() {\n  return 1 + nil;\n}\nprint "start";\nbad();', 2, ["start"]),
    ]
    for source, line, before in runtime:
        expect_error(lang, source, "runtime", line, before)
    syntax = [
        ("return 1;", 1),
        ("fn f( {\n}", 1),
        ("fn (a) {\n  return a;\n}", 1),
        ("print f(1, 2;", 1),
    ]
    for source, line in syntax:
        expect_error(lang, source, "syntax", line)
    print("  - wrong argument counts, calling non-functions, and return outside a "
          "function are errors")

    expect_repl(lang, "fn sq(n) { return n * n; }\nprint sq(9);\n", ["81"])
    print("  - functions defined in the REPL can be called on later lines")


CHECKS = [check_00, check_01, check_02, check_03, check_04, check_05, check_06]


# ---------------------------------------------------------------------------
# Practice problems
# ---------------------------------------------------------------------------
# Each lesson has a practice_NN.py file of small functions to fill in. The
# tests for them live here, so the practice files only contain the problems.
#
# Every problem is tested in its own Python process, so one that loops
# forever can be stopped without stopping the rest.


class NotStarted(Exception):
    """Raised when a practice function hasn't been written yet."""


def is_unstarted(function):
    """True if a function's body is still just `pass` (plus maybe a docstring)."""
    try:
        tree = ast.parse(inspect.cleandoc("\n" + inspect.getsource(function)))
    except (OSError, TypeError, SyntaxError):
        return False
    body = tree.body[0].body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]  # skip the docstring
    return all(isinstance(statement, ast.Pass) for statement in body)


class Practice:
    """Calls functions and classes from a practice file, and reports problems clearly."""

    def __init__(self, practice_module):
        self.practice_module = practice_module

    def get(self, name):
        thing = getattr(self.practice_module, name, None)
        if thing is None:
            fail(f"Couldn't find {name} in the practice file. Keep the names from the file.")
        return thing

    def require_started(self, *functions):
        """Raise NotStarted if every one of these functions is still a stub."""
        if all(is_unstarted(function) for function in functions):
            raise NotStarted()

    def call(self, name, *args):
        """Call the learner's function `name` and return its result."""
        function = self.get(name)
        self.require_started(function)
        return self.attempt(f"{name}()", function, *args)

    def attempt(self, label, function, *args):
        """Call any function, turning a crash into a clear message."""
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                return function(*args)
        except CheckFailed:
            raise
        except Exception as error:
            fail(f"{label} crashed with {type(error).__name__}: {error}")


def expect(name, args, got, want):
    """Fail with a clear message if a function returned the wrong thing."""
    if got != want or type(got) is not type(want) and not (
            isinstance(got, (int, float)) and isinstance(want, (int, float))
            and not isinstance(got, bool) and not isinstance(want, bool)):
        shown = ", ".join(repr(a) for a in args)
        fail(f"{name}({shown}) should return {want!r}, but returned {got!r}.")


def returns(p, name, *args, want):
    got = p.call(name, *args)
    expect(name, args, got, want)


def raises(p, name, *args, error=Exception, label=None):
    """Check that calling the function raises the given kind of exception."""
    function = p.get(name)
    p.require_started(function)
    shown = label or f"{name}({', '.join(repr(a) for a in args)})"
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            result = function(*args)
    except error as problem:
        return problem
    except Exception as problem:
        fail(f"{shown} should raise {error.__name__}, but raised "
             f"{type(problem).__name__}: {problem}")
    fail(f"{shown} should raise {error.__name__}, but returned {result!r}.")


# --- Module 01 --------------------------------------------------------------
def p01_read_number(p):
    returns(p, "read_number", "x = 42;", 4, want=(42.0, 6))
    returns(p, "read_number", "3.14)", 0, want=(3.14, 4))
    returns(p, "read_number", "7.", 0, want=(7.0, 1))
    returns(p, "read_number", "1.5.2", 0, want=(1.5, 3))
    returns(p, "read_number", "a 100", 2, want=(100.0, 5))


def p01_is_identifier(p):
    for word, want in [("score", True), ("_x", True), ("x2", True), ("my_var", True),
                       ("2x", False), ("", False), ("a-b", False), ("hi there", False)]:
        returns(p, "is_identifier", word, want=want)


def p01_line_of(p):
    text = "one\ntwo\nthree"
    for index, want in [(0, 1), (2, 1), (4, 2), (8, 3), (12, 3)]:
        returns(p, "line_of", text, index, want=want)


def p01_split_tokens(p):
    returns(p, "split_tokens", "x1 = (3+42)", want=["x1", "=", "(", "3", "+", "42", ")"])
    returns(p, "split_tokens", "  total*rate  ", want=["total", "*", "rate"])
    returns(p, "split_tokens", "a // comment\nb", want=["a", "b"])
    returns(p, "split_tokens", "", want=[])


# --- Module 02 --------------------------------------------------------------
def p02_balanced(p):
    for text, want in [("(a[b]{c})", True), ("", True), ("(]", False), ("((", False),
                       ("())(", False), ("{[()()]}", True), ("x)", False)]:
        returns(p, "balanced", text, want=want)


def p02_calculate(p):
    for text, want in [("2+3*4", 14), ("(2+3)*4", 20), ("10-4-3", 3), ("8/2/2", 2),
                       ("2*(3+(4-1))*2", 24), ("7", 7), (" 1 + 2 ", 3)]:
        returns(p, "calculate", text, want=want)


def p02_calc(p):
    returns(p, "calc", [10, "-", 4, "-", 3], want=3)
    returns(p, "calc", [1, "+", 2, "-", 3, "+", 4], want=4)
    returns(p, "calc", [5], want=5)


def p02_to_sexpr(p):
    returns(p, "to_sexpr", ("+", 1, ("*", 2, 3)), want="(+ 1 (* 2 3))")
    returns(p, "to_sexpr", ("-", ("-", 10, 4), 3), want="(- (- 10 4) 3)")
    returns(p, "to_sexpr", ("!", True), want="(! True)")
    returns(p, "to_sexpr", 42, want="42")


# --- Module 03 --------------------------------------------------------------
def p03_truthy(p):
    for value, want in [(None, False), (False, False), (True, True), (0, True),
                        ("", True), (0.0, True), ("no", True)]:
        returns(p, "truthy", value, want=want)


def p03_stringify(p):
    for value, want in [(None, "nil"), (True, "true"), (False, "false"), (3.0, "3"),
                        (2.5, "2.5"), (-7.0, "-7"), ("hi", "hi"), (100.0, "100")]:
        returns(p, "stringify", value, want=want)


def p03_evaluate(p):
    cases = [
        (("num", 3), 3),
        (("add", ("num", 1), ("num", 2)), 3),
        (("mul", ("num", 2), ("add", ("num", 3), ("num", 4))), 14),
        (("neg", ("sub", ("num", 1), ("num", 5))), 4),
        (("not", ("num", 0)), False),
        (("not", ("nil",)), True),
    ]
    for node, want in cases:
        returns(p, "evaluate", node, want=want)


def p03_equal(p):
    for a, b, want in [(1.0, 1.0, True), (1.0, True, False), (0.0, False, False),
                       (None, None, True), (None, False, False), ("a", "a", True),
                       ("1", 1.0, False), (True, True, True)]:
        returns(p, "equal", a, b, want=want)


# --- Module 04 --------------------------------------------------------------
def environment_class(p):
    cls = p.get("Environment")
    if not isinstance(cls, type):
        fail("Environment should be a class.")
    return cls


def p04_define_get(p):
    cls = environment_class(p)
    p.require_started(cls.define, cls.get)
    outer = p.attempt("Environment()", cls)
    inner = p.attempt("Environment(outer)", cls, outer)
    p.attempt("define()", outer.define, "a", 1)
    p.attempt("define()", inner.define, "b", 2)
    for env, name, want, where in [(outer, "a", 1, "outer"), (inner, "b", 2, "inner"),
                                   (inner, "a", 1, "inner")]:
        got = p.attempt("get()", env.get, name)
        if got != want:
            fail(f"{where}.get({name!r}) should return {want!r}, but returned {got!r}.")
    p.attempt("define()", inner.define, "a", "shadow")
    if p.attempt("get()", inner.get, "a") != "shadow" or p.attempt("get()", outer.get, "a") != 1:
        fail("Defining 'a' in the inner environment should shadow the outer 'a' "
             "without changing it.")
    try:
        outer.get("b")
    except NameError:
        pass
    except Exception as error:
        fail(f"outer.get('b') should raise NameError, but raised {type(error).__name__}.")
    else:
        fail("outer.get('b') should raise NameError: 'b' is only in the inner environment.")


def p04_assign(p):
    cls = environment_class(p)
    p.require_started(cls.assign)
    outer = cls()
    inner = cls(outer)
    outer.define("x", 1)
    p.attempt("assign()", inner.assign, "x", 5)
    if outer.get("x") != 5:
        fail("inner.assign('x', 5) should change the 'x' defined in the outer "
             f"environment, but outer.get('x') is {outer.get('x')!r}.")
    try:
        inner.assign("nope", 1)
    except NameError:
        pass
    except Exception as error:
        fail(f"assign() on an undefined name should raise NameError, not {type(error).__name__}.")
    else:
        fail("assign('nope', 1) should raise NameError: you can't assign to a "
             "variable that was never defined.")


def p04_lookup(p):
    scopes = [{"a": "global", "b": 2}, {"a": "outer"}, {"a": "inner", "c": 3}]
    returns(p, "lookup", scopes, "a", want="inner")
    returns(p, "lookup", scopes, "b", want=2)
    returns(p, "lookup", scopes[:2], "a", want="outer")
    returns(p, "lookup", scopes, "zzz", want=None)


# --- Module 05 --------------------------------------------------------------
def thunk(value, calls):
    """A function that records that it was called, then returns value."""
    def run():
        calls.append(value)
        return value
    return run


def p05_and_or(p):
    and_, or_ = p.get("and_"), p.get("or_")
    p.require_started(and_, or_)
    for name, function, left, right, want, should_call in [
        ("and_", and_, False, 1, False, False), ("and_", and_, None, 1, None, False),
        ("and_", and_, 0, 2, 2, True), ("or_", or_, "x", 2, "x", False),
        ("or_", or_, None, "d", "d", True), ("or_", or_, False, None, None, True),
    ]:
        calls = []
        got = p.attempt(f"{name}()", function, left, thunk(right, calls))
        if got != want or type(got) is not type(want):
            fail(f"{name}({left!r}, <right gives {right!r}>) should return {want!r}, "
                 f"but returned {got!r}.")
        if bool(calls) != should_call:
            fail(f"{name}({left!r}, ...) should {'' if should_call else 'NOT '}call the "
                 "right-hand function.")


def p05_run_while(p):
    state = {"n": 0}

    def condition():
        return state["n"] < 4 or None

    def body():
        state["n"] += 1

    got = p.call("run_while", condition, body)
    if got != 4 or state["n"] != 4:
        fail(f"run_while() should run the body 4 times and return 4, but returned {got!r}.")
    state["n"] = 10
    got = p.call("run_while", condition, body)
    if got != 0 or state["n"] != 10:
        fail("When the condition starts out falsy, run_while() shouldn't run the body.")
    count = {"n": 0}

    def zero_condition():
        count["n"] += 1
        return 0 if count["n"] <= 3 else False

    got = p.call("run_while", zero_condition, lambda: None)
    if got != 3:
        fail("run_while() should treat 0 as truthy (only false and nil are falsy), "
             f"so this loop should run 3 times, but it ran {got!r}.")


def p05_run_if(p):
    for condition, want in [(True, "then"), (False, "else"), (None, "else"),
                            (0, "then"), ("", "then")]:
        got = p.call("run_if", condition, lambda: "then", lambda: "else")
        if got != want:
            fail(f"run_if({condition!r}, ...) should run the {want} branch, "
                 f"but returned {got!r}.")


# --- Module 06 --------------------------------------------------------------
def p06_make_counter(p):
    first = p.call("make_counter")
    if not callable(first):
        fail("make_counter() should return a function.")
    second = p.call("make_counter")
    got = [first(), first(), second(), first()]
    if got != [1, 2, 1, 3]:
        fail(f"Two counters called a, a, b, a should give [1, 2, 1, 3], but gave {got}.")


def p06_compose(p):
    both = p.call("compose", lambda x: x + 1, lambda x: x * 10)
    if not callable(both):
        fail("compose() should return a function.")
    got = both(2)
    if got != 21:
        fail(f"compose(add_one, times_ten)(2) should be 21 (add_one(times_ten(2))), but was {got!r}.")


def p06_make_adders(p):
    adders = p.call("make_adders", 3)
    try:
        got = [add(10) for add in adders]
    except Exception as error:
        fail(f"Calling the adders crashed with {type(error).__name__}: {error}")
    if got != [10, 11, 12]:
        fail(f"make_adders(3) should give functions adding 0, 1 and 2, so calling each "
             f"with 10 should give [10, 11, 12], but gave {got}.")


def p06_checked_call(p):
    returns(p, "checked_call", lambda a, b: a + b, 2, [3, 4], want=7)
    returns(p, "checked_call", lambda: "hi", 0, [], want="hi")
    problem = raises(p, "checked_call", lambda a: a, 1, [1, 2], error=TypeError,
                     label="checked_call(f, 1, [1, 2])")
    if str(problem) != "Expected 1 arguments but got 2.":
        fail("The error message should be 'Expected 1 arguments but got 2.', "
             f"but was {str(problem)!r}.")


# These problems cover more than one function, so name them clearly.
p04_define_get.label = "Environment: define() and get()"
p04_assign.label = "Environment: assign()"
p05_and_or.label = "and_() and or_()"

# The problems for each module, in the order they appear in practice_NN.py.
PRACTICE_TESTS = {
    1: [p01_read_number, p01_is_identifier, p01_line_of, p01_split_tokens],
    2: [p02_balanced, p02_calculate, p02_calc, p02_to_sexpr],
    3: [p03_truthy, p03_stringify, p03_evaluate, p03_equal],
    4: [p04_define_get, p04_assign, p04_lookup],
    5: [p05_and_or, p05_run_while, p05_run_if],
    6: [p06_make_counter, p06_compose, p06_make_adders, p06_checked_call],
}


def run_one_practice(module, index, path):
    """(Runs in its own process.) Test one problem and print the result as JSON."""
    test = PRACTICE_TESTS[module][index]
    status, message = "pass", ""
    try:
        spec = importlib.util.spec_from_file_location("practice", path)
        practice_module = importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(practice_module)
        test(Practice(practice_module))
    except NotStarted:
        status = "todo"
    except CheckFailed as problem:
        status, message = "fail", str(problem)
    except Exception as error:
        status, message = "fail", f"Python couldn't load the file: {type(error).__name__}: {error}"
    print("\n" + json.dumps({"status": status, "message": message}))


def run_practice(module, path):
    """Test every practice problem for a module and print a short report."""
    tests = PRACTICE_TESTS[module]
    passed = 0
    for index, test in enumerate(tests):
        label = f"{index + 1}. " + getattr(test, "label", f"{test.__name__[4:]}()")
        try:
            result = subprocess.run(
                [sys.executable, "-B", os.path.abspath(__file__),
                 "--practice-one", str(module), str(index), path],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=TIMEOUT,
            )
            outcome = json.loads(result.stdout.strip().splitlines()[-1])
        except subprocess.TimeoutExpired:
            outcome = {"status": "fail", "message": f"Still running after {TIMEOUT} "
                       "seconds. Is there a loop that never ends?"}
        except (ValueError, IndexError):
            outcome = {"status": "fail", "message": result.stderr.strip()}

        if outcome["status"] == "pass":
            passed += 1
            print(f"[PASS]    {label}")
        elif outcome["status"] == "todo":
            print(f"[TODO]    {label}  (not started yet)")
        else:
            print(f"[NOT YET] {label}\n          {outcome['message']}")

    print(f"\n{passed} of {len(tests)} practice problems solved.")
    if passed == len(tests):
        print("All done. On to the steps!")
    sys.exit(0 if passed == len(tests) else 1)


def main():
    args = sys.argv[1:]

    # Used internally: test a single practice problem in a fresh process.
    if args[:1] == ["--practice-one"]:
        run_one_practice(int(args[1]), int(args[2]), args[3])
        return

    # python check.py practice N [file]
    if args[:1] == ["practice"]:
        if len(args) < 2 or not args[1].isdigit() or int(args[1]) not in PRACTICE_TESTS:
            print(f"Usage: python check.py practice N  (N is 1 to {len(PRACTICE_TESTS)})")
            sys.exit(1)
        module = int(args[1])
        path = os.path.abspath(args[2] if len(args) > 2 else f"practice_{module:02d}.py")
        if not os.path.isfile(path):
            print(f"Couldn't find {path}.")
            print(f"Copy practice_{module:02d}.py from the module's folder into this folder first.")
            sys.exit(1)
        run_practice(module, path)
        return

    if not args or not args[0].isdigit() or not 0 <= int(args[0]) < len(CHECKS):
        print(__doc__)
        sys.exit(1)
    module = int(args[0])
    folder = os.path.abspath(args[1] if len(args) > 1 else ".")

    try:
        lang = Language(folder)
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
