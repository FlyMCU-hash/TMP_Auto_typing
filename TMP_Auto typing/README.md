# Peak欧卡挂机助手 V1.5

Euro Truck Simulator 2 自动发送聊天消息工具，适用于 Peak 社区联机场景。

## 功能特性

- 🎮 自动检测 Euro Truck Simulator 2 进程
- 💬 后台向游戏窗口发送聊天消息
- ⏱️ 自定义发送间隔（最低5秒）
- 🖥️ 最小化到系统托盘运行
- ⌨️ 全局快捷键支持（F10 启动 / F11 停止）
- 🔒 未检测到游戏时禁止启动，防止误操作

## 使用方法

1. 启动 Euro Truck Simulator 2
2. 运行本程序，状态栏显示"检测到游戏运行中"
3. 在输入框中填写要发送的聊天内容
4. 设置发送间隔（秒），最低5秒
5. 点击"启动"或按 F10 开始自动发送
6. 点击"停止"或按 F11 停止

## 环境要求

- Windows 操作系统
- Python 3.8+
- Euro Truck Simulator 2

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 打包为 EXE

```bash
pip install pyinstaller
python build.py
```

打包完成后可执行文件位于 `dist/` 目录。

## 项目结构

```
├── main.py          # 程序入口
├── app.py           # GUI 界面与核心逻辑
├── win32_keys.py    # Windows 底层键盘消息与进程检测
├── build.py         # PyInstaller 打包脚本
├── app.ico          # 程序图标
├── requirements.txt # Python 依赖
├── LICENSE          # 开源许可证
└── README.md        # 项目说明
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| F10    | 启动自动发送 |
| F11    | 停止自动发送 |

## Peak 社区

- 车队接待群：515111100
- 车队联运 YY：8457

## 许可证

本项目基于 [MIT License](LICENSE) 开源。