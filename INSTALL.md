# 安装指南

## 系统要求

- **操作系统**：Windows 7/8/10/11（推荐 Windows 10+）
- **Python 版本**：3.7 或更高版本（仅源码运行需要；发布版已内置运行时）
- **内存**：至少 2GB RAM
- **磁盘空间**：至少 500MB

---

## 方式零：直接下载发布版（普通用户推荐）

不需要安装 Python：

1. 打开仓库的 **Releases** 页面
2. 下载最新 `Research_Tree_Generator_v*_win64.zip`
3. 解压到任意目录（建议非系统盘、路径不含中文）
4. 双击 `Research_Tree_Generator_v2.2.2.exe` 启动

> 发布版由 GitHub Actions 在打 tag 时自动构建，见 `.github/workflows/release.yml`。
> 二进制不进 git 仓库，只作为 Release 附件提供。

---

## 步骤 1：安装 Python

### 方法 A：从官网下载（推荐）

1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载最新版本的 Python 3.x
3. 运行安装程序
4. ⚠️ **重要**：勾选 "Add Python to PATH" 选项
5. 点击 "Install Now"

### 方法 B：使用 Microsoft Store

1. 打开 Microsoft Store
2. 搜索 "Python"
3. 选择最新版本并安装

### 验证安装

打开命令提示符（CMD）或 PowerShell，输入：

```bash
python --version
```

应该显示类似：`Python 3.11.5`

---

## 步骤 2：安装项目依赖

### 方法 A：从 GitHub 克隆（推荐）

```bash
git clone https://github.com/HonoriusAD395/Research_Tree_Generator.git
cd Research_Tree_Generator
```

> 也可以直接在仓库页面点 **Code → Download ZIP** 下载后解压。

### 方法 B：使用启动脚本（最简单）

进入项目目录后，直接双击 `run.bat`，脚本会检测 Python 并自动安装依赖。

### 方法 C：手动安装

1. 打开命令提示符（CMD）
2. 进入项目目录（把路径换成你实际解压/克隆的位置）：

```bash
cd 你放置项目的路径\Research_Tree_Generator
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

本项目运行时只需要 PyQt5，不需要 `pyqt5-tools`。

### 验证安装

```bash
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 安装成功！')"
```

---

## 步骤 3：运行程序

### 方法 A：使用启动脚本

双击 `run.bat` 即可启动。

### 方法 B：命令行启动

```bash
cd 你放置项目的路径\Research_Tree_Generator
python main.py
```

---

## 常见问题解决

### ❌ 问题 1：'python' 不是内部或外部命令

**原因**：Python 未添加到系统 PATH

**解决方案**：

1. 重新运行 Python 安装程序
2. 选择 "Modify"
3. 确保勾选 "Add Python to PATH"
4. 完成安装后重启电脑

或者手动添加 PATH：

1. 右键 "此电脑" → "属性" → "高级系统设置"
2. 点击 "环境变量"
3. 在 "系统变量" 中找到 "Path"
4. 添加 Python 安装路径（如 `C:\Python311\`）
5. 重启命令提示符

---

### ❌ 问题 2：ModuleNotFoundError: No module named 'PyQt5'

**原因**：PyQt5 未安装

**解决方案**：

```bash
pip install PyQt5
```

如果下载速度慢，使用国内镜像：

```bash
pip install PyQt5 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### ❌ 问题 3：pip 不是内部或外部命令

**原因**：pip 未正确安装或不在 PATH 中

**解决方案**：

```bash
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

---

### ❌ 问题 4：导入文件时出现编码错误

**原因**：文件编码不是 UTF-8

**解决方案**：

1. 用记事本打开 `.set` 文件
2. 点击 "文件" → "另存为"
3. 编码选择 "UTF-8"
4. 保存后重新导入

---

### ❌ 问题 5：界面显示模糊（高分屏）

**原因**：DPI 缩放问题

**解决方案**：

1. 右键 `main.py` 或 `run.bat`
2. 选择 "属性" → "兼容性"
3. 点击 "更改高 DPI 设置"
4. 勾选 "替代高 DPI 缩放行为"
5. 选择 "应用程序"

---

## 可选：创建桌面快捷方式

### 方法 1：手动创建

1. 右键桌面 → "新建" → "快捷方式"
2. 位置输入：

```
C:\Python311\python.exe 你放置项目的路径\Research_Tree_Generator\main.py
```

（根据实际的 Python 路径与项目路径修改）

3. 命名快捷方式为 "科技树生成器"
4. 右键快捷方式 → "属性" → "更改图标"
5. 选择一个喜欢的图标

### 方法 2：使用批处理文件

创建 `创建快捷方式.bat`：

```batch
@echo off
set SCRIPT="%TEMP%\CreateShortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\科技树生成器.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%cd%\run.bat" >> %SCRIPT%
echo oLink.WorkingDirectory = "%cd%" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%
echo 快捷方式已创建到桌面！
pause
```

---

## 更新程序

当仓库有新版本发布时（把路径换成你实际的项目目录）：

```bash
cd 你放置项目的路径\Research_Tree_Generator
git pull
pip install -r requirements.txt --upgrade
```

---

## 构建发布版（打包 exe）

想把源码打包成免安装的 exe：

```bash
cd 你放置项目的路径\Research_Tree_Generator

pip install -r requirements.txt pyinstaller
python test_imports.py                  # 先自检
python -m unittest discover -s tests    # 再跑测试

pyinstaller --noconfirm --clean Research_Tree_Generator.spec
```

产物在 `dist/Research_Tree_Generator_v2.2.2/`，把整个目录压缩成 zip 就是发布包。
`dist/` 与 `build/` 已在 `.gitignore` 中排除，**不会进入 git**。

### 用 GitHub Actions 自动发版（推荐）

仓库已配置 `.github/workflows/release.yml`：推送形如 `v2.2.2` 的 tag 时，会自动
安装依赖 → 自检 → 跑全部测试 → PyInstaller 打包 → 把 zip 上传到该 tag 的 Release。

```bash
git tag v2.2.2
git push origin v2.2.2
```

也可以在 **Actions → Release → Run workflow** 手动触发（只产出构建产物，不建 Release）。

---

## 版本控制（Git，可选但强烈推荐）

仓库自带 `.git`，当前是一个 v2.2.2 快照提交。它比"复制整个文件夹"更省空间、
可精确回滚到任意一次修改。基本操作：

```bash
cd 你放置项目的路径\Research_Tree_Generator

# 看当前有哪些改动
git status

# 每次改完、测试通过后，做一次快照（提交）
git add -A
git commit -m "说明这次改了什么"

# 查看历史
git log --oneline

# 回退某个文件的改动（放弃未提交的修改）
git restore src/main_window.py

# 回到历史某次快照
git checkout 4ff0d4b -- .
```

> 提示：`build/` `dist/` `.test_tmp/` `*.bak` `*.rtg_tmp` 已在 `.gitignore` 中排除，
> 不会被提交。首次使用请确认已安装 Git（`git --version`）。

---

## 卸载

1. 删除项目文件夹
2. （可选）卸载 PyQt5：

```bash
pip uninstall PyQt5 pyqt5-tools
```

---

## 获取帮助

如果遇到问题：

1. 查看 [README.md](README.md) 的常见问题部分
2. 检查 Python 和 PyQt5 版本是否兼容
3. 在项目 Issues 中搜索类似问题
4. 提交新的 Issue 并附上错误信息

---

**祝使用愉快！** 🎉

---
---

# Installation Guide (English)

> 中文完整指南见上方；本节为对应英文版本。
> The full Chinese guide is above; this is the English counterpart.

## Requirements

- **OS**: Windows 7/8/10/11 (Windows 10+ recommended)
- **Python**: 3.7+ (source install only — the released build bundles its runtime)
- **RAM**: 2 GB minimum
- **Disk**: 500 MB minimum

## Option 0: Download a release (recommended for end users)

No Python required:

1. Open the repository's **Releases** page
2. Download the latest `Research_Tree_Generator_v*_win64.zip`
3. Unpack anywhere (avoid system folders and non-ASCII paths)
4. Double-click `Research_Tree_Generator_v2.2.2.exe`

> Release builds are produced by GitHub Actions on tag push — see
> `.github/workflows/release.yml`. Binaries are never committed to git; they are
> Release attachments only.

## Option 1: Install from source (developers)

### 1. Clone

```bash
git clone https://github.com/HonoriusAD395/Research_Tree_Generator.git
cd Research_Tree_Generator
```

You can also use **Code → Download ZIP**.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Only PyQt5 is required at runtime; `pyqt5-tools` is **not** needed.

Verify:

```bash
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
```

### 3. Run

```bash
python main.py
```

Or double-click `run.bat`, which also installs dependencies on first run.

## Troubleshooting (quick reference)

| Symptom | Fix |
|---------|-----|
| `'python' is not recognized` | Reinstall Python with **Add Python to PATH**, or add the install dir to `PATH` |
| `ModuleNotFoundError: No module named 'PyQt5'` | `pip install PyQt5` (slow network: add `-i https://pypi.tuna.tsinghua.edu.cn/simple`) |
| `pip` not recognized | `python -m ensurepip --upgrade` then `python -m pip install --upgrade pip` |
| Encoding error when importing files | Re-save the `.set` file as **UTF-8** |
| Blurry UI on high-DPI screens | Right-click `main.py` / `run.bat` → Properties → Compatibility → Change high DPI settings → override scaling (Application) |

The Chinese guide above documents every issue in more detail.

## Build a release

```bash
pip install -r requirements.txt pyinstaller
python test_imports.py                  # self-check first
python -m unittest discover -s tests    # then the test suite

pyinstaller --noconfirm --clean Research_Tree_Generator.spec
```

The output lands in `dist/Research_Tree_Generator_v2.2.2/`; zip that directory to get
the release archive. `dist/` and `build/` are git-ignored and **never enter git**.

### Automatic release via GitHub Actions (recommended)

`.github/workflows/release.yml` is configured: pushing a tag like `v2.2.2` will
install dependencies → self-check → run all tests → build with PyInstaller →
upload the zip to that tag's Release.

```bash
git tag v2.2.2
git push origin v2.2.2
```

You can also trigger it manually via **Actions → Release → Run workflow** (build
artifact only, no Release).

## Version control (optional, recommended)

```bash
git status                     # what changed
git add -A
git commit -m "describe the change"
git log --oneline
git restore src/main_window.py # discard changes to one file
```

> `build/` `dist/` `.test_tmp/` `*.bak` `*.rtg_tmp` are excluded by `.gitignore`.
> Make sure Git is installed (`git --version`).

## Uninstall

1. Delete the project folder
2. Optionally remove PyQt5:

```bash
pip uninstall PyQt5
```

## Getting help

1. Check the FAQ in [README.md](README.md)
2. Verify Python / PyQt5 versions
3. Search existing Issues
4. Open a new Issue including the full error message

---

> **AI 生成声明**：本安装指南与项目源码主要由 AI 编码助手生成，经人工审核。
> 按 [MIT](LICENSE) 以 "AS IS" 提供，不附带担保。详见 [NOTICE](NOTICE)。
>
> **AI disclosure**: this guide and the project's source are primarily generated by
> AI coding assistants under human review, provided "AS IS" under [MIT](LICENSE).
> See [NOTICE](NOTICE).
