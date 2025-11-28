import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QStackedWidget
)
from PyQt6.QtCore import Qt
from book_search import BookSearchManager

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
        self.search_input.setPlaceholderText("Enter book title, author, or ISBN...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        # Results display
        self.results_label = QLabel("Results:")
        main_layout.addWidget(self.results_label)
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Title", "ISBN", "Authors", "Status"])
        self.results_table.resizeColumnsToContents()
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        main_layout.addWidget(self.results_table)

        # Button section
        button_layout = QHBoxLayout()
        borrow_button = QPushButton("Checkout Book")
        borrow_button.clicked.connect(self.on_borrow_book)
        button_layout.addWidget(borrow_button)
        main_layout.addLayout(button_layout)

        central_widget.setLayout(main_layout)

    def on_search(self):
        query = self.search_input.text()
        if not query.strip():
            self.results_table.setRowCount(0)
            self.results_label.setText("Results:")
            return
        
        results = BookSearchManager.search(query)
        self.results_table.setRowCount(len(results))
        
        result_count = len(results)
        self.results_label.setText(f"Found {result_count} result{'s' if result_count != 1 else ''}:")
        
        for row, book in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(book['Title']))
            self.results_table.setItem(row, 1, QTableWidgetItem(book['Isbn']))
            self.results_table.setItem(row, 2, QTableWidgetItem(book['Authors'] or 'Unknown'))
            self.results_table.setItem(row, 3, QTableWidgetItem(book['Status']))
        
        self.results_table.resizeColumnsToContents()

    def on_borrow_book(self):
        selected_row = self.results_table.currentRow()
        if selected_row >= 0:
            isbn = self.results_table.item(selected_row, 1).text()
            # TODO: Implement checkout logic with selected ISBN
        else:
            # TODO: Show message to select a book first
            pass


def main():
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
