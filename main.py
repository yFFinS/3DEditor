import sys
from PyQt5.QtWidgets import QApplication
from gui import Window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.showMaximized()
    sys.exit(app.exec_())
