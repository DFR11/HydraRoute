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
        print(f"      [Trans] {text[:25]}... -> {res[:25]}...")
        return res
    except Exception as e:
        print(f"      [Error] {e}")
        return text

def read_file_content(file_path):
    """尝试多种编码"""
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

def process_html_line(line, modified_flag):
    """专门处理 HTML 行的逻辑"""
    
    # 1. 匹配标签之间的内容： >内容<
    # 比如 <h1>Политики</h1> 匹配到 >Политики<
    tag_text_pattern = re.compile(r'(>)([^<]+?)(<)')
    
    # 2. 匹配特定属性的内容 (title, alt, placeholder)
    # 比如 placeholder="Поиск"
    attr_pattern = re.compile(r'\b(title|alt|placeholder|value|label)=([\"\'])(.*?)([\"\'])')

    # 3. 匹配 HTML 注释 <!-- ... -->
    comment_pattern = re.compile(r'(<!--\s*)(.*?)(\s*-->)')

    # --- 处理标签内容 ---
    def replace_tag_text(match):
        prefix, content, suffix = match.groups()
        if has_cyrillic(content):
            nonlocal modified_flag
            modified_flag[0] = True # 修改外部标志位
            return f"{prefix}{do_translate(content)}{suffix}"
        return match.group(0)
    
    line = tag_text_pattern.sub(replace_tag_text, line)

    # --- 处理属性 ---
    def replace_attr(match):
        attr_name, q_open, content, q_close = match.groups()
        if has_cyrillic(content):
            nonlocal modified_flag
            modified_flag[0] = True
            return f'{attr_name}={q_open}{do_translate(content)}{q_close}'
        return match.group(0)

    line = attr_pattern.sub(replace_attr, line)

    # --- 处理注释 ---
    def replace_comment(match):
        prefix, content, suffix = match.groups()
        if has_cyrillic(content):
            nonlocal modified_flag
            modified_flag[0] = True
            return f"{prefix}{do_translate(content)}{suffix}"
        return match.group(0)

    line = comment_pattern.sub(replace_comment, line)

    return line

def process_script_line(line, modified_flag):
    """处理脚本/配置文件行的逻辑 (原 V4.0 逻辑)"""
    
    # 字符串正则
    string_pattern = re.compile(r'(["\'])(.*?)(["\'])')
    # 注释正则
    comment_pattern = re.compile(r'^(.*?)(#\s+)(.*)$')

    if line.strip().startswith("#!"):
        return line

    # A. 注释
    match_comment = comment_pattern.match(line)
    if match_comment:
        pre, mark, content = match_comment.groups()
        if has_cyrillic(content):
            modified_flag[0] = True
            line = f"{pre}{mark}{do_translate(content)}\n"
    
    # B. 字符串
    def replace_str(match):
        q_open, content, q_close = match.groups()
        # 排除包含反引号的复杂命令
        if has_cyrillic(content) and '`' not in content:
            modified_flag[0] = True
            return f"{q_open}{do_translate(content)}{q_close}"
        return match.group(0)

    line = string_pattern.sub(replace_str, line)
    return line

def process_single_file(file_path, inside_tar=False):
    global TOTAL_MODIFIED
    prefix_log = "    " if inside_tar else ""
    
    # 扩展名配置
    script_exts = ['.sh', '.cfg', '.conf', '.list', '.txt', '.json', '.xml', '.lua']
    html_exts = ['.html', '.htm']
    valid_names = ['config', 'Makefile', 'control', 'postinst', 'prerm']
    
    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    is_script = any(file_path.endswith(e) for e in script_exts) or filename in valid_names
    is_html = ext in html_exts

    if not (is_script or is_html):
        return False

    print(f"{prefix_log}Checking: {filename}")
    lines, encoding = read_file_content(file_path)
    if not lines: return False

    new_lines = []
    # 使用列表存储布尔值以便在内部函数中修改
    modified_flag = [False] 

    for line in lines:
        if is_html:
            # 调用 HTML 处理逻辑
            line = process_html_line(line, modified_flag)
        else:
            # 调用 脚本 处理逻辑
            line = process_script_line(line, modified_flag)
        
        new_lines.append(line)

    if modified_flag[0]:
        print(f"{prefix_log}-> Modified: {filename}")
        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(new_lines)
        TOTAL_MODIFIED += 1
        return True
    return False

def process_tar_file(file_path):
    print(f"📦 Found Archive: {file_path}")
    temp_dir = tempfile.mkdtemp()
    modified_in_tar = False
    
    try:
        with tarfile.open(file_path, 'r') as tar:
            tar.extractall(path=temp_dir)
            
        print(f"  -> Extracted to temp. Scanning internal files...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                inner_path = os.path.join(root, file)
                if process_single_file(inner_path, inside_tar=True):
                    modified_in_tar = True

        if modified_in_tar:
            print(f"  -> Repacking archive: {file_path}")
            mode = 'w:gz' if file_path.endswith('.gz') or file_path.endswith('.tgz') else 'w'
            with tarfile.open(file_path, mode) as tar:
                tar.add(temp_dir, arcname="")
        else:
            print(f"  -> No changes inside archive.")

    except Exception as e:
        print(f"  [Error processing tar] {e}")
    finally:
        shutil.rmtree(temp_dir)

def main():
    exclude_dirs = ['.git', '.github']
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            if file.endswith(('.tar', '.tar.gz', '.tgz')):
                process_tar_file(file_path)
            else:
                process_single_file(file_path)

    print(f"\n✅ All Done. Total files modified: {TOTAL_MODIFIED}")

if __name__ == "__main__":
    main()
