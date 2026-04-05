from PIL import Image
import os
import csv

# ====================== 【调整部分】 ======================
INPUT_DIR = "./input"                # 图片放这里
OUTPUT_DIR = "./output"              # 输出文件夹
TARGET_SIZE = (1024, 1024)            # 统一分辨率
TARGET_PPI = 72                       # 统一PPI
ADAPT_MODE = "fit"                   # fit=等比例留白 / crop=裁剪
ENABLE_FILL = False                   # True=开启填充 / False=不填充
FILL_COLOR = "None"                  # white=白 / black=黑 / None=透明
QUALITY = 98
PROMPT = "3d模型，概念图，q版游戏模型，风格化场景，手绘材质，3渲2效果"
CSV_FILE = "annotation.csv"
# ======================================================================

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

success = 0
fail = 0

# 颜色映射
color_map = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    None: None
}
fill_rgb = color_map.get(FILL_COLOR, (255,255,255))

with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["image_name", "width", "height", "prompt"])

    for filename in os.listdir(INPUT_DIR):
        try:
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                img_path = os.path.join(INPUT_DIR, filename)
                save_path = os.path.join(OUTPUT_DIR, filename)

                with Image.open(img_path) as img:
                    # 透明图正常处理
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGBA")
                    else:
                        img = img.convert("RGB")

                    original_w, original_h = img.size
                    target_w, target_h = TARGET_SIZE

                    # 等比例缩放
                    scale = min(target_w / original_w, target_h / original_h)
                    new_w = int(original_w * scale)
                    new_h = int(original_h * scale)
                    resized_img = img.resize((new_w, new_h), Image.LANCZOS)

                    # 填充开关 + 颜色自选
                    if ENABLE_FILL and ADAPT_MODE == "fit":
                        if img.mode == "RGBA" and FILL_COLOR is None:
                            canvas = Image.new("RGBA", TARGET_SIZE)
                        else:
                            canvas = Image.new("RGB", TARGET_SIZE, fill_rgb)
                        offset_x = (target_w - new_w) // 2
                        offset_y = (target_h - new_h) // 2
                        canvas.paste(resized_img, (offset_x, offset_y), mask=resized_img if img.mode == "RGBA" else None)
                    else:
                        canvas = resized_img

                    # 保存 + 统一PPI
                    canvas.save(save_path, resolution=(TARGET_PPI, TARGET_PPI), quality=QUALITY)

                writer.writerow([filename, TARGET_SIZE[0], TARGET_SIZE[1], PROMPT])
                success += 1
                print(f"✅ 处理完成: {filename}")

        except Exception as e:
            fail += 1
            print(f"❌ 失败: {filename} | {str(e)[:50]}")

print("\n==================== 处理完成 ====================")
print(f"成功：{success} 张 | 失败：{fail} 张")
print(f"填充开关：{'开启' if ENABLE_FILL else '关闭'}")
print(f"填充颜色：{FILL_COLOR}")
print(f"标注文件：{CSV_FILE}")