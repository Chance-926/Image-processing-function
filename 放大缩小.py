from PIL import Image
import numpy as np

#将图像转化为灰度图，返回数组形式
def load_image(path):
    img = Image.open(path).convert('L')  # 灰度图
    return np.array(img, dtype=np.uint8)

#保存图片
def save_image(img_array, path):
    img = Image.fromarray(img_array)
    img.save(path)

def upscale_x2_fixed(img):
    h, w = img.shape
    out_h, out_w = h * 2, w * 2
    #创建全零矩阵，数据类型为8位无符号整数
    out = np.zeros((out_h, out_w), dtype=np.uint8)

    for y in range(out_h):
        for x in range(out_w):

            # 映射回原图（定点：1/2 → 右移）
            src_x = x >> 1
            src_y = y >> 1

            dx = x & 1   # 做“与运算”，x为奇数时 dx=1，偶数时 dx=0
            dy = y & 1   # 做“与运算”，y为奇数时 dy=1，偶数时 dy=0

            # 原图邻域像素
            p00 = img[src_y, src_x]
            p01 = img[src_y, min(src_x + 1, w - 1)]
            p10 = img[min(src_y + 1, h - 1), src_x]
            p11 = img[min(src_y + 1, h - 1), min(src_x + 1, w - 1)]

            # 权重（只可能是 0 或 0.5 或 1）
            if dx == 0 and dy == 0:
                val = p00
            elif dx == 1 and dy == 0:
                val = (p00 + p01) >> 1
            elif dx == 0 and dy == 1:
                val = (p00 + p10) >> 1
            else:
                val = (p00 + p01 + p10 + p11) >> 2

            out[y, x] = val

    return out

def downscale_x2_fixed(img):
    h, w = img.shape
    out_h, out_w = h // 2, w // 2

    out = np.zeros((out_h, out_w), dtype=np.uint8)

    for y in range(out_h):
        for x in range(out_w):

            p00 = img[2*y, 2*x]
            p01 = img[2*y, min(2*x + 1, w - 1)]
            p10 = img[min(2*y + 1, h - 1), 2*x]
            p11 = img[min(2*y + 1, h - 1), min(2*x + 1, w - 1)]

            # 平均（硬件：加法+右移2）对四个像素取平均
            val = (p00 + p01 + p10 + p11) >> 2

            out[y, x] = val

    return out

if __name__ == "__main__":
    input_path = r"E:\YOLO_dataset\coco128\images\train2017\1.jpg"
    up_output_path = r"E:\刘尚霖\大学\竞赛\集创赛\比赛\放大缩小模块\放大.jpg"
    down_output_path = r"E:\刘尚霖\大学\竞赛\集创赛\比赛\放大缩小模块\缩小.jpg"

    img = load_image(input_path)

    # 放大
    up_img = upscale_x2_fixed(img)
    save_image(up_img, up_output_path)

    # 缩小
    down_img = downscale_x2_fixed(img)
    save_image(down_img, down_output_path)