# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""以假的 gh／curl 驅動 fetch-external-sources 的 fetch.sh。"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import zipfile
import yaml

root = Path(__file__).resolve().parent.parent
script = root / ".github/actions/fetch-external-sources/fetch.sh"
URL = "https://github.com/TeamKugimiya/MMLP-CN-to-ZW/releases/download/latest/MMLP-CN-to-ZW.zip"
SECOND_URL = URL.replace("MMLP-CN-to-ZW.zip", "second.zip")

GOOD = [
    ("MMLP-A/", b""),
    ("MMLP-A/metadata.json", b"{}"),
    ("MMLP-A/1.20/zh_tw.json", b"{}"),
    ("MMLP-A/1.20/guide/空白 檔名.json", b"{}"),
    ("MMLP-A/1.20/guide/literal^J.json", b"literal caret"),
    ("MMLP-B/metadata.json", b"{}"),
]


def executable(path, body):
    path.write_text("#!/bin/sh\nset -eu\n" + body)
    path.chmod(0o755)


def build_zip(path, entries):
    """entries 為 (name, data[, kind[, create_system[, mode]]])。"""
    with zipfile.ZipFile(path, "w") as archive:
        for entry in entries:
            info = zipfile.ZipInfo(entry[0])
            info.create_system = entry[3] if len(entry) > 3 else 3
            if len(entry) > 2 and entry[2] == "symlink":
                mode = 0o120777
            elif entry[0].endswith("/"):
                mode = 0o40755
            else:
                mode = 0o100644
            info.external_attr = (entry[4] if len(entry) > 4 else mode) << 16
            archive.writestr(info, entry[1])


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class Sandbox:
    """一個翻譯專案、假的 gh 與 curl。curl 依呼叫順序回傳 downloads 中的檔案。"""

    def __init__(self, directory, existing=()):
        self.work = Path(directory)
        self.translation = self.work / "project/Translation"
        self.translation.mkdir(parents=True)
        for name in existing:
            (self.translation / name).mkdir()
            (self.translation / name / "keep.json").write_text('{"sentinel": "must remain unchanged"}')
        self.bin = self.work / "bin"
        self.bin.mkdir()

    def snapshot(self):
        entries = []
        for path in self.translation.rglob("*"):
            kind = stat.S_IFMT(path.lstat().st_mode)
            content = None
            if stat.S_ISLNK(kind):
                content = os.readlink(path)
            elif stat.S_ISREG(kind):
                content = sha256(path)
            entries.append((str(path.relative_to(self.translation)), kind, content))
        return sorted(entries)

    def run(self, sources, downloads, assets):
        (self.work / "release.json").write_text(json.dumps({"assets": assets}))
        (self.work / "downloads").write_text("".join(f"{path}\n" for path in downloads))
        (self.work / "counter").write_text("0")
        executable(self.bin / "gh", f'test "$1" = api\ncat "{self.work}/release.json"\n')
        executable(self.bin / "curl", f"""
out=""
while [ "$#" -gt 0 ]; do
  if [ "$1" = --output ]; then out=$2; shift; fi
  shift
done
n=$(($(cat "{self.work}/counter") + 1))
echo "$n" > "{self.work}/counter"
cp "$(sed -n "${{n}}p" "{self.work}/downloads")" "$out"
""")
        env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", SOURCES=sources,
                   PROJECT_PATH=str(self.work / "project"),
                   GITHUB_STEP_SUMMARY=str(self.work / "summary.md"))
        return subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=30)


def asset(path, name="MMLP-CN-to-ZW.zip"):
    return {"name": name, "digest": sha256(path), "updated_at": "2026-10-11T00:00:00Z"}


# 成功：解壓（含空白與非 ASCII 檔名）、略過註解與空行、summary 紀錄
with tempfile.TemporaryDirectory() as directory:
    box = Sandbox(directory)
    source = box.work / "source.zip"
    build_zip(source, GOOD)
    result = box.run(f"  # MMLP\n\n{URL}\n", [source], [asset(source)])
    assert result.returncode == 0, result.stderr
    assert (box.translation / "MMLP-A/1.20/guide/空白 檔名.json").is_file()
    assert (box.translation / "MMLP-B/metadata.json").is_file()
    assert (box.translation / "MMLP-A/1.20/guide/literal^J.json").read_bytes() == b"literal caret"
    assert not list(box.translation.glob(".external-*")), "成功後不應殘留暫存目錄"
    summary = (box.work / "summary.md").read_text()
    assert sha256(source)[len("sha256:"):] in summary and "MMLP-A" in summary and "MMLP-B" in summary
    print("ok  good")


def expect_failure(name, sources, reason, entries=GOOD, existing=(), mutate=None):
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, existing)
        source = box.work / "source.zip"
        build_zip(source, entries)
        assets = [asset(source)]
        if mutate:
            mutate(assets[0])
        before = box.snapshot()
        result = box.run(sources, [source], assets)
        assert result.returncode != 0, f"{name}: 應失敗\n{result.stdout}"
        assert f"::error::{reason}" in result.stderr, f"{name}: 失敗原因不符\n{result.stderr}"
        assert box.snapshot() == before, f"{name}: 失敗後 Translation/ 被改動"
        assert not list(box.translation.glob(".external-*")), f"{name}: 殘留暫存目錄"
        print(f"ok  {name}")


expect_failure("non github url", "https://example.com/x.zip", "外部來源必須是 GitHub Release 檔案網址")
expect_failure("dot segment url", "https://github.com/TeamKugimiya/../releases/download/latest/x.zip",
               "外部來源網址含有不安全的路徑片段")
expect_failure("only comments", "# 註解\n\n", "external_sources 沒有任何來源網址")
expect_failure("absolute path", URL, "zip 項目路徑不安全", [("/etc/passwd", b"x")])
expect_failure("parent segment", URL, "zip 項目路徑不安全", [("MMLP-A/../../evil", b"x")])
expect_failure("backslash", URL, "zip 項目路徑不安全", [("MMLP-A\\evil", b"x")])
expect_failure("symlink", URL, "zip 含有 symlink", [("MMLP-A/link", b"/etc/passwd", "symlink")])
expect_failure("top-level file", URL, "zip 最上層只能是目錄", [("README.md", b"x")])
expect_failure("existing directory", URL, "Translation/MMLP-B 已存在", existing=("MMLP-B",))
expect_failure("asset missing", URL, "Release 中找不到檔案", mutate=lambda a: a.update(name="other.zip"))
expect_failure("digest missing", URL, "Release 檔案 MMLP-CN-to-ZW.zip 沒有 SHA-256 digest",
               mutate=lambda a: a.pop("digest"))
expect_failure("digest mismatch", URL, "SHA-256 不符",
               mutate=lambda a: a.update(digest="sha256:" + "0" * 64))

expect_failure("vms symlink", URL, "zip 含有 symlink 或特殊檔案",
               [("MMLP-A/link", b"../../../../../../etc/passwd", "symlink", 2)], existing=("Existing",))
expect_failure("newline name", URL, "zip 項目名稱含有控制字元",
               [("MMLP-A/a\nb", b"first")], existing=("Existing",))
expect_failure("newline collision", URL, "zip 項目名稱含有控制字元",
               [("MMLP-A/a\nb", b"first"), ("MMLP-A/ab", b"second")], existing=("Existing",))
expect_failure("control character", URL, "zip 項目名稱含有控制字元",
               [("MMLP-A/.\x01./evil", b"x")], existing=("Existing",))
expect_failure("normalized name collision", URL,
               "解壓後的檔案數與 zip 不符（檔名可能含有控制字元或彼此衝突）",
               [("MMLP-A/./ab", b"first"), ("MMLP-A/ab", b"second")], existing=("Existing",))
expect_failure("unreadable staging directory", URL, "zip 含有 symlink 或特殊檔案",
               [("MMLP-A/", b"", "directory", 3, 0o40000),
                ("MMLP-A/link", b"../../../../../../etc/passwd", "symlink", 2)], existing=("Existing",))
expect_failure("dot top-level", URL, "zip 最上層目錄不得以 . 開頭：.external-abc",
               [(".external-abc/metadata.json", b"{}")], existing=("Existing",))

# 直接驗證落地檢查，避免解壓前的拒絕遮住第二道檢查。
with tempfile.TemporaryDirectory() as directory:
    box = Sandbox(directory, ("Existing",))
    source = box.work / "source.zip"
    build_zip(source, [(".external-abc/metadata.json", b"{}")])
    staging = box.work / "staging"
    (staging / ".external-abc").mkdir(parents=True)
    (staging / ".external-abc/metadata.json").write_bytes(b"{}")
    before = box.snapshot()
    result = subprocess.run(["bash", "-c", 'source "$1"; check_staging "$2" "$3" "$4"',
                             "_", str(script), str(source), str(staging), str(box.translation)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode != 0, "落地的點開頭目錄應被拒絕"
    assert "::error::zip 最上層目錄不得以 . 開頭：.external-abc" in result.stderr, result.stderr
    assert box.snapshot() == before
    assert not list(box.translation.glob(".external-*"))
    print("ok  dot staging top-level")

# find -exec ... \; 不保證傳遞 chmod 的失敗；清理仍須嘗試移除 staging。
with tempfile.TemporaryDirectory() as directory:
    box = Sandbox(directory, ("Existing",))
    source = box.work / "source.zip"
    build_zip(source, GOOD)
    executable(box.bin / "chmod", "exit 1\n")
    before = box.snapshot()
    result = box.run(URL, [source], [asset(source)])
    assert result.returncode != 0, "chmod 失敗時不得移入內容"
    assert "::error::無法調整暫存目錄權限" in result.stderr, result.stderr
    assert "::warning::無法調整暫存目錄權限" in result.stderr, result.stderr
    assert box.snapshot() == before, "chmod 失敗後 Translation/ 被改動"
    assert not list(box.translation.glob(".external-*")), "chmod 失敗後殘留 staging"
    print("ok  chmod failure")

# 第二個目錄移入失敗時，也必須回復同一來源已移入的第一個目錄。
with tempfile.TemporaryDirectory() as directory:
    box = Sandbox(directory, ("Existing",))
    source = box.work / "source.zip"
    build_zip(source, GOOD)
    executable(box.bin / "mv", f"""
counter="{box.work}/move-counter"
n=0
if [ -f "$counter" ]; then n=$(cat "$counter"); fi
n=$((n + 1))
echo "$n" > "$counter"
if [ "$n" -eq 2 ]; then exit 1; fi
exec "{shutil.which('mv')}" "$@"
""")
    before = box.snapshot()
    result = box.run(URL, [source], [asset(source)])
    assert result.returncode != 0, "第二個目錄的 mv 應失敗"
    assert box.snapshot() == before, "移入失敗後應回復同一來源已移入的內容"
    assert "::error::無法移入內容目錄" in result.stderr, result.stderr
    assert not list(box.translation.glob(".external-*")), "移入失敗後殘留暫存目錄"
    print("ok  promotion failure rollback")

# 第二個來源與第一個解出同名目錄：失敗且不覆蓋第一個來源的內容
with tempfile.TemporaryDirectory() as directory:
    box = Sandbox(directory)
    first, second = box.work / "first.zip", box.work / "second.zip"
    build_zip(first, GOOD)
    build_zip(second, [("MMLP-B/metadata.json", b'{"second": true}')])
    result = box.run(f"{URL}\n{SECOND_URL}\n", [first, second], [asset(first), asset(second, "second.zip")])
    assert result.returncode != 0, "第二個來源的同名目錄應失敗"
    assert "::error::Translation/MMLP-B 已存在" in result.stderr, result.stderr
    assert (box.translation / "MMLP-B/metadata.json").read_bytes() == b"{}"
    for name, data in GOOD:
        if not name.endswith("/"):
            assert (box.translation / name).read_bytes() == data
    assert not list(box.translation.glob(".external-*")), "第二個來源失敗後殘留暫存目錄"
    print("ok  overlapping second source")

ACTION = "TeamKugimiya/reusable-workflows/.github/actions/fetch-external-sources@"
for workflow_name, job in (("TranslationPack-Validate", "validate"), ("TranslationPack-Build", "build-packs")):
    workflow = yaml.safe_load((root / f".github/workflows/{workflow_name}.yml").read_text())
    inputs = workflow[True]["workflow_call"]["inputs"]  # PyYAML 把 on 解析成 True
    assert inputs["external_sources"]["type"] == "string", workflow_name
    assert inputs["external_sources"]["default"] == "", workflow_name
    steps = workflow["jobs"][job]["steps"]
    names = [step.get("uses", "") for step in steps]
    fetch = next(i for i, uses in enumerate(names) if uses.startswith(ACTION))
    setup = next(i for i, uses in enumerate(names) if "setup-toolkit" in uses)
    checkout = next(i for i, uses in enumerate(names) if uses.startswith("actions/checkout@"))
    assert checkout < fetch < setup, workflow_name
    assert steps[fetch]["if"] == "${{ inputs.external_sources != '' }}", workflow_name
    assert steps[fetch]["with"]["sources"] == "${{ inputs.external_sources }}", workflow_name
    if job == "validate":
        assert steps[fetch]["with"]["project_path"] == "${{ inputs.project_path }}", workflow_name
    else:
        assert "project_path" not in steps[fetch]["with"], workflow_name
    print(f"ok  {workflow_name} wiring")
