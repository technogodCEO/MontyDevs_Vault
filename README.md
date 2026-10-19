# MontyDevs_Vault

A collection of **project-based tutorials** for the MontyDevs CS club. Learn by building real things.

Think of it as a friendlier, more guided take on [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x). Every project is our own tutorial, split into small **modules** you work through one at a time. Where a great outside resource already exists, a module links to it rather than reinventing it.

## Structure

### Course numbers

Every course has a code, like a university course, that tells you its topic, level and place in the order: `TOPIC LNN`.

- **TOPIC** is the topic: `GAME`, `BOT` or `LANG` (more will come as topics are added).
- **L** is the level: `1` Beginner, `2` Intermediate, `3` Advanced.
- **NN** is the order within that topic and level. Lower numbers come first.
- **01–49 are project courses**, where you build one thing from start to finish. **50–99 are reserved for lesson-based courses**, which teach a subject through lessons and exercises instead of a single project.

| Code | Course | Level |
| --- | --- | --- |
| GAME 101 | Text Adventure | Beginner |
| BOT 201 | Discord Bot | Intermediate |
| LANG 201 | Tree-Walking Interpreter | Intermediate |
| LANG 301 | Bytecode Virtual Machine | Advanced |

### Prerequisites

Every course lists what you should know before you start, and links the course in the vault that teaches each skill. For example, LANG 301 links "recursion and tree structures" to LANG 201, and LANG 201 links "Python basics" to GAME 101. If a course feels too hard, follow its prerequisites back until you find where to start.

Some "Stuck?" hints link the exact module that teaches an idea, such as "closures: LANG 201, Module 06", so you can review one lesson rather than a whole course.

Prerequisites are suggestions, not requirements: every course stands on its own, and you can start anywhere you already know enough.

### Topics

Projects are grouped by **topic**. Within each topic they're numbered from easiest to hardest. Pick any project that fits your interests and level: each one stands on its own.

| Topic | What you'll build |
| --- | --- |
| [Games](projects/games/) | Playable games, from terminal adventures to real-time graphics |
| [Bots & Automation](projects/bots-and-automation/) | Chat bots, scripts, and tools that talk to other services |
| [Programming Languages](projects/programming-languages/) | Interpreters and compilers, to learn how code really runs |

More topics will be added as projects are written.

Each project is its own **mini course**. Its modules are meant to be done in order, from `00` to the end, and each one builds on the code you wrote in the last.

### Difficulty levels

Every project is labelled with one of three levels:

| Level | Who it's for |
| --- | --- |
| Beginner | You know the basics of one language (variables, loops, functions) and want to build your first complete project. |
| Intermediate | You've built a few small programs and are ready for multiple files, data structures, APIs and testing. |
| Advanced | You're comfortable programming and want to dig into how systems really work: interpreters, networking, databases and more. |

Each project uses whichever language suits it best, and its README says which one.

### Anatomy of a project

```
projects/
└── <topic>/
    └── 01-project-name/
        ├── README.md              # Overview: goal, language, prerequisites, module list
        ├── check.py               # Self-check: tells you when a module is done
        └── modules/
            ├── 00-setup/
            │   └── README.md      # Install tools, get the vault, make your project folder
            ├── 01-module-name/
            │   ├── README.md      # The lesson: concepts, practice, steps, Make it yours, Stuck?
            │   ├── practice_01.py # Practice problems to solve before the steps
            │   └── solution/      # Beginner projects only: example solution and practice answers
            └── 02-module-name/
                └── ...
```

Every project starts with **Module 00: Setup**, which gets you from nothing installed to a project folder that runs. From there you keep building on your own code, one module after another.

Beginner projects include an example `solution/` for each module, as a last resort when you're stuck. Intermediate and Advanced projects use hints you click to reveal instead, so you work out the code yourself.

These are projects, not copy-paste exercises. Every module has a **Make it yours** section, and the solutions are one example among many. Your version should look like yours.

## How to use a tutorial

New to coding tools? Start with the [guides](guides/): installing Python, using the terminal, setting up VS Code, and Git.

1. Pick a topic, then a project at your level, and read the project's `README.md`.
2. Do **Module 00: Setup** to install what you need and make your own project folder.
3. Read each lesson and do its **Practice** problems, then build that module's part of the project yourself. If you get stuck, try the module's **Stuck?** section and hints first.
4. Run the self-check. When it passes, go on to the next module and keep working in the same code.
5. Repeat until you've finished the last module.

## Contributing

Want to write a tutorial or improve one? See [CONTRIBUTING.md](CONTRIBUTING.md). A ready-to-copy skeleton lives in [`templates/project/`](templates/project/). Looking for something to work on? See [IDEAS.md](IDEAS.md).

## License

[MIT](LICENSE)
