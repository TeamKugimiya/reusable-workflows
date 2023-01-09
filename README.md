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

**用法**

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
| placeholder | string | 判斷字串，將判斷於它的空格過後一行來產生清單，預設為 ``<!-- readme contributors -->`` | false |
| branch | string | 所要提交的分支位置，預設為 ``main`` | false |
| pull_request | string | 合併請求到哪個分支中，當設定時將會自動建立合併請求 | false |
| path | string | 讀我文件的路徑，預設為 ``/README.md`` | false |
| commit_message | string | 提交的訊息，預設為 ``docs(contributor): 自動更新 Readme 貢獻者清單`` | false |

**用法**

```yaml
  Contributors:
    name: 貢獻者清單
    uses: TeamKugimiya/reusable-workflows/.github/workflows/Contributors.yml@main

```

### 同步分支資料夾

- [`sync-branch.yml`](.github/workflows/sync-branch.yml)

這個工作流程是專門拿來同步資料夾到另一個分支中

| ID | 類型 | 簡介 | 必要 |
| --- | --- | --- | --- |
| branch_name | String | 分支名稱 | true |
| path | String | 資料夾路徑，所設定的資料夾內的所有資料將會被轉移到該分支下的根目錄 | true |
| license_inculde | Boolean | 是否自動複製授權許可文件 | false |
| license_path | String | 授權許可文件的路徑，預設為 ``LICENSE`` | false |

### 環境變數宣告

- [`modpack-environment.yml`](.github/workflows/modpack-environment.yml)

這個工作流程是作為宣告環境變數到 outputs 中，並可以透過使用 needs 來讓下一個新的 job 接收到變數。

變數列表：

- modpack_name ``模組包名稱``
- resourcepack_patch_generate ``是否產生「模組包資源包補丁」``
- server_patch_generate ``是否產生「伺服器補丁」``
- download_mmlp ``是否下載「簡轉繁資源包」``

**用法**

```yaml
  Environment-Setup:
    name: 環境階段
    uses: TeamKugimiya/reusable-workflows/.github/workflows/modpack-environment.yml@main
```

### 製作資源包補丁

- [`modpack-resourcepack.yml`](.github/workflows/modpack-resourcepack.yml)

這個工作流程是從分支 ``resourcepack`` 中進行資源包優化，並輸出一個檔案名為 ``$模組包名稱$-Patches.zip`` 上傳到 artifact 中（名稱為 $模組包名稱$-Patches-Resourcepack）

選項列表：

- modpack-name ``模組包名稱``
- resourcepack-generate ``是否啟用或停用資源包產生``
- force_include_files  ``強制將指定檔案包入資源包，如果沒設定 PackSquash 將自動忽略非資源包相關的檔案，例如授權許可檔案``
- version_placeholder ``版本的替換符號，預設為 $RELEASE_VERSION``
- version ``該發布版本號碼，有給予數值時將會依照版本替換符號來更改 pack.mcmeta 的變數``

**用法**

```yaml
  Resourcepack-Maker:
    name: 資源包階段
    needs: Environment-Setup
    uses: TeamKugimiya/reusable-workflows/.github/workflows/modpack-resourcepack.yml@main
    with:
      modpack-name:
      resourcepack-generate:
```

### 製作補丁

- [`modpack-patch.yml`](.github/workflows/modpack-patch.yml)

這個工作流程是製作補丁，依照你的 Settings.config 來決定複製陣列、是否產生伺服器補丁與伺服器陣列等等

選項列表：

- modpack-name ``模組包名稱``
- modpack-version ``版本``
- modpack-resourcepack ``是否打包入補丁資源包``

**用法**

```yaml
  Patch-Maker:
    name: 補丁階段
    if: always()
    needs: [ Environment-Setup, Resourcepack-Maker ]
    uses: TeamKugimiya/reusable-workflows/.github/workflows/modpack-patch.yml@main
    with:
      modpack-name:
      modpack-version:
      modpack-resourcepack:
```

### 發布

- [`modpack-release.yml`](.github/workflows/modpack-release.yml)

這個工作流程是負責發布，並替換發布內容中的變數與下載成品中的補丁作為發布內容

選項列表：

- modpack-name ``模組包名稱``
- modpack-version ``版本``
- modpack-per-release ``預發布版``
- modpack-release-ignore ``忽略發布流程``
- release-body-path ``可選：指定發布內容 markdown 檔案位置``

**用法**

```yaml
  Release-It:
    name: 發布階段
    if: always()
    needs: [ Environment-Setup, Resourcepack-Maker, Patch-Maker ]
    uses: TeamKugimiya/reusable-workflows/.github/workflows/modpack-release.yml@main
    with:
      modpack-name:
      modpack-version:
      modpack-per-release:
      modpack-release-ignore:
```
