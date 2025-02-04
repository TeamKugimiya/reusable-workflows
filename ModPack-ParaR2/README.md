# 模組包 - Para R2

自動從 [ParaTranz](https://paratranz.cn/) 上下載特定模組包的壓縮包成品並上傳到 R2 進行儲存。

## 結構

1. 從平台上下載壓縮包成品
2. 上傳至 R2
3. 自動更新 Discord 上的 Webhook

## 腳本

main.py 所需的環境變數，有 `*` 為必須

- PROJECT_ID *專案 ID
- AUTH_TOKEN *Para 平台 Token
- PACK_FORMAT *資源包版本
- PACK_DESCRIPTION 資源包介紹
