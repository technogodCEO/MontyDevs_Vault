# Contributing to MontyDevs_Vault

Thanks for helping build the vault! This guide explains how to add a new project or improve an existing one.

## Adding a new project

1. **Pick a level**: `beginner/`, `intermediate/`, or `advanced/`. See the main [README](README.md#how-its-organized) for what each level means.
2. **Copy the template**:
   ```sh
   cp -r templates/project beginner/NN-your-project-name
   ```
   `NN` is a two-digit number that sets the project's place in the course (for example `03-text-adventure`). Learners do the projects in this order, so a project may only use skills taught in the projects before it, plus the ones it teaches itself. To slot a project in between, renumber its neighbours and fix their Previous/Next links.
3. **Fill in the project `README.md`**: goal, language, previous project, module list and next project.
4. **Write the modules**: copy `modules/01-module-name/` once per module and rename each copy (`01-setup`, `02-game-loop`, ...).
5. **Wire it into the course:** add it to its level's `README.md` table in order, and update the "Next" link of the project before it and the "Previous" link of the project after it.
6. Open a pull request.

## Writing good modules

- **One idea per module.** Each module should take a single sitting (roughly 30–90 minutes) and end with something that runs.
- **Starter and solution must both run.** `starter/` is the point where the learner begins, and `solution/` is a finished, working reference.
- **Chain the modules.** Learners keep working in their own code from module to module. A module's `starter/` must match the previous module's `solution/`, so anyone who falls behind can catch up.
- **Build on earlier projects.** Reuse and reinforce what earlier projects taught instead of re-teaching it, and link back to where it was taught.
- **Comment the solution code.** Explain *why*, not just *what*. The solution is a teaching tool.
- **Link outside resources on purpose.** If an article, video or doc already explains a concept well, link it in the module's "Resources" section and say what the reader should take from it.
- **End with challenges.** Optional stretch goals give stronger students something extra without slowing everyone else down.

## Naming conventions

- Folders use `kebab-case` with a two-digit prefix that sets the order: `01-hello-world`.
- Every project and every module has a `README.md`.
- Reference code goes in `solution/` and starting code in `starter/`, inside each module.

## Choosing a language

Use the language that best fits the project, and say why in the project README. When two choices are reasonable, prefer the one more club members already know.
