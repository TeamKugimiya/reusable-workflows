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
      modrinth_id: ABCDEFGH
      curseforge_id: "123456"
      project_id: modstranslationpack
    secrets: inherit
```

> `modrinth_id` / `curseforge_id` / `project_id` 留空可關閉對應平台發佈。設定 `project_id` 時必填 `anvil_api_token`；設定 `modrinth_id` / `curseforge_id` 時各自需要對應 token。

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
