from PyQt5.QtCore import QSize, QEvent, QObject, Qt
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QWidget, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QListWidgetItem, QLineEdit


class SceneExplorer(QWidget):
    def __init__(self, parent=None):
        super(SceneExplorer, self).__init__(parent)

        self.__mainLayout = QVBoxLayout()
        self.__list = SceneObjectList(self)

        #self.setStyleSheet("border:1px solid grey; ")
        #self.setStyleSheet('border: 1px inset grey;')

        self.__list.add_item(SceneObjectWidget())
        self.__list.add_item(SceneObjectWidget())
        self.__list.setFixedHeight(300)
        self.__list.setFixedWidth(300)
        self.__props = SceneObjectProperties()
        self.__props.setFixedWidth(300)

        self.__mainLayout.addWidget(self.__list)
        self.__mainLayout.addWidget(self.__props)

        self.setLayout(self.__mainLayout)


class SceneObjectProperties(QWidget):
    def __init__(self, *args):
        super(SceneObjectProperties, self).__init__(*args)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.__so = None
        self.__xyz = QWidget(self)
        xyz_layout = QHBoxLayout()
        x_edit = QLineEdit(self)
        y_edit = QLineEdit(self)
        z_edit = QLineEdit(self)
        xyz_layout.addWidget(x_edit)
        xyz_layout.addWidget(y_edit)
        xyz_layout.addWidget(z_edit)
        self.__xyz.setLayout(xyz_layout)
        layout.addWidget(self.__xyz)
        label = QLabel("Amogus", self)
        layout.addWidget(label)

    def set_object(self, scene_object):
        self.__so = scene_object


class PositionProperty(QWidget):
    def __init__(self, *args):
        super(PositionProperty, self).__init__(*args)


class SceneObjectList(QListWidget):
    def __init__(self, parent=None):
        super(SceneObjectList, self).__init__(parent)

    def add_item(self, so_widget):
        item = QListWidgetItem()
        item.setSizeHint(so_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, so_widget)


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

