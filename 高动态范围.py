from PIL import Image
import numpy as np

def generate_hdr_lut():
    """
    HDR LUT（抛物线型增强）

    """

    lut = [0] * 256

    for x in range(256):
        if x <= 128:
            y = (x ** 0.5)*(128**0.5)  # 抛物线增强暗部
        else:
            y = 256 - ((256 - x) **0.5)*(128**0.5) # 抛物线增强亮部

        # 饱和限制（硬件等价）
        if y < 0:
            y = 0
        elif y > 255:
            y = 255

        lut[x] = y

    return lut

class HDR_LUT:
    def __init__(self):
        self.lut = generate_hdr_lut()

    def step(self, pixel_in, valid_in):
        """
        硬件时序模型
        """
        if valid_in == 0:
            return 0, 0

        pixel_out = self.lut[pixel_in]

        return pixel_out, 1
    
def process_stream(img, module):
    h, w = img.shape
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
    input_path = "1.jpg"
    output_path = "高动态范围.jpg"

    img = load_image(input_path)

    hdr_module = HDR_LUT()

    out = process_stream(img, hdr_module)

    save_image(out, output_path)