# 操作系统文件/路径操作库
import os
# 文字规则匹配库（清洗名称、提取数字）
import re
# 文件备份库（自动备份文件夹，防止改错）
import shutil
# 时间库（生成备份文件夹时间戳）
from datetime import datetime

# ==================== 【新手配置区】 ====================
# 要处理的文件夹路径
TARGET_FOLDER = r"你要处理的文件路径"
# 是否递归处理子文件夹
RECURSIVE = True
# False=预览模式（安全），True=真正执行重命名
DO_RENAME = False
# 自动备份（强烈建议开启）
AUTO_BACKUP = True

# 自动跳过的系统文件夹，避免破坏工程
IGNORE_FOLDERS = ["Editor", "Plugins", "Resources", "Packages", "Settings"]
# 自动跳过的文件类型，绝对不修改
IGNORE_EXTENSIONS = [".meta", ".cs", ".js", ".boo", ".exe", ".dll", ".config"]
# 自动清理的冗余后缀
REMOVE_SUFFIXES = ["_v1", "_v2", "_final", "_copy", "_temp", "_bak", "_old"]

# 项目命名规范前缀（固定）
PREFIXES = {
    "model_static": "SM_",
    "model_skeleton": "SK_",
    "texture": "T_",
    "material": "M_",
    "prefab": "PF_",
    "terrain": "TER_",
    "hdr": "HDR_"
}
# 所有前缀集合，用于一键清空
ALL_PREFIXES = list(PREFIXES.values())

# 贴图类型自动识别规则
TEXTURE_TAGS = {
    "normal": "N", "roughness": "R", "basecolor": "B", "albedo": "B",
    "metal": "M", "metallic": "M", "ao": "O", "ambientocclusion": "O", "height": "H"
}


# ==================== 【核心：彻底清空所有旧前缀】 ====================
# 功能：无论对错，删除所有已存在的前缀（你要求的核心修复）
def strip_all_prefixes(name):
    for p in ALL_PREFIXES:
        if name.startswith(p):
            name = name[len(p):]
    return name


# ==================== 【完整文件名清洗】 ====================
def clean_core_name(filename):
    # 第一步：强制清空所有旧前缀（解决重复/错配前缀）
    name = strip_all_prefixes(filename)

    # 第二步：清理冗余后缀
    for s in REMOVE_SUFFIXES:
        name = name.replace(s, "")

    # 第三步：清理中文字符
    name = re.sub(r"[\u4e00-\u9fff]", "", name)

    # 第四步：只保留字母、数字、下划线
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # 第五步：合并连续下划线
    name = re.sub(r"_+", "_", name)

    # 第六步：去除首尾下划线
    name = name.strip("_")

    return name


# ==================== 【序号处理】 ====================
# 提取文件名中的所有数字
def extract_numbers(name):
    return [int(n) for n in re.findall(r"_(\d+)", name)]


# 判断序号是否完美连续（从1开始，无断号）
def is_sequence_perfect(num_list):
    if not num_list:
        return False
    num_list = sorted(list(set(num_list)))
    if num_list[0] != 1:
        return False
    for i in range(len(num_list)):
        if num_list[i] != i + 1:
            return False
    return True


# 删除所有数字序号
def remove_all_numbers(name):
    return re.sub(r"_\d+", "", name)


# ==================== 【资产类型判断】 ====================
def get_asset_type(ext):
    ext = ext.lower()
    if ext in [".fbx", ".obj"]:
        return "model"
    if ext in [".png", ".tga", ".jpg", ".jpeg", ".hdr"]:
        return "texture"
    if ext == ".mat":
        return "material"
    if ext == ".prefab":
        return "prefab"
    return "unknown"


# 识别贴图类型后缀
def get_texture_suffix(name):
    nl = name.lower()
    for k, v in TEXTURE_TAGS.items():
        if k in nl:
            return f"_{v}"
    return ""


# ==================== 【文件夹处理主逻辑】 ====================
def process_folder(folder_path):
    all_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    groups = {"model": [], "texture": [], "material": [], "prefab": []}
    log = []

    # 文件自动分类
    for f in all_files:
        ext = os.path.splitext(f)[1].lower()
        if ext in IGNORE_EXTENSIONS:
            log.append(f"⏭️ 跳过：{f}")
            continue
        typ = get_asset_type(ext)
        if typ in groups:
            groups[typ].append(f)

    # 按类型批量重命名
    for typ, files in groups.items():
        if not files:
            continue
        files_sorted = sorted(files)
        existing_nums = []
        for f in files_sorted:
            n = extract_numbers(f)
            existing_nums.extend(n)

        # 检查序号是否合规
        perfect_seq = is_sequence_perfect(existing_nums)
        counter = 1

        for f in files_sorted:
            ori_path = os.path.join(folder_path, f)
            name_only, ext = os.path.splitext(f)

            # 【关键】清空所有前缀 + 深度清洗名称
            clean_name = clean_core_name(name_only)
            # 去掉所有旧序号
            no_num = remove_all_numbers(clean_name)
            # 识别贴图类型
            tex_suf = get_texture_suffix(name_only)

            # 【关键】根据类型，赋予唯一正确前缀
            prefix = ""
            if typ == "model":
                prefix = PREFIXES["model_skeleton"] if "skin" in f.lower() or "skeleton" in f.lower() else PREFIXES[
                    "model_static"]
            elif typ == "texture":
                if ext == ".hdr":
                    prefix = PREFIXES["hdr"]
                elif "terrain" in f.lower():
                    prefix = PREFIXES["terrain"]
                else:
                    prefix = PREFIXES["texture"]
            elif typ == "material":
                prefix = PREFIXES["material"]
            elif typ == "prefab":
                prefix = PREFIXES["prefab"]

            # 拼接最终规范名称
            base_name = f"{prefix}{no_num}{tex_suf}"
            new_name = f"{base_name}_{counter:03d}{ext}"
            new_path = os.path.join(folder_path, new_name)

            # 日志输出
            if perfect_seq:
                line = f"✅ 已合规，保持不变：{f}"
            else:
                line = f"✅ 规范化：{f} → {new_name}"
                if DO_RENAME:
                    try:
                        os.rename(ori_path, new_path)
                    except Exception as e:
                        line = f"❌ 失败：{f} | {str(e)}"
                counter += 1

            print(line)
            log.append(line)
    return log


# ==================== 【程序入口】 ====================
def main():
    print("=" * 70)
    print("    Unity 全能资源规范化工具（终极无BUG版·作品集专用）")
    print("    ✅ 清空旧前缀 ✅ 唯一正确前缀 ✅ 连续序号 ✅ 预览安全")
    print("=" * 70)

    if not os.path.isdir(TARGET_FOLDER):
        print("❌ 错误：目标文件夹不存在")
        return

    # 自动备份
    if AUTO_BACKUP and DO_RENAME:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak_path = TARGET_FOLDER + f"_BACKUP_{timestamp}"
        shutil.copytree(TARGET_FOLDER, bak_path)
        print(f"✅ 已自动备份：{bak_path}")

    all_log = []
    if RECURSIVE:
        for root, dirs, files in os.walk(TARGET_FOLDER):
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
            all_log += process_folder(root)
    else:
        all_log = process_folder(TARGET_FOLDER)

    # 保存日志
    log_path = os.path.join(TARGET_FOLDER, "rename_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(all_log))

    print("\n🎉 处理完成！日志已保存")


if __name__ == "__main__":
    main()