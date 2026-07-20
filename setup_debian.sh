#!/bin/bash
# ═══════════════════════════════════════════════════════
# Debian 一键环境安装 — Flutter + Android SDK
# 适用：Debian 11/12 x86_64
# 运行：bash setup_debian.sh
# ═══════════════════════════════════════════════════════
set -e

echo "=== Step 1: 系统依赖 ==="
sudo apt update
sudo apt install -y openjdk-17-jdk-headless python3-pip git curl unzip wget
echo "Java: $(java -version 2>&1 | head -1)"

echo ""
echo "=== Step 2: Android SDK Command-line Tools ==="
ANDROID_HOME="$HOME/android-sdk"
mkdir -p "$ANDROID_HOME/cmdline-tools"
cd "$ANDROID_HOME/cmdline-tools"

# 下载最新 cmdline-tools
TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
wget -q "$TOOLS_URL" -O cmdline-tools.zip
unzip -qo cmdline-tools.zip
mv cmdline-tools latest 2>/dev/null || true
rm cmdline-tools.zip

# 写入环境变量
cat >> ~/.bashrc << 'EOF'

# Android SDK
export ANDROID_HOME="$HOME/android-sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"
EOF

export ANDROID_HOME="$HOME/android-sdk"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$PATH"

# 安装必要 SDK 组件
yes | sdkmanager --licenses 2>/dev/null || true
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0" "ndk;25.1.8937393"

echo "Android SDK 安装完成：$ANDROID_HOME"

echo ""
echo "=== Step 3: Flutter SDK ==="
FLUTTER_HOME="$HOME/flutter"
cd "$HOME"
curl -sL "https://storage.flutter-io.cn/flutter_infra_release/releases/stable/linux/flutter_linux_3.22.2-stable.tar.xz" -o flutter.tar.xz
tar xf flutter.tar.xz
rm flutter.tar.xz

cat >> ~/.bashrc << 'EOF'

# Flutter
export PUB_HOSTED_URL=https://pub.flutter-io.cn
export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn
export PATH="$HOME/flutter/bin:$PATH"
EOF

export PUB_HOSTED_URL=https://pub.flutter-io.cn
export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn
export PATH="$HOME/flutter/bin:$PATH"

flutter config --no-analytics
flutter precache
echo "Flutter 安装完成：$(flutter --version 2>&1 | head -1)"

echo ""
echo "=== Step 4: Python flet ==="
pip3 install flet --break-system-packages 2>/dev/null || pip3 install flet

echo ""
echo "=== Step 5: 环境验证 ==="
flutter doctor
echo ""
echo "=== 安装完毕 ==="
echo "请执行: source ~/.bashrc"
echo ""
echo "JDK:   $(java -version 2>&1 | head -1)"
echo "Flutter: $(flutter --version 2>&1 | head -1)"
echo "SDK:   $ANDROID_HOME"
