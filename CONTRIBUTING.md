# Contributing to MontyDevs_Vault

Thanks for helping build the vault! This guide explains how to add a new project or improve an existing one.

## Adding a new project

1. **Pick a level**: `beginner/`, `intermediate/`, or `advanced/`. See the main [README](README.md#how-its-organized) for what each level means.
2. **Copy the template**:
   ```sh
   cp -r templates/project beginner/NN-your-project-name
   ```
   `NN` is a two-digit number that sets the project's place in the difficulty order for that level (for example `03-text-adventure`). Renumber neighbours if you need to slot a project in between. Projects are standalone, so don't assume a learner has done any other project.
3. **Fill in the project `README.md`**: goal, language, prerequisites and the module list.
4. **Write the modules**: copy `modules/01-module-name/` once per module and rename each copy (`01-setup`, `02-game-loop`, ...).
5. **Add the project to its level's `README.md`** in difficulty order, so people can find it.
6. Open a pull request.

## Writing good modules

- **The modules are a course.** A project's modules run in order from a blank start to the finished project. Each module adds one piece and assumes everything taught in the modules before it.
- **One idea per module.** Each module should take a single sitting (roughly 30–90 minutes) and end with something that runs.
- **Starter and solution must both run.** `starter/` is the point where the learner begins, and `solution/` is a finished, working reference.
- **Chain the modules.** Learners keep working in their own code from module to module. A module's `starter/` must match the previous module's `solution/`, so anyone who falls behind can catch up.
- **Comment the solution code.** Explain *why*, not just *what*. The solution is a teaching tool.
- **Link outside resources on purpose.** If an article, video or doc already explains a concept well, link it in the module's "Resources" section and say what the reader should take from it.
- **End with challenges.** Optional stretch goals give stronger students something extra without slowing everyone else down.

## Naming conventions

- Folders use `kebab-case` with a two-digit prefix that sets the order: `01-hello-world`.
- Every project and every module has a `README.md`.
- Reference code goes in `solution/` and starting code in `starter/`, inside each module.

## Choosing a language

Use the language that best fits the project, and say why in the project README. When two choices are reasonable, prefer the one more club members already know.
