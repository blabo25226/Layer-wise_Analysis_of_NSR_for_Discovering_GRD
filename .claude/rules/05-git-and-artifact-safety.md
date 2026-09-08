# Git and Artifact Safety

- Check `git status --short` before and after work.
- Never use `git reset --hard`.
- Never force push.
- Never destroy another user/agent's uncommitted work.
- Never overwrite prior `results/runs/` or GPU_RUN reports.
- Use new run IDs and cycle IDs.
- Record branch and commit in manifests.
- Keep commits coherent when committing.
- Large artifacts do not need to be committed; preserve hashes and paths instead.
