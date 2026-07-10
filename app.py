import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pystray
from PIL import Image, ImageDraw
import sys
import os

from win32_keys import post_press, post_hotkey, post_text, find_ets2_window, check_eurotrucks2, register_hotkeys, unregister_hotkeys

BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Peak欧卡挂机V1.5")
        self.root.geometry("420x320")
        self.root.resizable(False, False)
        icon_path = os.path.join(BASE_DIR, "app.ico")
        if os.path.exists(icon_path):
            try:
                ico_temp = os.path.join(BASE_DIR, "_temp_icon.ico")
                img = Image.open(icon_path)
                img = img.resize((256, 256), Image.LANCZOS)
                img.save(ico_temp, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
                self.root.iconbitmap(ico_temp)
            except Exception:
                try:
                    self.root.iconbitmap(icon_path)
                except Exception:
                    pass
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.is_running = False
        self.interval = tk.StringVar(value="30")
        self.stop_event = threading.Event()
        self.process_check_event = threading.Event()
        self.eurotrucks2_running = False
        self.hotkey_thread_id = None

        self.create_widgets()
        self.start_process_check()
        self.setup_tray()
        self.setup_hotkeys()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10 6")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_row = ttk.Frame(main_frame)
        top_row.pack(fill=tk.X, pady=(0, 5))
        top_row.columnconfigure(0, weight=1)
        top_row.columnconfigure(1, weight=0)

        text_frame = ttk.LabelFrame(top_row, text="发送内容", padding="5")
        text_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.text_entry = tk.Text(text_frame, height=3, font=("Microsoft YaHei", 9), wrap=tk.WORD)
        self.text_entry.pack(fill=tk.BOTH, expand=True)

        right_col = ttk.Frame(top_row)
        right_col.grid(row=0, column=1, sticky="ns")
        top_row.columnconfigure(1, minsize=155)

        interval_frame = ttk.LabelFrame(right_col, text="间隔(秒)", padding="5")
        interval_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Entry(interval_frame, textvariable=self.interval, width=6, font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="秒", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=2)

        info_frame = ttk.LabelFrame(right_col, text="Peak 社区/Peak Community", padding="5")
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="车队接待群 515111100", font=("Microsoft YaHei", 8, "bold"), foreground="#1565C0").pack(anchor=tk.W)
        ttk.Label(info_frame, text="车队联运 YY8457", font=("Microsoft YaHei", 8, "bold"), foreground="#1565C0").pack(anchor=tk.W)

        status_frame = ttk.LabelFrame(main_frame, text="当前状态", padding="5")
        status_frame.pack(fill=tk.X, pady=(0, 6))

        self.status_label = ttk.Label(status_frame, text="等待启动", font=("Microsoft YaHei", 9))
        self.status_label.pack()

        self.process_status_label = ttk.Label(status_frame, text="", font=("Microsoft YaHei", 8), foreground="red")
        self.process_status_label.pack(pady=(3, 0))

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(0, 5))

        self.start_btn = tk.Button(action_frame, text="▶ 启动", command=self.start,
                                    font=("Microsoft YaHei", 10, "bold"),
                                    bg="#9E9E9E", fg="white", relief=tk.RAISED, cursor="hand2", state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 4), expand=True, fill=tk.BOTH, ipady=5)

        self.stop_btn = tk.Button(action_frame, text="■ 停止", command=self.stop,
                                   font=("Microsoft YaHei", 10, "bold"),
                                   bg="#9E9E9E", fg="white", relief=tk.RAISED, cursor="hand2", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 4), expand=True, fill=tk.BOTH, ipady=5)

        tk.Button(action_frame, text="最小化", command=self.minimize_to_tray,
                  font=("Microsoft YaHei", 9, "bold"),
                  bg="#607D8B", fg="white", relief=tk.RAISED, cursor="hand2").pack(side=tk.LEFT, expand=True, fill=tk.BOTH, ipady=5)

        hotkey_frame = ttk.Frame(main_frame)
        hotkey_frame.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(hotkey_frame, text="快捷键：F10 启动  |  F11 停止  |  后台发送",
                  font=("Microsoft YaHei", 8), foreground="#666666").pack(anchor=tk.CENTER)

        copyright_frame = ttk.Frame(main_frame)
        copyright_frame.pack(fill=tk.X, pady=(1, 0))
        ttk.Label(copyright_frame, text="软件所有权归Peak社区所有",
                  font=("Microsoft YaHei", 8), foreground="#555555").pack(anchor=tk.E)

    def setup_hotkeys(self):
        self.hotkey_thread_id = register_hotkeys(
            lambda: self.root.after(0, self.start),
            lambda: self.root.after(0, self.stop)
        )

    def process_check_loop(self):
        while not self.process_check_event.is_set():
            self.eurotrucks2_running = check_eurotrucks2()
            self.root.after(0, self.update_process_status)
            time.sleep(3)

    def start_process_check(self):
        self.process_check_thread = threading.Thread(target=self.process_check_loop, daemon=True)
        self.process_check_thread.start()

    def update_process_status(self):
        if self.eurotrucks2_running:
            self.process_status_label.config(text="✅ 检测到 Euro Truck Simulator 2 运行中", foreground="green")
            if not self.is_running:
                self.start_btn.config(state=tk.NORMAL, bg="#4CAF50")
        else:
            self.process_status_label.config(text="❌ 未检测到 Euro Truck Simulator 2，请先启动游戏", foreground="red")
            if not self.is_running:
                self.start_btn.config(state=tk.DISABLED, bg="#9E9E9E")

    def run_loop(self):
        while not self.stop_event.is_set():
            try:
                interval = int(self.interval.get())
            except ValueError:
                interval = 30

            self.stop_event.wait(interval)

            if self.stop_event.is_set():
                break

            self.execute_action()

    def execute_action(self):
        hwnd = find_ets2_window()
        if not hwnd:
            self.root.after(0, lambda: self.update_status("⚠ 未找到游戏窗口，跳过本次"))
            return

        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            self.root.after(0, lambda: self.update_status("⚠ 发送内容为空，跳过本次"))
            return

        try:
            post_press(hwnd, 'y')
            time.sleep(0.5)
            post_text(hwnd, text)
            time.sleep(0.3)
            post_press(hwnd, 'enter')
            display_text = text[:20] + "..." if len(text) > 20 else text
            self.root.after(0, lambda: self.update_status(f"已发送: {display_text}"))
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"发送错误: {str(e)}"))

    def start(self):
        if not self.eurotrucks2_running:
            messagebox.showwarning("警告", "未检测到 Euro Truck Simulator 2 进程！\n请先启动游戏。")
            return

        text = self.text_entry.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "发送内容不能为空！\n请在输入框中输入要发送的内容。")
            return

        try:
            interval = int(self.interval.get())
            if interval < 5:
                messagebox.showwarning("警告", "间隔时间不能少于5秒")
                return
        except ValueError:
            messagebox.showwarning("警告", "请输入有效的间隔时间")
            return

        self.is_running = True
        self.stop_event.clear()
        self.start_btn.config(state=tk.DISABLED, bg="#9E9E9E")
        self.stop_btn.config(state=tk.NORMAL, bg="#F44336")
        self.update_status("运行中...")

        self.worker_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.is_running = False
        self.stop_event.set()
        if self.eurotrucks2_running:
            self.start_btn.config(state=tk.NORMAL, bg="#4CAF50")
        else:
            self.start_btn.config(state=tk.DISABLED, bg="#9E9E9E")
        self.stop_btn.config(state=tk.DISABLED, bg="#9E9E9E")
        self.update_status("已停止")

    def update_status(self, text):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def create_tray_icon(self):
        icon_path = os.path.join(BASE_DIR, "app.ico")
        if os.path.exists(icon_path):
            try:
                image = Image.open(icon_path)
                image = image.resize((64, 64), Image.LANCZOS)
                return image
            except Exception:
                pass
        image = Image.new('RGB', (64, 64), color=(0, 128, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 20, 54, 44], fill=(255, 255, 255))
        draw.rectangle([18, 12, 46, 24], fill=(255, 255, 255))
        draw.rectangle([8, 28, 14, 38], fill=(100, 100, 100))
        draw.rectangle([50, 28, 56, 38], fill=(100, 100, 100))
        return image

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("显示窗口", self.show_window),
            pystray.MenuItem("退出", self.quit_app)
        )

        self.tray_icon = pystray.Icon(
            "Peak欧卡挂机",
            self.create_tray_icon(),
            "Peak欧卡挂机助手",
            menu
        )

        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def minimize_to_tray(self):
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        self.root.after(0, self._show_window)

    def _show_window(self):
        self.root.deiconify()
        self.root.lift()

    def on_closing(self):
        if messagebox.askyesno("最小化到托盘", "是否最小化到系统托盘运行？"):
            self.minimize_to_tray()
        else:
            self.quit_app()

    def quit_app(self, icon=None, item=None):
        self.stop()
        self.process_check_event.set()
        unregister_hotkeys(self.hotkey_thread_id)

        if hasattr(self, 'tray_icon'):
            self.tray_icon.stop()

        self.root.after(0, self._quit_app)

    def _quit_app(self):
        self.root.destroy()
        sys.exit(0)