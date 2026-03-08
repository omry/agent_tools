Never run `git push --force` or `git push --force-with-lease` unless I explicitly request it in that turn.
Never run `git reset --hard` unless I explicitly request it in that turn.
Before starting a new task, check whether the git worktree is dirty.
If there are pending changes and they are not ready to commit, call that out and stop.
If there are pending changes and they are ready to commit, commit them first, then continue working from a clean tree.
