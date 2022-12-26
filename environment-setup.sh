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
  echo "out_modpack_name=${ModPackName:?}" >> "$GITHUB_OUTPUT"

  ## 宣告是否生成模組包的資源包補丁
  echo "out_resourcepack_patch_generate=${Resourcepack_Patch_Generate:?}" >> "$GITHUB_OUTPUT"
}

# 主要呼叫
home
environment_setup
