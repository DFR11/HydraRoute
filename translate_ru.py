import os
import re
import time
import tarfile
import tempfile
import shutil
from deep_translator import GoogleTranslator

# --- 配置 ---
translator = GoogleTranslator(source='auto', target='en')
SLEEP_TIME = 0.5 

# --- 全局统计 ---
TOTAL_MODIFIED = 0

def do_translate(text):
    if not text or not text.strip():
        return text
    # 排除纯符号、数字、IP、路径
    if re.match(r'^[\W\d]+$', text) or '/opt/' in text or '192.168.' in text:
        return text
    
    try:
        res = translator.translate(text)
        time.sleep(SLEEP_TIME)
        # 日志截断
        print(f"      [Trans] {text[:25]}... -> {res[:25]}...")
        return res
    except Exception as e:
        print(f"      [Error] {e}")
        return text

def read_file_content(file_path):
    encodings = ['utf-8', 'windows-1251', 'cp1251', 'latin1']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.readlines()
            return content, enc
        except UnicodeDecodeError:
            continue
    return None, None

def has_cyrillic(text):
    return bool(re.search(r'[а-яА-Я]', text))

def process_single_file(file_path, inside_tar=False):
    """处理单个文本文件的逻辑"""
    global TOTAL_MODIFIED
    prefix_log = "    " if inside_tar else ""
    
    # 简单的扩展名/文件名过滤
    valid_exts = ['.sh', '.cfg', '.conf', '.list', '.txt', '.json', '.xml']
    valid_names = ['config', 'Makefile', 'control', 'postinst', 'prerm']
    
    if not (any(file_path.endswith(ext) for ext in valid_exts) or os.path.basename(file_path) in valid_names):
        # 如果不是目标文本文件，直接跳过
        return False

    print(f"{prefix_log}Checking: {os.path.basename(file_path)}")
    lines, encoding = read_file_content(file_path)
    if not lines:
        return False

    new_lines = []
    modified = False

    # 正则：匹配引号内容
    string_pattern = re.compile(r'(["\'])(.*?)(["\'])')
    # 正则：匹配注释
    comment_pattern = re.compile(r'^(.*?)(#\s+)(.*)$')

    for line in lines:
        if line.strip().startswith("#!"):
            new_lines.append(line)
            continue

        # A. 注释
        match_comment = comment_pattern.match(line)
        if match_comment:
            pre, mark, content = match_comment.groups()
            if has_cyrillic(content):
                trans_content = do_translate(content)
                line = f"{pre}{mark}{trans_content}\n"
                modified = True
        
        # B. 字符串 (引号内)
        def replace_str(match):
            q_open, content, q_close = match.groups()
            # 必须包含俄语，且不包含复杂的命令替换反引号
            if has_cyrillic(content) and '`' not in content:
                nonlocal modified
                modified = True
                return f"{q_open}{do_translate(content)}{q_close}"
            return match.group(0)

        line = string_pattern.sub(replace_str, line)
        new_lines.append(line)

    if modified:
        print(f"{prefix_log}-> Modified: {os.path.basename(file_path)}")
        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(new_lines)
        TOTAL_MODIFIED += 1
        return True
    return False

def process_tar_file(file_path):
    """处理压缩包：解压 -> 遍历翻译 -> 重打包"""
    print(f"📦 Found Archive: {file_path}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    modified_in_tar = False
    
    try:
        # 1. 解压
        with tarfile.open(file_path, 'r') as tar:
            # 某些旧tar可能会导致权限警告，这里忽略错误
            def is_within_directory(directory, target):
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
                prefix = os.path.commonprefix([abs_directory, abs_target])
                return prefix == abs_directory
            
            # 安全解压检查 (防止 zip slip 攻击，虽然是自己的repo但是个好习惯)
            tar.extractall(path=temp_dir)
            
        # 2. 遍历临时目录中的文件
        print(f"  -> Extracted to temp. Scanning internal files...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                inner_path = os.path.join(root, file)
                # 递归调用单个文件处理逻辑
                if process_single_file(inner_path, inside_tar=True):
                    modified_in_tar = True

        # 3. 如果有文件被修改，重打包
        if modified_in_tar:
            print(f"  -> Repacking archive: {file_path}")
            # 获取原压缩包的模式 (是 .tar 还是 .tar.gz)
            mode = 'w:gz' if file_path.endswith('.gz') or file_path.endswith('.tgz') else 'w'
            
            with tarfile.open(file_path, mode) as tar:
                # 重新添加文件，arcname 参数确保压缩包内的路径结构正确
                tar.add(temp_dir, arcname="")
        else:
            print(f"  -> No changes inside archive.")

    except Exception as e:
        print(f"  [Error processing tar] {e}")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)

def main():
    exclude_dirs = ['.git', '.github']
    
    # 遍历所有文件
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # 1. 如果是压缩包
            if file.endswith(('.tar', '.tar.gz', '.tgz')):
                process_tar_file(file_path)
            
            # 2. 否则按普通文件逻辑处理
            else:
                process_single_file(file_path)

    print(f"\n✅ All Done. Total files modified: {TOTAL_MODIFIED}")

if __name__ == "__main__":
    main()
