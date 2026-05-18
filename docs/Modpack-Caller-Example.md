# 模組包呼叫端 workflow 範例

這份文件是給個別模組包 repo 放在 `.github/workflows/` 的範例。Reusable workflow 本身只能定義 `workflow_call`，所以 PR / main 檢查與手動 checkbox 要在呼叫端 repo 定義。

> **Fork PR 注意**：GitHub 不會把 secrets 傳給來自 fork 的 PR。下面用 `on: pull_request` + `secrets: inherit` 的範例（驗證、ParaTranz 上傳）對 fork 貢獻者的 PR 會因 `toolkit_token` 為空而明確失敗。若 repo 為公開且需接受外部 PR，請改用同 repo 分支流程，或自行評估 `pull_request_target` 的安全風險。

## 驗證：PR 與 main 都檢查

```yaml
name: Modpack Validate

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Validate.yml@v1
    with:
      strict: true
    secrets: inherit
```

## 打包與發佈：先產 Artifact，填版本才發 Release

```yaml
name: Modpack Package

on:
  workflow_dispatch:
    inputs:
      version:
        description: "GitHub Release tag；留空只上傳 Artifact"
        required: false
        type: string
      prerelease:
        description: "標記為 pre-release"
        required: false
        type: boolean
        default: false

jobs:
  package:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Build.yml@v1
    secrets: inherit

  release:
    needs: package
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Release.yml@v1
    with:
      artifact_pattern: ${{ needs.package.outputs.artifact_pattern }}
      version: ${{ inputs.version }}
      prerelease: ${{ inputs.prerelease }}
```

## ParaTranz 上傳：PR dry-run，main 正式 upload

```yaml
name: ParaTranz Upload

on:
  pull_request:
  push:
    branches: [main]

jobs:
  upload:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Paratranz-Upload.yml@v1
    with:
      dry_run: ${{ github.event_name == 'pull_request' }}
    secrets: inherit
```

## ParaTranz 下載：定期開自動更新 PR

```yaml
name: ParaTranz Download

on:
  schedule:
    - cron: "0 20 * * *"
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  download:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Paratranz-Download.yml@v1
    secrets: inherit
```

> 需在 repo *Settings → Actions → General* 開啟 **Allow GitHub Actions to create and approve pull requests**，自動 PR 才能建立。
>
> 預設用 `GITHUB_TOKEN` 建的 PR **不會觸發**其他 workflow（驗證、上傳不會跑）。若要自動 PR 也跑 CI，設定一個 PAT 並透過 `secrets: inherit`（或顯式）傳入 `create_pull_request_token`：
>
> ```yaml
>     secrets:
>       toolkit_token: ${{ secrets.TOOLKIT_TOKEN }}
>       paratranz_token: ${{ secrets.PARATRANZ_TOKEN }}
>       create_pull_request_token: ${{ secrets.CREATE_PULL_REQUEST_TOKEN }}
> ```

`changed` / `branch` / `pull_request_url` output 為字串，下游 job 判斷需用 `== 'true'`：

```yaml
  notify:
    needs: download
    if: needs.download.outputs.changed == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo "已建立 PR：${{ needs.download.outputs.pull_request_url }}"
```
