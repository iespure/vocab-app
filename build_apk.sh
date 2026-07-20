#!/bin/bash
# ═══════════════════════════════════════════════════════
# 在 Debian 上构建 APK
# 用法：bash build_apk.sh
# ═══════════════════════════════════════════════════════
set -e

cd "$(dirname "$0")"

echo "[1/3] 安装 Python 依赖..."
pip3 install flet --break-system-packages 2>/dev/null || pip3 install flet --quiet

echo "[2/3] 检查 Flutter 环境..."
flutter doctor 2>&1 | head -5

echo "[3/3] 开始构建 APK..."
# 接受 Android 许可
yes | ~/android-sdk/cmdline-tools/latest/bin/sdkmanager --licenses 2>/dev/null || true

# 打包！
flet build apk \
  --project vocab_app \
  --org com.achao.vocab \
  --product "记单词" \
  --description "义务教育阶段英语单词记忆APP" \
  .

echo ""
echo "=== 构建完成 ==="
ls -lh build/apk/*.apk 2>/dev/null && echo "APK 在上方路径"
