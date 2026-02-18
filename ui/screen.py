from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt


class ShowScreen(QWidget):
    def __init__(self, parent=None):
        super(ShowScreen, self).__init__(parent)
        self.setStyleSheet("background-color: black;")

        self.isBlack = False

        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color: white; font-size: 28px;")

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

    def setText(self, text: str):
        if not self.isBlack:
            self.label.setText(text)

    def set_bg_color(self, color: str):
        self.setStyleSheet(f"background-color: {color}")

    def set_txt_color(self, color: str):
        self.label.setStyleSheet(f"color: {color}")

    def triggerBlack(self):
        if not self.isBlack:
            self.isBlack = True
            self.label.clear()
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