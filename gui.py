from PyQt5.QtCore import QSize, QEvent, QObject, Qt
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QWidget
import PyQt5.QtWidgets as Widgets
from PyQt5.QtWidgets import QWidget, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QListWidgetItem
from PyQt5.QtOpenGL import QGLWidget


class SceneExplorer(QWidget):
    def __init__(self):
        super(SceneExplorer, self).__init__()

        self.__mainLayout = QVBoxLayout()
        self.__list = QListWidget()

        label1 = QLabel("Camera 1 0 0")
        label2 = QLabel("Camera 1 2 0")

        self.setStyleSheet("border: 1px outset grey;")

        self.__mainLayout.addWidget(self.__list)
        item = QListWidgetItem("hadasdasdai")
        widget = Widgets.QWidget(self.__list)
        layout = Widgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(label1)
        self.__list.setItemWidget(item, widget)
        self.setLayout(self.__mainLayout)
