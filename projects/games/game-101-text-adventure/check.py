"""
Self-check for the Text Adventure project.

Run it from the folder that holds your adventure.py, and give it the module
number you just finished:

    python check.py 3
    python check.py 3 my_other_file.py

(Use 0 right after setup, in Module 00.)

It checks that module and every module before it, so you know nothing broke.

It also tests the practice problems in each lesson:

    python check.py practice 2               # tests practice_02.py
    python check.py practice 2 my_file.py

The checker doesn't care what your world looks like. It reads YOUR rooms and
items, then plays your game to make sure the features work. Your story,
rooms and messages can be anything you like.
"""

import ast
import builtins
import contextlib
import importlib.util
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
from collections import deque

# How long the game may run, in seconds, before we assume it's stuck.
TIMEOUT = 5


class CheckFailed(Exception):
    """Raised when one of the checks finds a problem."""


def fail(message):
    raise CheckFailed(message)


# ---------------------------------------------------------------------------
# Running the player's game
# ---------------------------------------------------------------------------
def run_game(game_path, commands, workdir=None):
    """Run the game, type each command in order, and return what it printed."""
    typed = "".join(command + "\n" for command in commands)
    # Make the game print in UTF-8 so emoji and accents don't crash it on Windows.
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        result = subprocess.run(
            [sys.executable, game_path],
            input=typed,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
            cwd=workdir or os.path.dirname(game_path),
            env=env,
        )
    except subprocess.TimeoutExpired:
        fail(
            f"Your game was still running {TIMEOUT} seconds after typing: {commands}\n"
            "Is there a loop that never stops, or does 'quit' not end the game?"
        )

    if "EOFError" in result.stderr:
        fail(
            f"Your game kept asking for input after these commands: {commands}\n"
            "The game should have ended. (If the last command wasn't 'quit', "
            "the game was supposed to end by itself, for example by winning.)"
        )
    if result.returncode != 0:
        fail(f"Your game crashed after these commands: {commands}\n\n{result.stderr}")
    return result.stdout


# This little program runs in a separate Python process. It loads the player's
# file WITHOUT starting the game, and prints their world data as JSON.
LOADER = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("adventure", sys.argv[1])
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)
names = ["rooms", "start_room", "goal_room"]
data = {name: getattr(game, name) for name in names if hasattr(game, name)}
print("\n" + json.dumps(data))
"""


def load_world(game_path):
    """Read the rooms, start_room and goal_room variables from the player's file."""
    try:
        result = subprocess.run(
            [sys.executable, "-B", "-c", LOADER, game_path],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT,
            cwd=os.path.dirname(game_path),
        )
    except subprocess.TimeoutExpired:
        fail("Loading your file took too long. Make sure the game only starts "
             "inside the  if __name__ == \"__main__\":  block at the bottom.")
    if "EOFError" in result.stderr:
        fail("Your game started as soon as the file was loaded. Keep the\n"
             "    if __name__ == \"__main__\":\n        main()\n"
             "lines at the bottom, and put your game code inside main().")
    if result.returncode != 0:
        fail(f"Python couldn't load your file:\n\n{result.stderr}")
    # The world data is on the last line (anything printed earlier is ignored).
    return json.loads(result.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# Helpers for reading the world and the game's output
# ---------------------------------------------------------------------------
def flatten(text):
    """Collapse all whitespace, so line wrapping in the output doesn't matter."""
    return " ".join(text.split())


def snippet(room):
    """A short, recognisable piece of a room's description."""
    return flatten(room["description"])[:25]


def locks(room):
    return room.get("locked", {})


def find_path(rooms, start, is_target, inventory=()):
    """
    Breadth-first search through the map. Returns (directions, room) for the
    nearest room where is_target(room_key) is True, or None. Locked exits are
    only used if the inventory holds the item they need.
    """
    queue = deque([(start, [])])
    seen = {start}
    while queue:
        key, path = queue.popleft()
        if is_target(key):
            return path, key
        for direction, next_key in rooms[key]["exits"].items():
            needed = locks(rooms[key]).get(direction)
            if needed is not None and needed not in inventory:
                continue
            if next_key not in seen:
                seen.add(next_key)
                queue.append((next_key, path + [direction]))
    return None


def solve(rooms, start, goal):
    """
    Find a list of commands that wins the game: explore every combination of
    'where am I' and 'what am I carrying' until the goal room is reached.
    """
    queue = deque([(start, frozenset(), [])])
    seen = {(start, frozenset())}
    while queue:
        key, carrying, commands = queue.popleft()
        if key == goal:
            return commands
        room = rooms[key]
        moves = []
        # Picking up any item still in this room.
        for item in room.get("items", []):
            if item not in carrying:
                moves.append((key, carrying | {item}, f"take {item}"))
        # Walking through any exit we're allowed through.
        for direction, next_key in room["exits"].items():
            needed = locks(room).get(direction)
            if needed is None or needed in carrying:
                moves.append((next_key, carrying, f"go {direction}"))
        for state in moves:
            if state[:2] not in seen:
                seen.add(state[:2])
                queue.append((state[0], state[1], commands + [state[2]]))
    return None


def all_items(rooms):
    return [item for room in rooms.values() for item in room.get("items", [])]


# ---------------------------------------------------------------------------
# The checks, one function per module
# ---------------------------------------------------------------------------
def check_00(game_path):
    # The checker runs your game with the same Python you ran it with.
    if sys.version_info < (3, 9):
        fail(f"You're using Python {sys.version.split()[0]}. This project needs 3.9 or newer.")
    load_world(game_path)
    if not run_game(game_path, ["quit"]).strip():
        fail("adventure.py ran, but didn't print anything.")
    print(f"  - Python {sys.version.split()[0]} works")
    print("  - adventure.py runs, and loads without starting the game")


def check_01(game_path):
    output = run_game(game_path, ["quit"])
    if not output.strip():
        fail("Your game didn't print anything. Start with a welcome message.")
    run_game(game_path, ["help", "", "dance wildly", "QUIT"])

    # Without 'quit', the loop should keep asking for more commands.
    # We stop typing after 'help', so a working loop runs out of input.
    try:
        run_game(game_path, ["help"])
    except CheckFailed:
        pass  # It kept asking (or crashed asking). That's what a loop does.
    else:
        fail("Your game ended without the player typing 'quit'. "
             "Use a while loop so it keeps asking for commands.")
    print("  - the game loop runs, and 'quit' ends it")
    print("  - 'help', empty lines and unknown commands don't crash it")


def check_02(game_path):
    world = load_world(game_path)
    rooms = world.get("rooms")
    start = world.get("start_room")

    # Is the world built the way the module describes?
    if not isinstance(rooms, dict):
        fail("Couldn't find a dictionary called `rooms` at the top level of your file.")
    if len(rooms) < 3:
        fail(f"Your world has {len(rooms)} room(s). Build at least 3.")
    for key, room in rooms.items():
        if not isinstance(room, dict):
            fail(f"rooms['{key}'] should be a dictionary.")
        if not isinstance(room.get("description"), str) or not room["description"].strip():
            fail(f"rooms['{key}'] needs a \"description\" string.")
        if not isinstance(room.get("exits"), dict):
            fail(f"rooms['{key}'] needs an \"exits\" dictionary, like {{\"north\": \"hall\"}}.")
        for direction, target in room["exits"].items():
            if direction != direction.lower():
                fail(f"Exit '{direction}' in rooms['{key}'] should be lowercase, "
                     "because the game lowercases what the player types.")
            if target not in rooms:
                fail(f"rooms['{key}'] has an exit '{direction}' to '{target}', "
                     "but there's no room with that key.")
    if start not in rooms:
        fail("Set `start_room` to the key of the room the player starts in.")
    unreachable = [k for k in rooms if find_path(rooms, start, lambda r, k=k: r == k,
                                                  inventory=all_items(rooms)) is None]
    if unreachable:
        fail(f"These rooms can't be reached from the start: {unreachable}. "
             "Check your exits.")
    print(f"  - your world has {len(rooms)} rooms, all connected")

    # Does the game describe the starting room?
    output = flatten(run_game(game_path, ["quit"]))
    if snippet(rooms[start]) not in output:
        fail("The game should describe the starting room when it begins.")

    # Does 'look' describe the room again?
    output = flatten(run_game(game_path, ["look", "quit"]))
    if output.count(snippet(rooms[start])) < 2:
        fail("'look' should print the current room's description again.")

    # Does 'go' move the player? Pick an exit that isn't locked (locks come in module 04).
    open_exits = [d for d in rooms[start]["exits"] if d not in locks(rooms[start])]
    if open_exits:
        direction = open_exits[0]
        target = rooms[rooms[start]["exits"][direction]]
        output = flatten(run_game(game_path, [f"go {direction}", "quit"]))
        if snippet(target) not in output:
            fail(f"After 'go {direction}' the game should describe the room you arrive in.")
    run_game(game_path, ["go", "go nowhere-at-all", "quit"])
    print("  - the start room is described, and 'look' and 'go' work")
    print("  - bad directions don't crash the game")


def check_03(game_path):
    rooms = load_world(game_path)["rooms"]
    start = load_world(game_path)["start_room"]

    for key, room in rooms.items():
        if not isinstance(room.get("items"), list):
            fail(f"rooms['{key}'] needs an \"items\" list (it can be empty: []).")
        for item in room["items"]:
            if not isinstance(item, str) or item != item.lower():
                fail(f"Item {item!r} in rooms['{key}'] should be a lowercase string.")
    if not all_items(rooms):
        fail("Put at least one item somewhere in your world.")

    # Walk to the nearest room with an item, without needing any keys.
    found = find_path(rooms, start, lambda k: rooms[k]["items"])
    if found is None:
        fail("There's no item the player can reach from the start without "
             "unlocking anything. Put one somewhere they can get to first.")
    path, key = found
    item = rooms[key]["items"][0]
    walk = [f"go {d}" for d in path]

    # Compare the output with and without taking the item. After 'take',
    # 'inventory' should mention the item, so it shows up more often.
    without = run_game(game_path, walk + ["inventory", "quit"]).count(item)
    with_take = run_game(game_path, walk + [f"take {item}", "inventory", "quit"]).count(item)
    if with_take <= without:
        fail(f"After 'take {item}', 'inventory' should list the {item}.")
    run_game(game_path, walk + [f"take {item}", f"drop {item}", f"take {item}", "i", "quit"])
    run_game(game_path, ["take", "take unicorn", "drop", "drop unicorn", "inventory", "quit"])
    print("  - every room has an items list")
    print(f"  - 'take {item}', 'drop {item}' and 'inventory' work")
    print("  - taking or dropping things that aren't there doesn't crash the game")


def check_04(game_path):
    world = load_world(game_path)
    rooms, start, goal = world["rooms"], world["start_room"], world.get("goal_room")

    if goal not in rooms:
        fail("Set `goal_room` to the key of the room that wins the game.")
    if goal == start:
        fail("`goal_room` shouldn't be the room the player starts in.")
    lock_list = [(k, d, item) for k, r in rooms.items() for d, item in locks(r).items()]
    if not lock_list:
        fail("Lock at least one exit with a \"locked\" dictionary, like "
             "\"locked\": {\"north\": \"key\"}.")
    for key, direction, item in lock_list:
        if direction not in rooms[key]["exits"]:
            fail(f"rooms['{key}'] locks '{direction}', but has no exit that way.")
        if item not in all_items(rooms):
            fail(f"The '{direction}' exit in rooms['{key}'] needs a {item}, "
                 "but there isn't one anywhere in your world.")

    solution = solve(rooms, start, goal)
    if solution is None:
        fail("Your game can't be won! There's no way to reach the goal room. "
             "Make sure every key can be reached before the door it opens.")
    print(f"  - the game can be won in {len(solution)} moves: {', '.join(solution)}")

    # A locked exit should block the player when they don't have the item.
    for key, direction, item in lock_list:
        found = find_path(rooms, start, lambda k, key=key: k == key)
        if found is None:
            continue
        walk = [f"go {d}" for d in found[0]]
        target = snippet(rooms[rooms[key]["exits"][direction]])
        before = flatten(run_game(game_path, walk + ["quit"])).count(target)
        after = flatten(run_game(game_path, walk + [f"go {direction}", "quit"])).count(target)
        if after > before:
            fail(f"'go {direction}' from {key} should be blocked until you have the {item}.")
        print(f"  - the '{direction}' exit in {key} stays locked without the {item}")
        break

    # Playing the winning moves should end the game by itself, with no 'quit'.
    output = flatten(run_game(game_path, solution))
    if snippet(rooms[goal]) not in output:
        fail("When the player reaches the goal room, describe it before the game ends.")
    print("  - reaching the goal room ends the game")


def check_05(game_path):
    rooms = load_world(game_path)["rooms"]
    start = load_world(game_path)["start_room"]

    # Play in an empty temporary folder, so the save file doesn't land in yours.
    with tempfile.TemporaryDirectory() as folder:
        # Loading before anything is saved should be handled politely.
        run_game(game_path, ["load", "quit"], workdir=folder)

        # Walk to an item, take it, and make sure we end up away from the start.
        path, key = find_path(rooms, start, lambda k: rooms[k]["items"])
        item = rooms[key]["items"][0]
        commands = [f"go {d}" for d in path] + [f"take {item}"]
        if key == start:
            open_exits = [d for d in rooms[start]["exits"] if d not in locks(rooms[start])]
            if not open_exits:
                fail("The checker needs at least one unlocked exit from the start room.")
            commands.append(f"go {open_exits[0]}")
            key = rooms[start]["exits"][open_exits[0]]

        run_game(game_path, commands + ["save", "quit"], workdir=folder)
        if not os.listdir(folder):
            fail("'save' should write your game to a file, but no file was created.")
        print("  - 'save' writes a save file, and 'load' with no save doesn't crash")

        # A new game that loads should be back where we saved...
        fresh = flatten(run_game(game_path, ["look", "quit"], workdir=folder))
        loaded = flatten(run_game(game_path, ["load", "look", "quit"], workdir=folder))
        if loaded.count(snippet(rooms[key])) <= fresh.count(snippet(rooms[key])):
            fail(f"After 'load', the player should be back in {key}, where they saved.")

        # ...and holding the item. The only difference between these two runs
        # is the 'inventory' command, so it must be what mentions the item.
        before = run_game(game_path, ["load", "quit"], workdir=folder).count(item)
        after = run_game(game_path, ["load", "inventory", "quit"], workdir=folder).count(item)
        if after <= before:
            fail(f"After 'load', the inventory should contain the {item} again.")
        print(f"  - 'load' puts you back in {key}, carrying the {item}")


CHECKS = [check_00, check_01, check_02, check_03, check_04, check_05]


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
    """Calls functions from a practice file, with fake typing and captured printing."""

    def __init__(self, practice_module):
        self.practice_module = practice_module

    def call(self, name, *args, inputs=()):
        """
        Call the learner's function `name`. Any input() it does is answered from
        `inputs`, in order. Returns (result, printed_text, answers_used).
        """
        function = getattr(self.practice_module, name, None)
        if function is None:
            fail(f"Couldn't find a function called {name}(). "
                 "Keep the function names from the practice file.")
        if is_unstarted(function):
            raise NotStarted()

        answers = list(inputs)
        used = []

        def fake_input(prompt=""):
            if not answers:
                fail(f"{name}() kept asking for input after these answers: {used}")
            used.append(answers.pop(0))
            return used[-1]

        printed = io.StringIO()
        real_input = builtins.input
        builtins.input = fake_input
        try:
            with contextlib.redirect_stdout(printed):
                result = function(*args)
        except CheckFailed:
            raise
        except Exception as error:
            fail(f"{name}() crashed with {type(error).__name__}: {error}")
        finally:
            builtins.input = real_input

        return result, printed.getvalue(), used


def expect(name, args, got, want):
    """Fail with a clear message if a function returned the wrong thing."""
    if got != want:
        shown = ", ".join(repr(a) for a in args)
        fail(f"{name}({shown}) should return {want!r}, but returned {got!r}.")


def returns(p, name, *args, want):
    got = p.call(name, *args)[0]
    expect(name, args, got, want)


# --- Module 01 --------------------------------------------------------------
def p01_clean(p):
    returns(p, "clean", "  QUIT ", want="quit")
    returns(p, "clean", "Go North", want="go north")
    returns(p, "clean", "look", want="look")


def p01_countdown(p):
    returns(p, "countdown", 3, want=[3, 2, 1])
    returns(p, "countdown", 1, want=[1])
    returns(p, "countdown", 0, want=[])


def p01_are_we_there_yet(p):
    _, printed, used = p.call("are_we_there_yet", inputs=["no", "maybe", " YES "])
    if len(used) < 3:
        fail(f"are_we_there_yet() stopped after {used}, before anyone said yes.")
    if "Finally!" not in printed:
        fail("are_we_there_yet() should print 'Finally!' once the answer is yes.")


def p01_password_door(p):
    try:
        p.call("password_door", inputs=["hello"])
    except CheckFailed as problem:
        if "kept asking" not in str(problem):
            raise
    else:
        fail("password_door() stopped asking after a wrong password ('hello').")
    _, printed, used = p.call("password_door", inputs=["hello", "  Open SESAME "])
    if "The door opens." not in printed:
        fail("password_door() should print 'The door opens.' after '  Open SESAME '.")


# --- Module 02 --------------------------------------------------------------
def p02_opposite(p):
    for direction, want in [("north", "south"), ("south", "north"),
                            ("east", "west"), ("west", "east"), ("up", "?")]:
        returns(p, "opposite", direction, want=want)


def p02_split_command(p):
    for text, want in [("go up the stairs", ("go", "up the stairs")),
                       ("look", ("look", "")), ("   ", ("", ""))]:
        got = p.call("split_command", text)[0]
        expect("split_command", [text], tuple(got) if isinstance(got, list) else got, want)


def p02_follow(p):
    world = {
        "a": {"exits": {"east": "b"}},
        "b": {"exits": {"west": "a", "north": "c"}},
        "c": {"exits": {}},
    }
    returns(p, "follow", world, "a", ["east", "north"], want="c")
    returns(p, "follow", world, "a", ["north", "east"], want="b")
    returns(p, "follow", world, "c", [], want="c")


def p02_describe_exits(p):
    returns(p, "describe_exits", {"exits": {"north": "hall", "east": "yard"}},
            want="Exits: north, east")
    returns(p, "describe_exits", {"exits": {"down": "cellar"}}, want="Exits: down")


# --- Module 03 --------------------------------------------------------------
def p03_move_item(p):
    source, target = ["lamp", "rope"], ["key"]
    returns(p, "move_item", "lamp", source, target, want=True)
    if source != ["rope"] or target != ["key", "lamp"]:
        fail(f"After move_item('lamp', ...), the lists should be ['rope'] and "
             f"['key', 'lamp'], but they're {source} and {target}.")
    returns(p, "move_item", "lamp", source, target, want=False)
    if source != ["rope"] or target != ["key", "lamp"]:
        fail("move_item() shouldn't change the lists when the item isn't there.")


def p03_add_to_bag(p):
    bag = ["map"]
    p.call("add_to_bag", "rope", bag)
    if bag != ["map", "rope"]:
        fail(f"After add_to_bag('rope', bag), the bag should be ['map', 'rope'], "
             f"but it's still {bag}.")


def p03_count_items(p):
    rooms = {"a": {"items": ["x", "y"]}, "b": {"items": []}, "c": {"items": ["z"]}}
    returns(p, "count_items", rooms, want=3)
    returns(p, "count_items", {}, want=0)


def p03_describe_items(p):
    returns(p, "describe_items", ["lamp", "rope"], want="You see: lamp, rope")
    returns(p, "describe_items", ["key"], want="You see: key")
    returns(p, "describe_items", [], want="There's nothing here.")


# --- Module 04 --------------------------------------------------------------
def p04_can_pass(p):
    hall = {"exits": {"north": "x", "east": "y"}, "locked": {"north": "key"}}
    returns(p, "can_pass", hall, "north", [], want=False)
    returns(p, "can_pass", hall, "north", ["lamp", "key"], want=True)
    returns(p, "can_pass", hall, "east", [], want=True)
    returns(p, "can_pass", {"exits": {"south": "z"}}, "south", [], want=True)


def p04_lock_for(p):
    returns(p, "lock_for", {"locked": {"north": "key"}}, "north", want="key")
    returns(p, "lock_for", {"locked": {"north": "key"}}, "east", want=None)
    returns(p, "lock_for", {"exits": {}}, "north", want=None)


def p04_missing_keys(p):
    rooms = {
        "yard": {"items": ["key"], "locked": {"north": "key", "east": "crowbar"}},
        "shed": {"items": []},
        "house": {"items": [], "locked": {"up": "lamp"}},
    }
    returns(p, "missing_keys", rooms, want=["crowbar", "lamp"])
    returns(p, "missing_keys", {"a": {"items": ["key"]}}, want=[])


# --- Module 05 --------------------------------------------------------------
def p05_settings(p):
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "settings.json")
        p.call("save_settings", {"volume": 7, "name": "Ana"}, path)
        if not os.path.exists(path):
            fail("save_settings() should create the file it's given.")
        returns(p, "load_settings", path, want={"volume": 7, "name": "Ana"})
        returns(p, "load_settings", os.path.join(folder, "missing.json"), want={})


def p05_load_scores(p):
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "scores.json")
        returns(p, "load_scores", path, want=[])
        with open(path, "w") as file:
            json.dump([5, 7], file)
        returns(p, "load_scores", path, want=[5, 7])


def p05_save_score(p):
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "scores.json")
        p.call("save_score", "Ana", 5, path)
        p.call("save_score", "Ben", 7, path)
        try:
            with open(path) as file:
                saved = json.load(file)
        except (OSError, ValueError):
            fail("save_score() should write the scores to the file as JSON.")
        want = [{"name": "Ana", "score": 5}, {"name": "Ben", "score": 7}]
        if saved != want:
            fail(f"After saving Ana (5) then Ben (7), the file should hold {want}, "
                 f"but it holds {saved}.")


# This problem covers two functions, so give it a clearer name in the report.
p05_settings.label = "save_settings() and load_settings()"

# The problems for each module, in the order they appear in practice_NN.py.
PRACTICE_TESTS = {
    1: [p01_clean, p01_countdown, p01_are_we_there_yet, p01_password_door],
    2: [p02_opposite, p02_split_command, p02_follow, p02_describe_exits],
    3: [p03_move_item, p03_add_to_bag, p03_count_items, p03_describe_items],
    4: [p04_can_pass, p04_lock_for, p04_missing_keys],
    5: [p05_settings, p05_load_scores, p05_save_score],
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
                       "seconds. Is there a while loop that never ends?"}
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
    game_path = os.path.abspath(args[1] if len(args) > 1 else "adventure.py")
    if not os.path.isfile(game_path):
        print(f"Couldn't find {game_path}.")
        print("Run this from the folder with your adventure.py, or pass the file's path.")
        sys.exit(1)

    # Run every module's checks up to the one asked for.
    for number in range(module + 1):
        print(f"Module {number:02d}:")
        try:
            CHECKS[number](game_path)
        except CheckFailed as problem:
            print(f"\n[NOT YET] {problem}")
            sys.exit(1)
    print(f"\n[PASS] Everything up to module {module:02d} works. Nice!")


if __name__ == "__main__":
    main()
