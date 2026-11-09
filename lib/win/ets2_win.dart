import 'dart:ffi';
import 'dart:isolate';

import 'package:ffi/ffi.dart';

const _wmKeyDown = 0x0100;
const _wmKeyUp = 0x0101;
const _wmChar = 0x0102;
const _wmHotkey = 0x0312;

const _vkY = 0x59;
const _scanY = 0x15;
const _vkEnter = 0x0D;
const _scanEnter = 0x1C;
const _vkF10 = 0x79;
const _vkF11 = 0x7A;

const _processQuery = 0x0400;
const _processVmRead = 0x0010;

final _user32 = DynamicLibrary.open('user32.dll');
final _kernel32 = DynamicLibrary.open('kernel32.dll');
final _psapi = DynamicLibrary.open('psapi.dll');

final _postMessageW = _user32.lookupFunction<
    Int32 Function(IntPtr hwnd, Uint32 msg, IntPtr wParam, IntPtr lParam),
    int Function(int hwnd, int msg, int wParam, int lParam)>('PostMessageW');

final _isWindowVisible =
    _user32.lookupFunction<Int32 Function(IntPtr hwnd), int Function(int hwnd)>(
        'IsWindowVisible');

final _getWindowTextLengthW =
    _user32.lookupFunction<Int32 Function(IntPtr hwnd), int Function(int hwnd)>(
        'GetWindowTextLengthW');

final _getWindowTextW = _user32.lookupFunction<
    Int32 Function(IntPtr hwnd, Pointer<Utf16> text, Int32 max),
    int Function(int hwnd, Pointer<Utf16> text, int max)>('GetWindowTextW');

final _enumWindows = _user32.lookupFunction<
    Int32 Function(Pointer<NativeFunction<EnumWindowsProc>> cb, IntPtr lParam),
    int Function(Pointer<NativeFunction<EnumWindowsProc>> cb, int lParam)>(
        'EnumWindows');

final _registerHotKey = _user32.lookupFunction<
    Int32 Function(IntPtr hwnd, Int32 id, Uint32 mods, Uint32 vk),
    int Function(int hwnd, int id, int mods, int vk)>('RegisterHotKey');

final _unregisterHotKey = _user32.lookupFunction<
    Int32 Function(IntPtr hwnd, Int32 id),
    int Function(int hwnd, int id)>('UnregisterHotKey');

final _getMessageW = _user32.lookupFunction<
    Int32 Function(Pointer<MSG> msg, IntPtr hwnd, Uint32 min, Uint32 max),
    int Function(Pointer<MSG> msg, int hwnd, int min, int max)>('GetMessageW');

final _postThreadMessageW = _user32.lookupFunction<
    Int32 Function(Uint32 tid, Uint32 msg, IntPtr wParam, IntPtr lParam),
    int Function(int tid, int msg, int wParam, int lParam)>('PostThreadMessageW');

final _getCurrentThreadId =
    _kernel32.lookupFunction<Uint32 Function(), int Function()>('GetCurrentThreadId');

final _openProcess = _kernel32.lookupFunction<
    IntPtr Function(Uint32 access, Int32 inherit, Uint32 pid),
    int Function(int access, int inherit, int pid)>('OpenProcess');

final _closeHandle =
    _kernel32.lookupFunction<Int32 Function(IntPtr handle), int Function(int handle)>(
        'CloseHandle');

final _enumProcesses = _psapi.lookupFunction<
    Int32 Function(Pointer<Uint32> pids, Uint32 cb, Pointer<Uint32> needed),
    int Function(Pointer<Uint32> pids, int cb, Pointer<Uint32> needed)>('EnumProcesses');

final _getModuleBaseNameA = _psapi.lookupFunction<
    Uint32 Function(IntPtr process, IntPtr module, Pointer<Uint8> name, Uint32 size),
    int Function(int process, int module, Pointer<Uint8> name, int size)>(
        'GetModuleBaseNameA');

typedef EnumWindowsProc = Int32 Function(IntPtr hwnd, IntPtr lParam);

final class POINT extends Struct {
  @Int32()
  external int x;

  @Int32()
  external int y;
}

final class MSG extends Struct {
  @IntPtr()
  external int hwnd;

  @Uint32()
  external int message;

  @IntPtr()
  external int wParam;

  @IntPtr()
  external int lParam;

  @Uint32()
  external int time;

  external POINT pt;

  @Uint32()
  external int lPrivate;
}

int? _foundHwnd;

int _enumWindowsProc(int hwnd, int lParam) {
  if (_isWindowVisible(hwnd) == 0) return 1;
  final len = _getWindowTextLengthW(hwnd);
  if (len <= 0) return 1;
  final buf = calloc<Uint16>(len + 1);
  try {
    final text = buf.cast<Utf16>();
    _getWindowTextW(hwnd, text, len + 1);
    final title = text.toDartString().toLowerCase();
    if (title.contains('euro truck')) {
      _foundHwnd = hwnd;
      return 0;
    }
  } finally {
    calloc.free(buf);
  }
  return 1;
}

final _enumCallback = Pointer.fromFunction<EnumWindowsProc>(_enumWindowsProc, 0);

/// 找到标题里带 Euro Truck 的可见窗口。找不到返回 0。
int findEts2Window() {
  _foundHwnd = null;
  _enumWindows(_enumCallback, 0);
  return _foundHwnd ?? 0;
}

bool isEuroTruckRunning() {
  const slots = 1024;
  final pids = calloc<Uint32>(slots);
  final needed = calloc<Uint32>();
  try {
    if (_enumProcesses(pids, slots * 4, needed) == 0) return false;
    final count = needed.value ~/ 4;
    for (var i = 0; i < count && i < slots; i++) {
      final pid = pids[i];
      if (pid == 0) continue;
      final handle = _openProcess(_processQuery | _processVmRead, 0, pid);
      if (handle == 0) continue;
      final nameBuf = calloc<Uint8>(260);
      try {
        if (_getModuleBaseNameA(handle, 0, nameBuf, 260) == 0) continue;
        final bytes = <int>[];
        for (var n = 0; n < 260; n++) {
          final b = nameBuf[n];
          if (b == 0) break;
          bytes.add(b);
        }
        final name = String.fromCharCodes(bytes).toLowerCase();
        if (name == 'eurotrucks2.exe') return true;
      } finally {
        calloc.free(nameBuf);
        _closeHandle(handle);
      }
    }
  } finally {
    calloc.free(pids);
    calloc.free(needed);
  }
  return false;
}

void _postKey(int hwnd, int vk, int scan, bool down) {
  final lParam = down ? (scan << 16) | 1 : (scan << 16) | 0xC0000001;
  _postMessageW(hwnd, down ? _wmKeyDown : _wmKeyUp, vk, lParam);
}

Future<void> postPress(int hwnd, {required int vk, required int scan}) async {
  _postKey(hwnd, vk, scan, true);
  await Future<void>.delayed(const Duration(milliseconds: 50));
  _postKey(hwnd, vk, scan, false);
}

Future<void> postChat(int hwnd, String text) async {
  await postPress(hwnd, vk: _vkY, scan: _scanY);
  await Future<void>.delayed(const Duration(milliseconds: 500));
  for (final unit in text.codeUnits) {
    _postMessageW(hwnd, _wmChar, unit, 0);
    await Future<void>.delayed(const Duration(milliseconds: 30));
  }
  await Future<void>.delayed(const Duration(milliseconds: 300));
  await postPress(hwnd, vk: _vkEnter, scan: _scanEnter);
}

/// 在独立 isolate 里注册 F10 / F11。先回传 `{tid, ok}`，之后回传 `start` / `stop`。
void hotkeyIsolateMain(SendPort send) {
  final tid = _getCurrentThreadId();
  final f10 = _registerHotKey(0, 1, 0, _vkF10);
  final f11 = _registerHotKey(0, 2, 0, _vkF11);
  send.send({'tid': tid, 'ok': f10 != 0 && f11 != 0});

  final msg = calloc<MSG>();
  try {
    while (_getMessageW(msg, 0, 0, 0) != 0) {
      if (msg.ref.message == _wmHotkey) {
        if (msg.ref.wParam == 1) send.send('start');
        if (msg.ref.wParam == 2) send.send('stop');
      }
    }
  } finally {
    _unregisterHotKey(0, 1);
    _unregisterHotKey(0, 2);
    calloc.free(msg);
  }
}

void quitHotkeyThread(int threadId) {
  if (threadId == 0) return;
  _postThreadMessageW(threadId, 0x0012, 0, 0);
}
