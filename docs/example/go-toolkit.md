# Go toolkit caller 範例

`translation-toolkit`、`paratranz-toolkit` 與 `modpack-toolkit` 共用同一套 CI／security／release orchestration。caller 只定義 repository event、binary 名稱與受限 profile。

## 一致性結論

| 面向 | 共用結果 | 保留差異 |
| --- | --- | --- |
| Go 與 CLI baseline | Go patch 一律由 caller `go.mod` 決定 | modpack 仍為 standard-library CLI；另外兩庫共用 Cobra／color baseline |
| Repository gate | 三庫都提供相同的 `scripts/check.sh` stage names，pre-commit 另由 `scripts/pre-submit.sh` 串接完整安全 gate | 每個 stage 的測試 package／timeout 由 caller repository 擁有 |
| CI | 三平台 build、unit／E2E、module hygiene、固定 lint tools、五平台 cross-compile 完全共用 | `translation-toolkit` 保留 CurseForge live integration；`paratranz-toolkit` 保留 built-binary E2E coverage |
| Security | `govulncheck`、`gosec`、Trivy、Semgrep CE、OpenGrep、Betterleaks 與 Gitleaks 的版本、規則、checksum、canary、SARIF 與 enforcement 完全共用 | 各 repository 保存自己的 `.github/security-baseline.json`，只承認已審查的既有 SAST finding |
| Build metadata | translation／paratranz 使用 `internal/buildinfo` 與 JSON metadata | modpack 使用 `internal/toolkit.Version` 與純文字 version profile |
| Release assets | 共同產生 Linux amd64／arm64、Darwin amd64／arm64、Windows amd64 與 `SHA512SUMS` | 只有 binary 名稱不同 |
| Release policy | 共同限制 `vX.Y.Z`、預設分支、tag 不可重複，且在 tag 前執行 gate、checksum 與版本 smoke test | buildinfo profile 讀正式 changelog；modpack profile 使用 GitHub-generated notes |

## CI

`paratranz-toolkit` 沒有預設 live integration job：

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Toolkit-CI.yml@v1
    with:
      binary_name: paratranz-tool
      e2e_profile: paratranz-toolkit
```

`translation-toolkit` 額外啟用受限的 CurseForge integration profile。來自 fork 的 PR 會整個略過 live integration job；同 repository PR 與 `main` push 若未設定 secret 則明確失敗：

```yaml
jobs:
  ci:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Toolkit-CI.yml@v1
    with:
      binary_name: translation-tool
      integration_profile: translation-toolkit
    secrets:
      curseforge_api_key: ${{ secrets.CURSEFORGE_API_KEY }}
```

`modpack-toolkit` 使用預設 profiles，只傳 `binary_name: modpack-tool`。

## Security

三庫使用相同的 thin caller；PR、`main` push、每週排程與手動觸發都會執行：

```yaml
name: Security

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "23 3 * * 1"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  security:
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Toolkit-Security.yml@v1
```

`.github/security-baseline.json` 以 rule、path、line 與 snippet 識別已審查 finding。新增或位移的 finding 會要求重新審查；修正既有 finding 後可刪除對應 baseline，但不得為了讓 CI 變綠而直接收錄未分析結果。Betterleaks 與 Gitleaks 掃完整 Git 歷史，Trivy 掃目前 filesystem／Go dependencies／misconfiguration；所有 report 只以 14 天 artifact 保存，不寫回 repository 或 GitHub Code Scanning。

## CLI release

buildinfo profile 的兩庫 release caller 只有 binary 名稱不同：

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      version:
        description: "Release version (e.g., v1.0.0)"
        required: true
        type: string

jobs:
  release:
    permissions:
      contents: write
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Toolkit-Release.yml@v1
    with:
      version: ${{ inputs.version }}
      binary_name: paratranz-tool
```

`translation-toolkit` 將最後一行改為 `binary_name: translation-tool`。`modpack-toolkit` 另傳 `release_profile: modpack-toolkit`。共用 workflow 只允許從 repository 預設分支發佈，並依序完成 release gate、profile-specific metadata／notes 檢查、五平台 cross-compile、`SHA512SUMS` 自我驗證、Linux amd64 版本 smoke test、tag 與 GitHub Release。

正式 caller 應 pin 已發布的 reusable-workflows release tag 或 commit；不要使用 `main`、`latest` 或其他浮動 branch。
