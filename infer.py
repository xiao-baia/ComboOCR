import cv2
import time
import sys
import torch
import numpy as np
from onnxocr.onnx_paddleocr import ONNXPaddleOcr, sav2Img
from utils.utils_doctr_plus import DocTr_Plus
from utils.utils_gcdrnet import convert_state_dict, stride_integral
from model.unext import UNext_full_resolution_padding, UNext_full_resolution_padding_L_py_L
#固定到onnx路径·
# sys.path.append('./paddle_to_onnx/onnx')

# OnnxOCR模型
model = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)

# 翘曲模型
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
dewarp_model = DocTr_Plus(weights="./models/doctr_plus/model.pt", device=device)

# # 加载外观增强模型
# gcnet = UNext_full_resolution_padding(num_classes=3, input_channels=3, img_size=512).to(device)
# state = convert_state_dict(
#     torch.load('./models/gcdr_net/gcnet/checkpoint.pkl', map_location=device)['model_state'])
# gcnet.load_state_dict(state)
# gcnet.eval()
#
# drnet = UNext_full_resolution_padding_L_py_L(num_classes=3, input_channels=6, img_size=512).to(device)
# state = convert_state_dict(
#     torch.load('./models/gcdr_net/drnet/checkpoint.pkl', map_location=device)['model_state'])
# drnet.load_state_dict(state)
# drnet.eval()


# image = cv2.imread('./onnxocr/test_images/715873facf064583b44ef28295126fa7.jpg')
image = cv2.imread('./onnxocr/test_images/blank.jpg')


# ## 外观增强模型推理
# im_org, padding_h, padding_w = stride_integral(image)
# h, w = im_org.shape[:2]
# im = im_org
# with torch.no_grad():
#     im = torch.from_numpy(im.transpose(2, 0, 1) / 255).unsqueeze(0)
#     im = im.float().to(device)
#     im_org = torch.from_numpy(im_org.transpose(2, 0, 1) / 255).unsqueeze(0)
#     im_org = im_org.float().to(device)
#
#     shadow = gcnet(im)
#     shadow = F.interpolate(shadow, (h, w))
#
#     model1_im = torch.clamp(im_org / shadow, 0, 1)
#     pred, _, _, _ = drnet(torch.cat((im_org, model1_im), 1))
#
#     shadow = shadow[0].permute(1, 2, 0).data.cpu().numpy()
#     shadow = (shadow * 255).astype(np.uint8)
#     shadow = shadow[padding_h:, padding_w:]
#
#     model1_im = model1_im[0].permute(1, 2, 0).data.cpu().numpy()
#     model1_im = (model1_im * 255).astype(np.uint8)
#     model1_im = model1_im[padding_h:, padding_w:]
#
#     pred = pred[0].permute(1, 2, 0).data.cpu().numpy()
#     pred = (pred * 255).astype(np.uint8)
#     pred = pred[padding_h:, padding_w:]
# image = np.clip(pred, 0, 255).astype(np.uint8)

## 翘曲模型推理
img_ori = image / 255.
h_, w_, c_ = img_ori.shape
img_ori = cv2.resize(img_ori, (2560, 2560))
h, w, _ = img_ori.shape
img = cv2.resize(img_ori, (288, 288))
img = img.transpose(2, 0, 1)
img = torch.from_numpy(img).float().unsqueeze(0)
img = img.to(device)
with torch.no_grad():
    bm = dewarp_model(img)
    bm = bm.cpu().numpy()[0]
    bm0 = bm[0, :, :]
    bm1 = bm[1, :, :]
    bm0 = cv2.blur(bm0, (3, 3))
    bm1 = cv2.blur(bm1, (3, 3))

    img_geo = cv2.remap(img_ori, bm0, bm1, cv2.INTER_LINEAR) * 255
    img_geo = cv2.resize(img_geo, (w_, h_))
image = np.clip(img_geo, 0, 255).astype(np.uint8)

## OnnxOCR模型推理
s = time.time()
result = model.ocr(image)
e = time.time()
print("total time: {:.3f}".format(e - s))
print("result:", result)
for box in result[0]:
    print(box)

sav2Img(image, result, name=str(time.time())+'.jpg')