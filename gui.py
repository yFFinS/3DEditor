from PyQt5.QtCore import QSize, QEvent, QObject, Qt
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QWidget, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QListWidgetItem



class SceneExplorer(QWidget):
    def __init__(self, parent=None):
        super(SceneExplorer, self).__init__(parent)
        #self.grabMouse()

        self.__mainLayout = QVBoxLayout()
        self.__list = QListWidget()

        self.setStyleSheet('border: 1px inset grey;')

        self.add_scene_object_widget(SceneObjectWidget())
        self.add_scene_object_widget(SceneObjectWidget())
        self.__mainLayout.addWidget(self.__list)
        self.setLayout(self.__mainLayout)

    def add_scene_object_widget(self, so_widget):
        item = QListWidgetItem()
        item.setSizeHint(so_widget.sizeHint())
        self.__list.addItem(item)
        self.__list.setItemWidget(item, so_widget)



class SceneObjectWidget(QWidget):
    def __init__(self, scene_object=None):
        super(SceneObjectWidget, self).__init__()
        #self.grabMouse()
        self.__layout = QHBoxLayout()

        #self.setStyleSheet("border: 0px solid grey;")

        font = QFont("Arial", 16)
        self.__name_label = QLabel(self)
        self.__name_label.setText("Hello world")
        self.__name_label.setFont(font)
        self.__layout.addWidget(self.__name_label)
        self._scene_object = scene_object

        self.__layout.addStretch()
        self.setLayout(self.__layout)

    def sizeHint(self):
        return self.__layout.sizeHint()

