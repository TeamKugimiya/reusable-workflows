#!/bin/bash

# Config 讀取變數
Config_Path=.github/configs/Settings.config

if [ -f "$Config_Path" ]; then
  # shellcheck source=/dev/null
  source $Config_Path
else
  echo "❗ 錯誤！無法找到設定檔案"
  exit 1
fi

# 回到 GitHub 工作目錄
home () {
    cd "$GITHUB_WORKSPACE" || exit
    # cd "$PWD" || exit
}

patch_maker () {
  ## 指定家目錄
  home=$GITHUB_WORKSPACE
  ## 製作一個臨時資料夾
  workdir="$(mktemp -d)"

  ## 複製內容到臨時資料夾
  for path in "${Client_Patch_Array[@]:?}"; do
    cp -r --parents "$path" "$workdir/"
  done

  cd "$workdir" && zip -r "$home/${Modpack_Name:?}-Patches-${version:?}.zip" *
  echo "版本 ${version:?}"
  home

  ## 伺服器補丁
  if [ "${Server_Patch_Generate:?}" = 'true' ]; then
    workdir="$(mktemp -d)"
    echo "伺服器補丁"
    for path in "${Server_Patch_Array[@]:?}"; do
      cp -r --parents "$path" "$workdir/"
    done
    cd "$workdir" && zip -r "$home/$Modpack_Name-Patches-Server-${version:?}.zip" *
    echo "$OLDPWD"
  fi
}

# 主要呼叫
home
patch_maker
