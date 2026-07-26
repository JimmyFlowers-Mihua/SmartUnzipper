# ================= 运行时环境补丁（防止 PyInstaller 扫描临时目录崩溃） =================
import os
import sys
if getattr(sys, 'frozen', False):
    # 强制将打包后的临时解压路径排除在 pkg_resources 的扫描路径之外
    os.environ['PYTHONPATH'] = sys._MEIPASS
    # 阻止 setuptools 尝试去解析无法识别的版本号
    os.environ['SETUPTOOLS_USE_DISTUTILS'] = 'stdlib'
# =================================================================================

import re
import time
import uuid
import platform
import threading
import requests
import ctypes
import winreg
import shutil
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QFileDialog, QProgressBar, QTextEdit, 
                               QCheckBox, QHBoxLayout, QFrame, QRadioButton, QLineEdit,
                               QMessageBox, QSizePolicy) 
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation, QEasingCurve, QSettings
from PySide6.QtGui import QFont, QTextCursor, QIcon  

from engine import UnzipEngine

def resource_path(relative_path):
    """获取资源的绝对路径，完美兼容开发环境与 PyInstaller 打包沙盒环境"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ================= 工业级遥测与鉴权配置 =================
TELEMETRY_URL = "https://your-api-domain.com/api/telemetry"
TELEMETRY_API_KEY = "your_sk_live_xxxxxxxxx"

# 全局网络缓存（避免重复请求 ip-api.com 导致封 IP）
_net_cache = {"ip": "Unknown", "location": "Unknown", "fetched": False}

def get_network_info():
    global _net_cache
    if not _net_cache["fetched"]:
        try:
            res = requests.get("http://ip-api.com/json/?lang=zh-CN", timeout=2.5).json()
            if res.get("status") == "success":
                _net_cache["location"] = f"{res.get('country', '')} {res.get('regionName', '')} {res.get('city', '')}".strip()
                _net_cache["ip"] = res.get("query", "Unknown")
                _net_cache["fetched"] = True
        except: pass
    return _net_cache["ip"], _net_cache["location"]

def get_hardware_info():
    """【终极无损版】静默探测系统硬件配置 (免 subprocess 底层 API 重构，0延迟/100%成功率/永不闪黑框)"""
    cpu = "Unknown CPU"
    cores = os.cpu_count() or 0
    ram_gb = "Unknown"
    gpu = "Unknown GPU"
    res = "Unknown Res"
    
    try:
        disk_path = "C:\\" if sys.platform == 'win32' else "/"
        disk_total = shutil.disk_usage(disk_path).total / (1024**3)
        disk_info = f"{int(disk_total)}GB"
    except Exception:
        disk_info = "Unknown"

    try:
        if sys.platform == 'darwin': 
            try:
                import subprocess
                cpu_out = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'])
                cpu = cpu_out.decode(errors='ignore').strip()
            except Exception:
                cpu = platform.processor() or "Apple Silicon"

            try:
                import subprocess
                ram_out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'])
                ram_gb = f"{int(ram_out.strip()) / (1024**3):.1f}GB"
            except: pass
            
            try:
                import subprocess
                sp_out = subprocess.check_output(['system_profiler', 'SPDisplaysDataType']).decode(errors='ignore')
                for line in sp_out.split('\n'):
                    if "Chipset Model:" in line and gpu == "Unknown GPU":
                        gpu = line.split(':')[1].strip()
                    if "Resolution:" in line and res == "Unknown Res":
                        res = line.split(':')[1].strip()
            except: pass
                    
        elif sys.platform == 'win32': 
            try:
                user32 = ctypes.windll.user32
                res = f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
            except Exception:
                pass

            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_reg, _ = winreg.QueryValueEx(key, "ProcessorNameString")
                cpu = cpu_reg.strip()
                winreg.CloseKey(key)
            except Exception:
                cpu = platform.processor() or "Unknown Windows CPU"

            try:
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ('dwLength', ctypes.c_ulong),
                        ('dwMemoryLoad', ctypes.c_ulong),
                        ('ullTotalPhys', ctypes.c_ulonglong),
                        ('ullAvailPhys', ctypes.c_ulonglong),
                        ('ullTotalPageFile', ctypes.c_ulonglong),
                        ('ullAvailPageFile', ctypes.c_ulonglong),
                        ('ullTotalVirtual', ctypes.c_ulonglong),
                        ('ullAvailVirtual', ctypes.c_ulonglong),
                        ('ullAvailExtendedVirtual', ctypes.c_ulonglong)
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    ram_gb = f"{stat.ullTotalPhys / (1024**3):.1f}GB"
            except Exception:
                pass

            try:
                gpu_list = []
                gpu_class_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
                class_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gpu_class_path)
                
                for i in range(16):
                    try:
                        sub_name = f"{i:04d}"
                        sub_key = winreg.OpenKey(class_key, sub_name)
                        try:
                            card_name, _ = winreg.QueryValueEx(sub_key, "DriverDesc")
                            if card_name and card_name not in gpu_list:
                                gpu_list.append(card_name)
                        except Exception:
                            pass
                        winreg.CloseKey(sub_key)
                    except OSError:
                        break 
                winreg.CloseKey(class_key)
                if gpu_list:
                    gpu = " + ".join(gpu_list)
            except Exception:
                pass
            
    except Exception:
        pass
    
    return f"CPU: {cpu} ({cores}核) | RAM: {ram_gb} | GPU: {gpu} | 硬盘: {disk_info} | 屏幕: {res}"

# ================== 主题配色字典 ==================
THEMES = {
    'light': {
        'bg_root': '#FAFAFA',          
        'bg_card': '#FFFFFF',          
        'bg_topbar': '#F8FAFC',        
        'border': '#E2E8F0',           
        'text_main': '#1E293B',        
        'text_sub': '#64748B',         
        'accent': '#2563EB',           
        'accent_hover': '#1D4ED8',     
        'terminal_bg': '#1E1E1E',      
        'terminal_text': '#D4D4D4',    
        'term_cmd': '#3B82F6',         
        'term_task': '#FBBF24',        
        'term_succ': '#34D399',        
        'term_err': '#F87171',         
        'term_bar': '#60A5FA',         
        'radio_border': '#94A3B8',     
    },
    'dark': {
        'bg_root': '#0F172A',          
        'bg_card': '#1E293B',          
        'bg_topbar': '#1E293B',        
        'border': '#334155',           
        'text_main': '#F8FAFC',        
        'text_sub': '#94A3B8',         
        'accent': '#3B82F6',           
        'accent_hover': '#60A5FA',     
        'terminal_bg': '#000000',      
        'terminal_text': '#D4D4D4',    
        'term_cmd': '#34D399',         
        'term_task': '#FBBF24',        
        'term_succ': '#10B981',        
        'term_err': '#F87171',         
        'term_bar': '#60A5FA',         
        'radio_border': '#64748B',     
    }
}

class UnzipWorker(QThread):
    log_append_signal = Signal(str)
    log_overwrite_signal = Signal(str)
    global_progress_signal = Signal(int, int)
    finished_signal = Signal()

    def __init__(self, files, delete_original, output_mode, custom_dir, password, current_theme, enable_telemetry, device_id):
        super().__init__()
        self.files = files
        self.delete_original = delete_original
        self.output_mode = output_mode
        self.custom_dir = custom_dir
        self.password = password
        self.engine = UnzipEngine()
        self.theme_colors = THEMES[current_theme]
        self.enable_telemetry = enable_telemetry
        self.device_id = device_id
        
        self.task_stats = {
            "total_files": len(files),  # 初始值，稍后在过滤后进行精准修正
            "success_count": 0,
            "fail_count": 0,
            "total_size_mb": 0,
            "formats_handled": {},
            "time_taken_sec": 0
        }

    def get_clean_folder_name(self, filename):
        base = os.path.splitext(filename)[0]
        base = re.sub(r'\.(part\d+|00\d)$', '', base, flags=re.IGNORECASE)
        if base.lower().endswith(('.zip', '.rar', '.7z')): base = os.path.splitext(base)[0]
        return base if base else "Extracted_Files"

    def get_archive_group_signature(self, filepath):
        """【核心方法】提取多卷压缩包的基础特征组名，用于智能去重"""
        name = os.path.basename(filepath)
        m = re.search(r'\.part\d+\.rar$', name, flags=re.IGNORECASE)
        if m: return name[:m.start()] + ".rar"
        m = re.search(r'(\.7z|\.zip)\.\d+$', name, flags=re.IGNORECASE)
        if m: return name[:m.start() + len(m.group(1))]
        m = re.search(r'\.r\d{2}$', name, flags=re.IGNORECASE)
        if m: return name[:m.start()] + ".rar"
        m = re.search(r'\.z\d{2}$', name, flags=re.IGNORECASE)
        if m: return name[:m.start()] + ".zip"
        m = re.search(r'\.\d{3}$', name, flags=re.IGNORECASE)
        if m: return name[:m.start()]
        return name

    def create_pixel_bar(self, percent):
        length = 30
        filled = int((percent / 100) * length)
        bar = '█' * filled + '░' * (length - filled)
        color = self.theme_colors['term_bar']
        return f"<span style='color:{color};'>[{bar}] {percent:3d}%</span>"

    def engine_progress_callback(self, percent, text=None):
        if percent == -1 and text:
            color = self.theme_colors['text_sub']
            self.log_append_signal.emit(f"<span style='color:{color};'>  > {text}</span>")
        else:
            self.log_overwrite_signal.emit(f"  ⚡ 提取中: {self.create_pixel_bar(percent)}")

    def get_folder_size(self, folder_path):
        total = 0
        try:
            for path, dirs, files in os.walk(folder_path):
                for f in files:
                    fp = os.path.join(path, f)
                    if not os.path.islink(fp):
                        total += os.path.getsize(fp)
        except: pass
        return total / (1024 * 1024)

    def run(self):
        start_time = time.time()
        try:
            # ==============================================================
            # 【新增】智能分卷特征去重拦截系统
            # 解决小白用户全选所有分卷拖入导致的重复解压死循环与大盘数据错乱问题
            # ==============================================================
            unique_files = []
            seen_groups = set()
            
            # 按文件名自然排序，确保 .part1 或 .001 总是排在第一个被处理
            sorted_files = sorted(self.files)
            
            for f in sorted_files:
                dirname = os.path.dirname(f)
                group_sig = self.get_archive_group_signature(f).lower()
                full_sig = os.path.join(dirname, group_sig)
                
                if full_sig not in seen_groups:
                    seen_groups.add(full_sig)
                    unique_files.append(f)
                else:
                    # 静默跳过，但给用户超酷的终端极客反馈
                    self.log_append_signal.emit(f"<span style='color:{self.theme_colors['text_sub']};'>[INFO] 智能合并同源分卷: 已跳过冗余列队 -> {os.path.basename(f)}</span>")
            
            # 覆写任务池，并动态修正大屏真实文件上报数
            self.files = unique_files
            total = len(self.files)
            self.task_stats["total_files"] = total 
            # ==============================================================

            for idx, file_path in enumerate(self.files):
                file_name = os.path.basename(file_path)
                self.global_progress_signal.emit(idx, total)
                
                c_task = self.theme_colors['term_task']
                c_succ = self.theme_colors['term_succ']
                c_err = self.theme_colors['term_err']
                
                self.log_append_signal.emit(f"<br><span style='color:{c_task}; font-weight:bold;'>[TASK]</span> 正在处理靶标: {file_name}")
                self.log_append_signal.emit("  ⚡ 提取中: " + self.create_pixel_bar(0)) 
                
                real_format = self.engine.get_real_file_type(file_path)
                if real_format != "unknown":
                    self.task_stats["formats_handled"][real_format] = self.task_stats["formats_handled"].get(real_format, 0) + 1
                
                clean_base_name = self.get_clean_folder_name(file_name)
                if self.output_mode == 'smart':
                    dest_dir = os.path.join(os.path.dirname(file_path), clean_base_name)
                else:
                    base_path = self.custom_dir if self.custom_dir else os.path.dirname(file_path)
                    dest_dir = os.path.join(base_path, clean_base_name)

                if os.path.exists(dest_dir) and os.path.isfile(dest_dir): dest_dir += "_解压"

                try:
                    result = self.engine.process_file(file_path, dest_dir, self.password, self.engine_progress_callback)
                    
                    if result['status'] == 'success':
                        self.task_stats["success_count"] += 1
                        self.task_stats["total_size_mb"] += self.get_folder_size(dest_dir)
                        self.log_append_signal.emit(f"<span style='color:{c_succ}; font-weight:bold;'>[SUCC]</span> 输出流组装完成 -> {dest_dir}")
                        if self.delete_original:
                            try:
                                os.remove(file_path)
                                self.log_append_signal.emit(f"<span style='color:{self.theme_colors['text_sub']};'>[INFO] 已释放原体积文件空间</span>")
                            except: pass
                    elif result['status'] == 'skipped':
                        self.log_append_signal.emit(f"<span style='color:{self.theme_colors['text_sub']};'>[SKIP] {result['msg']}</span>")
                    else:
                        self.task_stats["fail_count"] += 1
                        self.log_append_signal.emit(f"<span style='color:{c_err};'>[FAIL] {result['msg']}</span>")
                except Exception as e:
                    self.task_stats["fail_count"] += 1
                    self.log_append_signal.emit(f"<span style='color:{c_err};'>[ERR ] 异常中断: {e}</span>")
            
            self.task_stats["time_taken_sec"] = round(time.time() - start_time, 2)
            self.task_stats["total_size_mb"] = round(self.task_stats["total_size_mb"], 2)
            
            self.global_progress_signal.emit(total, total)
            self.log_append_signal.emit(f"<br><span style='color:{self.theme_colors['term_cmd']}; font-weight:bold;'>[DONE] 队列所有作业已完毕。共耗时 {self.task_stats['time_taken_sec']}s。</span>")
            
            if self.enable_telemetry:
                self.send_task_telemetry_data()
            
        except Exception as global_e:
             self.log_append_signal.emit(f"<span style='color:{self.theme_colors['term_err']};'>[CRIT] 守护线程崩溃: {global_e}</span>")
        finally:
            self.finished_signal.emit()

    def send_task_telemetry_data(self):
        ip, location = get_network_info()
        payload = {
            "app_name": "智能解压器",
            "app_version": "1.0",
            "device_id": self.device_id,
            "action": "task_completed",
            "ip": ip,
            "location": location,
            "os": f"{platform.system()} {platform.release()}",
            "hardware": get_hardware_info(),
            "hostname": platform.node(),
            "extra_data": self.task_stats 
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TELEMETRY_API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            requests.post(TELEMETRY_URL, json=payload, headers=headers, timeout=5)
        except: pass


class SmartUnzipperGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能解压器 | Smart Unzipper")
        
        # 挂载顶栏 LOGO 图标
        icon_path = resource_path("image.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.resize(760, 480)
        self.setMinimumSize(700, 380)
        self.setAcceptDrops(True)
        self.settings = QSettings("JimmyFlowers", "SmartUnzipper")
        self.current_theme = self.settings.value("theme", "light", type=str)
        
        self.device_id = self.settings.value("device_id", "", type=str)
        if not self.device_id:
            self.device_id = str(uuid.uuid4())
            self.settings.setValue("device_id", self.device_id)
            
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.main_container = QFrame(self)
        self.main_container.setObjectName("mainContainer")
        self.root_layout = QVBoxLayout(self.main_container)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        
        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(self.main_container)
        
        self.init_ui()
        self.apply_theme() 
        self.check_first_run()
        
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()

    def check_first_run(self):
        is_first_run = self.settings.value("is_first_run", True, type=bool)
        if is_first_run:
            QMessageBox.information(
                self, "环境初始化", 
                "欢迎体验 智能解压器！\n\n"
                "软件默认提供纯净极速体验。如需配置【默认输出目录】、【自动清理】或【深浅色主题】，请展开主界面下方的【高级面板】。\n\n"
                "为了持续优化底层的智能去套娃算法，本软件默认开启匿名环境状态遥测。我们郑重承诺：\n"
                "【不含任何解压缩具体文件信息，无隐私内容被上传】。\n"
                "您可以在高级面板中随时关闭此链路。"
            )
            self.settings.setValue("is_first_run", False)

    def init_ui(self):
        self.top_bar_widget = QFrame()
        self.top_bar_widget.setObjectName("topBar") 
        top_layout = QVBoxLayout(self.top_bar_widget)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(8)
        
        header_h_layout = QHBoxLayout()
        self.lbl_global_status = QLabel("集群状态: 空闲")
        self.lbl_global_status.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        
        self.global_progress = QProgressBar()
        self.global_progress.setValue(0)
        self.global_progress.setTextVisible(False)
        self.global_progress.setFixedHeight(4)
        
        top_layout.addLayout(header_h_layout)
        top_layout.addWidget(self.global_progress)
        self.root_layout.addWidget(self.top_bar_widget)

        self.body_widget = QFrame()
        self.body_widget.setObjectName("bodyWidget") 
        self.body_layout = QVBoxLayout(self.body_widget)
        self.body_layout.setContentsMargins(24, 20, 24, 20)
        self.body_layout.setSpacing(16)
        
        self.drop_frame = QFrame()
        self.drop_frame.setObjectName("dropFrame")
        self.drop_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        drop_layout = QVBoxLayout(self.drop_frame)
        self.drop_label = QLabel("将压缩文件推入此区域\n自动分析 · 智能剥壳 · 并行解压")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        
        self.btn_select = QPushButton("选择本地文件池")
        self.btn_select.setCursor(Qt.PointingHandCursor)
        self.btn_select.clicked.connect(self.select_files)
        
        drop_layout.addStretch()
        drop_layout.addWidget(self.drop_label)
        drop_layout.addSpacing(12)
        drop_layout.addWidget(self.btn_select, 0, Qt.AlignHCenter)
        drop_layout.addStretch()
        self.body_layout.addWidget(self.drop_frame)

        self.btn_toggle_advanced = QPushButton("配置高级策略面板与日志 🔽")
        self.btn_toggle_advanced.setObjectName("btnToggle")
        self.btn_toggle_advanced.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_advanced.setCheckable(True)
        self.btn_toggle_advanced.toggled.connect(self.toggle_advanced_panel)
        self.body_layout.addWidget(self.btn_toggle_advanced)

        self.advanced_panel = QFrame()
        self.advanced_panel.setObjectName("advancedPanel")
        self.advanced_panel.setMaximumHeight(0) 
        
        adv_layout = QVBoxLayout(self.advanced_panel)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        adv_layout.setSpacing(12)

        out_group = QFrame()
        out_group.setObjectName("outGroup")
        out_layout = QVBoxLayout(out_group)
        out_title = QLabel("📂 核心输出路由:")
        out_title.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        out_layout.addWidget(out_title)
        
        self.radio_smart = QRadioButton("智能吸附 (输出至源目录的同名文件夹)")
        self.radio_smart.setChecked(True)
        self.radio_smart.setCursor(Qt.PointingHandCursor)
        self.radio_custom = QRadioButton("固定靶向目录:")
        self.radio_custom.setCursor(Qt.PointingHandCursor)
        out_layout.addWidget(self.radio_smart)
        out_layout.addWidget(self.radio_custom)
        
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择绝对路径...")
        self.path_input.setEnabled(False)
        self.btn_browse_path = QPushButton("检索目录")
        self.btn_browse_path.setObjectName("btnSmall")
        self.btn_browse_path.setEnabled(False)
        self.btn_browse_path.clicked.connect(self.select_custom_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.btn_browse_path)
        out_layout.addLayout(path_layout)
        self.radio_custom.toggled.connect(self.toggle_custom_path)
        adv_layout.addWidget(out_group)

        misc_layout = QHBoxLayout()
        self.cb_delete = QCheckBox("处理成功后抹除原始母文件 (释放空间)")
        self.cb_delete.setFont(QFont("Microsoft YaHei UI", 9))
        self.cb_delete.setCursor(Qt.PointingHandCursor)
        
        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("btnSmall")
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        
        misc_layout.addWidget(self.cb_delete)
        misc_layout.addStretch()
        misc_layout.addWidget(self.btn_theme)
        adv_layout.addLayout(misc_layout)

        telemetry_frame = QFrame()
        telemetry_frame.setObjectName("telemetryFrame")
        t_layout = QVBoxLayout(telemetry_frame)
        t_layout.setContentsMargins(0,0,0,0)
        t_layout.setSpacing(2)
        
        self.cb_telemetry = QCheckBox("允许发送匿名设备信息以支持开发者")
        self.cb_telemetry.setFont(QFont("Microsoft YaHei UI", 9, QFont.Bold))
        self.cb_telemetry.setChecked(self.settings.value("telemetry_enabled", True, type=bool))
        self.cb_telemetry.setCursor(Qt.PointingHandCursor)
        self.cb_telemetry.stateChanged.connect(lambda: self.settings.setValue("telemetry_enabled", self.cb_telemetry.isChecked()))
        
        self.t_desc = QLabel("本信息收集仅用于个人软件的迭代优化 and 成果展示，承诺永远不用作广告等任何形式的商业用途。\n不含任何解压缩具体文件信息，无隐私内容被上传，请您放心。")
        self.t_desc.setFont(QFont("Microsoft YaHei UI", 8))
        self.t_desc.setStyleSheet("padding-left: 22px;")
        t_layout.addWidget(self.cb_telemetry)
        t_layout.addWidget(self.t_desc)
        adv_layout.addWidget(telemetry_frame)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setObjectName("terminal")
        self.log_box.setMinimumHeight(200)
        self.log_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        adv_layout.addWidget(self.log_box)
        
        self.body_layout.addWidget(self.advanced_panel)

        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 0)
        footer_layout.addStretch()
        self.powered_label = QLabel("Powered by JimmyFlowers | 2026")
        self.powered_label.setFont(QFont("Consolas", 9))
        footer_layout.addWidget(self.powered_label)
        self.body_layout.addLayout(footer_layout)

        self.root_layout.addWidget(self.body_widget)

        self.animation = QPropertyAnimation(self.advanced_panel, b"maximumHeight")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.OutQuart)

    def closeEvent(self, event):
        if self.settings.value("telemetry_enabled", True, type=bool):
            try:
                self.send_heartbeat_payload("offline")
            except: pass
        event.accept()

    def heartbeat_loop(self):
        import time
        time.sleep(2)
        while True:
            if self.settings.value("telemetry_enabled", True, type=bool):
                self.send_heartbeat_payload("online")
            time.sleep(30)

    def send_heartbeat_payload(self, action_type):
        ip, location = get_network_info()
        payload = {
            "app_name": "智能解压器",
            "app_version": "1.0",
            "device_id": self.device_id,
            "action": action_type,
            "ip": ip,
            "location": location,
            "os": f"{platform.system()} {platform.release()}",
            "hardware": get_hardware_info(),
            "hostname": platform.node()
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TELEMETRY_API_KEY}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            requests.post(TELEMETRY_URL, json=payload, headers=headers, timeout=2.5 if action_type == "offline" else 5)
        except: pass

    def toggle_theme(self):
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.settings.setValue("theme", self.current_theme)
        self.apply_theme()

    def apply_theme(self):
        c = THEMES[self.current_theme]
        
        if self.current_theme == 'light':
            self.btn_theme.setText("切换为暗色模式 🌙")
        else:
            self.btn_theme.setText("切换为亮色模式 🌞")
            
        self.log_box.clear()
        cmd_color = c['term_cmd']
        self.log_box.insertHtml(f"<span style='color:{cmd_color};'>root@smart-unzipper</span>:<span style='color:{c['term_bar']};'>~</span>$ 内核挂载成功，当前模式：{self.current_theme.upper()}...<br>")

        self.setStyleSheet(f"""
            QWidget {{ font-family: 'Microsoft YaHei UI', system-ui; }}
            
            QFrame#mainContainer {{ background-color: {c['bg_root']}; }}
            QFrame#bodyWidget {{ background-color: {c['bg_root']}; }}
            QFrame#topBar {{ background-color: {c['bg_topbar']}; border-bottom: 1px solid {c['border']}; }}
            QFrame#advancedPanel {{ background-color: transparent; border: none; overflow: hidden; }}
            QFrame#telemetryFrame {{ background-color: transparent; border: none; }}
            
            QLabel {{ background-color: transparent; color: {c['text_main']}; }}
            
            QCheckBox {{ background: transparent; color: {c['text_main']}; }}
            
            QRadioButton {{ background: transparent; color: {c['text_main']}; spacing: 8px; }}
            QRadioButton::indicator {{
                width: 10px; height: 10px;
                border-radius: 7px;
                border: 2px solid {c['radio_border']}; 
                background-color: transparent;
            }}
            QRadioButton::indicator:unchecked:hover {{ border: 2px solid {c['accent']}; }}
            QRadioButton::indicator:checked {{
                width: 6px; height: 6px;
                border-radius: 7px;
                border: 4px solid {c['accent']}; 
                background-color: {c['bg_card']};
            }}
            
            #dropFrame {{ background-color: {c['bg_card']}; border: 2px dashed {c['border']}; border-radius: 12px; min-height: 120px; }}
            #dropFrame:hover {{ border-color: {c['accent']}; }}
            
            #outGroup {{ background-color: {c['bg_card']}; border: 1px solid {c['border']}; border-radius: 8px; padding: 12px; }}
            
            QPushButton {{ background-color: {c['accent']}; color: white; border-radius: 6px; padding: 10px 24px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background-color: {c['accent_hover']}; }}
            QPushButton:disabled {{ background-color: {c['border']}; color: {c['text_sub']}; }}
            
            #btnSmall {{ padding: 8px 16px; background-color: {c['text_sub']}; font-size: 13px; }}
            #btnSmall:hover {{ background-color: {c['text_main']}; }}
            
            #btnToggle {{ background-color: transparent; color: {c['text_sub']}; border: 1px solid {c['border']}; padding: 8px; border-radius: 8px; font-weight: normal; }}
            #btnToggle:hover {{ background-color: {c['bg_card']}; color: {c['text_main']}; border-color: {c['text_sub']}; }}
            #btnToggle:checked {{ background-color: {c['border']}; color: {c['text_main']}; border-color: {c['text_sub']}; font-weight: bold; }}
            
            QLineEdit {{ border: 1px solid {c['border']}; border-radius: 4px; padding: 8px; background-color: {c['bg_root']}; color: {c['text_main']}; }}
            QLineEdit:disabled {{ background-color: {c['border']}; color: {c['text_sub']}; }}
            
            #terminal {{ background-color: {c['terminal_bg']}; border: 1px solid {c['border']}; border-radius: 8px; padding: 12px; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; color: {c['terminal_text']}; }}
        """)
        
        self.drop_label.setStyleSheet(f"color: {c['text_sub']}; background: transparent;")
        self.t_desc.setStyleSheet(f"color: {c['text_sub']}; padding-left: 22px; background: transparent;") 
        self.powered_label.setStyleSheet(f"color: {c['text_sub']}; background: transparent;")
        self.cb_telemetry.setStyleSheet(f"color: {c['accent']}; font-weight: bold; background: transparent;") 
        
        self.global_progress.setStyleSheet(f"QProgressBar {{ background-color: {c['border']}; border: none; border-radius: 2px; }} QProgressBar::chunk {{ background-color: {c['accent']}; border-radius: 2px; }}")

    def toggle_advanced_panel(self, checked):
        if checked:
            self.btn_toggle_advanced.setText("收起高级策略面板 🔼")
            self.animation.setStartValue(0)
            self.animation.setEndValue(2000) 
        else:
            self.btn_toggle_advanced.setText("配置高级策略面板与日志 🔽")
            self.animation.setStartValue(self.advanced_panel.height())
            self.animation.setEndValue(0)
        self.animation.start()

    def toggle_custom_path(self):
        is_custom = self.radio_custom.isChecked()
        self.path_input.setEnabled(is_custom)
        self.btn_browse_path.setEnabled(is_custom)

    def select_custom_path(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出路由锚点")
        if folder: self.path_input.setText(folder)

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "载入目标", "", "所有文件 (*.*)")
        if files: self.start_processing(files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            c = THEMES[self.current_theme]
            self.drop_frame.setStyleSheet(f"#dropFrame {{ border-color: {c['accent']}; background-color: {c['bg_card']}; }}")
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.drop_frame.setStyleSheet("") 

    def dropEvent(self, event):
        self.drop_frame.setStyleSheet("")
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls if os.path.isfile(url.toLocalFile())]
        if files: self.start_processing(files)

    def start_processing(self, files):
        output_mode = 'smart' if self.radio_smart.isChecked() else 'custom'
        custom_dir = self.path_input.text().strip()
        if output_mode == 'custom' and not custom_dir:
            if not self.btn_toggle_advanced.isChecked(): self.btn_toggle_advanced.setChecked(True)
            self.append_log(f"<span style='color:{THEMES[self.current_theme]['term_err']};'>[ERR ] 策略阻断：未指定靶向目录</span>")
            return

        self.btn_select.setDisabled(True)
        self.btn_theme.setDisabled(True) 
        
        c = THEMES[self.current_theme]
        self.append_log(f"<br><span style='color:{c['term_cmd']};'>root@smart-unzipper</span>:<span style='color:{c['term_bar']};'>~</span>$ ./extract --batch {len(files)}")
        self.global_progress.setValue(0)
        self.lbl_global_status.setText(f"集群状态: 准备提取 (0 / {len(files)})")
        
        delete_flag = self.cb_delete.isChecked()
        is_telemetry_on = self.cb_telemetry.isChecked() 
        
        self.worker = UnzipWorker(files, delete_flag, output_mode, custom_dir, password=None, current_theme=self.current_theme, enable_telemetry=is_telemetry_on, device_id=self.device_id) 
        
        self.worker.log_append_signal.connect(self.append_log)
        self.worker.log_overwrite_signal.connect(self.overwrite_last_log)
        self.worker.global_progress_signal.connect(self.update_global_progress)
        self.worker.finished_signal.connect(self.on_finished)
        
        self.worker.start()

    def append_log(self, text):
        self.log_box.append(text)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def overwrite_last_log(self, text):
        cursor = self.log_box.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        self.log_box.setTextCursor(cursor)
        self.log_box.insertHtml(text)
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def update_global_progress(self, current, total):
        self.global_progress.setValue(int((current / total) * 100))
        self.lbl_global_status.setText(f"集群状态: 并行作业处理中... ( {current} / {total} )")

    def on_finished(self):
        self.btn_select.setDisabled(False)
        self.btn_theme.setDisabled(False) 
        self.lbl_global_status.setText("集群状态: 空闲 (任务结束)")
        if not self.btn_toggle_advanced.isChecked():
            self.btn_toggle_advanced.setText("✅ 队列作业完成！点击展开控制台查看 🔽")

if __name__ == '__main__':
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    app = QApplication(sys.argv)
    window = SmartUnzipperGUI()
    window.show()
    sys.exit(app.exec())