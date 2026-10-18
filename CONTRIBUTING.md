# Contributing to MontyDevs_Vault

Thanks for helping build the vault! This guide explains how to add a new project or improve an existing one.

## Adding a new project

1. **Pick a topic folder** (for example `games/`). If none fits, create a new one in `kebab-case` with its own `README.md`, and add it to the topic table in the main README.
2. **Pick a difficulty**: Beginner, Intermediate, or Advanced. See [difficulty levels](README.md#difficulty-levels).
3. **Copy the template**:
   ```sh
   cp -r templates/project games/NN-your-project-name
   ```
   `NN` is a two-digit number that sets the project's place in the difficulty order for that topic (for example `03-text-adventure`). Renumber neighbours if you need to slot a project in between. Projects are standalone, so don't assume a learner has done any other project.
4. **Fill in the project `README.md`**: goal, difficulty, language, prerequisites and the module list.
5. **Write Module 00** from `modules/00-setup/` (see [Module 00: Setup](#module-00-setup)).
6. **Write the modules**: copy `modules/01-module-name/` once per module and rename each copy (`01-game-loop`, `02-rooms`, ...).
7. **Write a self-check** (see below) and remove `CHECK_GOES_HERE.md`.
8. **Add the project to its topic's `README.md`** in difficulty order, so people can find it.
9. Open a pull request.

[`games/01-text-adventure`](games/01-text-adventure/) is a complete example of every part of this guide.

## Learners work on their own

Club members do these projects on their own time and their own laptops, with no one around to ask. So every module needs to stand up by itself:

- **Link the [guides](guides/)** for setup, rather than assuming tools are installed. Add a guide if a project needs a tool that isn't covered yet.
- **Say what success looks like** after each step: the output to expect, or what to try.
- **Include a "Stuck?" section** listing the mistakes people actually make, and the error messages they cause.
- **Provide a self-check**, so learners know they've finished before moving on.

## Scaffolding by difficulty

How much a module hands over depends on the project's difficulty:

| | Beginner | Intermediate | Advanced |
| --- | --- | --- | --- |
| **Concepts** | Explained from scratch, with small examples | New libraries and patterns explained; basics assumed | Brief overview, plus links to deeper reading |
| **Steps** | Show the code for each new idea, then have the learner write similar pieces themselves ("Your turn") | Describe what to build; show code only for unfamiliar APIs or tricky parts | Give a spec of the behaviour; the learner designs the code |
| **Hints** | Inline, right where they're needed | In "Stuck?" | In "Stuck?" and in collapsible `<details>` blocks |
| **Self-check** | Checks each feature, with detailed messages | Checks behaviour, with shorter messages | Checks the spec only, like an acceptance test |
| **Solutions** | An example `solution/` in every module | None | None |

Even at Beginner, a module is never a pure copy-paste: every module should have at least one **Your turn** step where the learner writes code they weren't shown.

## Module 00: Setup

Every project starts with a `00-setup` module that takes a learner from nothing installed to a project folder that runs. It should:

- Link the [guides](guides/) for installing the language and editor, rather than repeating them, and say which version is needed.
- Explain getting the vault (with `git clone`, or **Download ZIP**) and where to put the learner's own project folder: outside the vault, so updates never touch their work.
- Have the learner create the project's first file themselves, and run it.
- End by running the self-check with `0`, which confirms the setup works.
- Say which steps can be skipped by someone who has already done a project in the same language.

There are no `starter/` folders: Module 00 is where the learner's code begins.

## Leave room to personalize

Each learner should end up with a project that's recognisably *theirs*.

- **Every module has a "Make it yours" section** with choices the learner makes: content, theme, design, which features to add.
- **Present the solution as one example.** Its content (story text, styling, names) is a sample, not the answer.
- **Self-checks test behaviour, not content.** Read the learner's own data and exercise it, rather than comparing against fixed output. The text adventure's checker, for example, reads the learner's rooms and plays their game. Where a check needs something to have a specific name (a function or variable), say so clearly in the module.

## Writing good modules

- **The modules are a course.** A project's modules run in order from a blank start to the finished project. Each module adds one piece and assumes everything taught in the modules before it.
- **One idea per module.** Each module should take a single sitting (roughly 30–90 minutes) and end with something that runs.
- **Chain the modules.** Learners keep working in their own code from module to module, starting from what they made in Module 00.
- **Beginner solutions build on each other.** A module's `solution/` must run, pass that module's check, and build directly on the previous module's solution, so a learner who falls badly behind can copy it and carry on.
- **Hide hints at Intermediate and Advanced.** With no solutions, put hints in collapsible blocks, from a gentle nudge to an almost complete answer:
  ```html
  <details><summary>Hint 1</summary>

  Your hint here.

  </details>
  ```
- **Comment the solution code.** Explain *why*, not just *what*. The solution is a teaching tool.
- **Link outside resources on purpose.** If an article, video or doc already explains a concept well, link it in the module's "Resources" section and say what the reader should take from it.
- **End with challenges.** Optional stretch goals give stronger students something extra without slowing everyone else down.

## Self-checks

- Run with one command, from the learner's own project folder, taking the module number: e.g. `python check.py 3`. Module `0` checks the setup.
- Check the given module **and every module before it**, so learners know nothing broke.
- Print plain-ASCII results (`[PASS]`, `[NOT YET]`) so they display on every terminal.
- Make failure messages say what to fix, in the learner's terms, not just that something failed.
- Before opening a PR, test the check against working and unfinished code for each module. For Beginner projects: each module's `solution/` should pass its check, and the previous module's solution should not.

## Naming conventions

- Folders use `kebab-case` with a two-digit prefix that sets the order: `01-hello-world`.
- Every project and every module has a `README.md`.
- Example code goes in `solution/` inside each module (Beginner projects only).

## Choosing a language

Use the language that best fits the project, and say why in the project README. When two choices are reasonable, prefer the one more club members already know.
