<!-- markdownlint-configure-file
{
  "MD036": false
}
-->

# 可重複使用工作流程

本專案收錄一些通用與常用的工作流程

## 可用的工作流程

### 簡易資源包發布

- [`Simple-ResourcePacker.yml`](.github/workflows/Simple-ResourcePacker.yml)

這個工作流程是專門針對於不需要發布版本號的資源包打包，它將會以 ``latest`` 的 tag 來持續更新資源包壓縮檔。

| ID | 類型 | 簡介 | 必要 |
| --- | --- | --- | --- |
| resourcepack_file_name | String | 資源包檔案名稱，需使用英文，GitHub Release 吃不到中文字 | true |
| release_title_name | String | 發布標題名稱 | true |
| release_body_path | String | 發布內容路徑，預設路徑為 ``.github/configs/release_body.md`` | false |
| force_include_files | String | 強制將指定檔案包入資源包，如果沒設定 PackSquash 將自動忽略非資源包相關的檔案，例如授權許可檔案 | false |
| release_tag | String | 發布的版本標籤，通常不需要動此數值，預設值為 ``latest`` | false |
| release_update | Boolean | 自動更新現有的版本標籤，預設值為 ``true`` | false |
| git_version_replacer | Boolean | 啟用自動轉換變數成該提交的 git hash | true |
| git_version_var | String | 自動轉換的變數名，預設為``$GIT_VAR`` | false |
| generate_time_replacer | Boolean | 啟用自動轉換變數成目前資源包產生時間，適合用於發布內容檔案 | true |
| generate_time_var | String | 自動轉換的變數名，預設為``$DATE_TIME`` | false |

**範例**

```yaml
  Simple-Packer:
    name: 簡易資源包發布
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Simple-ResourcePacker.yml@main
    with:
      resourcepack_file_name:
      release_title_name:
      release_body_path:
      force_include_files:
      release_tag:
      release_update:
      git_version_replacer:
      git_version_var:
      generate_time_replacer:
      generate_time_var:
```

### 貢獻者清單產生

- [`Contributors.yml`](.github/workflows/Contributors.yml)

這個工作流程專門產生貢獻者清單。

| ID | 類型 | 簡介 | 必要 |
| --- | --- | --- | --- |
| placeholder | String | 判斷字串，將判斷於它的空格過後一行來產生清單，預設為 ``<!-- readme contributors -->`` | false |
| branch | String | 所要提交的分支位置，預設為 ``main`` | false |
| pull_request | String | 合併請求到哪個分支中，當設定時將會自動建立合併請求 | false |
| path | String | 讀我文件的路徑，預設為 ``/README.md`` | false |
| commit_message | String | 提交的訊息，預設為 ``docs(contributor): 自動更新 Readme 貢獻者清單`` | false |

**範例**

```yaml
  Contributors:
    name: 貢獻者清單
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Contributors.yml@main

```

### 製作資源包補丁

- [`Modpack-Resourcepack.yml`](.github/workflows/Modpack-Resourcepack.yml)

這個工作流程會判斷是否資料夾名稱為 ``Patch-ResourcePack`` 內有 ``pack.mcmeta`` 檔案來進行生成補丁資源包，成品將會顯示為 ``Patches-Resourcepack``。

| ID | 類型 | 簡介 | 必要 |
| --- | --- | --- | --- |
| force_include_files | String | 強制將指定檔案包入資源包，如果沒設定 PackSquash 將自動忽略非資源包相關的檔案，例如授權許可檔案 | false |
| version_placeholder | String | 版本的替換符號，預設為 ``$RELEASE_VERSION`` | false |
| version | String | 該發布版本號碼，有給予數值時將會依照版本替換符號來更改 ``pack.mcmeta`` 的變數 | false |

**範例**

```yaml
  Resourcepack-Maker:
    name: 資源包階段
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Resourcepack.yml@main
    with:
      force_include_files: "LICENSE"
      version: ${{ github.event.inputs.tag }}
```

### 製作補丁

- [`Modpack-Patch-Maker.yml`](.github/workflows/Modpack-Patch-Maker.yml)

這個工作流程是製作用戶端、伺服器端補丁，依照你的 ``.github/configs/config.yml`` 內的設定來進行製作。

| ID | 類型 | 簡介 | 必要 |
| --- | --- | --- | --- |
| modpack-version | String | 版本 | true |
| modpack-patch_resourcepack_maker | String | 是否下載資源包補丁 | true |

**範例**

```yaml
  Patch-Maker:
    name: 補丁階段
    needs: [ Resourcepack-Maker ]
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Patch-Maker.yml@main
    with:
      modpack-version: ${{ github.event.inputs.tag }}
      modpack-patch_resourcepack_maker: ${{ needs.Resourcepack-Maker.outputs.modpack_patch_resourcepack_maker }}
```

### 發布

- [`Modpack-Release.yml`](.github/workflows/Modpack-Release.yml)

這個工作流程是負責發布，並替換發布內容中的變數與下載成品中的補丁作為發布內容。

| ID | 類型 | 簡介 | 必要 |
| --- | --- | --- | --- |
| modpack-version | String | 發布版本 | true |
| modpack-official-version | String | 模組包官方版本 | true |
| modpack-per-release | String | 預發布版 | true |
| modpack-release-ignore | String | 忽略發布流程 | false |
| release-body-path | String | 指定發布內容 markdown 檔案位置，預設路徑為 ``.github/configs/release_body.md`` | false |

**範例**

```yaml
  Release-It:
    name: 發布階段
    needs: [ Resourcepack-Maker, Patch-Maker ]
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Modpack-Release.yml@main
    with:
      modpack-version: ${{ github.event.inputs.tag }}
      modpack-official-version: ${{ github.event.inputs.modpack_version }}
      modpack-per-release: ${{ github.event.inputs.per_release }}
      modpack-release-ignore: ${{ github.event.inputs.no_release }}
```
