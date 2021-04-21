import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

DEBUG = True

if __name__ == "__main__":
    if DEBUG:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            print("Running in a Pyinstaller bundle.")
        else:
            print("Running in a normal Python process.")

        for a in sys.argv:
            print("sys.argv[]: {}".format(a))
        print(sys.executable)
        print(os.getcwd())

    if DEBUG:
        print("THIS RUNS")
    app = QApplication([])
    if DEBUG:
        print("THIS DOESN'T")
    win = QMainWindow()
    win.setGeometry(200, 200, 300, 450)
    win.setFixedSize(300, 450)

    win.show()
    sys.exit(app.exec())


# Translate asset paths to useable format for PyInstaller
# def resource_path(relative_path):
#     if hasattr(sys, '_MEIPASS'):
#         return os.path.join(sys._MEIPASS, relative_path)
#     return os.path.join(os.path.abspath('.'), relative_path)