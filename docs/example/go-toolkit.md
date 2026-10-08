# Go toolkit caller 範例

`translation-toolkit`、`paratranz-toolkit` 與 `modpack-toolkit` 共用同一套 CI／security／release orchestration。caller 只定義 repository event、binary 名稱與受限 profile。

## 一致性結論

| 面向 | 共用結果 | 保留差異 |
| --- | --- | --- |
| Go 與 CLI baseline | Go patch 一律由 caller `go.mod` 決定 | modpack 仍為 standard-library CLI；另外兩庫共用 Cobra／color baseline |
| Repository gate | 三庫都提供相同的 `scripts/check.sh` stage names，pre-commit 另由 `scripts/pre-submit.sh` 串接 secret 掃描 | 每個 stage 的測試 package／timeout 由 caller repository 擁有 |
| CI | 三平台 build、unit／E2E、module hygiene、固定 lint tools、六個跨平台 binary 的編譯與 Artifact 上傳完全共用 | `translation-toolkit` 保留真實平台 live integration（由其 `scripts/check.sh integration` 決定清單：CurseForge live 加 Modrinth staging）；`paratranz-toolkit` 保留 built-binary E2E coverage |
| Security | `govulncheck` 與 Betterleaks 的版本、checksum、canary 與 enforcement 完全共用 | 無 |
| Build metadata | translation／paratranz 使用 `internal/buildinfo` 與 JSON metadata | modpack 使用 `internal/toolkit.Version` 與純文字 version profile |
| Release assets | 共同產生 Linux amd64／arm64、Darwin amd64／arm64、Windows amd64／arm64 與 `SHA512SUMS` | 只有 binary 名稱不同 |
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

`translation-toolkit` 額外啟用受限的 integration profile，該 job 呼叫 caller 的 `./scripts/check.sh integration`。來自 fork 的 PR 會整個略過 live integration job；同 repository PR 與 `main` push 若未設定 secret 則明確失敗：

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

跨平台編譯成功後，會將 Linux、macOS（Darwin）、Windows 各自的 amd64／arm64 binary 上傳為 `${binary_name}-build-output` Artifact，可從該次 Actions run 下載。預設保留 14 天，caller 可透過 `artifact_retention_days` 調整。Linux／macOS 的 binary 下載解壓縮後，執行前需以 `chmod +x <binary>` 恢復執行權限。

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

govulncheck 只在程式碼實際呼叫到有弱點的 symbol 時失敗；每週排程讓新公布的弱點不必等到程式碼變動才被發現。Betterleaks 掃完整 Git 歷史，偵測到 secret 時直接阻擋，已遮蔽的 SARIF 只在失敗時以 14 天 artifact 保存，不寫回 repository 或 GitHub Code Scanning。

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

`translation-toolkit` 將最後一行改為 `binary_name: translation-tool`。`modpack-toolkit` 另傳 `release_profile: modpack-toolkit`。共用 workflow 只允許從 repository 預設分支發佈，並依序完成 release gate、profile-specific metadata／notes 檢查、六平台 cross-compile、`SHA512SUMS` 自我驗證、Linux runner 原生架構的版本 smoke test、tag 與 GitHub Release。

正式 caller 應 pin 已發布的 reusable-workflows release tag 或 commit；不要使用 `main`、`latest` 或其他浮動 branch。

`toolkit-ui` caller 傳入 `binary_name: toolkit-ui` 與 `release_profile: toolkit-ui`。
此 profile 與 `buildinfo` 共用版本注入及 changelog release notes，但使用 `-version`
驗證版本、commit 與建構時間，不要求 UI 提供 CLI 的 `version --format json` 子命令。
