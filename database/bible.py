import sqlite3
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QListWidget, QWidget, QLineEdit, QPushButton, QLabel, QToolBar
from PySide6.QtGui import QAction, QIntValidator, QCloseEvent
from PySide6.QtCore import QObject, Qt, QEvent
from ui.screen import ShowScreen

def init(window: QWidget,second_window: ShowScreen) -> None:
    C_BOOK: int = -1
    C_CHAPTER: int = -1
    C_VERSE: int = -1

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
        
    close_filter = CloseEventFilter(window)
    window.installEventFilter(close_filter)

    # Database
    db_path: Path = Path(__file__).parent / "RUF.SQLite3"
    conn: sqlite3.Connection = sqlite3.connect(database=f"file:{db_path}?mode=ro", uri=True)
    cursor: sqlite3.Cursor = conn.cursor()

    # QListWidgets
    book_list_widget: QListWidget  = window.findChild(QListWidget, "bookList") # type: ignore
    chapter_list_widget: QListWidget  = window.findChild(QListWidget, "chapterList") # type: ignore
    verse_list_widget: QListWidget  = window.findChild(QListWidget, "verseList") # type: ignore

    # QLineEdits
    book_edit: QLineEdit = window.findChild(QLineEdit, "bookEdit") # type: ignore
    chapter_edit: QLineEdit = window.findChild(QLineEdit, "chapterEdit") # type: ignore
    verse_edit: QLineEdit = window.findChild(QLineEdit, "verseEdit") # type: ignore

    # QPushButtons
    text_up: QPushButton = window.findChild(QPushButton, "textUp") # type: ignore
    text_down: QPushButton = window.findChild(QPushButton, "textDown") # type: ignore
    btn_next: QPushButton = window.findChild(QPushButton, "btnNext") # type: ignore

    # Actions
    action_hide: QAction = window.findChild(QAction, "actionHide") # type: ignore
    action_blank: QAction = window.findChild(QAction, "actionBlank") # type: ignore
    action_black: QAction = window.findChild(QAction, "actionBlack") # type: ignore

    action_hide.triggered.connect(lambda: hide())
    action_blank.triggered.connect(lambda: second_window.label.clear())
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
    def increase_font_size() -> None:
        f = verse_list_widget.font()
        f.setPointSize(f.pointSize() + 1)
        verse_list_widget.setFont(f)

    def decrease_font_size() -> None:
        f = verse_list_widget.font()
        f.setPointSize(max(1, f.pointSize() - 1))
        verse_list_widget.setFont(f)
    
    def next_verse() -> None:
        index = verse_list_widget.currentRow()
        index += 1
        if index == verse_list_widget.count():
            if chapter_list_widget.currentIndex().row() < chapter_list_widget.count()-1:
                chapter_list_widget.setCurrentRow(chapter_list_widget.currentRow()+1)
                verse_list_widget.setCurrentRow(0)
        else:
            verse_list_widget.setCurrentRow(index)
    
    def prev_verse() -> None:
        global C_CHAPTER
        index = verse_list_widget.currentRow()
        index -= 1
        if index < 0:
            if C_CHAPTER > 1:
                chapter_list_widget.setCurrentRow(chapter_list_widget.currentRow()-1)
                verse_list_widget.setCurrentRow(verse_list_widget.count()-1)
        else:
            verse_list_widget.setCurrentRow(index)

    text_up.clicked.connect(increase_font_size)
    text_down.clicked.connect(decrease_font_size)
    btn_next.clicked.connect(next_verse)

    # Get initial bible info
    cursor.execute("SELECT book_number, short_name, long_name FROM books ORDER BY book_number")
    rows: list[tuple[int, str, str]] = cursor.fetchall()
    books: list[BibleInfo] = [BibleInfo(int(r[0]), r[1], r[2]) for r in rows]

    book_list_widget.addItems([book.get_full_name() for book in books])

    # ListWidget row changed
    book_list_widget.currentRowChanged.connect(lambda index: selected_book_changed(index))
    chapter_list_widget.currentRowChanged.connect(lambda index: selected_chapter_changed(index))
    verse_list_widget.currentRowChanged.connect(lambda index: selected_verse_changed(index))
    verse_list_widget.clicked.connect(lambda index: selected_verse_clicked())

    def selected_book_changed(index: int) -> None:
        global C_BOOK
        if index < 0:
            return
        current = book_list_widget.item(index).text()
        C_BOOK = [book.id for book in books if book.get_full_name() == current][0]
        numbers = get_chapter_number(C_BOOK, cursor)
        chapter_list_widget.clear()
        chapter_list_widget.addItems([str(i) for i in range(1, numbers + 1)])
        chapter_edit.setValidator(QIntValidator(1, numbers, chapter_edit))

    def selected_chapter_changed(index: int) -> None:
        global C_BOOK; global C_CHAPTER
        if index < 0: return
        index += 1
        C_CHAPTER = index
        verses = get_verses(C_BOOK, index, cursor)
        verse_list_widget.clear()
        verse_list_widget.addItems([f"{str(verse[0]) + '.':<5} {verse[1]}" for verse in verses])
        verse_edit.setValidator(QIntValidator(1, len(verses)))

        text_info: QLabel = window.findChild(QLabel, "displayInfo") # type: ignore
        book = [book.short_name for book in books if book.id == C_BOOK][0]
        text_info.setText(book + "  " + str(C_CHAPTER))

    def selected_verse_changed(index: int):
        if index < 0:
            return
        second_window.setText(verse_list_widget.currentItem().text())

    def selected_verse_clicked():
        text  = verse_list_widget.currentItem().text()
        second_window.setText(text)

    # LineEdit text changed
    book_edit.textChanged.connect(lambda text: filter_books(text))
    chapter_edit.textChanged.connect(lambda text: chapter_changed(text))
    verse_edit.textChanged.connect(lambda text: verse_changed(text))

    def filter_books(text: str) -> None:
        filtered_books = [book.get_full_name() for book in books if (text.lower() in book.get_full_name().lower())]

        book_list_widget.clear()
        book_list_widget.addItems(filtered_books)

        if len(filtered_books) == 1:
            book_list_widget.setCurrentRow(0)
            QApplication.focusWidget().focusNextChild() # type: ignore
    
    def chapter_changed(text: str) -> None:
        filtered = [item for item in chapter_list_widget.findItems(text, Qt.MatchFlag.MatchStartsWith)]
        if len(filtered) == 1:
            chapter_list_widget.setCurrentItem(filtered[0])
            QApplication.focusWidget().focusNextChild() # type: ignore
        else:
            chapter_list_widget.setCurrentRow(-1)
    
    def verse_changed(text: str) -> None:
        filtered = [item for item in verse_list_widget.findItems(text, Qt.MatchFlag.MatchStartsWith)]
        if len(filtered) == 1:
            verse_list_widget.setCurrentItem(filtered[0])
            QApplication.focusWidget().focusNextChild() # type: ignore
        else:
            verse_list_widget.setCurrentRow(-1)

    # LineEdit finished (Enter)
    chapter_edit.editingFinished.connect(lambda: chapter_finished())
    verse_edit.editingFinished.connect(lambda: verse_finished())

    def chapter_finished() -> None:
        print("finished")
        text = chapter_edit.text()
        chapter_list_widget.setCurrentRow(int(text)-1)
        
        QApplication.focusWidget().focusNextChild() # type: ignore
    
    def verse_finished() -> None:
        text = verse_edit.text()
        verse_list_widget.setCurrentRow(int(text)-1)
        QApplication.focusWidget().focusNextChild() # type: ignore

    # Helper functions
    def get_chapter_number(book_index: int, cursor: sqlite3.Cursor) -> int:
        cursor.execute("SELECT chapter from verses WHERE book_number == ? GROUP by chapter", (book_index,))
        res = cursor.fetchall()
        return len(res)
    
    def get_verses(book_index: int, chapter_index: int, cursor: sqlite3.Cursor) -> list[tuple[int, str]]:
        cursor.execute("SELECT verse, text FROM verses WHERE book_number == ? AND chapter == ?", (book_index, chapter_index))
        res = cursor.fetchall()
        for i in range(len(res)):
            res[i] = (res[i][0], res[i][1].replace("<pb/>", "").replace("<t>", "").replace("</t>", ""))
        return res