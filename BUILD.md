# 记单词 APP — 构建部署指南

## 方式一：在你的电脑上直接打包 APK（推荐）

### 前提
- 安装 Flutter SDK：`winget install Flutter.Flutter` 或 https://docs.flutter.dev/get-started/install/windows/desktop
- 安装 Android Studio + Android SDK（Flutter doctor 会提示）
- 运行 `flutter doctor` 确认全部 green check

### 打包命令
```powershell
cd C:\Users\Administrator\.qclaw\workspace-tfxjjhfnjialcuju\vocab_app
flet build apk
```
生成的 APK 在 `vocab_app/build/apk/` 目录。

### 扩展名处理
如果 `flet` 命令不在 PATH 中，改用：
```powershell
python -m flet build apk
```

## 方式二：先桌面验证再打包

```powershell
# 桌面模式跑起来看效果
cd C:\Users\Administrator\.qclaw\workspace-tfxjjhfnjialcuju\vocab_app
python main.py
```
Flet 会自动打开桌面窗口，功能跑通后再 `flet build apk`。

## 项目概况

| 项目 | 内容 |
|------|------|
| 词库 | 1455 词，3-9 年级（JSON） |
| 记忆算法 | SM-2 间隔重复（SuperMemo 2） |
| 数据存储 | SQLite（完全离线） |
| 学习模式 | 闪卡翻转 + 选择题四选一 |
| 核心文件 | main.py / models.py / views/ |
