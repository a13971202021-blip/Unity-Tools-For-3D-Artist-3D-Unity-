from PIL import Image
import os
# 在代码同目录下新建 input 文件夹
# 把所有要处理的图片放进 input
# 直接运行代码 → 自动生成 output 文件夹，里面就是统一好的成品图

# ====================== 【你可以自由修改的参数】 ======================
# 目标统一分辨率（宽, 高）
TARGET_SIZE = (1920, 1080)

# 统一像素密度 PPI（打印/设计/软件识别用）
TARGET_PPI = 72  # 常用：72(屏幕)、96(设计)、300(印刷)

# 适配模式："fit" = 等比例留白（完整显示） | "crop" = 等比例裁剪（填满画布）
ADAPT_MODE = "fit"

# 留白填充颜色（仅 fit 模式生效）：(255,255,255)=白 / (0,0,0)=黑 / None=透明
FILL_COLOR = None

# 画质（JPG有效，1-100）
QUALITY = 98
# =====================================================================


def process_single_image(img_path, save_path, target_size, ppi, mode, fill_color, quality):
    """单张图片处理：等比例缩放 + 统一尺寸 + 统一PPI"""
    with Image.open(img_path) as img:
        # 转换格式，保证透明图正常处理
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        original_w, original_h = img.size
        target_w, target_h = target_size

        # 计算等比例缩放系数
        scale = min(target_w / original_w, target_h / original_h)
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)

        # 高质量缩放（Lanczos 最清晰，抗锯齿）
        resized_img = img.resize((new_w, new_h), Image.LANCZOS)

        # 创建目标画布
        if mode == "fit":
            # 留白模式：居中 + 填充背景
            if img.mode == "RGBA" and fill_color is None:
                canvas = Image.new("RGBA", target_size)
            else:
                canvas = Image.new("RGB", target_size, fill_color)
            # 居中粘贴
            offset_x = (target_w - new_w) // 2
            offset_y = (target_h - new_h) // 2
            canvas.paste(resized_img, (offset_x, offset_y), mask=resized_img if img.mode == "RGBA" else None)
        else:
            # 裁剪模式：填满画布
            canvas = Image.new("RGB", target_size)
            offset_x = (new_w - target_w) // 2
            offset_y = (new_h - target_h) // 2
            canvas.paste(resized_img.crop((-offset_x, -offset_y, target_w - offset_x, target_h - offset_y)))

        # 构建 PPI 信息（写入图片元数据）
        resolution = (ppi, ppi)

        # 保存（最高画质 + 统一PPI）
        if save_path.lower().endswith(("png", "webp")):
            canvas.save(save_path, resolution=resolution, quality=quality, optimize=True)
        else:
            canvas.save(save_path, resolution=resolution, quality=quality, optimize=True)


def batch_process_images(input_dir="input", output_dir="output"):
    """批量处理文件夹内所有图片"""
    # 自动创建输入输出文件夹
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # 支持的图片格式
    img_exts = (".jpg", ".jpeg", ".png", ".webp")
    img_list = [f for f in os.listdir(input_dir) if f.lower().endswith(img_exts)]

    if not img_list:
        print(f"⚠️ 未在 {input_dir} 文件夹中找到图片！")
        return

    print(f"✅ 找到 {len(img_list)} 张图片，开始批量处理...\n")

    for idx, filename in enumerate(img_list, 1):
        img_path = os.path.join(input_dir, filename)
        save_path = os.path.join(output_dir, filename)

        try:
            process_single_image(
                img_path=img_path,
                save_path=save_path,
                target_size=TARGET_SIZE,
                ppi=TARGET_PPI,
                mode=ADAPT_MODE,
                fill_color=FILL_COLOR,
                quality=QUALITY
            )
            print(f"[{idx}/{len(img_list)}] 处理完成：{filename}")
        except Exception as e:
            print(f"❌ 处理失败：{filename} | 错误：{str(e)}")

    print(f"\n🎉 全部处理完成！统一尺寸：{TARGET_SIZE}，统一PPI：{TARGET_PPI}")


if __name__ == "__main__":
    batch_process_images()