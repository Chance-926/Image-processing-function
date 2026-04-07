import numpy as np
from PIL import Image
import time

# ==========================================
# 模块 1：矩阵生成模块 
# ==========================================
def get_inverse_affine_matrix(scale_x, scale_y, angle_degree, tx, ty):
    theta = np.radians(angle_degree)
    
    S = np.array([[scale_x, 0, 0], [0, scale_y, 0], [0, 0, 1]])
    R = np.array([[np.cos(theta), -np.sin(theta), 0],
                  [np.sin(theta),  np.cos(theta), 0],
                  [0,              0,             1]])
    T = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]])
    
    M = np.dot(T, np.dot(R, S))#！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    return np.linalg.inv(M)

# ==========================================
# 模块 2：图像映射模块 (双线性插值)
# ==========================================
def affine_transform_bilinear(image_array, inv_M, out_shape):
    """
    基于双线性插值的反向映射仿射变换
    """
    in_h, in_w, channels = image_array.shape
    out_h, out_w = out_shape
    
    # 创建输出图像，使用浮点数防止计算过程溢出，最后再转回 uint8
    out_image = np.zeros((out_h, out_w, channels), dtype=np.float32)
    
    a00, a01, a02 = inv_M[0, 0], inv_M[0, 1], inv_M[0, 2]
    a10, a11, a12 = inv_M[1, 0], inv_M[1, 1], inv_M[1, 2]
    
    for dst_y in range(out_h):
        for dst_x in range(out_w):
            
            # 1. 计算原图的浮点坐标
            src_x_float = a00 * dst_x + a01 * dst_y + a02
            src_y_float = a10 * dst_x + a11 * dst_y + a12
            
            # 2. 获取周围 4 个像素的整数坐标 (向下取整)
            # 相当于硬件里的基地址寻址
            x0 = int(np.floor(src_x_float))
            y0 = int(np.floor(src_y_float))
            x1 = x0 + 1
            y1 = y0 + 1
            
            # 3. 计算小数部分的偏移量 (用于计算权重)
            dx = src_x_float - x0
            dy = src_y_float - y0
            
            # 边界检查：确保 4 个像素点都在原图范围内
            # 硬件中，为了处理边界通常会做边缘镜像或补零，这里我们简单处理为补黑
            if 0 <= x0 < in_w - 1 and 0 <= y0 < in_h - 1:
                
                # 4. 获取 4 个相邻像素的值 (硬件中对应从 Line Buffer 中读取数据)
                # p00(左上), p10(右上), p01(左下), p11(右下)
                p00 = image_array[y0, x0]
                p10 = image_array[y0, x1]
                p01 = image_array[y1, x0]
                p11 = image_array[y1, x1]
                
                # 5. 计算权重 (面积倒数法)
                w00 = (1 - dx) * (1 - dy)
                w10 = dx * (1 - dy)
                w01 = (1 - dx) * dy
                w11 = dx * dy
                
                # 6. 加权求和 (硬件中的乘加树 DSP MAC Operations)
                # 展开即：out = w00*p00 + w10*p10 + w01*p01 + w11*p11
                out_pixel = w00 * p00 + w10 * p10 + w01 * p01 + w11 * p11
                
                out_image[dst_y, dst_x] = out_pixel
                
    # 将浮点数限制在 0-255 并转换为图像标准的 8-bit 无符号整数
    out_image = np.clip(out_image, 0, 255).astype(np.uint8)#！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    return out_image

# ==========================================
# 模块 3：运行测试 
# ==========================================
if __name__ == "__main__":
    input_filename = "input.png"
    output_filename = "output_bilinear.png"
    
    print(f"正在读取图像 {input_filename} ...")
    try:
        # 打开图像并确保转换为 RGB 格式 (丢弃 Alpha 通道以简化处理)
        img = Image.open(input_filename).convert('RGB')
        img_array = np.array(img)
        
        # 获取原图尺寸作为输出尺寸 (你也可以修改为固定 1000x1000)
        in_h, in_w = img_array.shape[:2]
        out_shape = (in_h, in_w)
        
        # 设定参数：旋转 30 度，放大 1.2 倍，向右平移 100，向下平移 50
        inv_matrix = get_inverse_affine_matrix(scale_x=1.2, scale_y=1.2, angle_degree=30, tx=100, ty=50)
        
        print("开始执行双线性插值仿射变换...")
        start_time = time.time()
        
        # 执行变换
        out_img_array = affine_transform_bilinear(img_array, inv_matrix, out_shape)
        
        print(f"处理完成")
        
        # 保存结果
        result_img = Image.fromarray(out_img_array)
        result_img.save(output_filename)
        print(f"结果已保存为: {output_filename}")
        
    except FileNotFoundError:
        print(f"错误：找不到文件 '{input_filename}'。请确保图片放在代码同目录下。")