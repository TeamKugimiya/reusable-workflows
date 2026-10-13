# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""直接執行發佈 workflow 的 shell，以假的 gh／curl 驗證更新與取得端合約。"""
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import zipfile

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github/workflows/TranslationPack-Publish-Source.yml"
BASH = os.environ.get("PUBLISH_TEST_BASH", "bash")
ASSET = "Example+Source.zip"
NEXT = "Example+Source.next.zip"
SHA = "a" * 40
BRANCH = "main"
BODY = f"""此 Release 提供 translation-toolkit 的外部來源內容 `{ASSET}`，**不是資源包**，請勿直接放進遊戲。

其他翻譯包可透過 reusable-workflows 的 `external_sources`，在驗證與建構前下載它並解壓到 `Translation/`。內容在 {BRANCH} 更新後自動覆蓋，對應的 commit 即 `latest` tag 所指向的 commit。
"""
FILES = {"Z-Pack/metadata.json": b"{}", "A-Pack/guide/空白 檔名.json": b'{"new":true}',
         "A-Pack/guide/.hidden": b"hidden", "-Pack/file.json": b"{}"}
FAKE_GH = r'''
import json, os, sys
from pathlib import Path
from urllib.parse import quote
path = Path(os.environ["FAKE_STATE"])
state = json.loads(path.read_text())
args = sys.argv[1:]
state["calls"].append(args)
def save():
    path.write_text(json.dumps(state, ensure_ascii=False))
def fail(message):
    save()
    print(message, file=sys.stderr)
    sys.exit(1)
def value(flag):
    return args[args.index(flag) + 1]
def field(name):
    return next(a.split("=", 1)[1] for a in args if a.startswith(name + "="))
if args[0] == "api":
    endpoint = next(a for a in args if a.startswith("repos/"))
    assert endpoint.startswith("repos/Example/Source/")
    method = value("-X") if "-X" in args else "GET"
    if endpoint.endswith("/commits/" + quote(state["branch"], safe="")) and method == "GET":
        assert value("--jq") == ".sha"
        if state["scenario"] == "head-error":
            fail("模擬 HEAD 查詢失敗")
        print(state["head"])
    elif endpoint.endswith("/releases/tags/latest") and method == "GET":
        code = state["query_error"] or (200 if state["exists"] else 404)
        if "--include" in args:
            print(f"HTTP/2.0 {code} 模擬回應\r\nContent-Type: application/json\r\n\r")
        if code != 200:
            print(json.dumps({"message": "模擬錯誤", "status": str(code)}))
            fail(f"gh: 模擬錯誤 (HTTP {code})")
        print(json.dumps({"assets": state["assets"]}))
    elif "/releases/assets/" in endpoint:
        item = next(a for a in state["assets"] if a["id"] == int(endpoint.rsplit("/", 1)[1]))
        if method == "DELETE":
            state["events"].append("delete:" + item["name"])
            state["assets"].remove(item)
        elif method == "PATCH":
            state["events"].append("rename:" + item["name"])
            if state["scenario"] == "rename-error":
                fail("模擬改名失敗")
            assert not any(a["name"] == field("name") for a in state["assets"])
            item["name"] = field("name")
        else:
            fail("非預期的 asset 方法")
    elif endpoint.endswith("/git/refs/tags/latest") and method == "PATCH":
        if state["scenario"] == "tag-error":
            fail("模擬移動 tag 失敗")
        assert field("force") == "true"
        state["tag"] = field("sha")
        state["events"].append("tag")
    else:
        fail("非預期 API：" + repr(args))
elif args[:3] == ["release", "create", "latest"]:
    assert not state["exists"] and value("--repo") == "Example/Source"
    assert "--latest=false" in args and "--draft=false" in args and "--prerelease=false" in args
    state.update(exists=True, title=value("--title"), target=value("--target"),
                 body=Path(value("--notes-file")).read_text())
    state["created_body"] = state["body"]
    if state["tag"] is None:
        state["tag"] = value("--target")
    state["events"].append("create")
elif args[:3] == ["release", "upload", "latest"]:
    assert value("--repo") == "Example/Source" and state["exists"]
    upload = Path(args[3])
    assert not any(a["name"] == upload.name for a in state["assets"])
    state["events"].append("upload:" + upload.name)
    if state["scenario"] == "upload-error":
        fail("模擬上傳失敗")
    state["assets"].append({"id": state["next_id"], "name": upload.name, "content": upload.read_bytes().hex()})
    state["next_id"] += 1
elif args[:3] == ["release", "edit", "latest"]:
    assert value("--repo") == "Example/Source" and "--title" not in args
    if state["scenario"] == "body-error":
        fail("模擬更新 body 失敗")
    state["body"] = Path(value("--notes-file")).read_text()
    state["events"].append("body")
else:
    fail("非預期 gh 指令：" + repr(args))
save()
'''


def executable(path, body):
    path.write_text(f"#!{sys.executable}\n" + body)
    path.chmod(0o755)


class Sandbox:
    def __init__(self, directory, scenario="normal", asset=ASSET, ref=None, branch=BRANCH):
        self.work = Path(directory)
        self.project = self.work / "nested project"
        self.translation = self.project / "Translation"
        self.translation.mkdir(parents=True)
        for name, content in FILES.items():
            path = self.translation / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        (self.translation / "A-Pack/empty").mkdir()
        (self.translation / "ignored.txt").write_text("最上層檔案不打包")
        self.bin = self.work / "bin"
        self.bin.mkdir()
        executable(self.bin / "gh", FAKE_GH)
        self.state_path = self.work / "state.json"
        assets = [{"id": 1, "name": ASSET, "content": "old"}]
        if scenario == "residue":
            assets.append({"id": 2, "name": NEXT, "content": "residue"})
        self.initial = dict(scenario=scenario, branch=branch, head="newer" if scenario == "stale" else SHA,
                            query_error=int(scenario) if scenario.isdigit() else None,
                            exists=scenario != "missing", assets=[] if scenario == "missing" else assets,
                            tag=None if scenario == "missing" else "old", next_id=3,
                            title="保留原標題", body="old", calls=[], events=[])
        self.state_path.write_text(json.dumps(self.initial))
        self.context = {"inputs.asset_name": asset, "inputs.project_path": str(self.project),
                        "github.token": "fake-token", "github.repository": "Example/Source",
                        "github.sha": SHA, "github.ref": ref or f"refs/heads/{branch}",
                        "github.event.repository.default_branch": branch}
        self.executed = []

    def run(self, max_bytes=None):
        workflow = yaml.safe_load(WORKFLOW.read_text())
        job = workflow["jobs"]["publish"]
        outputs, logs = {}, []
        for index, step in enumerate(job["steps"]):
            if "if" in step:
                match = re.fullmatch(r"\$\{\{ steps\.(\w+)\.outputs\.(\w+) == 'true' \}\}", step["if"])
                assert match, f"未支援的條件：{step['if']}"
                if outputs.get((match[1], match[2])) != "true":
                    continue
            self.executed.append(step["name"])
            if "run" not in step:
                continue  # checkout 由暫存專案取代，其餘步驟全部執行真實 shell。
            assert "${{" not in step["run"], "run 不得直接內插 expression"
            output = self.work / f"output-{index}"
            output.write_text("")
            env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                       RUNNER_TEMP=str(self.work), GITHUB_OUTPUT=str(output), FAKE_STATE=str(self.state_path))
            for key, expression in {**job.get("env", {}), **step.get("env", {})}.items():
                match = re.fullmatch(r"\$\{\{ (.*?) \}\}", str(expression))
                env[key] = self.context[match[1]] if match else str(expression)
            # 只由本機 harness 縮小界線；正式 YAML 的上限必須是固定值，不能引用 caller input。
            if max_bytes is not None:
                env["MAX_BYTES"] = str(max_bytes)
            result = subprocess.run([BASH, "-euo", "pipefail", "-c", step["run"]], cwd=self.work,
                                    env=env, capture_output=True, text=True, timeout=30)
            logs.append(result.stdout + result.stderr)
            for line in output.read_text().splitlines():
                key, value = line.split("=", 1)
                outputs[(step.get("id"), key)] = value
            if result.returncode:
                return result.returncode, "".join(logs)
        return 0, "".join(logs)

    def state(self):
        return json.loads(self.state_path.read_text())

    def roundtrip(self):
        """只替換網路邊界；digest、zip 檢查與移入都使用取得端原始程式。"""
        archive = self.work / ASSET
        digest = "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()
        release = {"assets": [{"name": ASSET, "digest": digest, "updated_at": "2026-10-13"}]}
        executable(self.bin / "gh", f"print({json.dumps(release)!r})\n")
        executable(self.bin / "curl", "import shutil, sys\n"
                   f"shutil.copyfile({str(archive)!r}, sys.argv[sys.argv.index('--output') + 1])\n")
        destination = self.work / "consumer/Translation"
        destination.mkdir(parents=True)
        env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                   SOURCES=f"https://github.com/Example/Source/releases/download/latest/{ASSET}",
                   PROJECT_PATH=str(destination.parent), GH_TOKEN="fake-token",
                   GITHUB_STEP_SUMMARY=str(self.work / "summary"))
        result = subprocess.run([BASH, str(ROOT / ".github/actions/fetch-external-sources/fetch.sh")],
                                env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        actual = {str(p.relative_to(destination)): p.read_bytes() for p in destination.rglob("*") if p.is_file()}
        assert actual == FILES, "往返後的檔案內容不同"
        expected_dirs = {str(p.relative_to(self.translation)) for p in self.translation.rglob("*") if p.is_dir()}
        assert {str(p.relative_to(destination)) for p in destination.rglob("*") if p.is_dir()} == expected_dirs


def structure():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    call = workflow[True]["workflow_call"]
    assert set(call["inputs"]) == {"asset_name", "project_path", "runs_on"}
    assert call["inputs"]["asset_name"]["required"] is True
    assert all(spec["type"] == "string" for spec in call["inputs"].values())
    assert call["inputs"]["project_path"]["default"] == "."
    assert call["inputs"]["runs_on"]["default"] == "ubuntu-26.04-arm"
    assert not call.get("secrets")
    assert workflow["permissions"] == {"contents": "read"}
    job = workflow["jobs"]["publish"]
    assert job["permissions"] == {"contents": "write"}
    assert job["runs-on"] == "${{ inputs.runs_on }}"
    assert job["concurrency"] == {"group": "publish-external-source", "cancel-in-progress": False}
    steps = job["steps"]
    checkout = next(s for s in steps if s.get("uses", "").startswith("actions/checkout@"))
    validate = yaml.safe_load((ROOT / ".github/workflows/TranslationPack-Validate.yml").read_text())
    assert checkout["uses"] == validate["jobs"]["validate"]["steps"][0]["uses"]
    assert checkout["with"]["persist-credentials"] is False
    assert steps.index(checkout) > 0
    for step in steps[steps.index(checkout):]:
        assert step["if"] == "${{ steps.current.outputs.publish == 'true' }}"
    # 文件必須合併 job 層權限，呼叫端才能取得寫入授權。
    docs = runpy.run_path(str(ROOT / "scripts/gen_workflow_docs.py"))
    rendered = docs["render_doc"](next(w for w in docs["load_workflows"]() if w["path"] == WORKFLOW))
    assert "| `contents` | `write` |" in rendered
    assert "      contents: write" in rendered


def success(scenario, roundtrip=False, branch=BRANCH):
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, scenario, branch=branch)
        code, logs = box.run()
        assert code == 0, logs
        state = box.state()
        archive = box.work / ASSET
        assert state["assets"] == [{"id": 3, "name": ASSET, "content": archive.read_bytes().hex()}]
        assert state["tag"] == SHA and state["body"] == BODY.replace(BRANCH, branch)
        events = ["upload:" + NEXT, "delete:" + ASSET, "rename:" + NEXT, "tag", "body"]
        if scenario == "residue":
            events.insert(0, "delete:" + NEXT)
        elif scenario == "missing":
            events = ["create", "upload:" + NEXT, "rename:" + NEXT, "tag", "body"]
            assert state["title"] == "latest" and state["target"] == SHA and state["created_body"] == BODY
        else:
            assert state["title"] == "保留原標題"
        assert state["events"] == events, state["events"]
        # macOS zip 的 UTF-8 名稱未必設編碼旗標；依實際檔名字節讀取。
        with zipfile.ZipFile(archive, metadata_encoding="utf-8") as zipped:
            assert {n: zipped.read(n) for n in zipped.namelist() if not n.endswith("/")} == FILES
            tops = list(dict.fromkeys(n.split("/")[0] for n in zipped.namelist()))
            assert tops == sorted(tops), tops
        if roundtrip:
            box.roundtrip()


def reject(scenario="normal", asset=ASSET, ref=None, mutation=None, reason="::error::"):
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, scenario, asset, ref)
        if mutation:
            mutation(box.translation)
        code, logs = box.run()
        state = box.state()
        assert code != 0, "應失敗卻成功"
        assert reason in logs, logs
        assert not state["events"], f"失敗前不應寫入 Release：{state['events']}"
        for key in ("assets", "tag", "body", "exists"):
            assert state[key] == box.initial[key], key


def stale():
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, "stale")
        code, logs = box.run()
        assert code == 0 and "::notice::" in logs, logs
        assert not box.state()["events"]
        assert len(box.executed) == 1, box.executed
        assert not (box.work / ASSET).exists()


def interrupted(scenario):
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, scenario)
        code, _ = box.run()
        state = box.state()
        assert code != 0
        assert state["tag"] == "old" and state["body"] == "old"
        if scenario == "upload-error":
            assert state["assets"] == box.initial["assets"], "上傳失敗不得刪掉舊檔"
        else:
            assert [a["name"] for a in state["assets"]] == [NEXT], "保留暫存檔供下次清理"


def no_dirs(translation):
    import shutil
    for entry in translation.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry)


def versioned_file(collision=False, suffix=";1"):
    def mutate(translation):
        (translation / f"A-Pack/file{suffix}").write_bytes(b"versioned")
        if collision:
            (translation / "A-Pack/file").write_bytes(b"original")
    reject(mutation=mutate, reason="::error::一般檔案名稱不得以分號加零個或多個數字結尾")


def semicolon_preserved():
    # 只拒絕會被 unzip 移除的版本號；非數字後綴與目錄本身不應被誤擋。
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory)
        (box.translation / "A-Pack/dir;1").mkdir()
        for name in ("file;1x", "file;abc", "dir;1/file"):
            (box.translation / "A-Pack" / name).write_bytes("保留".encode())
        code, logs = box.run()
        assert code == 0, logs


def size_contract():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    pack = next(s for s in workflow["jobs"]["publish"]["steps"] if s["name"] == "打包內容目錄")
    assert pack.get("env", {}).get("MAX_BYTES") == "209715200", "正式上限必須固定為 200 MiB"
    fetch = ROOT / ".github/actions/fetch-external-sources/fetch.sh"
    result = subprocess.run([BASH, "-c", 'source "$1"; printf "%s" "$MAX_BYTES"', "_", str(fetch)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert result.stdout == pack["env"]["MAX_BYTES"], "發佈與取得端上限必須相同"


def size_boundary(over=False):
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory)
        # 先用真實打包步驟量出小型 fixture 的壓縮大小，再清空假 API 狀態。
        code, logs = box.run()
        assert code == 0, logs
        size = (box.work / ASSET).stat().st_size
        assert size < 1024 * 1024, "界線測試不應建立大型檔案"
        box.state_path.write_text(json.dumps(box.initial))
        code, logs = box.run(max_bytes=size - int(over))
        assert (box.work / ASSET).stat().st_size == size
        state = box.state()
        if over:
            assert code != 0, "壓縮檔超過上限 1 byte 應失敗"
            assert "::error::壓縮檔超過外部來源大小上限" in logs, logs
            assert not state["events"], "超限不得寫入 Release"
            assert state["assets"] == box.initial["assets"] and state["tag"] == "old" and state["body"] == "old"
        else:
            assert code == 0, logs
            assert [a["name"] for a in state["assets"]] == [ASSET]
            assert state["tag"] == SHA and state["body"] == BODY


def missing_branch():
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, branch="", ref="refs/heads/main")
        code, logs = box.run()
        assert code != 0
        assert "::error::此事件沒有 repository.default_branch，無法判斷預設分支；請從 push 或 workflow_dispatch 呼叫" in logs, logs
        assert not box.state()["calls"], "缺少分支資訊時不應呼叫 API"


def recovery(scenario):
    with tempfile.TemporaryDirectory() as directory:
        box = Sandbox(directory, "missing" if scenario == "first-upload-error" else scenario)
        if scenario == "first-upload-error":
            state = box.state()
            state["scenario"] = "upload-error"
            box.state_path.write_text(json.dumps(state))
        code, logs = box.run()
        assert code != 0, f"{scenario} 應先模擬失敗，實際成功：{logs}"
        state = box.state()
        if scenario == "rename-error":
            assert [a["name"] for a in state["assets"]] == [NEXT]
            assert state["tag"] == "old" and state["body"] == "old"
        elif scenario == "first-upload-error":
            assert state["exists"] and not state["assets"]
            assert state["tag"] == SHA and state["body"] == BODY
        elif scenario == "tag-error":
            assert [a["name"] for a in state["assets"]] == [ASSET]
            assert state["tag"] == "old" and state["body"] == "old"
        elif scenario == "body-error":
            assert [a["name"] for a in state["assets"]] == [ASSET]
            assert state["tag"] == SHA and state["body"] == "old"
        previous_events = len(state["events"])
        state["scenario"] = "normal"
        box.state_path.write_text(json.dumps(state))
        code, logs = box.run()
        assert code == 0, logs
        state = box.state()
        assert len(state["assets"]) == 1 and state["assets"][0]["name"] == ASSET
        assert state["assets"][0]["content"] == (box.work / ASSET).read_bytes().hex()
        assert state["tag"] == SHA and state["body"] == BODY
        events = state["events"][previous_events:]
        expected = ["upload:" + NEXT, "delete:" + ASSET, "rename:" + NEXT, "tag", "body"]
        if scenario == "rename-error":
            expected = ["delete:" + NEXT, "upload:" + NEXT, "rename:" + NEXT, "tag", "body"]
        elif scenario == "first-upload-error":
            expected = ["upload:" + NEXT, "rename:" + NEXT, "tag", "body"]
        assert events == expected, events


def documentation(topic):
    action = ROOT / ".github/actions/fetch-external-sources/action.yml"
    target = "../../../docs/example/translation-pack.md#來源專案驗證後發佈內容"
    if topic == "action":
        assert target in action.read_text().splitlines()[0], "action 註解應指向實際 zip 合約章節"
        return
    doc = (action.parent / target.split("#")[0]).resolve().read_text()
    section = doc.split("### 來源專案：驗證後發佈內容\n", 1)[1].split("\n## ", 1)[0]
    assert topic in section, f"來源專案合約缺少：{topic}"


def main():
    cases = [("workflow 結構與 caller 權限", structure),
             ("正常更新", lambda: success("normal")),
             ("清除殘留暫存 asset", lambda: success("residue")),
             ("首次建立 latest", lambda: success("missing")),
             ("發佈與取得往返合約", lambda: success("normal", roundtrip=True)),
             ("過期 run 略過所有後續步驟", stale),
             ("其他分支", lambda: reject(ref="refs/heads/other")),
             ("PR ref", lambda: reject(ref="refs/pull/1/merge")),
             ("HEAD 查詢失敗", lambda: reject("head-error", reason="模擬 HEAD 查詢失敗")),
             ("沒有內容目錄", lambda: reject(mutation=no_dirs)),
             ("點開頭內容目錄", lambda: reject(mutation=lambda p: (p / ".hidden").mkdir())),
             ("內容 symlink", lambda: reject(mutation=lambda p: (p / "A-Pack/link").symlink_to("missing"))),
             ("最上層 symlink 目錄", lambda: reject(mutation=lambda p: (p / "linked").symlink_to(p / "A-Pack"))),
             ("不安全內容目錄名", lambda: reject(mutation=lambda p: (p / "unsafe name").mkdir())),
             ("內容控制字元", lambda: reject(mutation=lambda p: (p / "A-Pack/a\nb").touch())),
             ("內容反斜線", lambda: reject(mutation=lambda p: (p / "A-Pack/a\\b").touch())),
             ("特殊檔案", lambda: reject(mutation=lambda p: os.mkfifo(p / "A-Pack/pipe"))),
             ("上傳失敗保留舊檔", lambda: interrupted("upload-error")),
             ("改名失敗不移 tag", lambda: interrupted("rename-error")),
             ("單檔 VMS 版本號", versioned_file),
             ("VMS 版本號名稱碰撞", lambda: versioned_file(collision=True)),
             ("單獨結尾分號", lambda: versioned_file(suffix=";")),
             ("合法分號名稱不誤擋", semicolon_preserved),
             ("兩端固定 200 MiB 上限", size_contract),
             ("壓縮檔剛好上限", size_boundary),
             ("壓縮檔超過上限 1 byte", lambda: size_boundary(over=True)),
             ("缺少預設分支資訊", missing_branch)]
    for topic in ("action", ";[0-9]*$", "200 MiB", "workflow_dispatch", "repository.default_branch", "不能啟用 immutable releases"):
        cases.append((f"文件合約 {topic}", lambda topic=topic: documentation(topic)))
    for branch in ("main#source", "main%25source", "translations/stable"):
        cases.append((f"分支 URL 編碼 {branch}", lambda branch=branch: success("normal", branch=branch)))
    for scenario in ("rename-error", "first-upload-error", "tag-error", "body-error"):
        cases.append((f"失敗後重跑恢復 {scenario}", lambda scenario=scenario: recovery(scenario)))
    for status in ("500", "403"):
        cases.append((f"Release 查詢 {status}", lambda status=status: reject(status, reason="::error::無法查詢 latest Release")))
    for value in ("", "source", "source.next.zip", "dir/source.zip", ".source.zip", "a b.zip", "a\n.zip", "a;id.zip"):
        cases.append((f"不合法 asset_name {value!r}", lambda value=value: reject(asset=value)))
    failed = 0
    for name, test in cases:
        try:
            test()
        except Exception as error:
            failed += 1
            print(f"FAIL {name}：{error}", file=sys.stderr)
        else:
            print(f"ok  {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
