<!-- markdownlint-configure-file
{
  "MD036": false
}
-->

# 可重複使用工作流程

此專案專門收錄模組包的通用工作流程。

## 可用的工作流程

### 環境變數宣告

- [`modpack-environment.yml`](.github/workflows/modpack-environment.yml)

這個工作流程是作為宣告環境變數到 outputs 中，並可以透過使用 needs 來讓下一個新的 job 接收到變數。

變數列表：

- modpack_name ``模組包名稱``
- resourcepack_patch_generate ``是否生成「模組包資源包補丁」``
- server_patch_generate ``是否生成「伺服器補丁」``
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
- resourcepack-generate ``是否啟用或停用資源包生成``

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

這個工作流程是製作補丁，依照你的 Settings.config 來決定複製陣列、是否生成伺服器補丁與伺服器陣列等等

選項列表：

- modpack-name ``模組包名稱``
- modpack-version ``版本``
- modpack-resourcepack ``是否打包入補丁資源包``
- modpack-mmlp ``是否下載簡轉繁資源包（過時）``

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
      modpack-mmlp:
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
