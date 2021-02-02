# History

The changelog is updated on release.
There is no need to add news entries for pull requests.

## Generation instructions:

Run in bash:

```bash
 git log HEAD --not `git describe --tags --abbrev=0` --pretty="* %B" > history/newversion.rst
```

Prune out anything not relevant to end users then optionally rebuild the docs.
