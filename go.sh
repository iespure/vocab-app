#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 记单词 APP — Debian 全自动构建
# 用法：bash go.sh
# ═══════════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"

echo "=========================================="
echo " 记单词 APP 自动构建"
echo " 环境安装 + APK打包"
echo "=========================================="

# ── Step 1: 系统依赖 ──
echo ""
echo "[1/5] 安装系统依赖..."
sudo apt update -qq
sudo apt install -y -qq openjdk-17-jdk-headless python3-pip curl unzip wget git

# ── Step 2: Android SDK ──
echo ""
echo "[2/5] 安装 Android SDK (约3GB，耐心等)..."
ANDROID_HOME="$HOME/android-sdk"
mkdir -p "$ANDROID_HOME/cmdline-tools"

if [ ! -f "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" ]; then
    cd /tmp
    wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
    unzip -qo commandlinetools-linux-11076708_latest.zip
    mv cmdline-tools "$ANDROID_HOME/cmdline-tools/latest"
    rm commandlinetools-linux-11076708_latest.zip
fi

export ANDROID_HOME="$HOME/android-sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
yes | sdkmanager --licenses 2>/dev/null || true
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" "ndk;25.1.8937393" 2>&1 | tail -3

# ── Step 3: Flutter SDK ──
echo ""
echo "[3/5] 安装 Flutter SDK..."
if [ ! -d "$HOME/flutter" ]; then
    cd /tmp
    wget -q https://storage.flutter-io.cn/flutter_infra_release/releases/stable/linux/flutter_linux_3.22.2-stable.tar.xz
    tar xf flutter_linux_3.22.2-stable.tar.xz -C "$HOME/"
    rm flutter_linux_3.22.2-stable.tar.xz
fi

export PUB_HOSTED_URL=https://pub.flutter-io.cn
export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn
export PATH="$HOME/flutter/bin:$PATH"
flutter config --no-analytics --quiet 2>/dev/null || true
flutter precache 2>&1 | tail -1

# ── Step 4: Python flet ──
echo ""
echo "[4/5] 安装 flet..."
pip3 install flet --break-system-packages 2>/dev/null || pip3 install flet

# ── Step 5: 构建 APK ──
echo ""
echo "[5/5] 构建 APK..."
cd "$(dirname "$0")"
flet build apk \
    --project vocab_app \
    --org com.achao.vocab \
    --product "记单词" \
    .

echo ""
echo "=========================================="
echo " 构建完成！"
echo "=========================================="
ls -lh build/apk/*.apk 2>/dev/null || echo "APK 路径: build/apk/"
