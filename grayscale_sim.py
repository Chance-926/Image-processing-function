import numpy as np
from PIL import Image

def bit_true_simulation_optimized():
    # --- [Testbench] 模块 1：数据激励注入 ---
    # (假设已经读取并处理好 8-bit 的 RGB 数据)
    try:
        img = Image.open('input.png').convert('RGB')
    except FileNotFoundError:
        return
    img_array = np.array(img, dtype=np.uint8)
    
    # 将 uint8 扩展为 uint16，模拟硬件进入计算节点前的位宽扩展
    R = img_array[:, :, 0].astype(np.uint16)
    G = img_array[:, :, 1].astype(np.uint16)
    B = img_array[:, :, 2].astype(np.uint16)

    # --- [DUT] 模块 2：优化后的流水线 ---
    # [级联 1] 常数乘法 (硬件中将由 LUTs 的 Shift-and-Add 综合)
    mult_R = 77 * R
    mult_G = 150 * G
    mult_B = 29 * B

    # [级联 2] 加法树与四舍五入补偿
    # 硬件设计规范：移位前加上被移位部分最大值的一半 (这里右移8位，故加 128)
    # 这在 FPGA 中只消耗加法器的进位链 (Carry Chain)，不增加额外时钟周期
    Y_16bit = mult_R + mult_G + mult_B + 128

    # [级联 3] 截断提取 (连线级别的无成本操作)
    Y_8bit = np.right_shift(Y_16bit, 8).astype(np.uint8)
    
    # --- [Testbench] 模块 3：结果回收 ---
    out_img = Image.fromarray(Y_8bit, mode='L')
    out_img.save('gray_optimized.jpg')

if __name__ == '__main__':
    bit_true_simulation_optimized()