# MontyDevs_Vault

A collection of **project-based tutorials** for the MontyDevs CS club. Learn by building real things.

Think of it as a friendlier, more guided take on [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x). Every project is our own tutorial, split into small **modules** you work through one at a time. Where a great outside resource already exists, a module links to it rather than reinventing it.

## How it's organized

The vault is a **project-based course**, meant to be followed in order:

**Beginner → Intermediate → Advanced**. Inside each level, work through the projects in number order. Inside each project, work through the modules in number order.

Each step builds on what came before. A project assumes you finished the projects ahead of it, and a module assumes you finished the modules ahead of it. If you already have experience, start at the level that fits you (see below), then go in order from there.

| Level | Who it's for |
| --- | --- |
| [Beginner](beginner/) | You know the basics of one language (variables, loops, functions) and want to build your first complete project. |
| [Intermediate](intermediate/) | You've built a few small programs and are ready for multiple files, data structures, APIs and testing. |
| [Advanced](advanced/) | You're comfortable programming and want to dig into how systems really work: interpreters, networking, databases and more. |

Each project uses whichever language suits it best, and its README says which one.

## Anatomy of a project

```
<level>/
└── 01-project-name/
    ├── README.md              # Overview: goal, language, prerequisites, module list
    └── modules/
        ├── 01-module-name/
        │   ├── README.md      # The lesson: concepts, steps, outside resources
        │   ├── starter/       # Code to begin this module with
        │   └── solution/      # A commented reference solution
        └── 02-module-name/
            └── ...
```

You keep building on your own code from one module to the next. Each module's `starter/` matches the previous module's `solution/`, so if your code is broken or you missed a session, copy `starter/` and carry on with the group.

## How to use a tutorial

1. Open your level's `README.md` and start with its first project you haven't done yet.
2. Read the project's `README.md`, then open module `01`.
3. Read the lesson and build it yourself in your own workspace. Only check `solution/` once you're done, or if you're truly stuck.
4. Go on to the next module. Use its `starter/` only if you need to catch up.
5. When you finish the last module, follow the link to the next project.

## Contributing

Want to write a tutorial or improve one? See [CONTRIBUTING.md](CONTRIBUTING.md). A ready-to-copy skeleton lives in [`templates/project/`](templates/project/).

## License

[MIT](LICENSE)
