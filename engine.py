import os
import shutil
import subprocess
import re
import tempfile
import uuid

class UnzipEngine:
    def __init__(self, seven_zip_path="7z.exe"):
        self.seven_zip_path = os.path.join(os.path.dirname(__file__), seven_zip_path)
    
    def get_real_file_type(self, file_path):
        if not os.path.exists(file_path): return None
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'PK\x03\x04'): return 'zip'
                elif header.startswith(b'Rar!\x1a\x07\x00') or header.startswith(b'Rar!\x1a\x07\x01\x00'): return 'rar'
                elif header.startswith(b'7z\xbc\xaf\x27\x1c'): return '7z'
        except: pass
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.zip', '.rar', '.7z', '.001']: return ext[1:]
        if re.search(r'\.part\d+\.rar$', file_path.lower()): return 'rar'
        return "unknown"

    def is_main_part_file(self, file_path):
        filename = os.path.basename(file_path).lower()
        if '.part' in filename and filename.endswith('.rar'):
            if not re.search(r'\.part0*1\.rar$', filename): return False
        if re.search(r'\.\d{3}$', filename):
            if not filename.endswith('.001'): return False
        return True

    def extract_archive(self, archive_path, output_dir, password=None, progress_cb=None):
        if not os.path.exists(archive_path): return False, "文件不存在"
        CREATE_NO_WINDOW = 0x08000000 
        # 新增 -bsp1 参数，让7z输出实时进度百分比到 stdout
        cmd = [self.seven_zip_path, "x", archive_path, f"-o{output_dir}", "-y", "-bsp1"]
        if password: cmd.append(f"-p{password}")
            
        try:
            # 采用 Popen 实时捕获输出流
            process = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='gbk', errors='ignore')
            
            for line in process.stdout:
                if progress_cb:
                    # 正则捕获 7z 输出的 "  23%" 格式
                    match = re.search(r'^\s*(\d+)%', line)
                    if match:
                        progress_cb(int(match.group(1)))
            
            process.wait()
            if process.returncode == 0: return True, "解压成功"
            else: return False, "解压过程中发生错误"
        except Exception as e:
            return False, str(e)

    def handle_nested_archives(self, target_dir, password, progress_cb=None):
        while True:
            found_nested = False
            items = os.listdir(target_dir)
            for item in items:
                item_path = os.path.join(target_dir, item)
                if os.path.isfile(item_path):
                    if self.is_main_part_file(item_path) and self.get_real_file_type(item_path) != "unknown":
                        # 发现嵌套，通过回调发送专门的文字提示
                        if progress_cb: progress_cb(-1, f"发现嵌套套娃: {item}，正在执行深层递归剥离...")
                        
                        temp_nested = os.path.join(target_dir, f"_temp_nest_{uuid.uuid4().hex[:8]}")
                        os.makedirs(temp_nested, exist_ok=True)
                        
                        # 把当前的进度回调传给子解压任务
                        success, msg = self.extract_archive(item_path, temp_nested, password, lambda p: progress_cb(p) if progress_cb else None)
                        
                        if success:
                            prefix = item.rsplit('.', 1)[0]
                            for f in os.listdir(target_dir):
                                if f.startswith(prefix) and os.path.isfile(os.path.join(target_dir, f)):
                                    try: os.remove(os.path.join(target_dir, f))
                                    except: pass
                            
                            for sub_item in os.listdir(temp_nested):
                                shutil.move(os.path.join(temp_nested, sub_item), target_dir)
                            os.rmdir(temp_nested)
                            found_nested = True
                            break 
                        else:
                            os.rmdir(temp_nested)
            if not found_nested: break 

    def safe_remove_matryoshka(self, target_dir):
        while True:
            items = os.listdir(target_dir)
            if len(items) == 1:
                single_item_path = os.path.join(target_dir, items[0])
                if os.path.isdir(single_item_path):
                    temp_sub_dir = os.path.join(target_dir, f"_temp_sub_{uuid.uuid4().hex[:8]}")
                    os.rename(single_item_path, temp_sub_dir)
                    sub_items = os.listdir(temp_sub_dir)
                    for sub_item in sub_items:
                        shutil.move(os.path.join(temp_sub_dir, sub_item), target_dir)
                    os.rmdir(temp_sub_dir)
                else: break
            else: break

    def process_file(self, file_path, final_dest_dir, password=None, progress_cb=None):
        if not self.is_main_part_file(file_path): return {"status": "skipped", "msg": "非主分卷，已自动忽略防止重复"}
        if self.get_real_file_type(file_path) == "unknown": return {"status": "error", "msg": "未识别出支持的格式"}

        sandbox_dir = os.path.join(tempfile.gettempdir(), f"smart_unzip_{uuid.uuid4().hex[:8]}")
        os.makedirs(sandbox_dir, exist_ok=True)

        try:
            if progress_cb: progress_cb(-1, f"准备提取主文件...")
            success, msg = self.extract_archive(file_path, sandbox_dir, password, lambda p: progress_cb(p) if progress_cb else None)
            if not success: return {"status": "error", "msg": msg}

            if progress_cb: progress_cb(-1, f"扫描分析内部环境结构...")
            self.handle_nested_archives(sandbox_dir, password, progress_cb)
            
            if progress_cb: progress_cb(-1, f"清理外层无用套娃外壳...")
            self.safe_remove_matryoshka(sandbox_dir)

            os.makedirs(final_dest_dir, exist_ok=True)
            for item in os.listdir(sandbox_dir):
                source_item = os.path.join(sandbox_dir, item)
                dest_item = os.path.join(final_dest_dir, item)
                if os.path.exists(dest_item):
                    if os.path.isdir(dest_item): shutil.rmtree(dest_item)
                    else: os.remove(dest_item)
                shutil.move(source_item, final_dest_dir)

            return {"status": "success", "msg": "解压并智能重组完成！"}
        finally:
            if os.path.exists(sandbox_dir): shutil.rmtree(sandbox_dir)