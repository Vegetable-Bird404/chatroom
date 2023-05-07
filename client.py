import threading
import socket
import json  # json.dumps(some)打包   json.loads(some)解包
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow,QMessageBox, QListWidgetItem
from PyQt5.QtCore import Qt, QTimer, QThread
from PyQt5.QtGui import QTextCharFormat, QImage, QColor, QPixmap, QKeyEvent, QStandardItemModel, QStandardItem

from Login import Ui_Form
from Chatroom import *


IP = ''
PORT = ''
user = ''
listbox1 = ''  # 用于显示在线用户的列表框
ii = 0  # 用于判断是开还是关闭列表框
users = []  # 在线用户列表

class login_window(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self):
        super(login_window, self).__init__()
        self.setupUi(self)  # 创建窗体对象
        self.init()

    def init(self):
        self.pushButton.clicked.connect(self.login_button)  # 连接槽
        self.lineEdit_2.setText("127.0.0.1:50007")

    def login_button(self):
        if self.lineEdit_2.text() == "":
            QMessageBox.warning(self, '警告', 'IP地址不能为空，请输入！')
            return None
        global IP, PORT, user, Ui_Main
        IP, PORT = self.lineEdit_2.text().split(':') # 获取IP和端口号
        PORT = int(PORT)  # 端口号需要为int类型
        user = self.lineEdit.text()
        if not user:
            QMessageBox.critical(self, 'Name type error', 'Username Empty!')
        else:
            self.close()
        Ui_Main = main_window()  # 生成主窗口的实例
        Ui_Main.setWindowTitle("User Name:" + user)
        Ui_Main.show()
        # 2关闭本窗口


class main_window(QtWidgets.QMainWindow, Ui_MainWindow):

    update_txt = QtCore.pyqtSignal(list)

    def __init__(self):
        super(main_window, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.r = threading.Thread()
        self.chat = '------Group chat-------'  # 聊天对象, 默认为群聊
        self.setupUi(self)  # 创建窗体对象
        # self.treeView.setHeaderLabels('Group Chat')
        self.init()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        重写QWidget类的closeEvent方法，在窗口被关闭的时候自动触发
        """
        reply = QtWidgets.QMessageBox.question(self, '提示', "确认退出吗？",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            super().closeEvent(event)  # 先添加父类的方法，以免导致覆盖父类方法（这是重点！！！）
            # self.r.terminate()
            self.s.close()
            event.accept()
        else:
            event.ignore()

    def init(self):
        self.pushButton.clicked.connect(self.send)  # 发送连接槽
        self.listWidget.currentItemChanged.connect(self.private)
        self.update_txt.connect(self.update_text)
        self.plainTextEdit.setReadOnly(True)
        global IP, PORT, user
        PORT = int(PORT)
        self.s.connect((IP, PORT))
        if user:
            self.s.send(user.encode())  # 发送用户名
        else:
            self.s.send('no'.encode())  # 没有输入用户名则标记no
        # 如果没有用户名则将ip和端口号设置为用户名
        addr = self.s.getsockname()  # 获取客户端ip和端口号
        addr = addr[0] + ':' + str(addr[1])
        if user == '':
            user = addr
        self.plainTextEdit.insertPlainText("Welcome to the chat room!")
        # 开始线程接收信息
        self.r = threading.Thread(target=self.recv)
        self.r.setDaemon(True)  # 设置保护线程 好像没什么用
        self.r.start()  # 开始线程接收信息

    def send(self, *args):
        # 没有添加的话发送信息时会提示没有聊天对象
        users.append('------Group chat-------')
        if self.chat not in users:
            QMessageBox.warning(self, 'Send error', 'There is nobody to talk to!')
            return
        if self.chat == user:
            QMessageBox.warning(self, 'Send error', 'Cannot talk with yourself in private!')
            return
        mes = self.plainTextEdit_2.toPlainText() + ':;' + user + ':;' + self.chat  # 添加聊天对象标记
        self.s.send(mes.encode())
        self.plainTextEdit_2.setPlainText('')  # 发送后清空文本框

    def recv(self):
        # 用于时刻接收服务端发送的信息并打印
        global users
        while True:
            data = self.s.recv(1024).decode()
            # 没有捕获到异常则表示接收到的是在线用户列表
            if ":;" not in data:
                data = json.loads(data)
                users = data
                self.listWidget.clear()
                number = ('   Users online: ' + str(len(data)))
                item1 = QListWidgetItem(number)
                item1.setForeground(QColor("green"))
                item1.setBackground(QColor("#f0f0ff"))
                self.listWidget.addItem(item1)
                item2 = QListWidgetItem("------Group chat-------")
                self.listWidget.addItem(item2)
                for i in range(len(data)):
                    item = QListWidgetItem(data[i])
                    item.setForeground(QColor("green"))
                    self.listWidget.addItem(item)
            else:
                data = data.split(':;')
                data1 = data[0].strip()  # 消息
                data2 = data[1]  # 发送信息的用户名
                data3 = data[2]  # 聊天对象
                list_signal = [data1, data2, data3]
                self.update_txt.emit(list_signal)

    def update_text(self, textlist):
        data1 = textlist[0]
        data2 = textlist[1]
        data3 = textlist[2]
        color_format = QTextCharFormat()
        if data3 == '------Group chat-------':
            if data2 == user:  # 如果是自己则将则字体变为蓝色
                color_format.setForeground(QColor("blue"))
                self.plainTextEdit.setCurrentCharFormat(color_format)
                self.plainTextEdit.appendPlainText(data1)
            else:
                color_format.setForeground(QColor("green"))
                self.plainTextEdit.setCurrentCharFormat(color_format)
                self.plainTextEdit.appendPlainText(data1)  # END将信息加在最后一行
        elif data2 == user or data3 == user:  # 显示私聊
            color_format.setForeground(QColor("red"))
            self.plainTextEdit.setCurrentCharFormat(color_format)
            self.plainTextEdit.appendPlainText(data1)  # END将信息加在最后一行
        # self.listWidget.scrollToBottom()  # 显示在最后
        QApplication.processEvents()

    def private(self, item):
        # 私聊功能
        # 获取点击的索引然后得到内容(用户名)
        self.chat = item.text()
        # 修改客户端名称
        if self.chat == '------Group chat-------':
            self.setWindowTitle(user)
            return
        ti = user + '  -->  ' + self.chat
        self.setWindowTitle(ti)


if __name__ == '__main__':
    from PyQt5 import QtCore
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # 自适应分辨率
    app = QtWidgets.QApplication(sys.argv)
    window = login_window()
    window.show()
    sys.exit(app.exec_())
