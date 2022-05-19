import datetime
import sys
from PyQt5.QtWidgets import QApplication
from gui.editor import Window
from profiling.profiler import Profiler

PROFILE = True

if __name__ == "__main__":
    if PROFILE:
        Profiler.init()

    app = QApplication(sys.argv)
    window = Window()
    window.showMaximized()
    exit_code = app.exec_()

    if PROFILE:
        log_name = ("profile_" + str(datetime.datetime.now()).split('.')[0]) + '.prof'
        log_name = log_name.replace(' ', '-').replace(':', '-')
        Profiler.dump(log_name)

    sys.exit(exit_code)
