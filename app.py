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
    # 主题配色
    BG_COLOR = "#F4F6F9"
    HEADER_BG = "#1E88E5"
    HEADER_FG = "#FFFFFF"
    PANEL_BG = "#FFFFFF"
    GREEN = "#43A047"
    RED = "#E53935"
    GRAY = "#9E9E9E"
    BLUE = "#1E88E5"
    DARK = "#263238"

    def __init__(self, root):
        self.root = root
        self.root.title("Peak欧卡挂机 V1.5")
        self.root.geometry("440x390")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG_COLOR)
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

    def make_button(self, parent, text, command, bg, active_bg, font_size=10, fg="white", side=tk.LEFT):
        """创建统一风格的圆角平面按钮"""
        def on_enter(e):
            e.widget.config(bg=active_bg, relief=tk.RAISED)
        def on_leave(e):
            e.widget.config(bg=bg, relief=tk.FLAT)
        btn = tk.Button(
            parent, text=text, command=command,
            font=("Microsoft YaHei", font_size, "bold"),
            bg=bg, fg=fg, relief=tk.FLAT, cursor="hand2",
            activebackground=active_bg, activeforeground=fg,
            bd=0, highlightthickness=0, pady=4
        )
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.pack(side=side, padx=2, expand=True, fill=tk.BOTH)
        return btn

    def create_header(self, parent):
        """顶部蓝色标题栏"""
        header = tk.Frame(parent, bg=self.HEADER_BG, height=46)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="Peak 欧卡挂机助手", font=("Microsoft YaHei", 14, "bold"),
                 bg=self.HEADER_BG, fg=self.HEADER_FG).pack(side=tk.LEFT, padx=14)
        tk.Label(header, text="Euro Truck Simulator 2 自动发送",
                 font=("Microsoft YaHei", 8), bg=self.HEADER_BG,
                 fg="#C7E3FF").pack(side=tk.RIGHT, padx=14)
        return header

    def create_widgets(self):
        self.create_header(self.root)

        # 主体容器
        main_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---------- 第一排：发送内容 + 右侧信息 ----------
        top_row = tk.Frame(main_frame, bg=self.BG_COLOR)
        top_row.pack(fill=tk.X, pady=(0, 8))
        top_row.columnconfigure(0, weight=1)
        top_row.columnconfigure(1, weight=0)

        # 发送内容卡片
        text_frame = tk.Frame(top_row, bg=self.PANEL_BG, highlightbackground="#DDE3EA",
                              highlightthickness=1, highlightcolor="#DDE3EA")
        text_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        tk.Label(text_frame, text="发送内容", font=("Microsoft YaHei", 9, "bold"),
                 bg=self.PANEL_BG, fg=self.DARK).pack(anchor=tk.W, padx=8, pady=(6, 2))

        self.text_entry = tk.Text(text_frame, height=3, font=("Microsoft YaHei", 10), wrap=tk.WORD,
                                  bd=0, highlightthickness=0, relief=tk.FLAT,
                                  padx=4, pady=2, bg="#FFFFFF")
        self.text_entry.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # 右侧栏
        right_col = tk.Frame(top_row, bg=self.BG_COLOR)
        right_col.grid(row=0, column=1, sticky="ns")
        top_row.columnconfigure(1, minsize=160)

        # 间隔卡片
        interval_frame = tk.Frame(right_col, bg=self.PANEL_BG, highlightbackground="#DDE3EA",
                                  highlightthickness=1, highlightcolor="#DDE3EA")
        interval_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(interval_frame, text="发送间隔", font=("Microsoft YaHei", 9, "bold"),
                 bg=self.PANEL_BG, fg=self.DARK).pack(anchor=tk.W, padx=8, pady=(6, 2))

        interval_row = tk.Frame(interval_frame, bg=self.PANEL_BG)
        interval_row.pack(anchor=tk.W, padx=8, pady=(0, 6))
        self.interval_entry = tk.Entry(interval_row, textvariable=self.interval, width=5, font=("Microsoft YaHei", 11, "bold"),
                                       justify=tk.CENTER, bd=0, highlightthickness=1,
                                       highlightbackground="#1E88E5", fg=self.BLUE, bg="#FFFFFF")
        self.interval_entry.pack(side=tk.LEFT, ipady=2)
        tk.Label(interval_row, text="秒", font=("Microsoft YaHei", 9),
                 bg=self.PANEL_BG, fg="#666666").pack(side=tk.LEFT, padx=(4, 0))

        # 社区信息卡片
        info_frame = tk.Frame(right_col, bg=self.PANEL_BG, highlightbackground="#DDE3EA",
                              highlightthickness=1, highlightcolor="#DDE3EA")
        info_frame.pack(fill=tk.X)

        tk.Label(info_frame, text="Peak 社区 / Peak Community", font=("Microsoft YaHei", 8, "bold"),
                 bg=self.BLUE, fg=self.HEADER_FG).pack(fill=tk.X, padx=0, ipady=2)

        tk.Label(info_frame, text="🚚 车队接待群  515111100", font=("Microsoft YaHei", 8, "bold"),
                 bg=self.PANEL_BG, fg="#1565C0").pack(anchor=tk.W, padx=8, pady=(5, 1))
        tk.Label(info_frame, text="🎙 车队联运  YY8457", font=("Microsoft YaHei", 8, "bold"),
                 bg=self.PANEL_BG, fg="#1565C0").pack(anchor=tk.W, padx=8, pady=(0, 5))

        # ---------- 当前状态卡片 ----------
        status_frame = tk.Frame(main_frame, bg=self.PANEL_BG, highlightbackground="#DDE3EA",
                                highlightthickness=1, highlightcolor="#DDE3EA")
        status_frame.pack(fill=tk.X, pady=(0, 8))

        status_header = tk.Frame(status_frame, bg=self.PANEL_BG)
        status_header.pack(fill=tk.X)
        self.status_dot = tk.Canvas(status_header, width=10, height=10, bg=self.PANEL_BG,
                                    highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(10, 6), pady=8)
        self.status_dot.create_oval(1, 1, 9, 9, fill="#BDBDBD", outline="")

        self.status_label = tk.Label(status_header, text="等待启动", font=("Microsoft YaHei", 9, "bold"),
                                     bg=self.PANEL_BG, fg=self.DARK)
        self.status_label.pack(side=tk.LEFT, pady=6)

        self.process_status_label = tk.Label(status_frame, text="", font=("Microsoft YaHei", 8),
                                             bg=self.PANEL_BG, fg=self.GRAY)
        self.process_status_label.pack(anchor=tk.W, padx=10, pady=(0, 6))

        # ---------- 操作按钮 ----------
        action_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        action_frame.pack(fill=tk.X, pady=(0, 8))

        self.start_btn = self.make_button(action_frame, "▶ 启动", self.start, self.GRAY, "#388E3C")
        self.stop_btn = self.make_button(action_frame, "■ 停止", self.stop, self.GRAY, "#D32F2F")
        self.make_button(action_frame, "最小化", self.minimize_to_tray, "#607D8B", "#455A64", font_size=9)

        # ---------- 快捷键说明 ----------
        hotkey_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        hotkey_frame.pack(fill=tk.X, pady=(2, 4))
        tip = ("F10 启动   |   F11 停止   |   最小化到托盘后自动向后台发送")
        tk.Label(hotkey_frame, text=tip, font=("Microsoft YaHei", 8),
                 bg=self.BG_COLOR, fg="#78909C").pack(anchor=tk.CENTER)

        # ---------- 版权 ----------
        copyright_frame = tk.Frame(main_frame, bg=self.BG_COLOR)
        copyright_frame.pack(fill=tk.X)
        tk.Label(copyright_frame, text="© 软件所有权归 Peak 社区所有",
                 font=("Microsoft YaHei", 8), bg=self.BG_COLOR,
                 fg="#B0BEC5").pack(anchor=tk.E)

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

    def set_status_dot(self, color):
        self.status_dot.delete("all")
        self.status_dot.create_oval(1, 1, 9, 9, fill=color, outline="")

    def update_process_status(self):
        if self.eurotrucks2_running:
            self.process_status_label.config(text="✅ 检测到 Euro Truck Simulator 2 运行中", foreground="#43A047")
            self.set_status_dot(self.GREEN)
            if not self.is_running:
                self.start_btn.config(state=tk.NORMAL, bg=self.GREEN)
        else:
            self.process_status_label.config(text="❌ 未检测到 Euro Truck Simulator 2，请先启动游戏", foreground="#E53935")
            self.set_status_dot("#BDBDBD")
            if not self.is_running:
                self.start_btn.config(state=tk.DISABLED, bg=self.GRAY)

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
        self.start_btn.config(state=tk.DISABLED, bg=self.GRAY)
        self.stop_btn.config(state=tk.NORMAL, bg=self.RED)
        self.update_status("运行中...")

        self.worker_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        self.is_running = False
        self.stop_event.set()
        if self.eurotrucks2_running:
            self.start_btn.config(state=tk.NORMAL, bg=self.GREEN)
            self.set_status_dot(self.GREEN)
        else:
            self.start_btn.config(state=tk.DISABLED, bg=self.GRAY)
            self.set_status_dot("#BDBDBD")
        self.stop_btn.config(state=tk.DISABLED, bg=self.GRAY)
        self.update_status("已停止")

    def update_status(self, text):
        self.status_label.config(text=text)
        if self.is_running:
            self.set_status_dot(self.BLUE)
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