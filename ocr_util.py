import json
import os

import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging

logging.disable(logging.WARNING)  # Disable logging
logging.disable(logging.DEBUG)

ocr = PaddleOCR(use_angle_cls=True, lang="ch")


def ocr_img(image_path):
    # 读取图片文件
    img = cv2.imread(image_path)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    # 识别图片中的文字
    result = ocr.ocr(img)
    return result[0]


if __name__ == '__main__':
    result = ocr_img("pic/screenshot.png")
    print("ocr reuslt:"+str(json.dumps(result)))