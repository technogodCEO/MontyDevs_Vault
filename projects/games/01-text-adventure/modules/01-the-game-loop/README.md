# Module 01: The Game Loop

**Goal:** a program that greets the player, keeps asking "what do you do?", and reacts until the player types `quit`.

## Concepts

### `input()` and `print()`

`print()` shows text. `input()` shows a prompt, waits for the player to type something and press Enter, then gives you what they typed as a string:

```python
name = input("What's your name? ")
print("Hello, " + name + "!")
```

### The `while` loop

A `while` loop repeats its indented block for as long as its condition is `True`:

```python
playing = True
while playing:
    # ...this runs again and again...
    playing = False   # ...until something sets playing to False
```

Almost every game has a loop like this at its heart, from text adventures to 3D shooters. Each pass through the loop is one "turn": show the world, get the player's input, update the game.

### Cleaning up input

Players type messily: `Quit`, `QUIT`, `  quit  `. Two string methods help:

- `.strip()` removes spaces from the start and end.
- `.lower()` turns everything lowercase.

So `input("> ").strip().lower()` turns all three of those into `"quit"`.

## Practice

Warm up on this module's ideas before you use them in your game.

### Think it through

Try each one in your head (or on paper) first, then click **Answer** to check.

**1. Predict the output.** What does this print?

```python
count = 3
while count > 0:
    print(count)
    count = count - 1
print("Liftoff!")
```

<details><summary>Answer</summary>

```
3
2
1
Liftoff!
```

The loop runs while `count > 0`: for 3, 2 and 1. When `count` reaches 0 the condition is `False`, so the loop stops and the last line runs.

</details>

**2. Predict the result.** What is `"  HeLLo ".strip().lower()`?

<details><summary>Answer</summary>

`"hello"`. `.strip()` removes the spaces at both ends, giving `"HeLLo"`, then `.lower()` makes it `"hello"`.

</details>

### Try it in code

[`practice_01.py`](practice_01.py) has small problems to solve in Python: cleaning up input, a countdown loop, a buggy loop to fix, and a password door.

1. Copy `practice_01.py` into your game folder, next to `check.py`.
2. Fill in each function where it says `# Your code here`. Problems marked **FIX THE BUG** already have code: find what's wrong and fix it.
3. Test your answers:
   ```sh
   python check.py practice 1
   ```
   Each problem shows `[PASS]`, `[TODO]` (not started yet) or `[NOT YET]` with a hint, so you can do them in any order.

Stuck? Example answers are in [`solution/practice_01.py`](solution/practice_01.py).

## Steps

Continue in the `adventure.py` you made in [Module 00](../00-setup/). Right now it prints `Hello, adventurer!` and stops. (Use `python3` instead of `python` on macOS or Linux.)

1. **Write a welcome message.** Replace the `print("Hello, adventurer!")` line inside `main()` with your game's title and a line or two of story. For example:
   ```python
   print("=== The Lighthouse ===")
   print("A storm is rolling in, and the old lighthouse has gone dark.")
   print("Type 'help' to see what you can do.")
   ```
   Don't copy this one. Write your own (see **Make it yours** below).

2. **Add the loop.** Under your welcome message, still inside `main()` (indented by 4 spaces), add:
   ```python
   playing = True
   while playing:
       command = input("> ").strip().lower()

       if command == "quit":
           print("Thanks for playing!")
           playing = False
       else:
           print("I don't understand that.")
   ```
   Run it. Type a few things, then `quit`.

3. **Your turn: add `help`.** Add an `elif` branch between the `if` and the `else` so that typing `help` lists the commands the game understands (right now, `help` and `quit`). An `elif` looks like this:
   ```python
   elif command == "something":
       # what to do
   ```

4. **Your turn: ignore empty input.** Right now, pressing Enter without typing anything prints "I don't understand that." Add another `elif` that checks for an empty string (`""`) and does nothing. (Hint: the keyword `continue` jumps straight back to the top of the loop.)

5. **Keep the bottom two lines.** The file must still end with:
   ```python
   if __name__ == "__main__":
       main()
   ```
   This starts the game when you run the file, but not when another program (like the checker) only loads it.

## Make it yours

This is where your game gets its identity. Before you move on, decide:

- **Where is it set?** A haunted school, a space station, a dragon's cave, a sandwich shop at 3 a.m.
- **Who is the player, and what do they want?** You don't need the whole plot yet. One sentence is plenty.
- **What's the tone?** Spooky, silly, mysterious? Let it show in your messages. Even "I don't understand that" can be in character: *"The ship's computer beeps in confusion."*

## Check your work

From your game's folder, run:

```sh
python check.py 1
```

`[PASS]` means you're ready for the next module. `[NOT YET]` tells you what to fix.

## Stuck?

- **`IndentationError` or `unexpected indent`**: Python uses indentation to know which lines belong inside the loop and the `if`. Everything inside `while playing:` needs 4 more spaces than the `while` line, and everything inside an `if` needs 4 more again. Don't mix tabs and spaces. VS Code's status bar shows which one you're using.
- **The game never stops**: make sure your `quit` branch sets `playing = False` (two `=` signs would compare instead of set, so use one).
- **Typing `QUIT` doesn't work**: check that you called `.lower()` on the input.
- **The checker says the game started when the file was loaded**: your code to start the game is outside `main()`. Put everything inside `def main():`, and keep the two `__name__` lines at the bottom.

## Resources

- [Python docs: `while` statements](https://docs.python.org/3/reference/compound_stmts.html#while): the official description. Skim it to see that `while` really is this simple.
- [Python docs: `if` statements](https://docs.python.org/3/tutorial/controlflow.html#if-statements): a short refresher on `if`, `elif` and `else`.
- [Real Python: Python "while" Loops](https://realpython.com/python-while-loop/): more examples, including `break` and `continue`.

## Challenges (optional)

- Count the turns: keep a number that goes up by 1 each time the player enters a command, and print it when they quit.
- Make `exit` and `q` work as well as `quit`.
- Ask for the player's name at the start and use it in your messages.

## Next

Continue to [Module 02: Rooms and Movement](../02-rooms-and-movement/).
