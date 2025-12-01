from app.db.database import get_connection, close_connection
from datetime import date, timedelta


class LoanManager:
    # Manages all loan operations including checkout and check-in.
    # Enforces business rules: max 3 active loans, no unpaid fines, book availability.
    
    MAX_ACTIVE_LOANS = 3
    LOAN_DURATION_DAYS = 14
    
    @staticmethod
    def checkout_book(isbn: str, card_id: str) -> str:
        # Attempts to checkout a book to a borrower
        conn = get_connection()
        if not conn:
            return "Database connection failed."
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # 1) Verify borrower exists
            cursor.execute("SELECT * FROM BORROWER WHERE Card_id = %s", (card_id,))
            borrower = cursor.fetchone()
            if not borrower:
                return f"Borrower {card_id} does not exist."
            
            # 2) Check active loans < MAX_ACTIVE_LOANS
            cursor.execute("""
                SELECT COUNT(*) AS loan_count 
                FROM LOAN 
                WHERE Card_id = %s AND Date_in IS NULL
            """, (card_id,))
            loan_count = cursor.fetchone()["loan_count"]
            if loan_count >= LoanManager.MAX_ACTIVE_LOANS:
                return f"Borrower already has maximum {LoanManager.MAX_ACTIVE_LOANS} active loans."
            
            # 3) Check if book already checked out
            cursor.execute("""
                SELECT * FROM LOAN
                WHERE Isbn = %s AND Date_in IS NULL
            """, (isbn,))
            if cursor.fetchone():
                return "Book is currently checked out."
            
            # 4) Check unpaid fines
            cursor.execute("""
                SELECT SUM(Fine_amt) AS total
                FROM FINE JOIN LOAN USING(Loan_id)
                WHERE Card_id = %s AND Paid = FALSE
            """, (card_id,))
            unpaid = cursor.fetchone()["total"]
            if unpaid and unpaid > 0:
                return f"Borrower has unpaid fines: ${unpaid:.2f}"
            
            # 5) Create loan record
            cursor.execute("SELECT IFNULL(MAX(Loan_id),0)+1 AS next_id FROM LOAN")
            next_id = cursor.fetchone()["next_id"]
            
            today = date.today()
            due = today + timedelta(days=LoanManager.LOAN_DURATION_DAYS)
            
            cursor.execute("""
                INSERT INTO LOAN (Loan_id, Isbn, Card_id, Date_out, Date_due, Date_in)
                VALUES (%s, %s, %s, %s, %s, NULL)
            """, (next_id, isbn, card_id, today, due))
            
            conn.commit()
            return f"SUCCESS — Book {isbn} checked out to {card_id}. Due {due}"
        
        except Exception as e:
            conn.rollback()
            return f"Checkout failed: {e}"
        
        finally:
            close_connection(conn, cursor)
    
    @staticmethod
    def search_active_loans(query: str):
       # Returns all currently checked-out loans where the ISBN, Card_id, or Borrower Name matches the search substring
        conn = get_connection()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        q = f"%{query}%"
        
        sql = """
            SELECT 
                l.Loan_id,
                l.Isbn,
                b.Title,
                br.Card_id,
                br.Bname,
                l.Date_out,
                l.Date_due
            FROM LOAN l
            JOIN BOOK b      ON l.Isbn = b.Isbn
            JOIN BORROWER br ON l.Card_id = br.Card_id
            WHERE l.Date_in IS NULL
              AND (b.Isbn LIKE %s
                OR br.Card_id LIKE %s
                OR br.Bname LIKE %s)
            ORDER BY l.Date_out
        """
        
        try:
            cursor.execute(sql, (q, q, q))
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print(f"[LOAN SEARCH ERROR] {e}")
            return []
        finally:
            close_connection(conn, cursor)
    
    @staticmethod
    def checkin_loans(loan_ids):
        # Marks the given loan IDs as returned (sets Date_in to today)
        if not loan_ids:
            return "No loans selected."
        
        conn = get_connection()
        if not conn:
            return "Database connection failed."
        
        cursor = conn.cursor()
        
        try:
            today = date.today()
            placeholders = ", ".join(["%s"] * len(loan_ids))
            
            sql = f"""
                UPDATE LOAN
                SET Date_in = %s
                WHERE Loan_id IN ({placeholders})
                  AND Date_in IS NULL
            """
            
            params = [today] + loan_ids
            cursor.execute(sql, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return "Nothing was checked in (maybe already checked in?)."
            
            return f"SUCCESS — {cursor.rowcount} loan(s) checked in."
        
        except Exception as e:
            conn.rollback()
            return f"Check-in failed: {e}"
        finally:
            close_connection(conn, cursor)
    
    @staticmethod
    def verify_borrower_exists(card_id: str) -> bool:
        # Check if a borrower exists in the system
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM BORROWER WHERE Card_id = %s", (card_id,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
        except Exception:
            return False
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_active_loan_count(card_id: str) -> int:
        # Get the number of active loans for a borrower
        conn = get_connection()
        if not conn:
            return -1
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) AS count
                FROM LOAN
                WHERE Card_id = %s AND Date_in IS NULL
            """, (card_id,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else 0
        except Exception:
            return -1
        finally:
            close_connection(conn)
    
    @staticmethod
    def is_book_available(isbn: str) -> bool:
        # Check if a book is available (not currently checked out)
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM LOAN
                WHERE Isbn = %s AND Date_in IS NULL
            """, (isbn,))
            available = cursor.fetchone() is None
            cursor.close()
            return available
        except Exception:
            return False
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_unpaid_fines_total(card_id: str) -> float:
        # Get the total amount of unpaid fines for a borrower
        conn = get_connection()
        if not conn:
            return -1.0
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT SUM(Fine_amt) AS total
                FROM FINE JOIN LOAN USING(Loan_id)
                WHERE Card_id = %s AND Paid = FALSE
            """, (card_id,))
            result = cursor.fetchone()
            cursor.close()
            total = result["total"] if result and result["total"] else 0.0
            return float(total)
        except Exception:
            return -1.0
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_loan_details(loan_id: int):
        # Retrieves detailed information about a specific loan.
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    l.Loan_id,
                    l.Isbn,
                    b.Title,
                    br.Card_id,
                    br.Bname,
                    l.Date_out,
                    l.Date_due,
                    l.Date_in
                FROM LOAN l
                JOIN BOOK b      ON l.Isbn = b.Isbn
                JOIN BORROWER br ON l.Card_id = br.Card_id
                WHERE l.Loan_id = %s
            """
            cursor.execute(sql, (loan_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"[LOAN ERROR] Failed to get loan details: {e}")
            return None
        finally:
            close_connection(conn)
    
    @staticmethod
    def is_loan_checked_in(loan_id: int) -> bool:
        # Check if a loan has already been checked in.
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT Date_in FROM LOAN WHERE Loan_id = %s
            """, (loan_id,))
            result = cursor.fetchone()
            cursor.close()
            return result and result[0] is not None
        except Exception:
            return False
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_active_loans_for_borrower(card_id: str):
        # Get all active (not yet returned) loans for a specific borrower.
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    l.Loan_id,
                    l.Isbn,
                    b.Title,
                    l.Date_out,
                    l.Date_due
                FROM LOAN l
                JOIN BOOK b ON l.Isbn = b.Isbn
                WHERE l.Card_id = %s AND l.Date_in IS NULL
                ORDER BY l.Date_due
            """
            cursor.execute(sql, (card_id,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            print(f"[LOAN ERROR] Failed to get active loans: {e}")
            return []
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_loan_by_isbn(isbn: str):
        # Get active loan information for a specific book by ISBN.
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            sql = """
                SELECT 
                    l.Loan_id,
                    l.Isbn,
                    b.Title,
                    l.Card_id,
                    br.Bname,
                    l.Date_out,
                    l.Date_due,
                    l.Date_in
                FROM LOAN l
                JOIN BOOK b ON l.Isbn = b.Isbn
                JOIN BORROWER br ON l.Card_id = br.Card_id
                WHERE l.Isbn = %s AND l.Date_in IS NULL
                LIMIT 1
            """
            cursor.execute(sql, (isbn,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"[LOAN ERROR] Failed to get loan by ISBN: {e}")
            return None
        finally:
            close_connection(conn)

if __name__ == "__main__":
    import sys
    
    # No args -> show usage
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python -m app.services.loan_manager checkout <ISBN> <CARD_ID>")
        print("  python -m app.services.loan_manager search <term>")
        print("  python -m app.services.loan_manager checkin <loan_id1> [loan_id2] ...")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "checkout":
        if len(sys.argv) < 4:
            print("Usage: python -m app.services.loan_manager checkout <ISBN> <CARD_ID>")
            sys.exit(1)
        
        isbn = sys.argv[2]
        card_id = sys.argv[3]
        print(LoanManager.checkout_book(isbn, card_id))
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Please provide a search term.")
            sys.exit(1)
        
        term = " ".join(sys.argv[2:])
        print(f"Searching active loans for: {term!r}")
        rows = LoanManager.search_active_loans(term)
        
        if not rows:
            print("No active loans found.")
        else:
            for r in rows:
                print(
                    f"Loan_id={r['Loan_id']}, Isbn={r['Isbn']}, "
                    f"Title={r['Title']}, Card_id={r['Card_id']}, "
                    f"Borrower={r['Bname']}, Out={r['Date_out']}, "
                    f"Due={r['Date_due']}"
                )
    
    elif cmd == "checkin":
        if len(sys.argv) < 3:
            print("Please provide at least one Loan_id to check in.")
            sys.exit(1)
        
        try:
            loan_ids = [int(x) for x in sys.argv[2:]]
        except ValueError:
            print("All Loan_id values must be integers.")
            sys.exit(1)
        
        print(LoanManager.checkin_loans(loan_ids))
    
    else:
        print("Unknown command:", cmd)
        print("Usage:")
        print("  python -m app.services.loan_manager checkout <ISBN> <CARD_ID>")
        print("  python -m app.services.loan_manager search <term>")
        print("  python -m app.services.loan_manager checkin <loan_id1> [loan_id2] ...")
