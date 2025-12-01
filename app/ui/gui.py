import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QStackedWidget, QDialog, QScrollArea, QSplitter,
    QMessageBox, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from decimal import Decimal

sys.path.insert(0, '..')
from services.book_search import BookSearchManager
from services.borrower_manager import BorrowerManager
from services.fine import FinesManager
from services.loan_manager import LoanManager

class FinesDialog(QDialog):
    def __init__(self, card_id, borrower_name, parent=None):
        super().__init__(parent)
        self.card_id = card_id
        self.borrower_name = borrower_name
        self.init_ui()
        self.load_fines()
    
    def init_ui(self):
        self.setWindowTitle(f"Fines - {self.borrower_name}")
        self.setGeometry(200, 200, 900, 500)
        
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(f"<h2>Fines for {self.borrower_name}</h2>")
        layout.addWidget(header)
        
        # Card ID
        card_label = QLabel(f"Card ID: {self.card_id}")
        layout.addWidget(card_label)
        
        # Show paid fines checkbox
        self.show_paid_checkbox = QCheckBox("Show paid fines")
        self.show_paid_checkbox.stateChanged.connect(self.load_fines)
        layout.addWidget(self.show_paid_checkbox)
        
        # Fines table
        self.fines_table = QTableWidget()
        self.fines_table.setColumnCount(7)
        self.fines_table.setHorizontalHeaderLabels([
            "Loan ID", "Book Title", "ISBN", "Due Date", "Return Date", "Fine Amount", "Status"
        ])
        self.fines_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fines_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.fines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.fines_table)
        
        # Summary section
        summary_group = QGroupBox("Summary")
        summary_layout = QVBoxLayout()
        
        self.total_label = QLabel("Total Fines: $0.00")
        self.unpaid_label = QLabel("Unpaid Fines: $0.00")
        
        self.total_label.setStyleSheet("font-size: 14px;")
        self.unpaid_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
        
        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.unpaid_label)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.pay_button = QPushButton("Pay All Fines")
        self.pay_button.clicked.connect(self.pay_fines)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.pay_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_fines(self):
        # Load and display fines for the borrower
        include_paid = self.show_paid_checkbox.isChecked()
        fines_info = FinesManager.get_borrower_fines(self.card_id, include_paid)
        
        if not fines_info:
            QMessageBox.warning(self, "Error", "Failed to load fines")
            return
        
        # Update summary
        self.total_label.setText(f"Total Fines: ${fines_info['total_fines']:.2f}")
        self.unpaid_label.setText(f"Unpaid Fines: ${fines_info['unpaid_fines']:.2f}")
        
        # Enable/disable pay button
        self.pay_button.setEnabled(fines_info['unpaid_fines'] > 0)
        
        # Update table
        fines = fines_info['fines']
        self.fines_table.setRowCount(len(fines))
        
        for row, fine in enumerate(fines):
            self.fines_table.setItem(row, 0, QTableWidgetItem(str(fine['Loan_id'])))
            self.fines_table.setItem(row, 1, QTableWidgetItem(fine['Title']))
            self.fines_table.setItem(row, 2, QTableWidgetItem(fine['Isbn']))
            self.fines_table.setItem(row, 3, QTableWidgetItem(str(fine['Date_due'])))
            
            return_date = str(fine['Date_in']) if fine['Date_in'] else "Not returned"
            self.fines_table.setItem(row, 4, QTableWidgetItem(return_date))
            
            fine_amt = Decimal(str(fine['Fine_amt']))
            self.fines_table.setItem(row, 5, QTableWidgetItem(f"${fine_amt:.2f}"))
            
            status = "PAID" if fine['Paid'] else "UNPAID"
            status_item = QTableWidgetItem(status)
            if fine['Paid']:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.fines_table.setItem(row, 6, status_item)
        
        self.fines_table.resizeColumnsToContents()
    
    def pay_fines(self):
        # Process payment for all unpaid fines.
        unpaid_text = self.unpaid_label.text().split('$')[1]
        
        # Confirm payment
        reply = QMessageBox.question(
            self,
            "Confirm Payment",
            f"Pay all unpaid fines for {self.borrower_name}?\n\nAmount: ${unpaid_text}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Process payment
        success, message, amount = FinesManager.pay_fines(self.card_id)
        
        if success:
            QMessageBox.information(
                self,
                "Payment Successful",
                f"{message}\n\nReceipt:\nBorrower: {self.borrower_name}\nCard ID: {self.card_id}\nAmount Paid: ${amount:.2f}"
            )
            self.load_fines()  # Refresh the display
        else:
            QMessageBox.critical(self, "Payment Failed", message)

class AllFinesDialog(QDialog):
    # Dialog for viewing all unpaid fines in the system
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_all_fines()
    
    def init_ui(self):
        self.setWindowTitle("All Unpaid Fines")
        self.setGeometry(200, 200, 800, 600)
        
        layout = QVBoxLayout()
        
        # Header
        self.header_label = QLabel("<h2>All Borrowers with Unpaid Fines</h2>")
        layout.addWidget(self.header_label)
        
        # Table
        self.fines_table = QTableWidget()
        self.fines_table.setColumnCount(5)
        self.fines_table.setHorizontalHeaderLabels([
            "Card ID", "Name", "Email", "Phone", "Total Unpaid"
        ])
        self.fines_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fines_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.fines_table.doubleClicked.connect(self.view_borrower_fines)
        layout.addWidget(self.fines_table)
        
        # Info label
        info = QLabel("Double-click a borrower to view their detailed fines")
        info.setStyleSheet("font-style: italic; color: gray;")
        layout.addWidget(info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        view_button = QPushButton("View Selected Borrower's Fines")
        view_button.clicked.connect(self.view_selected_borrower_fines)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(view_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_all_fines(self):
        # Load and display all unpaid fines.
        unpaid_fines = FinesManager.get_all_unpaid_fines()
        
        self.fines_table.setRowCount(len(unpaid_fines))
        
        total_system_fines = Decimal('0.00')
        
        for row, borrower in enumerate(unpaid_fines):
            self.fines_table.setItem(row, 0, QTableWidgetItem(borrower['Card_id']))
            self.fines_table.setItem(row, 1, QTableWidgetItem(borrower['Bname']))
            self.fines_table.setItem(row, 2, QTableWidgetItem(borrower['Email'] or ''))
            self.fines_table.setItem(row, 3, QTableWidgetItem(borrower['PhoneNumber'] or ''))
            
            total_unpaid = Decimal(str(borrower['Total_unpaid']))
            self.fines_table.setItem(row, 4, QTableWidgetItem(f"${total_unpaid:.2f}"))
            
            total_system_fines += total_unpaid
        
        self.fines_table.resizeColumnsToContents()
        
        # Update header with total
        self.header_label.setText(
            f"<h2>All Borrowers with Unpaid Fines</h2>"
            f"<p>Total borrowers: {len(unpaid_fines)} | Total unpaid fines: ${total_system_fines:.2f}</p>"
        )
    
    def view_selected_borrower_fines(self):
        # View fines for the selected borrower.
        selected_row = self.fines_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a borrower first")
            return
        
        self.view_borrower_fines()
    
    def view_borrower_fines(self):
        # View fines for a borrower (triggered by double-click or button).
        selected_row = self.fines_table.currentRow()
        if selected_row < 0:
            return
        
        card_id = self.fines_table.item(selected_row, 0).text()
        borrower_name = self.fines_table.item(selected_row, 1).text()
        
        dialog = FinesDialog(card_id, borrower_name, self)
        dialog.exec()
        
        # Refresh the list after closing the detail view
        self.load_all_fines()

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
    def __init__(self, isbn=None, parent=None):
        super().__init__(parent)
        self.isbn = isbn
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Select User")
        self.setGeometry(200, 200, 600, 400)

        layout = QVBoxLayout()

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter name or card ID...")
        self.search_input.returnPressed.connect(self.on_search)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Name", "Card ID", "Email", "Has Fine(s)"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.results_table)

        # Button section
        button_layout = QHBoxLayout()
        
        view_fines_button = QPushButton("View Fines")
        view_fines_button.clicked.connect(self.on_view_fines)
        
        select_button = QPushButton("Select")
        select_button.clicked.connect(self.on_select)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(view_fines_button)
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
            
            # Check for unpaid fines
            has_fines = FinesManager.has_unpaid_fines(borrower['Card_id'])
            fines_item = QTableWidgetItem("Yes" if has_fines else "No")
            if has_fines:
                fines_item.setForeground(Qt.GlobalColor.red)
            self.results_table.setItem(row, 3, fines_item)

        self.results_table.resizeColumnsToContents()

    def on_view_fines(self):
        selected_row = self.results_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a borrower first")
            return
        
        card_id = self.results_table.item(selected_row, 1).text()
        borrower_name = self.results_table.item(selected_row, 0).text()
        
        dialog = FinesDialog(card_id, borrower_name, self)
        dialog.exec()
        self.on_search()

    def on_select(self):
        selected_row = self.results_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a borrower first")
            return
        
        if not self.isbn:
            QMessageBox.warning(self, "Error", "No book selected for checkout")
            return
        
        card_id = self.results_table.item(selected_row, 1).text()
        borrower_name = self.results_table.item(selected_row, 0).text()
        
        result = LoanManager.checkout_book(self.isbn, card_id)
        
        if "SUCCESS" in result:
            QMessageBox.information(self, "Checkout Successful", f"{result}\n\nBorrower: {borrower_name}")
            self.accept()
        else:
            QMessageBox.warning(self, "Checkout Failed", result)

class LibraryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Library Management System")
        self.setGeometry(100, 100, 1280, 720)

        # Create menu bar
        self.create_menu_bar()

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

    def create_menu_bar(self):
        # Create the application menu bar.
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")
        
        books_action = QAction("Books", self)
        books_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        view_menu.addAction(books_action)
        
        users_action = QAction("Users", self)
        users_action.triggered.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        view_menu.addAction(users_action)

        # Fines menu
        fines_menu = menubar.addMenu("Fines")
        
        view_all_fines_action = QAction("View All Unpaid Fines", self)
        view_all_fines_action.triggered.connect(self.open_all_fines_dialog)
        fines_menu.addAction(view_all_fines_action)
        
        update_fines_action = QAction("Update Fines", self)
        update_fines_action.triggered.connect(self.update_fines)
        fines_menu.addAction(update_fines_action)

    def create_books_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter book title, author, or ISBN...")
        self.search_input.returnPressed.connect(self.on_search)
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
        status_label.setStyleSheet("color: green; font-size: 12px;")
        self.detail_layout.addWidget(status_label)

        checkout_button = QPushButton("Checkout Book")
        checkout_button.clicked.connect(self.open_user_selection_dialog)
        self.detail_layout.addWidget(checkout_button)

    def show_checked_out_book_details(self):
        status_label = QLabel("<b>Status: Checked Out</b>")
        status_label.setStyleSheet("color: red; font-size: 12px;")
        self.detail_layout.addWidget(status_label)

        selected_row = self.results_table.currentRow()
        if selected_row >= 0:
            isbn = self.results_table.item(selected_row, 1).text()
            loan_info = LoanManager.get_loan_by_isbn(isbn)
            
            if loan_info:
                checkout_info = QLabel(
                    f"<b>Loan ID:</b> {loan_info['Loan_id']}<br>"
                    f"<b>Checkout Date:</b> {loan_info['Date_out']}<br>"
                    f"<b>Due Date:</b> {loan_info['Date_due']}<br>"
                    f"<b>Borrower:</b> {loan_info['Bname']}<br>"
                    f"<b>Card ID:</b> {loan_info['Card_id']}"
                )
                checkout_info.setWordWrap(True)
                self.detail_layout.addWidget(checkout_info)
                
                checkin_button = QPushButton("Check In Book")
                checkin_button.clicked.connect(lambda: self.on_checkin_book(loan_info['Loan_id']))
                self.detail_layout.addWidget(checkin_button)

    def clear_detail_panel(self):
        while self.detail_layout.count():
            widget = self.detail_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

    def on_checkin_book(self, loan_id):
        reply = QMessageBox.question(
            self, "Confirm Check In",
            f"Check in this book?\n\nLoan ID: {loan_id}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        result = LoanManager.checkin_loans([loan_id])
        
        if "SUCCESS" in result:
            QMessageBox.information(self, "Check In Successful", result)
            self.on_search()
            self.on_book_selected()
        else:
            QMessageBox.warning(self, "Check In Failed", result)

    def open_user_selection_dialog(self):
        selected_row = self.results_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a book first")
            return
        
        isbn = self.results_table.item(selected_row, 1).text()
        dialog = UserSelectionDialog(isbn=isbn, parent=self)
        if dialog.exec():
            self.on_search()
            self.on_book_selected()

    def on_search(self):
        query = self.search_input.text()
        if not query.strip():
            self.results_table.setRowCount(0)
            return

        results = BookSearchManager.search(query)
        self.results_table.setRowCount(len(results))

        for row, book in enumerate(results):
            self.results_table.setItem(row, 0, QTableWidgetItem(book['Title']))
            self.results_table.setItem(row, 1, QTableWidgetItem(book['Isbn']))
            self.results_table.setItem(row, 2, QTableWidgetItem(book['Authors'] or 'Unknown'))
            self.results_table.setItem(row, 3, QTableWidgetItem(book['Status']))

        self.results_table.resizeColumnsToContents()

    def create_users_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        label = QLabel("User Management")
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(label)
        header_layout.addStretch()
        
        create_user_btn = QPushButton("Create New User")
        create_user_btn.clicked.connect(self.on_create_user_from_page)
        header_layout.addWidget(create_user_btn)
        layout.addLayout(header_layout)

        # Search section
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText("Enter name or card ID...")
        self.user_search_input.returnPressed.connect(self.on_user_search)
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.on_user_search)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.user_search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # Results table
        self.user_results_table = QTableWidget()
        self.user_results_table.setColumnCount(5)
        self.user_results_table.setHorizontalHeaderLabels(["Name", "Card ID", "Email", "Phone", "Has Fines"])
        self.user_results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.user_results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(self.user_results_table)

        # Action buttons
        button_layout = QHBoxLayout()
        view_fines_btn = QPushButton("View Fines")
        view_fines_btn.clicked.connect(self.on_view_user_fines)
        button_layout.addWidget(view_fines_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        page.setLayout(layout)
        return page

    def on_user_search(self):
        query = self.user_search_input.text()
        if not query.strip():
            self.user_results_table.setRowCount(0)
            return

        results = BorrowerManager.search_borrowers(query)
        self.user_results_table.setRowCount(len(results))

        for row, borrower in enumerate(results):
            self.user_results_table.setItem(row, 0, QTableWidgetItem(borrower['Bname']))
            self.user_results_table.setItem(row, 1, QTableWidgetItem(borrower['Card_id']))
            self.user_results_table.setItem(row, 2, QTableWidgetItem(borrower['Email'] or ''))
            self.user_results_table.setItem(row, 3, QTableWidgetItem(borrower['PhoneNumber'] or ''))
            
            has_fines = FinesManager.has_unpaid_fines(borrower['Card_id'])
            fines_item = QTableWidgetItem("Yes" if has_fines else "No")
            if has_fines:
                fines_item.setForeground(Qt.GlobalColor.red)
            else:
                fines_item.setForeground(Qt.GlobalColor.green)
            self.user_results_table.setItem(row, 4, fines_item)

        self.user_results_table.resizeColumnsToContents()

    def on_create_user_from_page(self):
        dialog = CreateUserDialog(self)
        if dialog.exec():
            self.on_user_search()

    def on_view_user_fines(self):
        selected_row = self.user_results_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a user first")
            return
        
        card_id = self.user_results_table.item(selected_row, 1).text()
        borrower_name = self.user_results_table.item(selected_row, 0).text()
        
        dialog = FinesDialog(card_id, borrower_name, self)
        dialog.exec()
        self.on_user_search()

    def open_all_fines_dialog(self):
        dialog = AllFinesDialog(self)
        dialog.exec()

    def update_fines(self):
        reply = QMessageBox.question(
            self, "Update Fines",
            "This will calculate and update all fines in the system.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        QMessageBox.information(self, "Processing", "Updating fines... Click OK to continue.")
        
        success, message, stats = FinesManager.update_fines()
        
        if success:
            QMessageBox.information(
                self, "Update Complete",
                f"{message}\n\n"
                f"Total loans processed: {stats['total_processed']}\n"
                f"New fines: {stats['new_fines']}\n"
                f"Updated fines: {stats['updated_fines']}\n"
                f"Paid (skipped): {stats['skipped_paid']}"
            )
        else:
            QMessageBox.critical(self, "Update Failed", f"Failed to update fines:\n{message}")

def main():
    app = QApplication(sys.argv)
    window = LibraryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()