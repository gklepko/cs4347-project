import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt

class LibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Library Management System")
        self.setGeometry(100, 100, 600, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Library Management System")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter book title or author...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        # Results display
        results_label = QLabel("Results:")
        main_layout.addWidget(results_label)
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        main_layout.addWidget(self.results_display)

        # Button section
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Book")
        add_button.clicked.connect(self.on_add_book)
        borrow_button = QPushButton("Borrow Book")
        borrow_button.clicked.connect(self.on_borrow_book)
        button_layout.addWidget(add_button)
        button_layout.addWidget(borrow_button)
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

    def on_search(self):
        query = self.search_input.text()
        self.results_display.setText(f"Searching for: {query}")

    def on_add_book(self):
        self.results_display.setText("Add Book dialog would open here")

    def on_borrow_book(self):
        self.results_display.setText("Borrow Book dialog would open here")


def main():
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
