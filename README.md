# Peak 欧卡挂机

给 Euro Truck Simulator 2 用的 Windows 挂机程序。游戏开着时，按设定的间隔把一段文字发进游戏聊天框。界面是 Peak 欧卡挂机 2.0。

## 做什么

- 检查欧卡是否已经启动，没检测到游戏就不能开始。
- 按间隔自动发送聊天。默认 60 秒，不能短于 60 秒。
- 用 F10 开始，F11 停止。
- 关掉窗口可以收到托盘里，后台继续发。
- 发送内容和间隔记在本机，下次打开还在。

发给游戏的内容由使用者自己填写。

## 怎么做的

用 Flutter 3.47 / Dart 3.13 写 Windows 桌面界面。找游戏、按键和热键走 Windows 接口，不读游戏内存。

1. 每隔几秒看系统里有没有 `eurotrucks2.exe`。
2. 到时间后，找到标题里带 Euro Truck 的窗口。
3. 向这个窗口发送 `Y`，打开聊天；再逐字送入文字；最后发送回车。
4. F10、F11 用全局热键注册，游戏在前台时也能用。
5. 窗口和托盘图标都用同一份 ICO。

## 改了什么

这一版替换了原来的 Python 程序。

- 界面和逻辑改成 Flutter / Dart，Python 源码已去掉。
- 最短发送间隔从 5 秒改为 60 秒，默认也是 60 秒。
- 聊天内容和间隔会保存，旧版每次都要重填。
- 窗口、任务栏和托盘统一使用原来的 ICO。
- 发送方式没变：仍然是 `Y`、文字、回车，热键仍是 F10 / F11。

## 文件

| 文件 | 作用 |
| --- | --- |
| `lib/main.dart` | 界面、窗口和托盘 |
| `lib/afk_controller.dart` | 间隔校验、计时和发送循环 |
| `lib/win/ets2_win.dart` | 检测游戏进程、向窗口发按键、注册 F10 / F11 |
| `assets/tray/app.ico` | 托盘图标 |
| `windows/runner/resources/app_icon.ico` | 窗口和程序图标 |
| `windows/runner/Runner.rc` | 把程序图标编进 Windows 程序 |
| `pubspec.yaml` | 项目名称、版本和依赖 |
| `test/widget_test.dart` | 间隔数字的校验 |
| `analysis_options.yaml` | 代码检查规则 |
| `LICENSE` | MIT 许可证 |

Peak 社区：车队接待群 515111100，车队联运 YY 8457。
