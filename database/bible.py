import sqlite3
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QListWidget, QWidget, QLineEdit, QPushButton, QLabel, QHBoxLayout
from PySide6.QtGui import QAction, QIntValidator
from PySide6.QtCore import QObject, Qt, QEvent
from ui.screen import ShowScreen
from database.books_manager import init_books, find_books
import re

current_book: int = -1
"""Current book id"""
current_chapter: int = -1
"""Cuurent chapter row"""
current_verse: int = -1
"""Cuurent verse row+1"""
cursor: sqlite3.Cursor | None = None


class CloseEventFilter(QObject):
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Close:
            windows = QApplication.topLevelWidgets()
            watched.removeEventFilter(self)
            for w in windows:
                w.close()
        return super().eventFilter(watched, event)
    
class BibleInfo:
    def __init__(self, id: int, short_name: str, long_name: str):
        self.id: int = id
        self.short_name: str = short_name
        self.long_name: str = long_name

    def get_full_name(self) -> str:
        return f"({self.short_name}) {self.long_name}"
    
books: list[BibleInfo]

def init(window: QWidget,second_window: ShowScreen):
    global cursor, current_book, current_chapter, current_verse, books

    class ListKeyFilter(QObject):
        def eventFilter(self, obj, event):
            if obj is self.parent() and event.type() == event.Type.KeyPress:
                if event.key() == Qt.Key.Key_Down:
                    next_verse()
                    return True
                elif event.key() == Qt.Key.Key_Up:
                    prev_verse()
                    return True
            return False

    close_filter = CloseEventFilter(window)
    window.installEventFilter(close_filter)

    init_books(window)

    # Database
    book_list = find_books()
    if len(book_list) > 0:
        cursor = init_db(book_list[0],cursor)

    books = get_bible_info(cursor)


    # QListWidgets
    book_list_widget: QListWidget  = window.findChild(QListWidget, "bookList") # type: ignore
    chapter_list_widget: QListWidget  = window.findChild(QListWidget, "chapterList") # type: ignore
    verse_list_widget: QListWidget  = window.findChild(QListWidget, "verseList") # type: ignore

    # QLineEdits
    book_edit: QLineEdit = window.findChild(QLineEdit, "bookEdit") # type: ignore
    chapter_edit: QLineEdit = window.findChild(QLineEdit, "chapterEdit") # type: ignore
    verse_edit: QLineEdit = window.findChild(QLineEdit, "verseEdit") # type: ignore

    text_info: QLabel = window.findChild(QLabel, "displayInfo") # type: ignore

    # QPushButtons
    text_up: QPushButton = window.findChild(QPushButton, "textUp") # type: ignore
    text_down: QPushButton = window.findChild(QPushButton, "textDown") # type: ignore
    btn_next: QPushButton = window.findChild(QPushButton, "btnNext") # type: ignore

    # Actions
    action_hide: QAction = window.findChild(QAction, "actionHide") # type: ignore
    action_blank: QAction = window.findChild(QAction, "actionBlank") # type: ignore
    action_black: QAction = window.findChild(QAction, "actionBlack") # type: ignore

    action_hide.triggered.connect(lambda: hide())
    action_blank.triggered.connect(lambda: second_window.main_label.clear())
    action_black.triggered.connect(lambda: second_window.triggerBlack())

    def hide():
        if action_hide.isChecked():
            second_window.hide()
        else:
            second_window.show()
        

    # Custom keyevents for verse list
    filter = ListKeyFilter(verse_list_widget)
    verse_list_widget.installEventFilter(filter)

    # Button functions
    def increase_font_size():
        f = verse_list_widget.font()
        f.setPointSize(f.pointSize() + 1)
        verse_list_widget.setFont(f)

    def decrease_font_size():
        f = verse_list_widget.font()
        f.setPointSize(max(1, f.pointSize() - 1))
        verse_list_widget.setFont(f)
    
    def next_verse():
        index = verse_list_widget.currentRow()
        index += 1
        if index == verse_list_widget.count():
            if chapter_list_widget.currentIndex().row() < chapter_list_widget.count()-1:
                chapter_list_widget.setCurrentRow(chapter_list_widget.currentRow()+1)
                verse_list_widget.setCurrentRow(0)
        else:
            verse_list_widget.setCurrentRow(index)
    
    def prev_verse():
        global current_chapter
        index = verse_list_widget.currentRow()
        index -= 1
        if index < 0:
            if current_chapter > 1:
                chapter_list_widget.setCurrentRow(chapter_list_widget.currentRow()-1)
                verse_list_widget.setCurrentRow(verse_list_widget.count()-1)
        else:
            verse_list_widget.setCurrentRow(index)

    text_up.clicked.connect(increase_font_size)
    text_down.clicked.connect(decrease_font_size)
    btn_next.clicked.connect(next_verse)

    book_list_widget.addItems([book.get_full_name() for book in books])

    # ListWidget row changed
    book_list_widget.currentRowChanged.connect(lambda index: selected_book_changed(index))
    chapter_list_widget.currentRowChanged.connect(lambda index: selected_chapter_changed(index))
    verse_list_widget.currentRowChanged.connect(lambda index: selected_verse_changed(index))
    verse_list_widget.clicked.connect(lambda index: selected_verse_clicked())

    def selected_book_changed(index: int):
        global current_book
        if index < 0:
            return
        current = book_list_widget.item(index).text()
        current_book = [book.id for book in books if book.get_full_name() == current][0]
        numbers = get_chapter_number(current_book, cursor)
        chapter_list_widget.clear()
        chapter_list_widget.addItems([str(i) for i in range(1, numbers + 1)])
        chapter_edit.setValidator(QIntValidator(1, numbers, chapter_edit))

    def selected_chapter_changed(index: int):
        global current_chapter
        if index < 0: return
        index += 1
        current_chapter = index
        verses = get_verses(current_book, index, cursor)
        verse_list_widget.clear()
        verse_list_widget.addItems([f"{str(verse[0]) + '.':<5} {verse[1]}" for verse in verses])
        verse_edit.setValidator(QIntValidator(1, len(verses)))

        book = [book.short_name for book in books if book.id == current_book][0]
        text_info.setText(book + " " + str(current_chapter))

    def selected_verse_changed(index: int):
        global current_verse
        if index < 0:
            return
        current_verse = index
        footer = text_info.text() + ":" + str(current_verse+1)
        second_window.setText(verse_list_widget.currentItem().text(), footer)

    def selected_verse_clicked():
        footer = text_info.text() + ":" + str(current_verse+1)
        text  = verse_list_widget.currentItem().text()
        second_window.setText(text, footer)

    # LineEdit text changed
    book_edit.textChanged.connect(lambda text: filter_books(text))
    chapter_edit.textChanged.connect(lambda text: chapter_changed(text))
    verse_edit.textChanged.connect(lambda text: verse_changed(text))

    def filter_books(text: str):
        filtered_books = [book.get_full_name() for book in books if (text.lower() in book.get_full_name().lower())]

        book_list_widget.clear()
        book_list_widget.addItems(filtered_books)

        if len(filtered_books) == 1:
            book_list_widget.setCurrentRow(0)
            QApplication.focusWidget().focusNextChild() # type: ignore
    
    def chapter_changed(text: str):
        filtered = [item for item in chapter_list_widget.findItems(text, Qt.MatchFlag.MatchStartsWith)]
        if len(filtered) == 1:
            chapter_list_widget.setCurrentItem(filtered[0])
            QApplication.focusWidget().focusNextChild() # type: ignore
        else:
            chapter_list_widget.setCurrentRow(-1)
    
    def verse_changed(text: str):
        filtered = [item for item in verse_list_widget.findItems(text, Qt.MatchFlag.MatchStartsWith)]
        if len(filtered) == 1:
            verse_list_widget.setCurrentItem(filtered[0])
            QApplication.focusWidget().focusNextChild() # type: ignore
        else:
            verse_list_widget.setCurrentRow(-1)

    # LineEdit finished (Enter)
    chapter_edit.editingFinished.connect(lambda: chapter_finished())
    verse_edit.editingFinished.connect(lambda: verse_finished())

    def chapter_finished():
        text = chapter_edit.text()
        chapter_list_widget.setCurrentRow(int(text)-1)
        
        QApplication.focusWidget().focusNextChild() # type: ignore
    
    def verse_finished():
        text = verse_edit.text()
        verse_list_widget.setCurrentRow(int(text)-1)
        QApplication.focusWidget().focusNextChild() # type: ignore

# Helper functions
def get_bible_info(cursor: sqlite3.Cursor | None) -> list[BibleInfo]:
    if cursor == None:
        return []
    cursor.execute("SELECT book_number, short_name, long_name FROM books ORDER BY book_number")
    rows: list[tuple[int, str, str]] = cursor.fetchall()
    return [BibleInfo(int(r[0]), r[1], r[2]) for r in rows]


def get_chapter_number(book_index: int, cursor: sqlite3.Cursor | None) -> int:
    if cursor == None:
        return -1
    cursor.execute("SELECT chapter from verses WHERE book_number == ? GROUP by chapter", (book_index,))
    res = cursor.fetchall()
    return len(res)

def get_verses(book_index: int, chapter_index: int, cursor: sqlite3.Cursor | None) -> list[tuple[int, str]]:
    if cursor == None:
        return []
    cursor.execute("SELECT verse, text FROM verses WHERE book_number == ? AND chapter == ?", (book_index, chapter_index))
    res = cursor.fetchall()
    for i in range(len(res)):
        res[i] = (res[i][0], re.sub(r"\s{2,}", " ", re.sub(r"<[^>]*>|\[[^\]]*\]", "",  res[i][1])).strip()) # bro what the helly is this? if you can deocode this : tip fedora
    return res
    
def init_db(name: str, cursor: sqlite3.Cursor | None) -> sqlite3.Cursor:
    if cursor != None:
        cursor.close()
        cursor.connection.close()
    db_path: Path = Path(__file__).parent / f"books/{name}.SQLite3"
    conn: sqlite3.Connection = sqlite3.connect(database=f"file:{db_path}?mode=ro", uri=True)
    return conn.cursor()

def change_bible(name: str):
        global cursor, current_book, current_chapter, current_verse, books
        top_level = QApplication.topLevelWidgets()
        window = [top for top in top_level if top.objectName() == "MainWindow"][0]

        book_list_widget: QListWidget  = window.findChild(QListWidget, "bookList") # type: ignore
        chapter_list_widget: QListWidget  = window.findChild(QListWidget, "chapterList") # type: ignore
        verse_list_widget: QListWidget  = window.findChild(QListWidget, "verseList") # type: ignore
        try:
            cursor = init_db(name, cursor)
            books = get_bible_info(cursor)
            
            book_list_widget.clear()
            book_list_widget.addItems([book.get_full_name() for book in books])

            book_row = books.index([b for b in books if b.id == current_book][0])
            book_list_widget.setCurrentRow(book_row)

            chapter_list_widget.setCurrentRow(current_chapter-1)
            verse_list_widget.setCurrentRow(current_verse)
        except Exception as e:
            print(f"Error changing database to {name}: {e}")