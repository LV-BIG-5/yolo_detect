import login
import sys
import json
import registration
import camera_menu
from PyQt5.QtWidgets import  QApplication, QWidget, QMessageBox, QPushButton, QVBoxLayout, QDialog, QMainWindow
import os
import select
import cv2
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtCore import QTimer
import yolo_detect
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import datetime
import threading
class Communicate(QObject):
    closeSignal = pyqtSignal()


class MainWindow(QMainWindow):
    def __init__(self,parent=None):
        super(QMainWindow,self).__init__(parent)
        self.ui = login.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.lineEdit.textChanged.connect(self.get_text)
        self.ui.lineEdit_2.textChanged.connect(self.get_text)
        self.ui.pushButton.clicked.connect(self.login_camera)
        self.ui.pushButton_2.clicked.connect(self.regedit)

    def get_text(self):
        self.user_name = self.ui.lineEdit.text()
        self.password = self.ui.lineEdit_2.text()

    def login_camera(self):
        with open("client.json", "r") as f:
            client_dict = json.load(f)
        if self.user_name in client_dict:
            if self.password == client_dict[self.user_name]:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("请在终端输入你的产品序列号")
                msg.exec_()
                while True:
                    with open("random_serial_numbers.json", "r") as f:
                        data = json.load(f)
                        cord = input()
                        if cord in data:
                            break
                        else:
                            msg = QMessageBox()
                            msg.setIcon(QMessageBox.Warning)
                            msg.setText("序列号不存在，请重新输入")
                            msg.exec_()
                            os.system("cls")
                self.close()
                camera_page.show()
            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("密码错误")
                msg.exec_()
        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("用户名不存在")
            msg.exec_()

    def regedit(self):
        self.close()
        regedit_window.show()

class Regedit(QMainWindow):
    def __init__(self,parent=None):
        super(QMainWindow, self).__init__(parent)
        self.ui = registration.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.lineEdit_2.textChanged.connect(self.get_text)
        self.ui.lineEdit_3.textChanged.connect(self.get_text)
        self.ui.pushButton.clicked.connect(self.write_json)

    def get_text(self):
        self.username = self.ui.lineEdit_2.text()
        self.passward = self.ui.lineEdit_3.text()

    def write_json(self):
        with open("client.json", "r") as f:
            client_dict = json.load(f)
        if self.username in client_dict:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("用户已经存在")
            msg.exec_()
        else:
            client_dict[self.username] = self.passward
            with open("client.json", "w") as f:
                json.dump(client_dict, f)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("注册成功")
            msg.exec_()
            self.close()
            login_menu.show()


class cameraPage(QMainWindow):
    def __init__(self,parent=None):
        super(QMainWindow, self).__init__(parent)
        self.ui = camera_menu.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton_4.clicked.connect(self.get_area)
        self.ui.pushButton.clicked.connect(self.initCamera)
        self.ui.pushButton_2.clicked.connect(self.close_camera)
        self.ui.pushButton_3.clicked.connect(self.quite_camera)
        self.model = yolo_detect.yolov5_model()
        select_area.c.closeSignal.connect(self.reload_background)
        self.timer = QTimer(self)
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.judge_save)
        self.timer2.start(100)
        self.slm = QStringListModel()
        self.qlist = []
        self.q_count = 0
        self.count = 0
        self.slm.setStringList(self.qlist)
        self.ui.listView.setModel(self.slm)

    def get_area(self):
        p_list.clear()
        self.close_camera()
        blank_image = np.zeros((640, 640, 3), np.uint8)
        select_area.data.emit()
        select_area.show()

    def get_camera(self):
        ret, img = capture.read()
        img = cv2.resize(img,(640, 640))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        ans = yolo_detect.make_ans(self.model, img_rgb)
        visual = img
        result = []
        result = [get_bbox_from_corners(corners) for corners in ans]
        result = non_max_suppression(result, 0.7)
        result = [[[x_min,y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]]for x_min, y_min, x_max, y_max in result]
        result1 = []
        if len(p_list) == 0:
            result1 = result
        else:
            for i in result:
                for j in i:
                    if in_or_out(j, p_list) :
                        result1.append(i)
                        break
                    else:
                        continue
        self.count = len(result1)
        blank_image = np.zeros((640, 640, 3), np.uint8)
        cv2.polylines(blank_image, [np.array(p_list, np.int32).reshape((-1, 1, 2))], isClosed=True, color=(255, 0, 0),
                      thickness=2)
        for i in result1:
            cv2.polylines(blank_image, [np.array(i, np.int32).reshape((-1, 1, 2))], isClosed=True,
                          color=(203, 192, 255),
                          thickness=2)
        result = cv2.addWeighted(blank_image, 0.5, img_rgb, 1, 0)
        h, w, ch = result.shape
        bytesPerLine = ch*w
        convertToQtFormat = QImage(result.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convertToQtFormat)
        self.ui.label.setPixmap(pixmap)
        self.ui.label.setScaledContents(True)

    def close_camera(self):
        self.timer.stop()
        self.timer2.stop()
        self.ui.label.clear()

    def reload_background(self):
        if flag:
            self.initCamera()
        else:
            self.close_camera()

    def quite_camera(self):
        flag = False
        self.close()

    def initCamera(self):
        flag = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_camera)
        self.timer.start(100)
        self.timer2.start(10000)

    def judge_save(self):
        ret, img = capture.read()
        img = cv2.resize(img, (640, 640))
        if self.count>self.q_count:
            now = datetime.datetime.now()
            now_formatted = now.strftime('%Y%m%d %H%M%S')
            img_rgb = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            cv2.imwrite(f'./data_r/{now_formatted}.jpg', img_rgb)
            self.q_count = self.count
            text = f"{now_formatted}\t\t./data_r/{now_formatted}.jpg"
            index = self.count
            self.slm.beginInsertRows(QModelIndex(), index-1, index-1)
            self.qlist.append(text)
            self.slm.setStringList(self.qlist)
            self.slm.endInsertRows()
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("有违停，请及时处理")
            msg.exec_()
        else:
            self.q_count = self.count
        self.timer2.start(10000)

class select_a(QMainWindow):
    data = pyqtSignal()
    def __init__(self, parent=None):
        super(QMainWindow,self).__init__(parent)
        self.c = Communicate()
        self.ui = select.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton.clicked.connect(self.makesure)
        self.p_list = []
        self.data.connect(self.get_image)
        #self.thread = threading.Thread(target=self.reload_img)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton :
            pos = event.pos()
            pos_list = [pos.x(), pos.y()]
            p_list.append(pos_list)
        blank_image = np.zeros((640, 640, 3), np.uint8)
        blank_image = cv2.cvtColor(blank_image, cv2.COLOR_BGR2RGB)
        cv2.polylines(blank_image, [np.array(p_list, np.int32).reshape(( -1, 1, 2))], isClosed=True, color=(255, 0, 0),
                      thickness=2)
        result = cv2.addWeighted(blank_image, 1, self.img_v, 1, 0)
        h, w, ch = result.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(result.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convertToQtFormat)
        self.ui.label.setPixmap(pixmap)
        self.ui.label.setScaledContents(True)
    def makesure(self):
        self.close()

    def closeEvent(self, event):
        self.c.closeSignal.emit()
        super(select_a, self).closeEvent(event)

    def get_image(self):
        self.ret_v, self.img_v = capture.read()
        self.img_v = cv2.resize(self.img_v, (640, 640))
        self.img_v = cv2.cvtColor(self.img_v, cv2.COLOR_BGR2RGB)
        h, w, ch = self.img_v.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(self.img_v.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convertToQtFormat)
        self.ui.label.setPixmap(pixmap)
        self.ui.label.setScaledContents(True)

    def start(self):
        self.thread.start()

"""    def reload_img(self):
        blank_image = np.zeros((640, 640, 3), np.uint8)
        blank_image = cv2.cvtColor(blank_image, cv2.COLOR_BGR2RGB)
        cv2.polylines(blank_image, [np.array(p_list, np.int32).reshape((-1, 1, 2))], isClosed=True, color=(255, 0, 0),
                      thickness=2)
        print("1")
        result = cv2.addWeighted(blank_image, 0.5, self.img_v, 1, 0)
        h, w, ch = result.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(result.data, w, h, bytesPerLine, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(convertToQtFormat)
        self.ui.label.setPixmap(pixmap)
        self.ui.label.setScaledContents(True)"""

#write by heheyang
def in_or_out(point,rangelist): #point为点，rangelist为多边形的定点
    rlon = []
    rlat = []
    for p in rangelist:
        rlon.append(p[0])
        rlat.append(p[1])
    maxlon = max(rlon)
    maxlat = max(rlat)
    minlon = min(rlon)
    minlat = min(rlat)

    if (point[0] > maxlon or point[0] < minlon or point[1] > maxlat or point[1] < minlat):
        return False

    # 构建各边
    s_list = []
    for i in range(len(rangelist)):
        if i != len(rangelist) - 1:
            s_list.append([rangelist[i], rangelist[i + 1]])
        else:
            s_list.append([rangelist[i], rangelist[0]])

    # 判断射线与各边的交点个数以及交点是否在边
    common = 0
    p = False
    for s in s_list:
        if s[1][0] - s[0][0] == 0:  # 垂直边
            if point[0] == s[0][0] and min(s[0][1], s[1][1]) <= point[1] <= max(s[0][1], s[1][1]):
                p = True
                break  # 水平射线恰好在垂直边上
        else:
            y = ((s[1][1] - s[0][1]) / (s[1][0] - s[0][0])) * (point[0] - s[0][0]) + s[0][1]
            if point[1] == y and point[0] <= max(s[0][0], s[1][0]):
                p = True
                break  # 水平射线恰好通过顶点
            elif point[1] < y <= max(s[0][1], s[1][1]) and point[0] < max(s[0][0], s[1][0]):
                common += 1  # 有效交点计数

    # 判断in or out
    return common % 2 != 0 or p


def get_bbox_from_corners(corners):
    xs = [corner[0] for corner in corners]
    ys = [corner[1] for corner in corners]
    return [min(xs), min(ys), max(xs), max(ys)]


def bb_intersection_over_union(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    iou = interArea / float(boxAArea + boxBArea - interArea)

    return iou


def non_max_suppression(boxes, iou_threshold):
    if len(boxes) == 0:
        return []

    boxes = sorted(boxes, key=lambda x: (x[0], x[1]))
    keep = []

    while boxes:
        current = boxes[0]
        keep.append(current)
        # 剩下的矩形中去除与当前矩形IoU大于阈值的矩形
        boxes = [box for box in boxes[1:] if bb_intersection_over_union(current, box) < iou_threshold]

    return keep

if __name__ == "__main__":
    capture = cv2.VideoCapture(0)
    flag = False
    visual = np.zeros((640, 640, 3), np.uint8)
    p_list = []
    app =   QApplication(sys.argv)
    login_menu = MainWindow()
    regedit_window = Regedit()
    select_area = select_a()
    camera_page = cameraPage()
    login_menu.show()
    sys.exit(app.exec_())
