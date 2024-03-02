import torch
from PIL import Image
from torchvision import transforms
import models
import torch
import cv2
import time

def yolov5_model():
    # GPU
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    # Model
    model = torch.hub.load('',
                           'yolov5s',
                           pretrained=True,
                           source='local')  # or yolov5m, yolov5l, yolov5x, custom
    model = model.to(device)
    model = model.eval()
    return model

def make_ans(model, img):
    to_tensor = transforms.ToTensor()
    tensor_image = to_tensor(img)
    tensor_image = tensor_image.unsqueeze(0)
    results = model(tensor_image)
    results = results.squeeze(0)
    index = 4
    threshold = 0.5
    col_data = results[:, index]
    val = (col_data >= threshold)
    results = results[val]
    results = results.tolist()
    ans = []
    for i in results:
        x =  i[0]
        y = i[1]
        w = i[2]
        h = i[3]
        list_q = i[-3:]
        kind = list_q.index(max(list_q))
        if kind == 2:
            continue
        else:
            pre_ans = [[x+w/2,y+h/2], [x+w/2, y-h/2], [x-w/2, y-h/2], [x-w/2, y+h/2]]
            ans.append(pre_ans)
    return ans