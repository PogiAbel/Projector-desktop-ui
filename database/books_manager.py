from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QCheckBox, QMessageBox, QListWidget, QProgressBar, QLabel
from PySide6.QtCore import QFile, Qt,  QThread, Signal
from urllib.request import urlretrieve
import zipfile
import os
from utils.file_manager import find_books

class BibleBook:
    def __init__(self, name:str, id:str, url: str):
        self.name = name
        self.id = id
        self.url = url

    def __str__(self) -> str:
        return f"{self.name} ({self.id}) : {self.url}"

books = [
    BibleBook('Úf','HUNB', 'https://www.ph4.org/_dl.php?back=bbl&a=HUNB&b=mybible&c'),
    BibleBook('Kar','KB', 'https://www.ph4.org/_dl.php?back=bbl&a=KB&b=mybible&c'),
    BibleBook('RKar','KSZE', 'https://www.ph4.org/_dl.php?back=bbl&a=KSZE&b=mybible&c'),
    BibleBook('Rúf','RUF', 'https://www.ph4.org/_dl.php?back=bbl&a=RUF&b=mybible&c'),
]

def init_books(main_window: QWidget):
    from database.bible import change_bible
    book_window = load_ui()
    layout_books(main_window)

    # Book window
    check_boxes = book_window.findChildren(QCheckBox)
    bnt_download_books: QPushButton = book_window.findChild(QPushButton, "btnDownloadBooks") # type: ignore
    bnt_download_books.clicked.connect(lambda: btn_download())

    # Book changing
    btn_books: QPushButton = main_window.findChild(QPushButton, "btnBooks") # type: ignore
    btn_refresh: QPushButton = book_window.findChild(QPushButton, "btnRefresh") # type: ignore
    
    btn_books.clicked.connect(lambda: book_window.show())
    btn_refresh.clicked.connect(lambda: layout_books(main_window))

    def btn_download():
        info_window = DownloadInfo(main_window)
        info_window.show()
        info_window.set_state(DownloadInfo.DOWNLOADING)

        check_ed = [c for c in check_boxes if (c.isEnabled() and c.isChecked())]
        books_to_download = []

        for item in check_ed:
            txt = item.objectName().removeprefix("check")
            book = [book for book in books if book.id == txt][0]
            books_to_download.append(book)

        worker = DownloadWorker(books_to_download)

        worker.progress.connect(info_window.set_progress)
        worker.finished.connect(lambda: on_download_finished(info_window, worker))
        worker.failed.connect(lambda msg: on_download_failed(info_window, worker, msg))

        worker.start()

    def on_download_finished(info_window, worker):
        info_window.set_state(DownloadInfo.FINISHED)
        set_check_boxes()
        layout_books(main_window)
        worker.deleteLater()

    def on_download_failed(info_window, worker, msg):
        info_window.set_state(DownloadInfo.FAILED)
        info_window.label.setText(f"Download failed: {msg}")
        worker.deleteLater()
            
    def set_check_boxes():
        found_books = find_books()
        for item in check_boxes:
            if item.objectName().removeprefix("check") in found_books:
                item.setChecked(True)
                item.setEnabled(False)

    bible_list: QListWidget = main_window.findChild(QListWidget, "bibleList") # type: ignore
    bible_list.currentRowChanged.connect(lambda x: change_bible(x))
    bible_list.setCurrentRow(0)
    set_check_boxes()

def layout_books(main_window):
    found_books = find_books()
    bible_list: QListWidget = main_window.findChild(QListWidget, "bibleList") # type: ignore
    if not bible_list:
        return
    c_book = bible_list.currentIndex()
    bible_list.clear()
    bible_list.addItems(found_books)
    bible_list.setCurrentIndex(c_book)

def clear_layout(layout: QListWidget):
    while layout.count():
        item:QLayoutItem = layout.takeAt(0) # type: ignore
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()

def load_ui() -> QWidget:
    ui_file_name = "ui/downloadBooks.ui"
    ui_file = QFile(ui_file_name)
    loader = QUiLoader()
    book_window:QWidget = loader.load(ui_file)
    ui_file.close()

    return book_window

def download_book(book: BibleBook):
    path = f"./database/books/{book.id}.zip"

    urlretrieve(book.url, path)
    with zipfile.ZipFile(path, mode="r") as archive:
        archive.extract(f"{book.id}.SQLite3", f"./database/books")
    os.remove(path)

def show_finished_alert():
    alert = QMessageBox()
    alert.setWindowTitle("Download Complete")
    alert.setText("Finished downloading")
    alert.setIcon(QMessageBox.Icon.Information)
    alert.setWindowFlags(alert.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    alert.exec()

def show_download():
    alert = QMessageBox()
    alert.setWindowTitle("Download in progress")
    alert.setText("Wait for downloading")
    alert.setIcon(QMessageBox.Icon.Information)
    alert.setWindowFlags(alert.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    alert.show()

class DownloadInfo(QMessageBox):
    IDLE = 0
    DOWNLOADING = 1
    FINISHED = 2
    FAILED = 3

    def __init__(self, parent=None):
        super().__init__(parent)

        self.state = self.IDLE

        self.setWindowTitle("Downloading...")
        self.setIcon(QMessageBox.Icon.Information)

        # UI elements
        self.label = QLabel("Preparing download...")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)

        self.addButton(self.ok_button, QMessageBox.ButtonRole.AcceptRole)

        layout: QLayout = self.layout() # type: ignore
        layout.addWidget(self.label, 0, 1)
        layout.addWidget(self.progress, 1, 1)

        # Disable close button initially
        self.setStandardButtons(QMessageBox.StandardButton.NoButton)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self.set_state(self.IDLE)

    def set_state(self, state: int):
        self.state = state

        if state == self.IDLE:
            self.label.setText("Waiting to start download...")
            self.progress.setValue(0)
            self.ok_button.setEnabled(False)
            self._lock_window(True)

        elif state == self.DOWNLOADING:
            self.label.setText("Downloading...")
            self.ok_button.setEnabled(False)
            self._lock_window(True)

        elif state == self.FINISHED:
            self.label.setText("Download finished successfully!")
            self.progress.setValue(100)
            self.ok_button.setEnabled(True)
            self._lock_window(False)

        elif state == self.FAILED:
            self.label.setText("Download failed.")
            self.ok_button.setEnabled(True)
            self._lock_window(False)

    def set_progress(self, percent: int):
        """Update progress (0–100)."""
        self.progress.setValue(percent)
        self.label.setText(f"Downloading... {percent}%")

    def _lock_window(self, locked: bool):
        """Prevent closing while downloading."""
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, not locked)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, not locked)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, not locked)
        self.setWindowFlag(Qt.WindowType.CustomizeWindowHint, True)
        self.show()

    def closeEvent(self, event):
        """Block closing while downloading."""
        if self.state == self.DOWNLOADING:
            event.ignore()
        else:
            event.accept()

class DownloadWorker(QThread):
    progress = Signal(int)
    finished = Signal()
    failed = Signal(str)

    def __init__(self, books, parent=None):
        super().__init__(parent)
        self.books = books

    def run(self):
        total = len(self.books)
        try:
            for index, book in enumerate(self.books, start=1):
                download_book(book)
                percent = int(index / total * 100)
                self.progress.emit(percent)
            self.finished.emit()
        except Exception as e:
            self.failed.emit(str(e))

if __name__ == "__main__":
 pass