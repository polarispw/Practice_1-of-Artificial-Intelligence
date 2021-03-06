import os
import json

import torch
from PIL import Image
from torchvision import transforms
from tqdm import tqdm
import numpy as np
import cv2
from model import efficientnetv2_s as create_model

def scaleRadius(img,scale):
    x = img[int(img.shape[0]/2),:,:].sum(1) # 图像中间1行的像素的3个通道求和。输出（width*1）
    r = (x>x.mean()/10).sum()/2 # x均值/10的像素是为眼球，计算半径
    s = scale*1.0/r
    return cv2.resize(img,(0,0),fx=s,fy=s)

def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    img_size = {"s": [300, 384],  # train_size, val_size
                "m": [384, 480],
                "l": [384, 480]}
    num_model = "m"

    # read class_indict
    json_path = './class_indices.json'
    assert os.path.exists(json_path), "file: '{}' dose not exist.".format(json_path)

    with open(json_path, "r") as f:
        class_indict = json.load(f)

    # create model
    model = create_model(num_classes=4).to(device)
    model01 = create_model(num_classes=2).to(device)
    model12 = create_model(num_classes=2).to(device)
    model23 = create_model(num_classes=2).to(device)
    model_bi = [model01, model12, model23]
    weights_list = ["best_weight_01.pth", "best_weight_12.pth", "best_weight_23.pth"]
    for i, path in enumerate(weights_list):
        if os.path.exists(path):
            weights_dict = torch.load(path, map_location=device)
            load_weights_dict = {k: v for k, v in weights_dict.items()
                                 if model_bi[i].state_dict()[k].numel() == v.numel()}
            print(model_bi[i].load_state_dict(load_weights_dict, strict=False))
        else:
            raise FileNotFoundError("No weights file: {}".format(model_bi[i]))
    # load model weights
    model_weight_path = "best_weight_0523-0135.pth"
    model.load_state_dict(torch.load(model_weight_path, map_location=device))
    model.eval()

    data_transform = transforms.Compose(
        [transforms.Resize(img_size[num_model][1]),
         transforms.CenterCrop(img_size[num_model][1]),
         transforms.ToTensor(),
         transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])])

    # procedure
    data_path = "../../test"
    img_names = os.listdir(data_path)
    res = []
    for i in tqdm(img_names):
        img_path = data_path + "/" + i
        assert os.path.exists(img_path), "file: '{}' dose not exist.".format(img_path)

        img = cv2.imread(img_path)
        scale = 300
        a = scaleRadius(img, scale)
        # subtract local mean color
        a = cv2.addWeighted(a, 4, cv2.GaussianBlur(a, (0, 0), scale / 30),-4, 128)
        # remove out er 10%
        b = np.zeros(a.shape)
        cv2.circle(b, (int(a.shape[1] / 2), int(a.shape[0] / 2)), int(scale * 0.9), (1, 1, 1), -1, 8, 0)
        a = a * b + 128 * (1 - b)
        cv2.imwrite('./temp.png', a)
        img = Image.open('./temp.png')

        img = data_transform(img)
        # expand batch dimension
        img = torch.unsqueeze(img, dim=0)

        with torch.no_grad():
            # predict class
            output = torch.squeeze(model(img.to(device))).cpu()
            predict = torch.softmax(output, dim=0)
            predict_cls = torch.argmax(predict).item()

            prob = predict/predict.sum()

            prob_ = prob.clone()
            first_max = prob[predict_cls]
            prob_[predict_cls] = 0
            second_max, second_label = torch.max(prob_, dim=0)

            if first_max - second_max < 0.25:
                if (predict_cls == 0 and second_label == 1):
                    p_ = model_bi[0](img.to(device))
                    c = torch.max(p_, dim=1)[1]
                    predict_cls = c
                elif (predict_cls == 1 and second_label == 2) or (predict_cls == 2 and second_label == 1):
                    p_ = model_bi[1](img.to(device))
                    c = torch.max(p_, dim=1)[1] + 1
                    predict_cls = c
                elif (predict_cls == 3 and second_label == 2):
                    p_ = model_bi[2](img.to(device))
                    c = torch.max(p_, dim=1)[1] + 2
                    predict_cls = c

        res.append([str(i), int(predict_cls)])

    np.save("./pre.npy", res)
    print("Results have been saved in pre.npy")

if __name__ == '__main__':
    main()
    res = np.load('pre.npy')
    print(res)
