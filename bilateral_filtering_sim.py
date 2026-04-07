import numpy as np
import cv2
import math

# ==========================================
# 模块 1 & 2：空间权重计算模块 (模拟硬件中的 2D ROM)
# ==========================================
def create_spatial_weight_rom(radius, sigma_s):
    """
    预计算空间距离权重。
    在 FPGA 中，这会综合成一块只读存储器 (ROM) 或者直接用 LUT 资源实现。
    因为窗口大小固定，各点到中心的距离不变，硬件运行时绝对不应该实时算指数。
    """
    window_size = 2 * radius + 1
    spatial_rom = np.zeros((window_size, window_size), dtype=np.float32)
    
    for y in range(-radius, radius + 1):
        for x in range(-radius, radius + 1):
            # 空间高斯公式
            spatial_rom[y + radius, x + radius] = math.exp(-(x**2 + y**2) / (2 * sigma_s**2))
            
    return spatial_rom

# ==========================================
# 模块 3：值域权重计算模块 (模拟硬件中的 1D 查找表 LUT)
# ==========================================
def create_range_weight_lut(sigma_r):
    """
    预计算亮度差值权重。
    对于 8-bit 图像，像素差值的绝对值范围是 0~255。
    在 FPGA 中，我们会用两像素之差的绝对值作为地址，去查一个深度为 256 的 BRAM。
    """
    range_lut = np.zeros(256, dtype=np.float32)
    for diff in range(256):
        # 值域高斯公式
        range_lut[diff] = math.exp(-(diff**2) / (2 * sigma_r**2))
        
    return range_lut

# ==========================================
# 模块 4 & 5：核心滤波流水线 (滑动窗口 + 乘加归一化)
# ==========================================
def bilateral_filter_single_channel_core(channel_img, radius, spatial_rom, range_lut):
    """单通道双边滤波核心 (只用来处理 Y 通道)"""

    height, width = channel_img.shape
    window_size = 2 * radius + 1
    padded_img = np.pad(channel_img, radius, mode='symmetric').astype(np.float32)
    output_channel = np.zeros_like(channel_img, dtype=np.float32)
    
    for y in range(height):
        for x in range(width):
            window = padded_img[y:y+window_size, x:x+window_size]
            center_pixel = window[radius, radius]

            weight_sum = 0.0
            pixel_sum = 0.0
            
            for wy in range(window_size):
                for wx in range(window_size):
                    
                    curr_pixel = window[wy, wx]
                    w_spatial = spatial_rom[wy, wx]
                    diff = int(abs(curr_pixel - center_pixel))
                    w_range = range_lut[diff]
                    w_joint = w_spatial * w_range

                    pixel_sum += curr_pixel * w_joint
                    weight_sum += w_joint

            output_channel[y, x] = pixel_sum / weight_sum
    return output_channel


def bilateral_filter_yuv_architecture_cv2(img_bgr, radius, sigma_s, sigma_r):

    # 使用库函数完成 BGR 到 YUV 的转换
    img_yuv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YUV)
    
    # 拆分通道 (Y, U, V)
    Y, U, V = cv2.split(img_yuv)
    
    # 预计算权重表
    spatial_rom = create_spatial_weight_rom(radius, sigma_s)
    range_lut = create_range_weight_lut(sigma_r)
    
    print("  -> 执行 Y 通道双边滤波...")
    # 只将 Y 通道送入我们手写的“硬件模拟核”
    Y_filtered = bilateral_filter_single_channel_core(Y, radius, spatial_rom, range_lut)
    
    # 将处理后的 Y_filtered 限制在 0-255 并转回 uint8
    Y_filtered = np.clip(Y_filtered, 0, 255).astype(np.uint8)
    
    print("  -> 合并滤波后的 Y 与原始 U, V 通道...")
    # 将新的 Y 通道与原来的 U, V 通道重新打包
    img_yuv_filtered = cv2.merge([Y_filtered, U, V])
    
    print("  -> cv2.cvtColor 执行 YUV to BGR 转换...")
    # 直接使用库函数转回 BGR 格式以便保存和显示
    output_bgr = cv2.cvtColor(img_yuv_filtered, cv2.COLOR_YUV2BGR)
    
    return output_bgr

# ==========================================
# 测试与验证逻辑
# ==========================================
if __name__ == "__main__":
    input_filename = 'input.png'
    # 以彩色模式读取 (OpenCV 默认读取为 BGR 格式)
    img = cv2.imread(input_filename, cv2.IMREAD_COLOR)
    
    if img is None:
        print(f"错误：无法读取 {input_filename}。")
        
    radius = 2
    sigma_s = 2.0
    sigma_r = 30.0

    print(" 开始执行 YUV 架构双边滤波 ")
    
    # 调用精简后的顶层架构
    filtered_img = bilateral_filter_yuv_architecture_cv2(img, radius, sigma_s, sigma_r)
    
    output_filename = "output_filtered_cv2_arch.png"
    success = cv2.imwrite(output_filename, filtered_img)
    
    if success:
        print(f"=== 计算完成！结果已保存至: {output_filename} ===")
    else:
        print("保存失败，请检查目录读写权限。")