from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QCheckBox, QMessageBox
from PySide6.QtCore import QFile, Qt
from urllib.request import urlretrieve
import zipfile
import os
from pathlib import Path

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
    book_window = load_ui()
    layout_books(main_window)

    # Book window
    check_boxes = book_window.findChildren(QCheckBox)
    bnt_download_books: QPushButton = book_window.findChild(QPushButton, "btnDownloadBooks") # type: ignore
    bnt_download_books.clicked.connect(lambda: btn_download())

    # Book changing
    btn_books: QPushButton = main_window.findChild(QPushButton, "btnBooks") # type: ignore
    btn_books.clicked.connect(lambda: book_window.show())

    def btn_download():
        for item in check_boxes:
            if item.isEnabled() and item.isChecked():
                txt = item.objectName().removeprefix("check")
                book = [book for book in books if book.id == txt][0]
                download_book(book)
        set_check_boxes()
        show_finished_alert()
        layout_books(main_window)
            
    def set_check_boxes():
        found_books = find_books()
        for item in check_boxes:
            if item.objectName().removeprefix("check") in found_books:
                item.setChecked(True)
                item.setEnabled(False)

    set_check_boxes()

def layout_books(main_window):
    from database.bible import change_bible
    found_books = find_books()
    book_list: QHBoxLayout = main_window.findChild(QHBoxLayout, "bibleBookLayout")  # type: ignore
    if not book_list:
        return
    clear_layout(book_list)
    for i, x in enumerate(found_books):
        better = [book.name for book in books if book.id == x]
        title = x if len(better) == 0 else better[0]
        btn_book = QPushButton(title, main_window)
        btn_book.setProperty("bookName", x)
        btn_book.setObjectName(f"btn{x}")
        btn_book.clicked.connect(lambda checked=False, x=x: change_bible(x))
        book_list.insertWidget(i, btn_book)

def clear_layout(layout: QHBoxLayout):
    while layout.count():
        item:QLayoutItem = layout.takeAt(0) # type: ignore
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()

def find_books() -> list[str]:
    """Find sql databases in database/books | returns their name without extension"""
    path = Path(__file__).parent / "books"
    files = os.listdir(path)
    return [f.split(".")[0] for f in files]

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

if __name__ == "__main__":
 pass