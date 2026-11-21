# Desktop app bundles

Standalone builds of the spektrafilm GUI, made with
[PyInstaller](https://pyinstaller.org/). End users do not need Python.

## CI/CD

- `.github/workflows/ci.yml` runs the test suite on Linux, macOS and Windows
  and builds the sdist/wheel on every push to `main` and on pull requests.
- `.github/workflows/release.yml` builds the bundles on all three platforms,
  starts each one in smoke-test mode, and uploads them as workflow artifacts.
  Run it manually from the Actions tab, or push a version tag to also publish
  a GitHub Release with the bundles, sdist and wheel attached:

  ```bash
  git tag v0.3.4
  git push origin v0.3.4
  ```

| Platform | Artifact |
|---|---|
| Linux x86_64 | `spektrafilm-<version>-linux-x86_64.tar.gz` (run `spektrafilm/spektrafilm`) |
| macOS Apple silicon | `spektrafilm-<version>-macos-arm64.dmg` |
| Windows x86_64 | `spektrafilm-<version>-windows-x86_64.zip` (run `spektrafilm\spektrafilm.exe`) |

The macOS app is ad-hoc signed, not notarized. After copying it to
Applications, clear the quarantine flag once:

```bash
xattr -dr com.apple.quarantine /Applications/spektrafilm.app
```

## Building locally

```bash
uv venv --python 3.13
source .venv/bin/activate        # Windows: .venv\Scripts\activate
uv pip install . "pyinstaller>=6.11"
pyinstaller --noconfirm packaging/spektrafilm.spec
```

The bundle lands in `dist/` (`dist/spektrafilm.app` on macOS). To check that
it starts, run it with `SPEKTRAFILM_SMOKE_TEST=1`: it builds the GUI, runs a
small simulation and exits with status 0 on success.
