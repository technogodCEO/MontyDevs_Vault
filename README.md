# MontyDevs_Vault

A collection of **project-based tutorials** for the MontyDevs CS club. Learn by building real things.

Think of it as a friendlier, more guided take on [build-your-own-x](https://github.com/codecrafters-io/build-your-own-x). Every project is our own tutorial, split into small **modules** you work through one at a time. Where a great outside resource already exists, a module links to it rather than reinventing it.

## How it's organized

Projects are grouped by **level**. Within each level they're numbered roughly from easiest to hardest.

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

Each module builds on the one before it, so its `starter/` code is roughly the previous module's `solution/`. You can jump in at any module and still have working code to start from.

## How to use a tutorial

1. Pick a project at your level and read its `README.md`.
2. Open the first module, read the lesson, and copy its `starter/` code into your own workspace.
3. Build it yourself. Only check `solution/` once you're done, or if you're truly stuck.
4. Move on to the next module.

## Contributing

Want to write a tutorial or improve one? See [CONTRIBUTING.md](CONTRIBUTING.md). A ready-to-copy skeleton lives in [`templates/project/`](templates/project/).

## License

[MIT](LICENSE)
