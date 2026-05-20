# 釘宮翻譯組 — Reusable Workflows

釘宮翻譯組專用的 GitHub Actions [Reusable Workflows](https://docs.github.com/zh/actions/sharing-automations/reusing-workflows) 集合。

> ⚠️ 本工作流程針對組內專案的結構與流程量身打造，直接套用至其他專案可能需要大量調整。歡迎參考用法與設計思路。

## 可用工作流程

每個工作流程的詳細 inputs / secrets / 範例請點擊連結進入 `docs/`。下表由 `scripts/gen_workflow_docs.py` 自動生成，請勿手改。

<!-- workflows:start -->

### 模組包

| 工作流程 | 用途 |
| --- | --- |
| [模組包｜打包](docs/Modpack-Build.md) | 透過 modpack-tool 建構模組包 zip 並上傳為 Artifact |
| [模組包｜ParaTranz 下載](docs/Modpack-Paratranz-Download.md) | 從 ParaTranz 下載譯文並建立自動更新 PR |
| [模組包｜ParaTranz 上傳](docs/Modpack-Paratranz-Upload.md) | 檢查或上傳 modpack-tool ParaTranz 原文；PR 可 dry-run，main 可正式 upload |
| [模組包｜發佈](docs/Modpack-Release.md) | 下載模組包 Artifact，預設整理為發佈候選 Artifact，填入版本時建立 GitHub Release |
| [模組包｜驗證](docs/Modpack-Validate.md) | 透過 modpack-tool doctor 驗證模組包專案；建議在 PR 與 main push 呼叫 |

### 翻譯包

| 工作流程 | 用途 |
| --- | --- |
| [翻譯包｜建構](docs/TranslationPack-Build.md) | 透過 translation-toolkit 建構翻譯資源包並上傳為 Artifact |
| [翻譯包｜發佈](docs/TranslationPack-Release.md) | 下載翻譯資源包 Artifact 並發佈至 Anvil、Modrinth 與 CurseForge |
| [翻譯包｜驗證](docs/TranslationPack-Validate.md) | 透過 translation-toolkit doctor 驗證翻譯專案健康狀態 |

<!-- workflows:end -->

## 文件

- [開發指南](docs/development.md) — 新增 / 修改 workflow、文件產生流程、慣例
- [模組包呼叫端 workflow 範例](docs/example/modpack.md) — PR / main 驗證與手動打包發佈範例
- [翻譯包呼叫端 workflow 範例](docs/example/translation-pack.md) — 驗證、建構與 matrix 逐版發佈範例
