#!/usr/bin/env bash
# 下載 GitHub Release 上的外部來源內容，以 Release API 的 SHA-256 digest 驗證並檢查 zip 項目後，
# 先解到暫存目錄並檢查實際結果，再移入 <PROJECT_PATH>/Translation/。
# 由 action.yml 以 SOURCES、PROJECT_PATH、GH_TOKEN 呼叫；
# 被 source 時只載入函式。本機 bash 3.2 也要能執行，不使用關聯陣列與 mapfile。
set -euo pipefail

# 與 .github/workflows/TranslationPack-Publish-Source.yml 打包步驟的 MAX_BYTES 同步。
readonly MAX_BYTES=$((200 * 1024 * 1024))
readonly URL_PATTERN='^https://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/([^/]+)$'

fail() {
  printf '::error::%s\n' "$1" >&2
  exit 1
}

is_safe_segment() {
  [[ "$1" =~ ^[A-Za-z0-9_.+-]+$ && "$1" != "." && "$1" != ".." ]]
}

# 印出「owner repo tag asset」。
parse_source_url() {
  local owner repo tag asset part
  [[ "$1" =~ $URL_PATTERN ]] || fail "外部來源必須是 GitHub Release 檔案網址：$1"
  # is_safe_segment 也用 =~，會覆寫 BASH_REMATCH，先取出。
  owner=${BASH_REMATCH[1]} repo=${BASH_REMATCH[2]} tag=${BASH_REMATCH[3]} asset=${BASH_REMATCH[4]}
  for part in "$owner" "$repo" "$tag" "$asset"; do
    is_safe_segment "$part" || fail "外部來源網址含有不安全的路徑片段：$1"
  done
  printf '%s %s %s %s\n' "$owner" "$repo" "$tag" "$asset"
}

# 從 Release JSON 取出指定檔案的 SHA-256（十六進位）。
asset_sha256() {
  local count digest
  count=$(jq --arg name "$2" '[.assets[] | select(.name == $name)] | length' <<<"$1")
  [ "$count" = 1 ] || fail "Release 中找不到檔案 $2"
  digest=$(jq -r --arg name "$2" '.assets[] | select(.name == $name) | .digest // ""' <<<"$1")
  [[ "$digest" =~ ^sha256:([0-9a-f]{64})$ ]] || fail "Release 檔案 $2 沒有 SHA-256 digest"
  printf '%s\n' "${BASH_REMATCH[1]}"
}

verify_sha256() {
  local actual
  actual=$(sha256sum "$1" | cut -d' ' -f1)
  [ "$actual" = "$2" ] || fail "SHA-256 不符：預期 $2，實際 $actual"
}

# 解壓前檢查 zip 顯示名稱中的 ASCII 路徑結構，不以顯示文字判斷檔案型別。
check_zip() {
  local zip=$1 translation=$2 names name top tops=""
  names=$(zipinfo -1 "$zip" 2>/dev/null) || fail "無法讀取 zip 或 zip 沒有任何項目"
  [ -n "$names" ] || fail "zip 沒有任何項目"
  while IFS= read -r name; do
    case "$name" in
      /* | *\\*) fail "zip 項目路徑不安全：$name" ;;
    esac
    [[ "/$name/" != *"/../"* ]] || fail "zip 項目路徑不安全：$name"
    [[ "$name" == */* ]] || fail "zip 最上層只能是目錄：$name"
    top=${name%%/*}
    [[ "$top" != .* ]] || fail "zip 最上層目錄不得以 . 開頭：$top"
    is_safe_segment "$top" || fail "zip 最上層目錄名稱不安全：$top"
    tops+="$top"$'\n'
  done <<<"$names"
  tops=$(printf '%s' "$tops" | sort -u)
  while IFS= read -r top; do
    if [ -e "$translation/$top" ] || [ -L "$translation/$top" ]; then
      fail "Translation/$top 已存在，不覆蓋既有內容"
    fi
  done <<<"$tops"
  printf '%s\n' "$tops"
}

# 解壓後以實際檔案型別、名稱、數量與目的地為準；全部檢查通過才允許移入。
check_staging() {
  local zip=$1 staging=$2 translation=$3 special controls names expected actual entries entry top tops=""
  special=$(find "$staging" ! -type d ! -type f) || fail "無法檢查解壓後的檔案型別"
  [ -z "$special" ] || fail "zip 含有 symlink 或特殊檔案"
  controls=$(LC_ALL=C find "$staging" -name '*[[:cntrl:]]*') || fail "無法檢查解壓後的檔名"
  [ -z "$controls" ] || fail "zip 項目名稱含有控制字元"
  names=$(zipinfo -1 "$zip") || fail "無法讀取 zip"
  expected=$(LC_ALL=C awk '!/\/$/ {n++} END {print n+0}' <<<"$names") || fail "無法計算 zip 的檔案數"
  actual=$(find "$staging" -type f -print0 | LC_ALL=C tr -cd '\000' | wc -c) \
    || fail "無法計算解壓後的檔案數"
  [ "$actual" -eq "$expected" ] \
    || fail "解壓後的檔案數與 zip 不符（檔名可能含有控制字元或彼此衝突）"
  entries=$(find "$staging" -mindepth 1 -maxdepth 1) || fail "無法列出解壓後的內容目錄"
  [ -n "$entries" ] || fail "zip 沒有任何內容目錄"
  while IFS= read -r entry; do
    top=${entry##*/}
    [ -d "$entry" ] || fail "zip 最上層只能是目錄：$top"
    [[ "$top" != .* ]] || fail "zip 最上層目錄不得以 . 開頭：$top"
    is_safe_segment "$top" || fail "zip 最上層目錄名稱不安全：$top"
    if [ -e "$translation/$top" ] || [ -L "$translation/$top" ]; then
      fail "Translation/$top 已存在，不覆蓋既有內容"
    fi
    tops+="$top"$'\n'
  done <<<"$entries"
  printf '%s' "$tops" | sort
}

adjust_staging_permissions() {
  local failed
  # 保持先處理目錄再往下走；find -exec ... \; 的子命令失敗不會反映在 find 退出碼。
  failed=$(find "$staging" -type d ! -exec chmod u+rwx {} \; -print) || return 1
  [ -z "$failed" ]
}

cleanup_staging() {
  local top
  if [ -n "${staging:-}" ]; then
    # 同一來源尚未完成時，回復已移入的目錄；不影響先前完成的來源。
    while IFS= read -r top; do
      [ -n "$top" ] || continue
      if ! mv "$staging_translation/$top" "$staging/$top"; then
        printf '::error::無法回復內容目錄 %s，保留暫存內容供復原\n' "$top" >&2
        return 1
      fi
    done <<<"${promoted_dirs:-}"
    # unzip 會還原目錄權限；先由外往內開放目前使用者存取，且不跟隨 symlink。
    adjust_staging_permissions || printf '::warning::無法調整暫存目錄權限，仍嘗試清理\n' >&2
    rm -rf "$staging"
  fi
}

main() {
  local translation="${PROJECT_PATH:-.}/Translation" index=0 line parts owner repo tag asset
  local release expected zip dirs updated summary top
  [ -d "$translation" ] || fail "找不到 $translation"
  work=$(mktemp -d)
  staging=""
  promoted_dirs=""
  trap 'rm -rf "$work"; cleanup_staging' EXIT
  summary="$work/summary.md"
  printf '## 外部來源\n\n| 來源 | 檔案更新時間 | SHA-256 | 內容目錄 |\n| --- | --- | --- | --- |\n' >"$summary"
  while IFS= read -r line || [ -n "$line" ]; do
    line=$(sed 's/^[[:space:]]*//;s/[[:space:]]*$//' <<<"$line")
    case "$line" in '' | '#'*) continue ;; esac
    parts=$(parse_source_url "$line")
    read -r owner repo tag asset <<<"$parts"
    release=$(gh api "repos/$owner/$repo/releases/tags/$tag")
    expected=$(asset_sha256 "$release" "$asset")
    index=$((index + 1))
    zip="$work/source-$index.zip"
    curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' \
      --max-filesize "$MAX_BYTES" --output "$zip" "$line"
    verify_sha256 "$zip" "$expected"
    check_zip "$zip" "$translation" >/dev/null
    staging=$(mktemp -d "$translation/.external-XXXXXX")
    staging_translation=$translation
    # 保留控制字元，避免 unzip 靜默改名後無法發現單一非法檔名；檢查後不會將其移入。
    unzip -q -o -^ "$zip" -d "$staging" </dev/null || fail "無法解壓 zip"
    adjust_staging_permissions || fail "無法調整暫存目錄權限"
    dirs=$(check_staging "$zip" "$staging" "$translation")
    while IFS= read -r top; do
      mv "$staging/$top" "$translation/$top" || fail "無法移入內容目錄 $top"
      promoted_dirs+="$top"$'\n'
    done <<<"$dirs"
    rmdir "$staging"
    staging=""
    promoted_dirs=""
    updated=$(jq -r --arg name "$asset" '.assets[] | select(.name == $name) | .updated_at' <<<"$release")
    # shellcheck disable=SC2016 # 反引號是 Markdown 的程式碼標記，不是命令替換。
    printf '| `%s/%s@%s/%s` | %s | `%s` | %s |\n' "$owner" "$repo" "$tag" "$asset" "$updated" "$expected" \
      "$(tr '\n' ' ' <<<"$dirs")" >>"$summary"
    echo "::notice::${asset}：解出 $(wc -l <<<"$dirs" | tr -d ' ') 個內容目錄"
  done <<<"${SOURCES:-}"
  [ "$index" -gt 0 ] || fail "external_sources 沒有任何來源網址"
  if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    cat "$summary" >>"$GITHUB_STEP_SUMMARY"
  fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main
fi
