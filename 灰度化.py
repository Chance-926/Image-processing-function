import numpy as np
from PIL import Image

def bit_true_simulation():
    # ==========================================
    # 模块 1：数据激励注入 (Testbench Source)
    # ==========================================
    print(">>> [Testbench] 模块 1: 准备输入激励...")
    input_filename = '1.jpg'
    
    try:
        # 使用 PIL 读取图像，并强制确保转换为 RGB 三通道模式
        img = Image.open(input_filename).convert('RGB')
    except FileNotFoundError:
        print(f"[Error] 找不到测试文件 {input_filename}，请检查路径。")
        return

    # 将图像对象转换为 NumPy 多维数组，数据类型严格限定为 8位无符号整数 (uint8)
    # 这相当于从 DDR/SRAM 中读取出的 8-bit 原始视频像素流
    img_array = np.array(img, dtype=np.uint8)
    height, width, channels = img_array.shape
    
    print(f"[Info] 视频流锁定: 宽={width}, 高={height}, 通道={channels} (RGB)")
    print(f"[Info] 输入像素数据类型: {img_array.dtype}")

    # ==========================================
    # 模块 2：核心算法模拟 (DUT - 定点化处理引擎)
    # ==========================================
    print("\n>>> [DUT] 模块 2: 执行流水线定点化运算...")
    
    # 硬件设计核心：位宽控制 (Bit-width Control)
    # 8-bit 的 RGB 乘以系数后一定会超出 255 的限制。
    # 在硬件中，DSP48 的乘法器会输出更宽的位宽。我们在 Python 中必须显式地将其
    # 从 8-bit (uint8) 扩展为 16-bit (uint16) 线网，防止运算溢出。
    R = img_array[:, :, 0].astype(np.uint16)
    G = img_array[:, :, 1].astype(np.uint16)
    B = img_array[:, :, 2].astype(np.uint16)

    # 完美模拟 FPGA 中的三级流水线：
    # [级联 1] 并行乘法运算：消耗 3 个 DSP48 乘法器硬核
    mult_R = 77 * R
    mult_G = 150 * G
    mult_B = 29 * B

    # [级联 2] 加法树累加：消耗 DSP48 内部累加器或外部逻辑切片 (LUTs/CARRY4)
    # 此时 Y_16bit 的理论最大值约为 255*77 + 255*150 + 255*29 = 65280，刚好卡在 16-bit 范围内
    Y_16bit = mult_R + mult_G + mult_B

    # [级联 3] 移位与截断提取
    # 右移 8 位等效于除以 256。在硬件中，这一步是“零成本”的，只需改变连线，
    # 直接提取 Y_16bit 的高 8 位 [15:8] 作为最终输出，并强制转换回 8-bit。
    Y_8bit = np.right_shift(Y_16bit, 8).astype(np.uint8)
    
    print("[Info] 流水线运算完成，已成功剥离色度通道，保留亮度 (Y) 通道。")

    # ==========================================
    # 模块 3：结果回收与验证 (Testbench Sink)
    # ==========================================
    print("\n>>> [Testbench] 模块 3: 输出结果保存...")
    
    # mode='L' 在 PIL 库中代表 8-bit 单通道灰度图 (Luminance)
    # 这相当于把单通道结果重新写入一块新的外部显存
    out_img = Image.fromarray(Y_8bit, mode='L')
    
    output_filename = '灰度化.jpg'
    out_img.save(output_filename)
    print(f"[Success] 处理后的图像已保存为: {output_filename}")

if __name__ == '__main__':
    bit_true_simulation()