# adventure.py: The Lighthouse (Module 01 solution)
#
# This is ONE example of a finished Module 01. Your game should have its own
# title, story and messages. The structure is what matters.
#
# Every text adventure is built around a loop:
#   1. show the player something
#   2. ask what they want to do
#   3. react to it
#   4. repeat until the game ends


def main():
    # The opening lines are the player's first impression of your world.
    print("=== The Lighthouse ===")
    print("A storm is rolling in, and the old lighthouse has gone dark.")
    print("Type 'help' to see what you can do.")

    # This variable controls the loop. The game keeps running while it's True.
    playing = True

    while playing:
        # input() pauses until the player types something and presses Enter.
        # .strip() removes extra spaces, and .lower() makes "QUIT" and "quit"
        # count as the same command.
        command = input("> ").strip().lower()

        if command == "quit":
            print("Thanks for playing!")
            # Setting playing to False means the loop stops after this turn.
            playing = False
        elif command == "help":
            print("Commands: help, quit")
        elif command == "":
            # The player just pressed Enter. Skip the rest and ask again.
            continue
        else:
            # Anything we don't recognise gets a friendly reply.
            print("I don't understand that. Type 'help' for commands.")


# Only start the game when this file is run directly (python adventure.py).
# This also lets other programs, like the checker, load your code
# without the game starting by itself.
if __name__ == "__main__":
    main()
