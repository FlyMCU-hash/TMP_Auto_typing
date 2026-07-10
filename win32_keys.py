import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi

HOTKEY_START_ID = 1
HOTKEY_STOP_ID = 2
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
VK_F10 = 0x79
VK_F11 = 0x7A

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

SCAN_CODES = {
    'y': 0x15,
    'enter': 0x1C,
    'ctrl': 0x1D,
    'v': 0x2F,
}

VK_CODES = {
    'y': 0x59,
    'enter': 0x0D,
    'ctrl': 0x11,
    'v': 0x56,
}


def post_key_down(hwnd, key):
    key = key.lower()
    vk = VK_CODES[key]
    sc = SCAN_CODES[key]
    lParam = (sc << 16) | 1
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, lParam)


def post_key_up(hwnd, key):
    key = key.lower()
    vk = VK_CODES[key]
    sc = SCAN_CODES[key]
    lParam = (sc << 16) | 0xC0000001
    user32.PostMessageW(hwnd, WM_KEYUP, vk, lParam)


def post_press(hwnd, key):
    post_key_down(hwnd, key)
    time.sleep(0.05)
    post_key_up(hwnd, key)


def post_hotkey(hwnd, *keys):
    for key in keys:
        post_key_down(hwnd, key)
    time.sleep(0.05)
    for key in reversed(keys):
        post_key_up(hwnd, key)


def post_text(hwnd, text):
    encoded = text.encode('utf-16-le')
    for i in range(0, len(encoded), 2):
        code_unit = int.from_bytes(encoded[i:i+2], byteorder='little')
        user32.PostMessageW(hwnd, WM_CHAR, code_unit, 0)
        time.sleep(0.03)


def find_ets2_window():
    result = wintypes.HWND(0)

    def callback(hwnd, _):
        nonlocal result
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if 'euro truck' in buf.value.lower():
                result = hwnd
                return False
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return result


def check_eurotrucks2():
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010

    psapi.EnumProcesses.argtypes = [ctypes.POINTER(wintypes.DWORD), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    psapi.EnumProcesses.restype = wintypes.BOOL

    psapi.GetModuleBaseNameA.argtypes = [wintypes.HANDLE, wintypes.HMODULE, ctypes.c_char_p, wintypes.DWORD]
    psapi.GetModuleBaseNameA.restype = wintypes.DWORD

    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE

    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    cb = 1024 * ctypes.sizeof(wintypes.DWORD)
    process_ids = (wintypes.DWORD * (cb // ctypes.sizeof(wintypes.DWORD)))()
    cb_returned = wintypes.DWORD()

    if not psapi.EnumProcesses(process_ids, cb, ctypes.byref(cb_returned)):
        return False

    num_processes = cb_returned.value // ctypes.sizeof(wintypes.DWORD)

    for i in range(num_processes):
        pid = process_ids[i]
        if pid == 0:
            continue

        hProcess = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not hProcess:
            continue

        module_name = ctypes.create_string_buffer(260)
        if psapi.GetModuleBaseNameA(hProcess, None, module_name, 260):
            try:
                name = module_name.value.decode('mbcs', errors='ignore').lower()
            except Exception:
                name = ''
            if name == 'eurotrucks2.exe':
                kernel32.CloseHandle(hProcess)
                return True

        kernel32.CloseHandle(hProcess)

    return False


def register_hotkeys(callback_start, callback_stop):
    hotkey_thread_id = None

    def hotkey_loop():
        nonlocal hotkey_thread_id
        hotkey_thread_id = kernel32.GetCurrentThreadId()
        user32.RegisterHotKey(None, HOTKEY_START_ID, 0, VK_F10)
        user32.RegisterHotKey(None, HOTKEY_STOP_ID, 0, VK_F11)
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == WM_HOTKEY:
                if msg.wParam == HOTKEY_START_ID:
                    callback_start()
                elif msg.wParam == HOTKEY_STOP_ID:
                    callback_stop()
        user32.UnregisterHotKey(None, HOTKEY_START_ID)
        user32.UnregisterHotKey(None, HOTKEY_STOP_ID)

    import threading
    thread = threading.Thread(target=hotkey_loop, daemon=True)
    thread.start()
    return hotkey_thread_id


def unregister_hotkeys(hotkey_thread_id):
    if hotkey_thread_id:
        user32.PostThreadMessageW(hotkey_thread_id, WM_QUIT, 0, 0)