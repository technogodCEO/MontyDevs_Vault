# practice_06.py: practice problems for Module 06: Functions
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your language's folder with:
#
#     python check.py practice 6
#
# Each problem gets its own result, so you can do them in any order.
# There are no answers to copy: the lesson's "Try it in code" section has hints.


# 1. make_counter()
# Return a function. Each time that function is called, it returns the
# next number: 1, then 2, then 3... Every counter keeps its own count.
#     a = make_counter()
#     b = make_counter()
#     a(), a(), b(), a()  -> 1, 2, 1, 3
def make_counter():
    # Your code here
    pass


# 2. compose(f, g)
# Return a new function that takes x and returns f(g(x)).
#     compose(lambda x: x + 1, lambda x: x * 10)(2)  -> 21
def compose(f, g):
    # Your code here
    pass


# 3. FIX THE BUG: make_adders(n)
# Return a list of n functions: the first adds 0 to its argument, the next
# adds 1, and so on. But every one of them adds n - 1. Why?
#     [add(10) for add in make_adders(3)]  -> [10, 11, 12]
def make_adders(n):
    adders = []
    for i in range(n):
        adders.append(lambda x: x + i)
    return adders


# 4. checked_call(function, arity, args)
# Your interpreter must check a call has the right number of arguments
# before running the function. If len(args) isn't arity, raise a TypeError
# with the message "Expected <arity> arguments but got <len(args)>.".
# Otherwise call function with the arguments and return its result.
#     checked_call(lambda a, b: a + b, 2, [3, 4])  -> 7
#     checked_call(lambda a: a, 1, [1, 2])         # TypeError: Expected 1 arguments but got 2.
def checked_call(function, arity, args):
    # Your code here
    pass
