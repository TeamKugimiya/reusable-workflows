#!/bin/bash

############################
#### Modpack env setup ####
############################

# 回到 GitHub 工作目錄
home () {
    cd "$GITHUB_WORKSPACE" || exit
}

# Config 讀取變數
Config_Path=.github/configs/Settings.config

if [ -f "$Config_Path" ]; then
  # shellcheck source=/dev/null
  source $Config_Path
else
  echo "❗ 錯誤！無法找到設定檔案"
  exit 1
fi

# GitHub 環境設置

environment_setup () {
  ## 宣告模組包名稱
  echo "modpack_name=${ModPackName:?}" >> "$GITHUB_OUTPUT"

  ## 宣告是否生成模組包的資源包補丁
  echo "resourcepack_patch_generate=${Resourcepack_Patch_Generate:?}" >> "$GITHUB_OUTPUT"

  ## 宣告是否生成伺服器補丁
  echo "server_patch_generate=${Server_Patch_Generate:?}" >> "$GITHUB_OUTPUT"

  ## 宣告陣列
  echo "patch_array=${Patch_Array:?}" >> "$GITHUB_OUTPUT"
  echo "server_array=${Server_Array:?}" >> "$GITHUB_OUTPUT"
}

# 主要呼叫
home
environment_setup
