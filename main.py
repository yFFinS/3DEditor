import datetime
import sys
from PyQt5.QtWidgets import QApplication
from gui.editor import Window
from profiling.profiler import Profiler

if __name__ == "__main__":
    profile = '-p' in sys.argv or '--profile' in sys.argv

    if profile:
        Profiler.init()

    app = QApplication(sys.argv)
    window = Window()
    window.showMaximized()

    exit_code = app.exec_()

    if profile:
        log_name = ("profile_"
                    + str(datetime.datetime.now()).split('.')[0]
                    + '.prof')
        log_name = log_name.replace(' ', '-').replace(':', '-')
        Profiler.dump(log_name)

    sys.exit(exit_code)
