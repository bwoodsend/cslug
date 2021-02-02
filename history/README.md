# History

The changelog is updated on release.
There is no need to add news entries for pull requests.

## Generation instructions:

Run in bash:

```bash
 git log HEAD --not `git log --grep "Release v" -n1 --pretty="%H"` --pretty="* %B" > history/newversion.rst
```

Prune out anything not relevant to end users, fixup ReST syntax
then check it in and optionally rebuild the docs.
