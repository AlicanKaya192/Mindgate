# Unity

The source pack targets Unity 6.3 LTS (6000.3); version and behavior information is the owner's declaration of 11 November 2026 and was not independently verified.

## Read the project first
- Version: `ProjectSettings/ProjectVersion.txt`. Packages: `Packages/manifest.json` and the lock file `Packages/packages-lock.json`.
- Before adding a package, look at the lock file and ask the user.
- Scene, prefab and `.meta` files are in text format (Unity YAML). Verify a change with grep: reference, GUID, field name.

## Verification
**Scope:** Building and testing from the command line.

- The build is done with `-buildTarget` and `-executeMethod`. The called method reports the result with an explicit exit code; in this case `-quit` is not given together.
- `BuildPlayer` returning does not mean success; check that it is `BuildResult.Succeeded`.
- Read the test result from the NUnit XML, do not trust the exit code alone. Search the log for `error CS`.
- If the test filter is wrong, no test runs and the result looks clean; read the number of tests that ran.
- The source has read-only check scripts (`check_unity_project.py`, `check_unity_build_size.py`, `build_report.py`); these were not read and not installed.

## Pitfalls
- `?.`, `??` and `is null` do not catch a destroyed (Destroy) Unity object. Check with `if (obj)`.
- When the name of a serialized field changes, the value in the Inspector is lost. Declare the old name with `FormerlySerializedAs`.
- A "Missing script" warning is the loss of the `.meta` file or the GUID. Move the file together with its `.meta`.
- IL2CPP code stripping removes only code called by reflection. Write the types to keep into `link.xml`.
- A misspelled Animator parameter gives no error, it silently does not work. On the input side `FindAction` is the same.
- A change made in play mode is either lost or (in assets such as a ScriptableObject) becomes permanent and leaks. In tests change the asset by copying it.
- `Lerp` clamps outside 0..1; overshoot easing is not visible.

## Build size
- Start with an upper limit of 2048 for texture `MaxSize`, raise if needed.
- LZ4HC compression enlarges the Steam patch.
- A texture embedded in glTF skips Unity's texture compression.
- itch.io accepts 200 MB per file (`workflows.md`).
- The source's size script suggests running a glTF tool with `npx`. This skill does not install or run that tool; if it is needed, say what is needed and why, and ask permission (#35).
