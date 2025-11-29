import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QStackedWidget, QDialog, QScrollArea, QSplitter,
    QMessageBox
)
from PyQt6.QtCore import Qt

sys.path.insert(0, '..')
from services.book_search import BookSearchManager
from services.borrower_manager import BorrowerManager


class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Create New User")
        self.setGeometry(200, 200, 400, 350)

        layout = QVBoxLayout()

        # First Name
        fname_layout = QHBoxLayout()
        fname_label = QLabel("*First Name:")
        fname_label.setFixedWidth(100)
        self.fname_input = QLineEdit()
        fname_layout.addWidget(fname_label)
        fname_layout.addWidget(self.fname_input)
        layout.addLayout(fname_layout)

        # Last Name
        lname_layout = QHBoxLayout()
        lname_label = QLabel("*Last Name:")
        lname_label.setFixedWidth(100)
        self.lname_input = QLineEdit()
        lname_layout.addWidget(lname_label)
        lname_layout.addWidget(self.lname_input)
        layout.addLayout(lname_layout)

        # SSN
        ssn_layout = QHBoxLayout()
        ssn_label = QLabel("*SSN:")
        ssn_label.setFixedWidth(100)
        self.ssn_input = QLineEdit()
        self.ssn_input.setPlaceholderText("XXX-XX-XXXX")
        ssn_layout.addWidget(ssn_label)
        ssn_layout.addWidget(self.ssn_input)
        layout.addLayout(ssn_layout)

        # Address
        address_layout = QHBoxLayout()
        address_label = QLabel("*Address:")
        address_label.setFixedWidth(100)
        self.address_input = QLineEdit()
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_input)
        layout.addLayout(address_layout)

        # Email (optional)
        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        email_label.setFixedWidth(100)
        self.email_input = QLineEdit()
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        layout.addLayout(email_layout)

        # Phone (optional)
        phone_layout = QHBoxLayout()
        phone_label = QLabel("Phone:")
        phone_label.setFixedWidth(100)
        self.phone_input = QLineEdit()
        phone_layout.addWidget(phone_label)
        phone_layout.addWidget(self.phone_input)
        layout.addLayout(phone_layout)

        layout.addStretch()

        # Button section
        button_layout = QHBoxLayout()
        create_button = QPushButton("Create")
        create_button.clicked.connect(self.on_create)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_create(self):
        fname = self.fname_input.text().strip()
        lname = self.lname_input.text().strip()
        ssn = self.ssn_input.text().strip()
        address = self.address_input.text().strip()
        email = self.email_input.text().strip() or None
        phone = self.phone_input.text().strip() or None

        # Validate required fields
        if not fname or not lname or not ssn or not address:
            QMessageBox.warning(self, "Validation Error", "Please fill in all required fields (First Name, Last Name, SSN, Address)")
            return

        # Create full name
        full_name = f"{fname} {lname}"

        # Create borrower
        success, message, card_id = BorrowerManager.create_borrower(
            full_name, ssn, address, fname, lname, email, phone
        )

        if success:
            QMessageBox.information(self, "Success", f"User created successfully!\nCard ID: {card_id}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to create user:\n{message}")


class UserSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Select User")
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name or card ID...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Name", "Card ID", "Email"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.results_table)

        # Button section
        button_layout = QHBoxLayout()
        create_button = QPushButton("Create New User")
        create_button.clicked.connect(self.on_create_user)
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.on_select)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(create_button)
        button_layout.addStretch()
        button_layout.addWidget(select_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def on_search(self):
        query = self.search_input.text()
        if not query.strip():
            self.results_table.setRowCount(0)
            return

        results = BorrowerManager.search_borrowers(query)
        self.results_table.setRowCount(len(results))

        for row, borrower in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(borrower['Bname']))
            self.results_table.setItem(row, 1, QTableWidgetItem(borrower['Card_id']))
            self.results_table.setItem(row, 2, QTableWidgetItem(borrower['Email'] or ''))


    def on_create_user(self):
        dialog = CreateUserDialog(self)
        if dialog.exec():
            # Refresh the search after creating a new user
            self.on_search()

    def on_select(self):
        selected_row = self.results_table.currentRow()
        if selected_row >= 0:
            # TODO: Implement checkout with selected user
            self.accept()

class LibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Library Management System")
        self.setGeometry(100, 100, 1280, 720)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()

        # Title
        title = QLabel("Library Management System")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)

        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()

        # Books page
        self.books_page = self.create_books_page()
        self.stacked_widget.addWidget(self.books_page)

        # Users page
        self.users_page = self.create_users_page()
        self.stacked_widget.addWidget(self.users_page)

        main_layout.addWidget(self.stacked_widget)
        central_widget.setLayout(main_layout)

        # Show books page by default
        self.stacked_widget.setCurrentIndex(0)

    def create_books_page(self):
        page = QWidget()
        layout = QVBoxLayout()

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
        layout.addLayout(search_layout)

        # Results display with detail panel
        results_label = QLabel("Results:")
        layout.addWidget(results_label)

        # Splitter for table and detail panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)

        # Left side: Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Title", "ISBN", "Authors", "Status"])
        self.results_table.resizeColumnsToContents()
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_table.itemSelectionChanged.connect(self.on_book_selected)
        splitter.addWidget(self.results_table)

        # Right side: Detail panel
        self.detail_panel = self.create_detail_panel()
        splitter.addWidget(self.detail_panel)

        layout.addWidget(splitter, 1)
        page.setLayout(layout)
        return page

    def create_detail_panel(self):
        panel = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Book Details")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.detail_content = QWidget()
        self.detail_layout = QVBoxLayout()
        self.detail_content.setLayout(self.detail_layout)
        scroll.setWidget(self.detail_content)
        layout.addWidget(scroll)

        panel.setLayout(layout)
        return panel

    def on_book_selected(self):
        selected_row = self.results_table.currentRow()
        if selected_row < 0:
            self.clear_detail_panel()
            return

        # Get book data
        title = self.results_table.item(selected_row, 0).text()
        isbn = self.results_table.item(selected_row, 1).text()
        authors = self.results_table.item(selected_row, 2).text()
        status = self.results_table.item(selected_row, 3).text()

        # Clear previous content
        while self.detail_layout.count():
            widget = self.detail_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        # Add book info
        info_label = QLabel(f"<b>{title}</b><br>ISBN: {isbn}<br>Authors: {authors}")
        info_label.setWordWrap(True)
        self.detail_layout.addWidget(info_label)

        self.detail_layout.addSpacing(10)

        # Add status-specific content
        if status == "IN":
            self.show_available_book_details()
        else:
            self.show_checked_out_book_details()

        self.detail_layout.addStretch()

    def show_available_book_details(self):
        status_label = QLabel("<b>Status: Available</b>")
        status_label.setStyleSheet("color: green;")
        self.detail_layout.addWidget(status_label)

        checkout_button = QPushButton("Checkout Book")
        checkout_button.clicked.connect(self.open_user_selection_dialog)
        self.detail_layout.addWidget(checkout_button)

    def show_checked_out_book_details(self):
        status_label = QLabel("<b>Status: Checked Out</b>")
        status_label.setStyleSheet("color: red;")
        self.detail_layout.addWidget(status_label)

        # Dummy checkout information
        checkout_info = QLabel(
            "<b>Checkout Date:</b> 2024-11-15<br>"
            "<b>Due Date:</b> 2024-12-15<br>"
            "<b>Borrower:</b> John Doe<br>"
            "<b>Card ID:</b> 12345"
        )
        checkout_info.setWordWrap(True)
        self.detail_layout.addWidget(checkout_info)

    def clear_detail_panel(self):
        while self.detail_layout.count():
            widget = self.detail_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def open_user_selection_dialog(self):
        dialog = UserSelectionDialog(self)
        dialog.exec()

    def show_books_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_users_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def on_search(self):
        query = self.search_input.text()
        if not query.strip():
            self.results_table.setRowCount(0)
            return

        results = BookSearchManager.search(query)

        result_count = len(results)
        self.results_table.setRowCount(result_count)


        for row, book in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(book['Title']))
            self.results_table.setItem(row, 1, QTableWidgetItem(book['Isbn']))
            self.results_table.setItem(row, 2, QTableWidgetItem(book['Authors'] or 'Unknown'))
            self.results_table.setItem(row, 3, QTableWidgetItem(book['Status']))

        self.results_table.resizeColumnsToContents()

    def create_users_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("User Management")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(label)

        # Placeholder for user management components
        placeholder = QLabel("User management components will go here")
        layout.addWidget(placeholder)
        layout.addStretch()

        page.setLayout(layout)
        return page

def main():
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
