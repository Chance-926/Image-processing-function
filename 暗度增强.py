from PIL import Image
import numpy as np

#=================================================================================
#功能：生成 Gamma 查找表（0~255 → 0~255），对实际图片无影响，但在硬件中是一个
#   重要的预处理步骤，等价于在 FPGA 中烧录一块 ROM 来存储非线性映射关系。
#注意：gamma=0.5是默认值，如果传参时没有指定 gamma，则使用 0.5 来增强暗部。
#核心：gamma < 1：增强暗部
#      gamma = 1：线性不变
#      gamma > 1：抑制亮部
#==================================================================================
def generate_gamma_lut(gamma=0.5):
    lut = [0] * 256

    for i in range(256):
        norm = i / 255.0  # 归一化到 [0, 1]
        val = int((norm ** gamma) * 255.0 + 0.5)

        # 饱和限制（硬件等价）
        if val > 255:
            val = 255
        elif val < 0:   # 这一步在理论上不太可能发生，因为输入和输出都是非负的，添加了这个检查以确保安全。
            val = 0

        lut[i] = val

    return lut

#初始化暗光增强模块
class DarkEnhanceLUT:
    def __init__(self, gamma=0.5):
        self.lut = generate_gamma_lut(gamma)

    #该函数返回两个值，第一个是映射后的像素值，第二个是一个有效信号布尔值
    def step(self, pixel_in, valid_in):
        """
        模拟硬件时序接口
        """
        if valid_in == 0:
            return 0, 0

        # 查表（ROM）
        pixel_out = self.lut[pixel_in]

        return pixel_out, 1

#=================================================================================
#功能：处理图像流
#说明：在实际的 FPGA 设计中，图像数据是以像素流的形式从 DDR/SRAM 中读取出来的，每个时钟周
#     期处理一个像素，并通过 valid 信号来控制数据流动。这里我们用一个二维列表来模拟这个过
#     程，逐像素处理输入图像，并生成输出图像。
#实现逻辑：
#=================================================================================
def process_image_stream(img, module):
    h, w = img.shape
    #创建一个w*h的二维列表，初始值为0，数据类型为8位无符号整数
    out = [[0]*w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            pixel_in = int(img[y][x])
            pixel_out, valid_out = module.step(pixel_in, 1)

            if valid_out:
                out[y][x] = pixel_out

    return out


def load_image(path):
    img = Image.open(path).convert('L')
    return np.array(img, dtype=np.uint8)

def save_image(img_array, path):
    img = Image.fromarray(np.array(img_array, dtype=np.uint8))
    img.save(path)


if __name__ == "__main__":
    input_path = r"E:\YOLO_dataset\coco128\images\train2017\1.jpg"
    output_path = r"E:\刘尚霖\大学\竞赛\集创赛\比赛\放大缩小模块\暗度增强.jpg"

    img = load_image(input_path)

    # 初始化模块（gamma<1增强暗光）
    dark_module = DarkEnhanceLUT(gamma=0.5)

    out = process_image_stream(img, dark_module)

    save_image(out, output_path)