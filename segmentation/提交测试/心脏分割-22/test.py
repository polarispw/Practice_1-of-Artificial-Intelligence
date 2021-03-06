# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'im1.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

import cv2
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QBrush
from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow
from PyQt5.QtGui import QIcon
import sys
from PyQt5.QtCore import QThread, pyqtSignal
import argparse
import os

from PIL import Image

global  printed_mask

import sys
import threading
import time


import os
import json
import torch
import argparse
import numpy as np
from tqdm import tqdm

from PIL import Image
import cv2
from torch.utils.data import DataLoader
from torchvision import transforms
import segmentation_models_pytorch as smp
from data_process import get_validation_augmentation, get_preprocessing
from my_dataset import Dataset, generate_path_list
from model import efficientnetv2_m as create_model
from utils import collate

def read(i):
    file = open('data.txt', 'w')

    f=file.readlines()

    file.close()
    return





class infer(QThread):
    sig = pyqtSignal(list)
    sig1 = pyqtSignal(int)

    def __init__(self):


        super(infer, self).__init__()


    def run(self):

        parser = argparse.ArgumentParser()
        parser.add_argument('--data-path', type=str, default=imgNamepath)
        parser.add_argument('--seg_weight-path', type=str, default='best_weight_seg.pth')
        parser.add_argument('--cls_weight-path', type=str, default='best_weight_cls.pth')

        args = parser.parse_args()

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        # seg
        model = torch.load(args.seg_weight_path, map_location=device)
        encoder = "resnet18"
        preprocessing_fn = smp.encoders.get_preprocessing_fn(encoder)

        # create test dataset
        valid_img_list = generate_path_list(args.data_path)
        global total
        total = len(valid_img_list)

        test_dataset = Dataset(
            valid_img_list,
            augmentation=get_validation_augmentation(),
            preprocessing=get_preprocessing(preprocessing_fn),
        )
        test_dataloader = DataLoader(test_dataset)

        # cls
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
        cls_model = create_model(num_classes=3).to(device)
        model_weight_path = args.cls_weight_path
        cls_model.load_state_dict(torch.load(model_weight_path, map_location=device))
        cls_model.eval()

        data_transform = transforms.Compose(
            [transforms.Resize(img_size[num_model][1]),
             transforms.CenterCrop(img_size[num_model][1]),
             transforms.ToTensor(),
             transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])])

        # predict
        pre_folder = ''
        f = True

        for n, i in enumerate(tqdm(test_dataloader)):

            # ??????
            image = i.to(device)
            pr_mask = model.predict(image)
            pr_mask = (pr_mask.squeeze().cpu().numpy().round())
            classes = [85, 170, 255]
            mask = np.zeros((384, 480))
            for l in range(pr_mask.shape[0]):
                layer = np.where((pr_mask[l] > 0) & (mask == 0), classes[l], 0)
                mask += layer
            lab = Image.fromarray(mask).convert('L')
            mask = cv2.resize(mask, (256, 208))

            # ??????
            raw = Image.open(valid_img_list[n])
            raw = raw.resize((480, 384))
            cls_img = Image.blend(raw, lab, 0.3)
            cls_img = cls_img.convert("RGB")
            cls_img = data_transform(cls_img)
            # expand batch dimension
            cls_img = torch.unsqueeze(cls_img, dim=0)

            with torch.no_grad():
                # predict class
                output = torch.squeeze(cls_model(cls_img.to(device))).cpu()
                predict = torch.softmax(output, dim=0)
                predict_cls = torch.argmax(predict).item()
                cls_res = class_indict[str(predict_cls)]

            # ??????
            path = valid_img_list[n]
            name = "label" + path.split('\\')[2].split('e')[1].split('.')[0] + f"-{cls_res}" + ".png"
            save_dir = os.path.join("Label", path.split('\\')[1])
            os.makedirs(save_dir) if not os.path.exists(save_dir) else ...
            save_path = os.path.join(save_dir, name)

            cv2.imwrite(save_path, mask)

            if pre_folder != save_dir and f is False:
                collate(pre_folder)
                pre_folder = save_dir
            elif f:
                f = False
                collate(save_dir)
                pre_folder = save_dir

            self.sig.emit([n+1, total])
        collate(save_dir)

        self.sig1.emit(1)










class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(702, 272)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setDocumentMode(True)
        MainWindow.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(170, 80, 411, 31))
        self.lineEdit.setObjectName("lineEdit")
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setGeometry(QtCore.QRect(580, 80, 81, 31))
        font = QtGui.QFont()
        font.setFamily("Agency FB")
        font.setPointSize(9)
        self.pushButton_2.setFont(font)
        self.pushButton_2.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(10, 80, 161, 31))
        self.pushButton.setObjectName("pushButton")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(10, 150, 681, 41))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 702, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton_2.setText(_translate("MainWindow", "??????"))
        self.pushButton.setText(_translate("MainWindow", "????????????????????????"))




class MainCode(QMainWindow, Ui_MainWindow):


    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)



        self.setupUi(self)
        self.thread1 = infer()
        self.thread1.sig.connect(self.update_progress)
        self.thread1.sig1.connect(self.over)
        self.pushButton.clicked.connect(self.openfolder)
        self.pushButton_2.clicked.connect(self.train)






    def openfolder(self):
        global imgNamepath
        imgNamepath = QFileDialog.getExistingDirectory(self.centralwidget, directory="./")

        print(imgNamepath)
        self.lineEdit.setText(imgNamepath)
        # total=len(generate_path_list(imgNamepath))
        return imgNamepath
    def train(self):


        self.thread1.start()




    def over(self,i):
        if i:
            self.close()
            title = '?????????'
            info = "???????????????"
            QtWidgets.QMessageBox.information(self, title, info)



    def update_progress(self,ls):

        self.progressBar.setValue(int(ls[0] / ls[1] * 100))


    # def set_btn(self):
    #     self.pushButton_2.setEnabled(True)
    #

        # main(opt)




global  res
app = QApplication(sys.argv)
md = MainCode()
md.show()
app.exec_()
    # sys.exit(app.exec_())