import 'dart:async';

import 'package:flutter/foundation.dart';

import 'win/ets2_win.dart';

/// 发送间隔下限。
const minIntervalSeconds = 60;

/// 把输入解析成秒。空或非数字返回 null。
int? parseInterval(String raw) => int.tryParse(raw.trim());

class AfkController extends ChangeNotifier {
  AfkController();

  bool gameRunning = false;
  bool running = false;
  String status = '等待启动';
  String message = '';
  String intervalText = '$minIntervalSeconds';

  void Function(String message)? onWarn;

  Timer? _watch;
  int _gen = 0;

  void startWatch() {
    _watch?.cancel();
    _poll();
    _watch = Timer.periodic(const Duration(seconds: 3), (_) => _poll());
  }

  void _poll() {
    bool on = false;
    try {
      on = isEuroTruckRunning();
    } catch (_) {
      on = false;
    }
    if (on == gameRunning) return;
    gameRunning = on;
    notifyListeners();
  }

  int get loopInterval {
    final n = parseInterval(intervalText);
    if (n == null || n < minIntervalSeconds) return minIntervalSeconds;
    return n;
  }

  /// 校验通过后开始循环。失败时弹出原因并返回 false。
  bool start() {
    if (running) return true;
    if (!gameRunning) {
      onWarn?.call('未检测到 Euro Truck Simulator 2 进程！\n请先启动游戏。');
      return false;
    }
    final text = message.trim();
    if (text.isEmpty) {
      onWarn?.call('发送内容不能为空！\n请在输入框中输入要发送的内容。');
      return false;
    }
    final interval = parseInterval(intervalText);
    if (interval == null) {
      onWarn?.call('请输入有效的间隔时间');
      return false;
    }
    if (interval < minIntervalSeconds) {
      onWarn?.call('间隔时间不能少于$minIntervalSeconds秒');
      return false;
    }

    running = true;
    status = '运行中...';
    final gen = ++_gen;
    notifyListeners();
    unawaited(_loop(gen));
    return true;
  }

  void stop() {
    if (!running && status == '已停止') return;
    running = false;
    _gen++;
    status = '已停止';
    notifyListeners();
  }

  Future<void> _loop(int gen) async {
    while (running && gen == _gen) {
      final seconds = loopInterval;
      final keepGoing = await _wait(Duration(seconds: seconds), gen);
      if (!keepGoing || !running || gen != _gen) break;
      await _execute(gen);
    }
  }

  Future<bool> _wait(Duration total, int gen) async {
    final end = DateTime.now().add(total);
    while (DateTime.now().isBefore(end)) {
      if (!running || gen != _gen) return false;
      final left = end.difference(DateTime.now());
      final slice = left < const Duration(milliseconds: 200)
          ? left
          : const Duration(milliseconds: 200);
      if (slice <= Duration.zero) break;
      await Future<void>.delayed(slice);
    }
    return running && gen == _gen;
  }

  Future<void> _execute(int gen) async {
    final hwnd = findEts2Window();
    if (gen != _gen) return;
    if (hwnd == 0) {
      status = '未找到游戏窗口，跳过本次';
      notifyListeners();
      return;
    }
    final text = message.trim();
    if (text.isEmpty) {
      status = '发送内容为空，跳过本次';
      notifyListeners();
      return;
    }
    try {
      status = '正在发送...';
      notifyListeners();
      await postChat(hwnd, text);
      if (gen != _gen) return;
      final shown = text.length > 20 ? '${text.substring(0, 20)}...' : text;
      status = '已发送: $shown';
    } catch (e) {
      if (gen != _gen) return;
      status = '发送错误: $e';
    }
    notifyListeners();
  }

  @override
  void dispose() {
    _watch?.cancel();
    running = false;
    _gen++;
    super.dispose();
  }
}
