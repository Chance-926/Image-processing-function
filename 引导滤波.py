from PIL import Image
import numpy as np

#=======================================================
# 行缓存 + 3×3窗口生成
#=======================================================
class LineBuffer3x3:
    def __init__(self, width):
        self.width = width
        self.line0 = [0] * width
        self.line1 = [0] * width
        self.line2 = [0] * width
        self.x = 0                  #表示当前行内像素位置

    def shift_in(self, pixel):
        self.line2[self.x] = pixel

        # 取3×3窗口
        def get(line, idx):
            if idx < 0:
                return line[0]
            elif idx >= self.width:
                return line[self.width - 1]
            return line[idx]

        x = self.x

        window = [
            get(self.line0, x-1), get(self.line0, x), get(self.line0, x+1),
            get(self.line1, x-1), get(self.line1, x), get(self.line1, x+1),
            get(self.line2, x-1), get(self.line2, x), get(self.line2, x+1),
        ]

        self.x += 1         #下一个像素位置

        # 行结束滚动
        if self.x == self.width:
            self.x = 0
            self.line0 = self.line1[:]
            self.line1 = self.line2[:]
            self.line2 = [0] * self.width

        return window

#=======================================================
# 均值计算（9点平均）
#=======================================================
def mean_3x3(window):
    s = 0
    for v in window:
        s += v
    return s // 9   # 可替换为 >>3 近似

#=======================================================
# 方差近似（最大值 - 最小值）
#=======================================================
def variance_approx(window):
    max_v = window[0]
    min_v = window[0]

    for v in window:
        if v > max_v:
            max_v = v
        if v < min_v:
            min_v = v

    return max_v - min_v

#=================================================================================
#功能：生成 gamma LUT
#说明：gamma LUT 存储了输入像素值（0-255）到输出像素值（0-255）的映射关系。gamma 函数的公式为：
#       output = 255 * (input / 255) ^ gamma
#       其中，input 是输入像素值，output 是输出像素值，gamma 是一个控制映射曲线形状的参数。通过调整 gamma 的值，可以实现不同程度的暗部增强或亮部抑制。
#实现逻辑：
#       1. 初始化一个长度为 256 的 LUT 数组，初始值为 0。
#       2. 对于每个输入像素值 i（从0到255），计算归一化值 norm = i / 255.0。
#       3. 使用 gamma 函数计算输出值 val = int((norm **gamma) * 255.0 + 0.5)，并进行四舍五入。
#       4. 对计算得到的 val 进行饱和限制，确保其在 0 到 255 的范围内。
#       5. 将计算得到的 val 存储在 LUT 的对应位置。
#       6. 返回生成的 LUT 数组。
#=================================================================================
class GuidedFilterLite:
    def __init__(self, width, threshold):
        self.lb = LineBuffer3x3(width)
        self.threshold = threshold

    def step(self, pixel_in, valid_in):
        if valid_in == 0:
            return 0, 0

        window = self.lb.shift_in(pixel_in)

        center = window[4]

        # 计算均值
        mean = mean_3x3(window)

        # 计算“方差近似”
        var = variance_approx(window)

        # 自适应选择
        if var < self.threshold:
            pixel_out = mean      # 平滑
        else:
            pixel_out = center    # 保边缘

        return pixel_out, 1

#=================================================================================
# 整帧流式测试（功能与全文一样）
#=================================================================================
def process_stream(img, module):
    h, w = img.shape
    out = [[0]*w for _ in range(h)]

    for y in range(h):
        for x in range(w):
            pixel_in = int(img[y][x])
            pixel_out, valid = module.step(pixel_in, 1)

            if valid:
                out[y][x] = pixel_out

    return out

def load_image(path):
    img = Image.open(path).convert('L')
    return np.array(img, dtype=np.uint8)

def save_image(img_array, path):
    img = Image.fromarray(np.array(img_array, dtype=np.uint8))
    img.save(path)

#主函数
if __name__ == "__main__":
    input_path = "1.jpg"
    output_path_before = "引导滤波处理前.jpg"
    output_path_after = "引导滤波处理后.jpg"

    img = load_image(input_path)

    #人为加入噪声，用于测试引导滤波的效果，后续可删
    noise = np.random.randint(-20, 20, img.shape)
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    save_image(img, output_path_before)

    module = GuidedFilterLite(width=img.shape[1], threshold=150) #threshold参数可调节，控制平滑程度

    out = process_stream(img, module)

    save_image(out, output_path_after)