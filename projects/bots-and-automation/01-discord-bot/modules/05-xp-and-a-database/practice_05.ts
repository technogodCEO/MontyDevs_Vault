/*
 * Practice for Module 05: SQL with node:sqlite.
 *
 * Copy this file into your bot's folder (next to check.ts), fill in each
 * function, and test your answers with:
 *
 *     node check.ts practice 5
 *
 * The checker gives each function a fresh in-memory database that setup()
 * has already run on. Hints are in the lesson, under "Try it in code".
 */

import type { DatabaseSync } from "node:sqlite";

// Creates the tables. (Done for you.)
export function setup(db: DatabaseSync): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, text TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS scores (user_id TEXT PRIMARY KEY, points INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT NOT NULL);
  `);
}

// 1. Save a note, and return its new id (a number).
export function addNote(db: DatabaseSync, userId: string, text: string): number {
  // Your code here
  throw new Error("TODO");
}

//    And list one user's notes' text, oldest first ([] if they have none).
export function notesFor(db: DatabaseSync, userId: string): string[] {
  // Your code here
  throw new Error("TODO");
}

// 2. Add points to a user's score in the scores table, creating their row if
//    it doesn't exist yet, and return their new total. Use ONE statement.
export function addPoints(db: DatabaseSync, userId: string, points: number): number {
  // Your code here
  throw new Error("TODO");
}

// 3. Move `amount` points from one user to another (who may not have a row
//    yet). If `from` has fewer than `amount` points, change nothing and
//    return false. Otherwise return true. Use a transaction, so the two
//    updates happen together or not at all.
export function transferPoints(db: DatabaseSync, from: string, to: string, amount: number): boolean {
  // Your code here
  throw new Error("TODO");
}

// 4. FIX THE BUG: find a user's id by name, or null if there's no such user.
//    Try it with the name O'Brien. Then with:  x' OR '1'='1
export function findUserId(db: DatabaseSync, name: string): string | null {
  const row = db.prepare(`SELECT id FROM users WHERE name = '${name}'`).get() as { id: string } | undefined;
  return row ? row.id : null;
}
