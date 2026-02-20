from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ShowScreen(QWidget):
    def __init__(self, parent=None):
        super(ShowScreen, self).__init__(parent)
        self.setStyleSheet("background-color: black;")

        self.isBlack = False

        self.main_label = QLabel("", self)
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_label.setWordWrap(True)
        self.main_label.setStyleSheet("color: white; font-size: 80px;")

        self.footer_label = QLabel("", self)
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_label.setWordWrap(True)
        self.footer_label.setStyleSheet("color: white; font-size: 40px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.main_label)
        layout.addWidget(self.footer_label)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setStretch(0,1)
        self.setLayout(layout)

    def setText(self, main_text: str, footer:str = ""):
        if not self.isBlack:
            self.main_label.setText(main_text)
            self.footer_label.setText(footer)

    def set_bg_color(self, color: str):
        self.setStyleSheet(f"background-color: {color}")

    def set_txt_color(self, color: str):
        self.main_label.setStyleSheet(f"color: {color}")

    def triggerBlack(self):
        if not self.isBlack:
            self.isBlack = True
            self.main_label.clear()
        else:
            self.isBlack = False

    def show_header(self):
        self.setWindowFlags(Qt.WindowType.Window)

    def hide_header(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)



if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = ShowScreen()
    sample = (
        "This is a sample long text that will wrap inside the black box and remain centered. "
        "Resize or run full-screen to see wrapping behavior."
    )
    w.setText(sample)
    # w.showFullScreen()
    w.showNormal()
    sys.exit(app.exec())