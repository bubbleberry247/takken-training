#!/bin/bash
# deploy_and_verify.sh — clasp push + deploy + OAuth診断チェック
# Usage: bash tools/deploy_and_verify.sh "デプロイの説明"
set -euo pipefail

DEPLOY_ID="AKfycbx9f7KnJ5WMuH3T3AWrewGaU14V5k8xn4uelGlxB9YFZyOL-So2IcF_D7J5jmggk-vYdg"
DEPLOY_DESC="${1:-update}"
EXEC_URL="https://script.google.com/macros/s/${DEPLOY_ID}/exec"

echo "=== Step 1: clasp push ==="
npx clasp push
echo ""

echo "=== Step 2: clasp deploy ==="
npx clasp deploy -i "$DEPLOY_ID" -d "$DEPLOY_DESC"
echo ""

echo "=== Step 3: OAuth診断チェック ==="
echo "以下のURLをブラウザで開いて確認してください:"
echo ""
echo "  ${EXEC_URL}?diag=oauth"
echo ""
echo "チェックポイント:"
echo "  1. RESOLVED_APP_EXEC_URL と DEPLOY_URL が一致していること"
echo "  2. GOOGLE_CLIENT_ID が SET であること"
echo "  3. GOOGLE_CLIENT_SECRET が SET であること"
echo "  4. validation.URL_MATCH が OK であること"
echo ""
echo "=== 姉妹アプリ確認 ==="
echo "archi にも同じ修正が必要ですか？ 必要なら:"
echo "  cd ../archi-16w-training && bash tools/deploy_and_verify.sh \"$DEPLOY_DESC\""
