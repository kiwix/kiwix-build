# Download dependencies archive action

This action download dependencies archive made by kiwix-build.
It is intended to be used in projects using theses dependencies

## Inputs

### `base_url`

The base url where we can download the archive.
This input is provided for greater customization but you probably shouldn't set it.

### `os_name`

The os "name" on which the compilation is done.
By default this use the `OS_NAME` env var, which is set in the docker file.


### `target_platform`

**Required** The targeted platform. Must be provided. Values are kind of :
- native_dyn
- android_arm
- ...

### `project`

The name of the project being compiled.
By default, the name of the repository.


### `branch`

The name of the "branch" to try to download (`/dev_preview/<branch>`).
By default, the current branch on which the action is run.

### `extract_dir`

Where to extract the dependencies archive. By default it is `$HOME`


## Example usage

```yaml
uses: kiwix/kiwix-build/actions/dl_deps_archive@main
with:
  target_platform: ${{ matrix.target_platform }}
```

```
uses: kiwix/kiwix-build/actions/dl_deps_archive@main
with:
  target_platform: native_mixed
  os_name: windows
```
