# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Exercise the workflow's actual smoke-test commands against profile fixtures."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

import yaml

root = Path(__file__).resolve().parent.parent
workflow = yaml.safe_load((root / ".github/workflows/Toolkit-Release.yml").read_text())
steps = workflow["jobs"]["release"]["steps"]
smoke = next(step["run"] for step in steps if step["name"] == "Smoke test release metadata")


def executable(path, body):
    path.write_text("#!/bin/sh\nset -eu\n" + body)
    path.chmod(0o755)


with tempfile.TemporaryDirectory() as directory:
    work = Path(directory)
    (work / "dist").mkdir()
    (work / "bin").mkdir()
    executable(work / "bin/uname", "echo aarch64\n")
    # The real Ubuntu runner provides coreutils timeout; keep this test portable.
    executable(work / "bin/timeout", 'test "$1" = 15s\nshift\nexec "$@"\n')
    env = dict(os.environ, PATH=f"{work / 'bin'}:{os.environ['PATH']}",
               BINARY_NAME="toolkit-ui", RELEASE_VERSION="v0.1.0",
               BUILD_COMMIT="0123456789", BUILD_TIME="2026-09-27T00:00:00Z")
    metadata = dict(name="toolkit-ui", version=env["RELEASE_VERSION"],
                    commit=env["BUILD_COMMIT"], build_time=env["BUILD_TIME"], platform="linux/arm64")
    cases = {
        "toolkit-ui": ('test "$#" = 1 && test "$1" = -version',
                       'toolkit-ui v0.1.0 (commit 0123456789, built 2026-09-27T00:00:00Z)'),
        "buildinfo": ('test "$#" = 3 && test "$1" = version && test "$2" = --format && test "$3" = json',
                      json.dumps(metadata)),
        "modpack-toolkit": ('test "$#" = 1 && test "$1" = version', 'v0.1.0'),
    }
    for profile, (arguments, output) in cases.items():
        for valid in (True, False):
            value = output if valid else output.replace("v0.1.0", "dev")
            executable(work / "dist/toolkit-ui-linux-arm64", arguments + "\nprintf '%s\\n' " + shlex.quote(value) + "\n")
            result = subprocess.run(["bash", "-c", smoke], cwd=work,
                                    env=dict(env, RELEASE_PROFILE=profile), capture_output=True, text=True, timeout=20)
            if (result.returncode == 0) != valid:
                raise AssertionError(f"{profile}, valid={valid}: {result.stdout}\n{result.stderr}")
    validate = next(step["run"] for step in workflow["jobs"]["test"]["steps"] if step["name"] == "Validate release request")
    executable(work / "bin/gh", "echo 'HTTP 404' >&2\nexit 1\n")
    env.update(DEFAULT_BRANCH="main", GITHUB_REF="refs/heads/main", GITHUB_REPOSITORY="TeamKugimiya/toolkit-ui")
    for profile in cases:
        for has_notes in (True, False):
            (work / "CHANGELOG.md").write_text("## v0.1.0（2026-09-27）\nRelease notes\n" if has_notes else "## 未發佈\n")
            result = subprocess.run(["bash", "-c", validate], cwd=work,
                                    env=dict(env, RELEASE_PROFILE=profile), capture_output=True, timeout=20)
            assert (result.returncode == 0) == (has_notes or profile == "modpack-toolkit"), (profile, has_notes, result.stderr)
    # UI checks must reject stale commit and build-time metadata too.
    arguments, output = cases["toolkit-ui"]
    for old in ("0123456789", "2026-09-27T00:00:00Z"):
        executable(work / "dist/toolkit-ui-linux-arm64", arguments + "\nprintf '%s\\n' " + shlex.quote(output.replace(old, "unknown")) + "\n")
        result = subprocess.run(["bash", "-c", smoke], cwd=work,
                                env=dict(env, RELEASE_PROFILE="toolkit-ui"), capture_output=True, timeout=20)
        assert result.returncode != 0, f"accepted stale {old}"
print("Release profile smoke tests passed (all three profiles; invalid metadata rejected).")
