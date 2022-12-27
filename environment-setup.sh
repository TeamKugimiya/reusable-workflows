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

# 驗證 function

github_output () {
  echo "$1=$2" >> "$GITHUB_OUTPUT"
}

verify_var () {
  id=$1
  var=$2
  if [ -n "$var" ]; then
    echo "$id 已設置變數為 $var"
    github_output "$id" "$var"
  else
    echo "錯誤！空值或無法識別"
    exit 1
  fi
}

# GitHub 環境設置

environment_setup () {
  ## 宣告模組包名稱
  verify_var modpack_name "${Modpack_Name:?}"

  ## 宣告是否生成模組包的資源包補丁
  verify_var resourcepack_patch_generate "${Resourcepack_Patch_Generate:?}"

  ## 宣告是否生成伺服器補丁
  verify_var server_patch_generate "${Server_Patch_Generate:?}"

  ## 宣告是否下載簡轉繁資源包
  verify_var download_mmlp "${Download_MMLP:?}"
}

# 主要呼叫
home
environment_setup
