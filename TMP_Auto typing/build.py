import subprocess
import sys
import os

def build():
    script = "main.py"
    output_dir = "dist"
    icon_path = None
    if os.path.exists("app.ico"):
        try:
            from PIL import Image as PILImage
            img = PILImage.open("app.ico")
            img = img.resize((256, 256), PILImage.LANCZOS)
            img.save("_build_icon.ico", format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            icon_path = "_build_icon.ico"
        except Exception:
            icon_path = "app.ico"
    
    cmd = [
        "pyinstaller",
        "--noconsole",
        "--onefile",
        "--windowed",
        "--name", "Peak欧卡挂机V1.5",
        "--distpath", output_dir,
        "--add-data", "app.ico" + os.pathsep + ".",
    ]

    if icon_path:
        cmd.extend(["--icon", icon_path])

    cmd.extend([
        "--hidden-import", "app",
        "--hidden-import", "win32_keys",
        "--hidden-import", "psutil",
        "--hidden-import", "pystray",
        "--hidden-import", "PIL",
        "--exclude-module", "PyQt5",
        "--exclude-module", "numpy",
        "--exclude-module", "pygame",
        "--exclude-module", "cv2",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "sklearn",
        script
    ])
    
    print(f"正在构建可执行文件...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(f"输出目录: {os.path.abspath(output_dir)}")
        
        exe_path = os.path.join(output_dir, "Peak欧卡挂机V1.5.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"✅ 可执行文件已生成: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print("❌ 可执行文件未找到")
            
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    build()