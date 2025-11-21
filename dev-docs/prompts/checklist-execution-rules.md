# Task List Management

Guidelines for managing task lists in markdown files to track progress when working on ongoing development checklist palns.

## Task Implementation
- **One sub-task at a time:** Do **NOT** start the next sub‑task until you ask the user for permission and they say "yes" or "y"
- Make sure to always be surgical with your implementation by work on one task/subtask at a time and don't take too large chunks of work in one go.
- Do NOT overwrite the entire file or very large chunk of code to avoid unintentional broken/altered code. 

- **Completion protocol:**  
  1. When you finish a **sub‑task**, immediately mark it as completed by changing `[ ]` to `[x]`.

  2. Update the last work to the progress tracking document @dev-docs/task-completion-update.txt

  3. Once all the subtasks are marked completed and changes have been committed, mark the **parent task** as completed.

- Stop after each sub‑task and wait for the user's go‑ahead.


## Task List Maintenance

1. **Update the task list as you work:**
   - Mark tasks and subtasks as completed (`[x]`) per the protocol above.
   - Add new tasks if new issues arise during the refactoring process.

2. **Maintain the "Relevant Files" section:**
   - List every file created or modified.
   - Give each file a one‑line description of its purpose.

## AI Instructions

When working with task lists, the AI must:

1. Regularly update the task list file after finishing any significant work.
2. Follow the completion protocol:
   - Mark each finished **sub‑task** `[x]`.
   - Mark the **parent task** `[x]` once **all** its subtasks are `[x]`.
   - Update the latest work to the progress tracking document @dev-docs/task-completion-update.txt
3. Add newly discovered tasks if new issues arise during the refactoring process.
4. Keep "Relevant Files" section accurate and up to date.
5. Before starting work, always make sure to firstly check which sub‑task is next.
6. After implementing a sub‑task, update the file and then pause for user approval.
