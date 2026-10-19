# practice_01.py: practice problems for Module 01: Hello, Discord
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your bot's folder with:
#
#     python check.py practice 1
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? The lesson has hints for each problem.

import asyncio

# Commands registered with @register end up in here.
COMMANDS = {}


# 1. register(name)
# A decorator that stores a function in COMMANDS under `name`, then gives the
# function back unchanged. It's a tiny version of how @bot.tree.command works.
#     @register("wave")
#     def wave():
#         return "o/"
#
#     COMMANDS["wave"]()  -> "o/"
#     wave()              -> "o/"   (still works as normal)
def register(name):
    # Your code here
    pass


# 2. slow_double(x)
# An async function that waits 0.1 seconds (without freezing everything
# else), then returns x * 2.
#     await slow_double(21)  -> 42
async def slow_double(x):
    # Your code here
    pass


# 3. double_all(numbers)
# An async function that doubles every number with slow_double() and returns
# the results as a list, in order. Doubling 10 numbers should take about 0.1
# seconds in total, not 1 second: run them at the same time.
#     await double_all([1, 2, 3])  -> [2, 4, 6]
async def double_all(numbers):
    # Your code here
    pass


# 4. FIX THE BUG: shout_greeting(name)
# This should return "HELLO, ANA!" for "Ana", but it crashes.
async def get_greeting(name):
    await asyncio.sleep(0.01)
    return f"Hello, {name}!"


async def shout_greeting(name):
    greeting = get_greeting(name)
    return greeting.upper()
