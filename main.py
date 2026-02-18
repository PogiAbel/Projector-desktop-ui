import sys
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QFile, QIODevice, QRect
from database.bible import init
from ui.screen import ShowScreen
    
class MainApp:
    def __init__(self):
        self.load_main_window()
        self.second_window = ShowScreen()
        init(self.main_window,self.second_window)

        screens = QApplication.screens()
        screens.remove(self.main_window.screen())
        if len(screens)<1:
            self.second_window.setGeometry(QRect(50,50,800,400))
            self.second_window.show_header()
        else:
            self.second_window.setGeometry(screens[0].geometry())
            self.second_window.hide_header()
        
        self.main_window.show()
        self.second_window.show()


    def load_main_window(self):
        ui_file_name = "ui/mainwindow.ui"
        ui_file = QFile(ui_file_name)
        if not ui_file.open(QIODevice.ReadOnly): # type: ignore
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        loader = QUiLoader()
        self.main_window = loader.load(ui_file)
        ui_file.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    main = MainApp()
    
    sys.exit(app.exec())