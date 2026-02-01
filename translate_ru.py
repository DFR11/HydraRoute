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
    # 排除纯符号、数字、IP、路径、URL
    if re.match(r'^[\W\d]+$', text) or '/opt/' in text or 'http' in text:
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

# --- 1. HTML 处理逻辑 ---
def process_html_lines(lines, modified_flag):
    new_lines = []
    tag_text_pattern = re.compile(r'(>)([^<]+?)(<)')
    attr_pattern = re.compile(r'\b(title|alt|placeholder|value|label)=([\"\'])(.*?)([\"\'])')
    comment_pattern = re.compile(r'(<!--\s*)(.*?)(\s*-->)')

    for line in lines:
        # 处理标签内容
        def replace_tag(match):
            p, c, s = match.groups()
            if has_cyrillic(c):
                modified_flag[0] = True
                return f"{p}{do_translate(c)}{s}"
            return match.group(0)
        line = tag_text_pattern.sub(replace_tag, line)

        # 处理属性
        def replace_attr(match):
            k, q1, c, q2 = match.groups()
            if has_cyrillic(c):
                modified_flag[0] = True
                return f'{k}={q1}{do_translate(c)}{q2}'
            return match.group(0)
        line = attr_pattern.sub(replace_attr, line)

        # 处理注释
        def replace_comment(match):
            p, c, s = match.groups()
            if has_cyrillic(c):
                modified_flag[0] = True
                return f"{p}{do_translate(c)}{s}"
            return match.group(0)
        line = comment_pattern.sub(replace_comment, line)
        
        new_lines.append(line)
    return new_lines

# --- 2. Markdown 处理逻辑 (关键修复) ---
def process_md_lines(lines, modified_flag):
    new_lines = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()
        
        # 检测代码块标记 ```
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
        
        # 在代码块内，或空行，或者是HTML标签，跳过
        if in_code_block or not stripped or stripped.startswith('<'):
            new_lines.append(line)
            continue
            
        # 只有包含俄语才翻译
        if has_cyrillic(line):
            # 提取 Markdown 前缀 (如 # 标题, - 列表, > 引用, 1. 数字列表)
            # group(1) 是前缀，group(2) 是内容
            prefix_match = re.match(r'^(\s*(?:#+|\-|\*|\d+\.|>)\s+)?(.*)', line)
            
            if prefix_match:
                prefix, content = prefix_match.groups()
                if prefix is None: prefix = ""
                
                # 保护 Markdown链接 [text](url) - 简单策略：不翻带大量链接的行，或者直接硬翻
                # 这里选择直接翻译内容，DeepTranslator 通常能保留格式，但为了安全，
                # 如果内容里链接太多，Google Translate 可能会弄乱括号。
                # 暂时直接翻译 content 部分
                
                translated = do_translate(content)
                new_lines.append(f"{prefix}{translated}\n")
                modified_flag[0] = True
                continue

        new_lines.append(line)
    return new_lines

# --- 3. 脚本代码 处理逻辑 ---
def process_script_lines(lines, modified_flag):
    new_lines = []
    string_pattern = re.compile(r'(["\'])(.*?)(["\'])')
    comment_pattern = re.compile(r'^(.*?)(#\s+)(.*)$')

    for line in lines:
        if line.strip().startswith("#!"):
            new_lines.append(line)
            continue

        # 注释
        match_comment = comment_pattern.match(line)
        if match_comment:
            pre, mark, content = match_comment.groups()
            if has_cyrillic(content):
                modified_flag[0] = True
                line = f"{pre}{mark}{do_translate(content)}\n"
        
        # 字符串
        def replace_str(match):
            q1, c, q2 = match.groups()
            if has_cyrillic(c) and '`' not in c:
                modified_flag[0] = True
                return f"{q1}{do_translate(c)}{q2}"
            return match.group(0)

        line = string_pattern.sub(replace_str, line)
        new_lines.append(line)
    return new_lines

# --- 主文件处理逻辑 ---
def process_single_file(file_path, inside_tar=False):
    global TOTAL_MODIFIED
    prefix_log = "    " if inside_tar else ""
    
    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    
    # 扩展名定义
    script_exts = ['.sh', '.cfg', '.conf', '.list', '.txt', '.json', '.xml', '.lua']
    html_exts = ['.html', '.htm']
    md_exts = ['.md', '.markdown'] # 新增 MD
    valid_names = ['config', 'Makefile', 'control', 'postinst', 'prerm']
    
    is_script = any(file_path.endswith(e) for e in script_exts) or filename in valid_names
    is_html = ext in html_exts
    is_md = ext in md_exts # 标记 MD

    if not (is_script or is_html or is_md):
        return False

    print(f"{prefix_log}Checking: {filename}")
    lines, encoding = read_file_content(file_path)
    if not lines: return False

    modified_flag = [False]
    new_lines = []

    # 分发处理逻辑
    if is_html:
        new_lines = process_html_lines(lines, modified_flag)
    elif is_md:
        new_lines = process_md_lines(lines, modified_flag)
    else:
        new_lines = process_script_lines(lines, modified_flag)

    if modified_flag[0]:
        print(f"{prefix_log}-> Modified: {filename}")
        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(new_lines)
        TOTAL_MODIFIED += 1
        return True
    return False

# --- Tar 处理 ---
def process_tar_file(file_path):
    print(f"📦 Found Archive: {file_path}")
    temp_dir = tempfile.mkdtemp()
    modified_in_tar = False
    try:
        with tarfile.open(file_path, 'r') as tar:
            tar.extractall(path=temp_dir)
        print(f"  -> Extracted. Scanning...")
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                inner_path = os.path.join(root, file)
                if process_single_file(inner_path, inside_tar=True):
                    modified_in_tar = True
        if modified_in_tar:
            print(f"  -> Repacking: {file_path}")
            mode = 'w:gz' if file_path.endswith('.gz') or file_path.endswith('.tgz') else 'w'
            with tarfile.open(file_path, mode) as tar:
                tar.add(temp_dir, arcname="")
        else:
            print(f"  -> No changes inside.")
    except Exception as e:
        print(f"  [Error tar] {e}")
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
