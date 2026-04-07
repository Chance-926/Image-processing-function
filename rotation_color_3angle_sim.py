import numpy as np
from PIL import Image
import time

# ==========================================
# 模块 1：硬件资源建模 (DDR 与 BRAM)
# ==========================================

class VirtualDDR:
    """模拟外部 DDR 存储器（基于 numpy 1D 数组加速）"""
    def __init__(self, data_1d):
        # 接收一个 1D numpy 数组模拟 DDR 中的连续物理内存
        self.memory = data_1d
        self.total_reads = 0 # 用于统计 AXI 突发读取次数

    def read_burst(self, start_addr, length):
        """模拟 AXI4 突发读取"""
        self.total_reads += 1
        return self.memory[start_addr : start_addr + length]

class BRAM_Cache:
    def __init__(self, block_size):
        self.N = block_size
        self.data = np.zeros((self.N, self.N, 3), dtype=np.uint8)

    def write_row(self, row_index, row_data):
        self.data[row_index, :, :] = row_data

    def read_rotated_block(self, angle):
        """根据输入的角度，决定 BRAM 内部的微观旋转"""
        #可展开#############################################################################################################
        if angle == 90:
            return np.rot90(self.data, k=-1, axes=(0, 1)) # 顺时针90度
        elif angle == 180:
            return np.rot90(self.data, k=-2, axes=(0, 1)) # 顺时针180度
        elif angle == 270:
            return np.rot90(self.data, k=-3, axes=(0, 1)) # 顺时针270度
        else:
            return self.data # 0度（不旋转）
    
# ==========================================
# 模块 2：AXI Master 调度器与旋转引擎
# ==========================================

def axi_master_rotator_universal(ddr, W_in, H_in, B_size, angle=90):
    """
    全能版 AXI Master 调度器：支持 90, 180, 270 度顺时针旋转
    """
    print(f"[-] 启动 AXI 流水线... 模式: 顺时针 {angle} 度")
    
    # 1. 确定输出画布的宽高
    if angle in [90, 270]:
        W_out, H_out = H_in, W_in   # 90和270度，宽高互换
    else:
        W_out, H_out = W_in, H_in   # 0和180度，宽高不变
        
    output_image = np.zeros((H_out, W_out, 3), dtype=np.uint8)
    bram = BRAM_Cache(block_size=B_size)

    for block_y in range(0, H_out, B_size):
        for block_x in range(0, W_out, B_size):
            
            # ==========================================
            # 步骤 A: 宏观层地址逆映射 (硬件状态机的核心逻辑)
            # ==========================================
            if angle == 90:
                src_block_x = block_y
                src_block_y = H_in - B_size - block_x
                
            elif angle == 180:
                # 180度：相当于中心对称，原图右下角的块跑到左上角
                src_block_x = W_in - B_size - block_x
                src_block_y = H_in - B_size - block_y
                
            elif angle == 270:
                # 270度：相当于逆时针90度
                src_block_x = W_in - B_size - block_y
                src_block_y = block_x
                
            else: # 0度
                src_block_x = block_x
                src_block_y = block_y

            # ==========================================
            # 步骤 B: DDR 突发读取入 BRAM (底层走线永远不变！)
            # ==========================================
            for row_offset in range(B_size):
                current_src_y = src_block_y + row_offset
                ddr_addr = current_src_y * W_in + src_block_x
                
                burst_data = ddr.read_burst(ddr_addr, length=B_size)
                bram.write_row(row_offset, burst_data)
                
            # ==========================================
            # 步骤 C: 微观层 BRAM 内部旋转并输出
            # ==========================================
            rotated_block = bram.read_rotated_block(angle) # 传入角度参数
            output_image[block_y : block_y + B_size, block_x : block_x + B_size, :] = rotated_block

    return output_image


# ==========================================
# 模块 3：测试平台 (读取图像 -> 预处理对齐 -> 执行 -> 裁剪保存)
# ==========================================

# ==========================================
# 模块 3：测试平台 (支持 0, 90, 180, 270 度自适应裁剪)
# ==========================================

def run_universal_simulation(image_path, angle=90, B_size=32):
    """
    全角度测试平台：加载图像、填充对齐、硬件仿真、定位裁剪
    """
    # 1. 图像加载与前期准备
    print(f"\n>>> 1. 正在加载彩色图像，目标：顺时针旋转 {angle} 度...")
    img = Image.open(image_path).convert('RGB')
    W_orig, H_orig = img.size
    
    # 2. 硬件对齐 (Padding 补齐到 B_size 的整数倍)
    pad_W = (W_orig + B_size - 1) // B_size * B_size
    pad_H = (H_orig + B_size - 1) // B_size * B_size
    
    # 原图放在对齐画布的左上角 (0, 0)
    padded_img = Image.new('RGB', (pad_W, pad_H), color=(0, 0, 0))
    padded_img.paste(img, (0, 0))
    
    # 转换为 1D 像素字流送入 DDR 模型 
    #可展开#################################################################################################################
    img_array = np.array(padded_img)
    img_pixel_stream = img_array.reshape(-1, 3) 
    ddr = VirtualDDR(img_pixel_stream)

    # 3. 运行全能版 FPGA 旋转调度器 (调用前面重构的通用模块)
    print(">>> 2. 正在执行硬件流水线...")
    # 注意：这里调用的是上一轮为你写的全角度通用函数 axi_master_rotator_universal
    rotated_padded_array = axi_master_rotator_universal(ddr, pad_W, pad_H, B_size, angle)

    # 4. 根据角度动态计算裁剪坐标 (Crop)
    print(">>> 3. 正在计算有效边界并重组图像...")
    final_img_padded = Image.fromarray(rotated_padded_array, 'RGB')
    #可展开#################################################################################################################
    
    # PIL crop 的参数是 (左, 上, 右, 下)
    if angle == 90:
        # 90度：原左上角 -> 现右上角
        crop_box = (pad_H - H_orig, 0, pad_H, W_orig)
    elif angle == 180:
        # 180度：原左上角 -> 现右下角
        crop_box = (pad_W - W_orig, pad_H - H_orig, pad_W, pad_H)
    elif angle == 270:
        # 270度：原左上角 -> 现左下角
        crop_box = (0, pad_W - W_orig, H_orig, pad_W)
    else:
        # 0度：原左上角 -> 还是左上角
        crop_box = (0, 0, W_orig, H_orig)
        
    final_img = final_img_padded.crop(crop_box)
    
    # 5. 保存结果
    output_path = f"output_rotated_{angle}deg.png"
    final_img.save(output_path)
    print(f"[-] 成功！{angle} 度旋转图像已保存至: {output_path}")

# 执行入口
if __name__ == "__main__":
    
    run_universal_simulation("input.png", angle=180, B_size=32)
    # run_universal_simulation("input.png", angle=180, B_size=32)
    # run_universal_simulation("input.png", angle=270, B_size=32)