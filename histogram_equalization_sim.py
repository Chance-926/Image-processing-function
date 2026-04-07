import cv2
import numpy as np

def rgb_to_ycbcr(image_rgb):
    """
    模块 4：将 RGB 图像转换为 YCbCr 色彩空间
    采用 ITU-R BT.601 标准公式
    """
    # 拆分 R, G, B 通道。注意：为了计算不溢出，先转换为 float 格式
    R = image_rgb[:, :, 0].astype(np.float32)
    G = image_rgb[:, :, 1].astype(np.float32)
    B = image_rgb[:, :, 2].astype(np.float32)
    
    # --- 硬件矩阵乘加运算 (MAC) 的底层数学逻辑 ---
    # 在 FPGA 中，这需要 9 个乘法器和相关的加法树来并行完成
    Y  =  0.299 * R + 0.587 * G + 0.114 * B
    Cb = -0.1687 * R - 0.3313 * G + 0.5 * B + 128
    Cr =  0.5 * R - 0.4187 * G - 0.0813 * B + 128
    
    # 限制范围在 0-255 之间，并转回硬件常见的 8-bit 无符号整数
    Y = np.clip(Y, 0, 255).astype(np.uint8)
    Cb = np.clip(Cb, 0, 255).astype(np.uint8)
    Cr = np.clip(Cr, 0, 255).astype(np.uint8)
    
    return Y, Cb, Cr


def ycbcr_to_rgb(Y, Cb, Cr):
    """
    模块 5：将 YCbCr 逆转换为 RGB 色彩空间
    """
    # 同样先转换为 float32 进行高精度运算
    Y = Y.astype(np.float32)
    Cb = Cb.astype(np.float32) - 128.0
    Cr = Cr.astype(np.float32) - 128.0
    
    # 逆矩阵运算
    R = Y + 1.402 * Cr
    G = Y - 0.344136 * Cb - 0.714136 * Cr
    B = Y + 1.772 * Cb
    
    # 裁剪到 0-255 并组合回三通道图像
    R = np.clip(R, 0, 255).astype(np.uint8)
    G = np.clip(G, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)
    
    # 使用 numpy.stack 沿着深度方向把 R,G,B 叠在一起
    image_rgb_eq = np.stack((R, G, B), axis=-1)
    return image_rgb_eq


def calculate_histogram(image_gray):
    """
    模块 1：统计图像的灰度直方图
    """
    # 初始化一个长度为256的数组，全部填0。索引代表灰度值(0-255)，对应的值代表该灰度出现的次数。
    hist = np.zeros(256, dtype=int)
    
    # 获取图像的高度和宽度
    height, width = image_gray.shape
    
    # --- 概念理解 ---
    # 底层逻辑是遍历图像的每一个像素点，进行统计。
    # 比如看到一个像素值是 150，就把 hist[150] 的值加 1。
    # 在 Python 中如果用双层 for 循环处理 1000*1000 的图片会非常慢，
    # 但为了理解硬件思维，其核心逻辑等同于以下注释代码：
    '''
    for y in range(height):
        for x in range(width):
            pixel_value = image_gray[y, x]
            hist[pixel_value] += 1
    '''
    
    # 在 Python 中，我们使用 numpy 的高级操作来加速这个过程，效果与上面双层循环完全一致
    hist = np.bincount(image_gray.flatten(), minlength=256)#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    return hist


def calculate_cdf(hist):
    """
    模块 2：计算累积分布函数
    """
    # 初始化一个同样长度为256的数组用于存放累加结果
    cdf = np.zeros(256, dtype=int)
    
    # 第一个元素就是直方图的第一个元素
    cdf[0] = hist[0]
    
    # 从第二个元素开始，当前 CDF 值 = 当前直方图值 + 前一个 CDF 值
    for i in range(1, 256):
        cdf[i] = cdf[i-1] + hist[i]
        
    return cdf


def equalize_image(image_gray, cdf):
    """
    模块 3：归一化 CDF 并映射新图像
    """
    height, width = image_gray.shape
    total_pixels = height * width  # 比如 1000 * 1000 = 1000000
    
    # 找到 CDF 中第一个不为 0 的值（图像中的最小有效灰度）
    cdf_min = 0
    for val in cdf:
        if val > 0:
            cdf_min = val
            break
            
    # 建立查找表 (Look-Up Table, 简称 LUT)
    # 核心公式： 新像素值 = round( (当前CDF - 最小CDF) / (总像素数 - 最小CDF) * 255 )
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        if cdf[i] > 0:
            # 使用浮点运算计算比例，然后四舍五入转为整数 (0-255)
            numerator = cdf[i] - cdf_min
            denominator = total_pixels - cdf_min
            lut[i] = np.round((numerator / denominator) * 255)
            
    # --- 映射过程 ---
    # 底层逻辑同样是遍历原图每个像素，根据查表得出新像素值：
    # new_image[y, x] = lut[ original_image[y, x] ]
    
    # 在 Python 中直接利用 Numpy 的数组索引特性完成高速映射
    image_equalized = lut[image_gray] #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    return image_equalized, lut


if __name__ == "__main__":
    input_filename = 'input.png'
    output_filename = 'color_equalized_output.png'
    
    # 1. 读取原始图像 (彩色图)
    # OpenCV 默认读取格式是 BGR，为了符合通用习惯，我们先将其翻转为 RGB
    img_bgr = cv2.imread(input_filename, cv2.IMREAD_COLOR)
    
    if img_bgr is None:
        print(f"错误：未找到图片 {input_filename}")
    else:
        print(">> 1. 成功读取彩色图片，开始执行硬件级色彩流水线处理...")
        
        # 将 BGR 转为标准 RGB 数组
        img_rgb = img_bgr[:, :, ::-1] 
        
        # --- 以下是严格模拟 FPGA ISP 流水线的执行顺序 ---
        
        # 色彩空间转换 (提取亮度 Y 和色度 CbCr)
        print(">> 2. 执行 RGB -> YCbCr 转换...")
        Y, Cb, Cr = rgb_to_ycbcr(img_rgb)
        
        # 仅对亮度通道(Y)进行直方图均衡化 (复用你之前写的模块)
        print(">> 3. 对 Y 通道进行直方图均衡化计算...")
        hist = calculate_histogram(Y)
        cdf = calculate_cdf(hist)
        Y_eq, lut = equalize_image(Y, cdf)
        
        # 色彩重建 (将均衡化后的 Y_eq 与原来的 Cb, Cr 合并)
        print(">> 4. 执行 YCbCr -> RGB 逆转换...")
        img_rgb_eq = ycbcr_to_rgb(Y_eq, Cb, Cr)
        
        # -----------------------------------------------
        
        # 将处理后的 RGB 图像转回 BGR 格式以便 OpenCV 保存
        img_bgr_eq = img_rgb_eq[:, :, ::-1]
        success = cv2.imwrite(output_filename, img_bgr_eq)
        
        if success:
            print(f">> 处理完成。具有原始色彩、但对比度大幅增强的图像已保存为: {output_filename}")
