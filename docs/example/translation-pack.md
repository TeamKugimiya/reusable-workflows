# 翻譯包呼叫端 workflow 範例

這份文件是給個別翻譯包 repo（例如 `ModsTranslationPack`、`ParaTranslationPack`）放在 `.github/workflows/` 的範例。Reusable workflow 本身只能定義 `workflow_call`，呼叫端要自行定義觸發條件、`pack_name` 與發佈目標 ID。

> **Fork PR 注意**：GitHub 不會把 secrets 傳給來自 fork 的 PR。下方驗證範例對 fork 貢獻者的 PR 會因 `toolkit_token` 為空而失敗。若 repo 為公開且需接受外部 PR，請改用同 repo 分支流程，或自行評估 `pull_request_target` 的安全風險。

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
