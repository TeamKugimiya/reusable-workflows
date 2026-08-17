# 翻譯包呼叫端 workflow 範例

這份文件是給個別翻譯包 repo（例如 `ModsTranslationPack`、`ParaTranslationPack`）放在 `.github/workflows/` 的範例。Reusable workflow 本身只能定義 `workflow_call`，呼叫端要自行定義觸發條件、`pack_name` 與發佈目標 ID。

> **Fork PR 注意**：GitHub 不會把 secrets 傳給來自 fork 的 PR。下方驗證範例對 fork 貢獻者的 PR 會因 `toolkit_token` 為空而失敗。若 repo 為公開且需接受外部 PR，請改用同 repo 分支流程，或自行評估 `pull_request_target` 的安全風險。

## ParaTranz：來源與譯文的完整循環

ParaTranz 翻譯包使用兩條獨立 reusable workflow：

- `TranslationPack-Paratranz-Push.yml`：以 `translation-tool` 更新模組原文，並以 `paratranz-tool` 將已提交的 source 推到 ParaTranz。
- `TranslationPack-Paratranz-Pull.yml`：產生新 artifact、拉回 `zh_tw.json`、更新進度、驗證與建構，最後建立翻譯 PR。

兩條 workflow 都要求明確指定 `paratranz_toolkit_version`，且安裝時會驗證 release 的 `SHA512SUMS`。`PARATRANZ_TOKEN` 只存在於同步 job；建立 PR 的 job 不會取得該 secret。兩條 caller 必須傳入相同的 `concurrency_group`，避免同一 ParaTranz project 的 Push 與 Pull 交錯。

### 來源更新：先 PR，合併後才 Push

排程偵測上游模組變更時先設 `apply: false`，只建立 source PR。該 PR 合併進 `main` 後，再由 `push` event 以 `sync_sources: false`、`apply: true` 把已提交的 canonical source 寫入 ParaTranz：

```yaml
name: ParaTranz Source Sync

on:
  schedule:
    - cron: "20 18 * * 1"
  workflow_dispatch:
  push:
    branches: [main]
    paths:
      - ".github/workflows/paratranz-source.yml"
      - "Translation/**/en_us.json"
      - "Translation/**/metadata.json"
      - "config/paratranz.json"
      - "config/paratranz-files.json"

permissions:
  contents: write
  pull-requests: write

jobs:
  discover:
    if: github.event_name != 'push'
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Paratranz-Push.yml@v1
    with:
      sync_sources: true
      apply: false
      create_pull_request: true
      paratranz_toolkit_version: v1.0.0
      concurrency_group: project-9900
    secrets:
      toolkit_token: ${{ secrets.TOOLKIT_TOKEN }}
      paratranz_token: ${{ secrets.PARATRANZ_TOKEN }}
      curseforge_api_key: ${{ secrets.CURSEFORGE_API_KEY }}

  push-merged-source:
    if: github.event_name == 'push'
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Paratranz-Push.yml@v1
    with:
      sync_sources: false
      apply: true
      create_pull_request: false
      paratranz_toolkit_version: v1.0.0
      concurrency_group: project-9900
    secrets:
      toolkit_token: ${{ secrets.TOOLKIT_TOKEN }}
      paratranz_token: ${{ secrets.PARATRANZ_TOKEN }}
```

> `paratranz-tool` 目前只會 apply 已有 `file_id` 且遠端路徑一致的 source update。全新模組與 path reconciliation 會出現在 dry-run report，但在任何 mutation 前 fail closed；不可用 workflow shell command 繞過此安全閘門。

### 譯文更新：Artifact → `zh_tw.json` PR

```yaml
name: ParaTranz Translation Sync

on:
  schedule:
    - cron: "20 18 * * 4"
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  pull:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Paratranz-Pull.yml@v1
    with:
      pack_name: ParaTranslationPack
      generate_artifact: true
      create_pull_request: true
      paratranz_toolkit_version: v1.0.0
      concurrency_group: project-9900
    secrets:
      toolkit_token: ${{ secrets.TOOLKIT_TOKEN }}
      paratranz_token: ${{ secrets.PARATRANZ_TOKEN }}
```

有差異時，Pull workflow 只允許提交 `Translation/**/zh_tw.json` 與 `Translation/**/metadata.json`，並在建立 PR 前完成：

1. artifact generation read-after-write；
2. translation pull dry-run 與 apply；
3. 相同 artifact 的 no-op 重跑；
4. `translation-tool progress`；
5. `translation-tool doctor --strict`；
6. 資源包 build 與 ZIP 完整性檢查。

PR 合併後再由既有的 TranslationPack Build／Release caller 發布；同步 job 本身不直接發布。

## 驗證：PR 與 main 都檢查

```yaml
name: Translation Pack Validate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Validate.yml@v1
    with:
      strict: true
    secrets: inherit
```

診斷結果分兩個地方呈現，不需要額外設定：

- **Annotation**（預設 `format: github`、`severity: error`）只標註 error，直接顯示在 Files changed 對應的檔案上。
- **Job summary**（預設 `job_summary: true`）附上 warning 以上的完整表格。

之所以不把 warning 也做成 annotation，是因為 GitHub 每個 step 每種等級最多只顯示 10 則。專案累積的既有 warning 會把額度吃光，本次 PR 真正相關的項目反而被擠掉。Job summary 沒有筆數上限，適合放整個專案的健康清單。

既有 warning 清乾淨後，加上 `strict: true` 就能讓警告也成為擋門條件。若不需要 summary（例如另有儀表板），設 `job_summary: false`；`remote: true` 時會自動略過，避免重跑一次遠端驗證。

需要額外驗證 Modrinth / CurseForge / 最新版 JAR 時加 `remote: true`，並把 `curseforge_api_key` 傳進來：

```yaml
jobs:
  validate:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Validate.yml@v1
    with:
      strict: true
      remote: true
    secrets: inherit
```

## 建構與發佈：手動觸發、依版本群組逐版發佈

`TranslationPack-Build` 會輸出 `release_targets`（含 `zip` / `version` / `game_versions` / `update_ci_latest`），透過 matrix 搭配 `max-parallel: 1` 依序餵給 `TranslationPack-Release`，避免並行寫 `ci_latest` tag 衝突。`update_ci_latest` 由建構工作流自動設定為「最後一個版本才為 true」。

```yaml
name: Translation Pack Release

on:
  workflow_dispatch:
    inputs:
      version_group:
        description: "指定版本群組（留空建置全部）"
        required: false
        type: string

jobs:
  build:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Build.yml@v1
    with:
      pack_name: ModsTranslationPack
      version_group: ${{ inputs.version_group }}
    secrets: inherit

  release:
    needs: build
    permissions:
      contents: write
    strategy:
      fail-fast: false
      max-parallel: 1
      matrix:
        target: ${{ fromJson(needs.build.outputs.release_targets) }}
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Release.yml@v1
    with:
      version: ${{ matrix.target.version }}
      artifact_pattern: ${{ matrix.target.zip }}
      game_versions: ${{ matrix.target.game_versions }}
      update_ci_latest: ${{ matrix.target.update_ci_latest }}
      release_version: git-${{ needs.build.outputs.short_sha }}
      release_name: ${{ matrix.target.version }}｜git ${{ needs.build.outputs.short_sha }}
      modrinth_id: ABCDEFGH
      curseforge_id: "123456"
      project_id: modstranslationpack
    secrets: inherit
```

> `modrinth_id` / `curseforge_id` / `project_id` 留空可關閉對應平台發佈。設定 `project_id` 時必填 `anvil_api_token`；設定 `modrinth_id` / `curseforge_id` 時各自需要對應 token。

### 版本號與版本名稱

`release_version` 與 `release_name` 由呼叫端決定，因為命名慣例是各翻譯包自己的事（例如模組翻譯包用 `git-<短 SHA>`，正式版改用 `v1.9.3`）。兩者不能共用同一個值：

- `release_version` 會成為 Modrinth 的 `version_number`，限制為 ``^[a-zA-Z0-9!@$()`.+,_"-]+$``、最長 32 字元，**不允許空格**，所以要寫成 `git-2e170e2`。
- `release_name` 是顯示名稱，沒有字元限制，可以寫成 `1.21｜git 2e170e2`。

`${{ github.sha }}` 是 40 碼、加上前綴會超過 32 字元上限，因此請改用建構 workflow 的 `short_sha` output。`matrix.target.version` 就是 `config/minecraft_versions.json` 的群組 key（`1.21`、`26.1`、`26.2`），直接使用即可。

`release_version` 留空時會 fallback 成 `version`，這代表每次發佈同一個 MC 群組都會產生同名版本 —— Modrinth 不擋重複的 `version_number`，但專案頁會出現多個無法分辨的版本，因此建議一律明確傳入。

## PR 預覽：自動貼出免登入下載連結

`post_preview_comment: true` 會在 PR 上貼一則留言，把每個版本的 [nightly.link](https://nightly.link/) 下載連結列成表格。貢獻者不需要 GitHub 帳號、也不用進 Actions 頁面翻 artifact，點連結拿到的就是資源包本身（因為 artifact 以 `archive: false` 上傳，不會多包一層 zip）。

同一個 PR 推新 commit 時會就地更新原留言，不會洗版。

```yaml
name: Build

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  build:
    permissions:
      contents: read
      pull-requests: write
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Build.yml@v1
    with:
      pack_name: ModsTranslationPack
      post_preview_comment: true
    secrets: inherit
```

> **必須自己授權 `pull-requests: write`**。Reusable workflow 的權限「只能維持或縮小，不能放大」，所以呼叫端沒給的話 reusable workflow 這邊宣告也沒用。權限不足時留言步驟只會留下 warning，不會讓建構變紅。
>
> 來自 fork 的 PR 拿到的是唯讀 token，貼不了留言——不過 fork PR 本來就會因為缺 `toolkit_token` 而在更前面失敗。

## 只跑建構：不發佈，只留 Artifact

```yaml
name: Translation Pack Build

on:
  workflow_dispatch:

jobs:
  build:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/TranslationPack-Build.yml@v1
    with:
      pack_name: ParaTranslationPack
    secrets: inherit
```
