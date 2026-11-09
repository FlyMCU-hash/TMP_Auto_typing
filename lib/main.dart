import 'dart:async';
import 'dart:io';
import 'dart:isolate';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:tray_manager/tray_manager.dart';
import 'package:window_manager/window_manager.dart';

import 'afk_controller.dart';
import 'win/ets2_win.dart';

final _navKey = GlobalKey<NavigatorState>();

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await windowManager.ensureInitialized();
  const opts = WindowOptions(
    size: Size(440, 640),
    center: true,
    title: 'Peak欧卡挂机',
    titleBarStyle: TitleBarStyle.normal,
    backgroundColor: Color(0xFFF2F2F7),
  );
  await windowManager.waitUntilReadyToShow(opts, () async {
    await windowManager.setResizable(false);
    await windowManager.setPreventClose(true);
    await windowManager.show();
    await windowManager.focus();
  });
  runApp(const PeakAfkApp());
}

class PeakAfkApp extends StatelessWidget {
  const PeakAfkApp({super.key});

  @override
  Widget build(BuildContext context) {
    const accent = Color(0xFF007AFF);
    return MaterialApp(
      navigatorKey: _navKey,
      title: 'Peak欧卡挂机',
      debugShowCheckedModeBanner: false,
      locale: const Locale('zh', 'CN'),
      theme: ThemeData(
        useMaterial3: true,
        fontFamily: 'Microsoft YaHei UI',
        colorScheme: ColorScheme.fromSeed(seedColor: accent),
        scaffoldBackgroundColor: const Color(0xFFF2F2F7),
        cardTheme: const CardThemeData(
          color: Colors.white,
          elevation: 0,
          margin: EdgeInsets.zero,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(16)),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(0, 44),
            textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ),
      home: const AfkPage(),
    );
  }
}

class AfkPage extends StatefulWidget {
  const AfkPage({super.key});

  @override
  State<AfkPage> createState() => _AfkPageState();
}

class _AfkPageState extends State<AfkPage> with WindowListener, TrayListener {
  final _controller = AfkController();
  final _message = TextEditingController();
  final _interval = TextEditingController(text: '$minIntervalSeconds');
  SharedPreferences? _prefs;
  ReceivePort? _hotkeys;
  int _hotkeyThread = 0;
  bool _trayReady = false;
  bool _quitting = false;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onController);
    _controller.onWarn = _warn;
    _message.addListener(_syncFields);
    _interval.addListener(_syncFields);
    windowManager.addListener(this);
    unawaited(_boot());
  }

  Future<void> _boot() async {
    final prefs = await SharedPreferences.getInstance();
    _prefs = prefs;
    final savedMessage = prefs.getString('afk_message') ?? '';
    final storedInterval = prefs.getInt('afk_interval') ?? minIntervalSeconds;
    final savedInterval = storedInterval < minIntervalSeconds ? minIntervalSeconds : storedInterval;
    _message.text = savedMessage;
    _interval.text = '$savedInterval';
    _controller.message = savedMessage;
    _controller.intervalText = '$savedInterval';
    _controller.startWatch();
    await windowManager.setSize(const Size(440, 640));
    await _initTray();
    await _initHotkeys();
    if (mounted) setState(() {});
  }

  void _syncFields() {
    _controller.message = _message.text;
    _controller.intervalText = _interval.text;
    final prefs = _prefs;
    if (prefs == null) return;
    unawaited(prefs.setString('afk_message', _message.text));
    final n = parseInterval(_interval.text);
    if (n != null && n >= minIntervalSeconds) unawaited(prefs.setInt('afk_interval', n));
  }

  void _onController() {
    if (mounted) setState(() {});
  }

  Future<void> _warn(String text) async {
    if (_quitting) return;
    await windowManager.show();
    await windowManager.focus();
    final ctx = _navKey.currentContext;
    if (ctx == null || !ctx.mounted) return;
    await showDialog<void>(
      context: ctx,
      builder: (dialogContext) => AlertDialog(
        title: const Text('提示'),
        content: Text(text),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('知道了'),
          ),
        ],
      ),
    );
  }

  Future<void> _initTray() async {
    try {
      await trayManager.setIcon('assets/tray/app.ico');
      await trayManager.setToolTip('Peak欧卡挂机');
      await trayManager.setContextMenu(Menu(items: [
        MenuItem(key: 'show', label: '显示窗口'),
        MenuItem.separator(),
        MenuItem(key: 'exit', label: '退出'),
      ]));
      trayManager.addListener(this);
      _trayReady = true;
    } catch (_) {
      _trayReady = false;
    }
  }

  Future<void> _initHotkeys() async {
    final port = ReceivePort();
    _hotkeys = port;
    port.listen((message) {
      if (message is Map) {
        _hotkeyThread = (message['tid'] as int?) ?? 0;
        return;
      }
      if (message == 'start') _controller.start();
      if (message == 'stop') _controller.stop();
    });
    try {
      await Isolate.spawn(hotkeyIsolateMain, port.sendPort);
    } catch (_) {
      _hotkeyThread = 0;
    }
  }

  Future<void> _hideToTray() async {
    if (_trayReady) {
      await windowManager.hide();
    } else {
      await windowManager.minimize();
    }
  }

  Future<void> _quit() async {
    if (_quitting) return;
    _quitting = true;
    _controller.stop();
    quitHotkeyThread(_hotkeyThread);
    _hotkeys?.close();
    if (_trayReady) {
      try {
        await trayManager.destroy();
      } catch (_) {}
    }
    await windowManager.setPreventClose(false);
    await windowManager.close();
    exit(0);
  }

  @override
  void onWindowClose() {
    unawaited(_askClose());
  }

  Future<void> _askClose() async {
    final ctx = _navKey.currentContext;
    if (ctx == null || !ctx.mounted) {
      await _quit();
      return;
    }
    final hide = await showDialog<bool>(
      context: ctx,
      builder: (dialogContext) => AlertDialog(
        title: const Text('最小化到托盘'),
        content: const Text('是否最小化到系统托盘运行？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('退出'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('最小化'),
          ),
        ],
      ),
    );
    if (hide == true) {
      await _hideToTray();
    } else if (hide == false) {
      await _quit();
    }
  }

  @override
  void onTrayIconMouseDown() {
    unawaited(windowManager.show());
    unawaited(windowManager.focus());
  }

  @override
  void onTrayIconRightMouseDown() {
    unawaited(trayManager.popUpContextMenu());
  }

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'show':
        unawaited(windowManager.show());
        unawaited(windowManager.focus());
      case 'exit':
        unawaited(_quit());
    }
  }

  @override
  void dispose() {
    windowManager.removeListener(this);
    trayManager.removeListener(this);
    quitHotkeyThread(_hotkeyThread);
    _hotkeys?.close();
    _controller.dispose();
    _message.dispose();
    _interval.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final running = _controller.running;
    final gameOn = _controller.gameRunning;
    final canStart = gameOn && !running;
    final dot = running
        ? const Color(0xFF007AFF)
        : gameOn
            ? const Color(0xFF34C759)
            : const Color(0xFFC7C7CC);
    final processText = gameOn
        ? '检测到 Euro Truck Simulator 2 运行中'
        : '未检测到 Euro Truck Simulator 2，请先启动游戏';
    final processColor = gameOn ? const Color(0xFF34C759) : const Color(0xFFFF3B30);

    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Peak 欧卡挂机',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, height: 1.2),
            ),
            const SizedBox(height: 2),
            Text(
              'Euro Truck Simulator 2 自动发送',
              style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor),
            ),
            const SizedBox(height: 14),
            _card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _Caption('发送内容'),
                  const SizedBox(height: 6),
                  TextField(
                    controller: _message,
                    minLines: 3,
                    maxLines: 3,
                    style: const TextStyle(fontSize: 14, height: 1.3),
                    decoration: _field(hint: '要发到游戏聊天框的文字', fixedHeight: false),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            _card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _Caption('发送间隔'),
                  const SizedBox(height: 6),
                  Row(
                    children: [
                      SizedBox(
                        width: 88,
                        child: TextField(
                          controller: _interval,
                          textAlign: TextAlign.center,
                          keyboardType: TextInputType.number,
                          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700, height: 1.2),
                          decoration: _field(),
                        ),
                      ),
                      const SizedBox(width: 8),
                      const Text('秒', style: TextStyle(fontSize: 14)),
                      const Spacer(),
                      Text('最少 $minIntervalSeconds 秒', style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            _card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 10,
                        height: 10,
                        decoration: BoxDecoration(color: dot, shape: BoxShape.circle),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _controller.status,
                          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(processText, style: TextStyle(fontSize: 12, color: processColor, height: 1.3)),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton(
                    onPressed: canStart ? () => _controller.start() : null,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF34C759),
                      disabledBackgroundColor: const Color(0xFFC7C7CC),
                      foregroundColor: Colors.white,
                      disabledForegroundColor: Colors.white,
                    ),
                    child: const Text('启动'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton(
                    onPressed: running ? _controller.stop : null,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFFFF3B30),
                      disabledBackgroundColor: const Color(0xFFC7C7CC),
                      foregroundColor: Colors.white,
                      disabledForegroundColor: Colors.white,
                    ),
                    child: const Text('停止'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: FilledButton(
                    onPressed: _hideToTray,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF8E8E93),
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('最小化'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              'F10 启动    F11 停止    最小化到托盘后仍会后台发送',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor, height: 1.3),
            ),
            const Spacer(),
            _card(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Peak 社区', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
                  SizedBox(height: 4),
                  Text('车队接待群  515111100', style: TextStyle(fontSize: 13, color: Color(0xFF007AFF))),
                  SizedBox(height: 2),
                  Text('车队联运  YY 8457', style: TextStyle(fontSize: 13, color: Color(0xFF007AFF))),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '© 软件所有权归 Peak 社区所有',
              textAlign: TextAlign.right,
              style: TextStyle(fontSize: 11, color: Theme.of(context).hintColor),
            ),
          ],
        ),
      ),
    );
  }
}

class _Caption extends StatelessWidget {
  const _Caption(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(text, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700));
  }
}

Widget _card({required Widget child, EdgeInsetsGeometry padding = const EdgeInsets.all(12)}) {
  return Card(
    child: Padding(padding: padding, child: child),
  );
}

const _fieldBox = BoxConstraints(minHeight: 44, maxHeight: 44);

InputDecoration _field({String? hint, bool fixedHeight = true}) {
  return InputDecoration(
    hintText: hint,
    isDense: true,
    filled: true,
    fillColor: const Color(0xFFF2F2F7),
    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
    constraints: fixedHeight ? _fieldBox : const BoxConstraints(minHeight: 44),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: BorderSide.none,
    ),
  );
}
