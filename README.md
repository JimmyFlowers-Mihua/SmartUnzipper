# 📦 智能解压器 (Smart Unzipper)

[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue.svg)](#)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/UI-PySide6-green.svg)](#)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Funder](https://img.shields.io/badge/Powered%20by-JimmyFlowers-orange.svg)](#)

一款基于 Python (PySide6) + 原生 7z 引擎架构开发的轻量级、极客风智能桌面解压软件。彻底解决传统解压软件“多层嵌套文件夹（套娃）”和“分卷重复解压报错”的痛点。

本项目已实现将底层 C++ 引擎与 Python 运行库进行单文件沙盒化封装。双击即开，无需安装，用完即走，为您提供工业级的数据吞吐与极其纯净的极客体验。

---

## 🚀 极速下载与运行提示（小白/用户通道）

### 📥 软件直接下载
如果您不想配置 Python 环境进行编译，**推荐直接下载原作者已打包好的单文件免安装版本**：

[📊 点击前往 Release 页面下载最新版 (.exe / .app)](https://github.com/JimmyFlowers-Mihua/SmartUnzipper/releases)

> **⚠️ 运行必看：**
> 1. **单文件沙盒初始化（正常现象）**：由于本软件为极致的单文件绿色版本，内置了原生 7z 底层引擎，首次双击运行时系统需在内存中释放虚拟环境，**约有 1-3 秒的加载延迟，这是完全正常的**。
> 2. **杀毒软件误报**：单文件打包技术（PyInstaller）常被 360 或 Windows Defender 误判为未知程序。本软件代码完全开源且不包含任何恶意逻辑，若遇拦截请添加信任。
> 3. **macOS 提示“文件损坏”**：苹果系统的安全防护机制极其严格，若遇报错请参考下方 [🔧 macOS 权限解锁指南](#-macos-权限解锁与损坏解决指南)。

---

## 💡 开发者真诚的请求 (Telemetry & Data Request)

本软件在 **原作者编译分发的官方 Release 版本** 中，内置了基于异步无阻塞架构的设备状态遥测模块。

> **🎓 致技术社区的一封信：**
> 本项目作为作者本人的 **求职面试与技术能力展示的支撑成果**，非常需要收集一些真实用户的匿名使用数据和装机量进行生态大盘展示。
> * **隐私绝对安全**：我郑重承诺，遥测链路 **全程阻断任何解压缩的具体文件名及文件内容**。收集的数据仅包含：粗略地理位置、硬件配置指纹、处理文件总量及成功率。
> * **数据承诺**：收集到的所有大盘数据**永远不会用于广告、画像等任何形式的商业用途或牟利**。
> * **版本请求**：如果您觉得这个软件对您有帮助，**恳请您尽可能直接使用我官方 Release 页面分发的编译版本**。其他人自行下载源码重新打包分发的版本，由于没有我的安全密钥，无法参与数据贡献，且其安全性作者无法保证。
> 
> 感谢每一位为开发者求职助力点灯的老师与技术同仁！

---

## ✨ 核心亮点与技术特性

### 🤖 智能去套娃算法 (Smart Extraction)
* **物理提档与空壳抹杀**：自动检测解压后是否存在“文件夹里只有同名文件夹”的冗余嵌套（套娃）。一旦触发特征，引擎将瞬间把内层文件提档至外层，并物理抹杀多余空壳，一步到位。
* **智能路径吸附**：无需手动选择输出路径，软件默认将解压流组装至源压缩包同级目录。

### ⚡ 极速多线程队列与底层并发
* **三路独立线程架构**：主线程专职渲染 UI 动画，后台独立挂载解压守护线程与心跳守护线程。无论吞吐多少 GB 的超大文件，界面永远丝滑，绝不卡死无响应。
* **多核榨干机制**：内置原生 7z 核心，单任务执行时瞬间接管 CPU 全核心进行暴力运算，挑战磁盘 I/O 物理极限。

### 🗂️ 智能分卷特征去重 (Smart Deduplication)
* **小白防呆设计**：当用户错误地将 `part1` 到 `part10` 全部拖入软件时，独家自研的同源特征去重算法会瞬间介入。自动踢出冗余任务，只对头部分卷发起一次合并解压请求，彻底杜绝死循环覆盖与数据错乱。

### 🎨 极客级 UI 与双轨主题
* **PySide6 工业级渲染**：彻底摒弃传统解压软件的陈旧外观，融入现代扁平化与控制台风格。
* **深浅色无缝热切换**：内置 Light / Dark 双轨主题引擎，配置一键持久化至系统底层注册表（QSettings），绿色无痕。

---

## 🛠️ 项目文件结构

```text
SmartUnzipper/
├── main.py                 # PySide6 客户端主线程、UI 渲染与遥测心跳钩子
├── engine.py               # 核心解压引擎、智能去套娃与异常捕获逻辑
├── image.ico               # Windows 应用程序图标
├── 7z.exe                  # Windows 环境 7z 核心底层二进制引擎
└── 7z.dll                  # Windows 环境 7z 运行动态链接库
```

---

## 💻 开发者运行与本地编译指南

在开始前，请克隆本项目并进入根目录：

```bash
git clone https://github.com/JimmyFlowers-Mihua/SmartUnzipper.git
cd SmartUnzipper
```

### 1. 依赖环境安装
建议在虚拟环境或全局环境下执行以下安装（包含核心框架与打包工具）：

```bash
pip install PySide6 requests pyinstaller
```

### 2. 开发者脱敏说明
在分发或编译前，如果你需要配置自己的遥测监控大屏服务端，请修改 `main.py` 顶部的以下变量：

```python
# 将其修改为你自己的 Webhook 地址和校验密钥
TELEMETRY_URL = "https://your-api-domain.com/api/telemetry"
TELEMETRY_API_KEY = "your_sk_live_xxxxxxxxx"
```

---

## 📦 跨平台单文件打包 (Release Build)

本项目已经过精细的打包资源挂载优化，包含运行时沙盒补丁，彻底解决打包后无法读取 `7z` 引擎及左上角 Logo 图标丢失的问题。

### 🔌 Windows 端终极打包口令
请确保 `image.ico`、`7z.exe`、`7z.dll` 与 `main.py` 同处一个根目录下。在终端中执行以下命令（包含无黑框隐藏、图标注入与二进制文件内嵌）：

```cmd
python -m PyInstaller -F -w -n "智能解压器" -i "image.ico" --add-data "image.ico;." --add-binary "7z.exe;." --add-binary "7z.dll;." main.py
```
打包完成后，在 `dist` 目录下会生成一个独立的 `智能解压器.exe`，直接双击运行即可体验。

### 🍎 macOS 端打包与权限解锁
*(注：若需在 macOS 下打包，需将项目内的 `7z.exe/dll` 替换为 Mac 版的原生 `7zz` 二进制文件，并修改相应的打包命令与 `engine.py` 调用路径。)*
##本项目本次没有针对macOS优化，请自行检查macOS兼容性，您可能需要修改一定量的代码内容##

由于 macOS 的安全防护机制（Gatekeeper）非常严格，对于未付费签名的开发者作品，会默认拦截并提示“已损坏”。解除限制请在终端输入：
```bash
sudo spctl --master-disable
# 若双击仍报错，请使用以下命令清除 App 安全隔离属性：
xattr -cr /Applications/智能解压器.app
```

---

## ⚖️ 开源许可协议 & 商业限制声明 (License)

本项目代码在 **GPL v3.0 (GNU General Public License v3)** 协议下开源，并附加以下双重许可与商业行为限制条款：

1. **强制开源传染 (GPL v3.0)**
任何个人或团队在分发、修改或基于本项目进行二次开发时，衍生作品必须同样以 GPL v3.0 协议完全开源，严禁闭源。

2. **严禁未经授权的商业行为 (Commercial Use Restriction)**
* **严禁闭源牟利**：任何个人、团队或商业机构，不得在未经原作者（JimmyFlowers）书面授权的情况下，将本项目代码或编译后的程序进行直接售卖、倒卖或闭源打包商业化。
* **严禁未授权集成**：本软件及其任何代码片段、算法逻辑（如智能去套娃模块），不得作为收费系统的内置模块使用。
* **必须保留署名**：任何分发 and 修改版本中，必须在显著位置保留原作者 JimmyFlowers 的署名及本项目 GitHub 源代码仓库链接。

💡 **商业授权获取**：
如果您需要在企业内部闭源部署使用、将本项目用于商业盈利性整合、或进行任何不适用 GPL v3.0 开源传染限制的商业集成，请主动联系原作者 JimmyFlowers 协商获取商业许可证书。

---

Created with ❤️ by JimmyFlowers  
如果您觉得这个项目或大屏生态闭环的设计帮到了您，欢迎在 GitHub 上点一个 ⭐ Star！如有任何问题或优化建议，欢迎提交 Issue。
