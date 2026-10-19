# practice_05.py: practice problems for Module 05: XP and a Database
#
# Fill in each function where it says "# Your code here" (delete the `pass`).
# Problems marked FIX THE BUG already have code: find what's wrong and fix it.
#
# Test your answers from your bot's folder with:
#
#     python check.py practice 5
#
# Each problem gets its own result, so you can do them in any order.
# Stuck? The lesson has hints for each problem.
#
# Every function gets `conn`, an open sqlite3 connection with this table:
#
#     CREATE TABLE notes (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT)
#
# Always use ? placeholders for values, never f-strings (see problem 4).


# 1. add_note(conn, user_id, text) and notes_for(conn, user_id)
# add_note() saves a note. notes_for() returns the text of every note for that
# user, oldest first, as a list of strings.
#     add_note(conn, 1, "buy milk")
#     add_note(conn, 1, "call Sam")
#     notes_for(conn, 1)  -> ["buy milk", "call Sam"]
#     notes_for(conn, 3)  -> []
def add_note(conn, user_id, text):
    # Your code here
    pass


def notes_for(conn, user_id):
    # Your code here
    pass


# 2. top_users(conn, limit)
# Return the users with the most notes, as (user_id, number_of_notes) pairs,
# most first, at most `limit` of them. Let SQL do the counting (GROUP BY).
#     top_users(conn, 2)  -> [(2, 3), (3, 2)]
def top_users(conn, limit):
    # Your code here
    pass


# 3. delete_note(conn, note_id)
# Delete the note with that id. Return True if a note was deleted, or False
# if there was no such note.
def delete_note(conn, note_id):
    # Your code here
    pass


# 4. FIX THE BUG: find_notes(conn, word)
# This should return the text of every note containing `word`, oldest first.
# It works for "lunch", but crashes for "don't", and returns every note for
# "' OR '1'='1". Fix it properly, with a ? placeholder.
def find_notes(conn, word):
    rows = conn.execute(f"SELECT text FROM notes WHERE text LIKE '%{word}%' ORDER BY id")
    return [row[0] for row in rows]
