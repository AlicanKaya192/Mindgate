## What changed and why?

<!-- A short description of the change and the reason for it. -->

## Related issue

<!-- Example: Closes #12 -->

## Type

- [ ] Bug fix
- [ ] Guard change
- [ ] Installer or uninstaller
- [ ] New or changed skill, agent or rule
- [ ] Translation
- [ ] Documentation

## Checks

- [ ] `setup/installer_test.py` passes
- [ ] `vault/_system/run_tests.py` passes
- [ ] User-facing text changed in **both** English (`vault/`, `setup/`) and Turkish (`locales/tr/`)
- [ ] No personal data: names, paths, e-mail addresses, machine names, secrets, note content
- [ ] A guard change comes with a test for the harmful case it must still stop
- [ ] If the installer's writes changed: `--dry-run` summary pasted below

<!-- Paste the relevant --dry-run lines here if needed. -->
