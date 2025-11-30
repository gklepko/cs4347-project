#This code will attempt to checkout a book to a borrower
from app.database import get_connection, close_connection
from datetime import date, timedelta

def checkout_book(isbn: str, card_id: str) -> str:
   

    conn = get_connection()
    if not conn:
        return " Database connection failed."

    cursor = conn.cursor(dictionary=True)

    try:
        
        cursor.execute("SELECT * FROM BORROWER WHERE Card_id = %s", (card_id,))
        borrower = cursor.fetchone()
        if not borrower:
            return f" Borrower {card_id} does not exist."

        
        cursor.execute("""
            SELECT COUNT(*) AS loan_count 
            FROM LOAN 
            WHERE Card_id = %s AND Date_in IS NULL
        """, (card_id,))
        loan_count = cursor.fetchone()["loan_count"]
        if loan_count >= 3:
            return " Borrower already has maximum 3 active loans."

        
        cursor.execute("""
            SELECT * FROM LOAN
            WHERE Isbn = %s AND Date_in IS NULL
        """, (isbn,))
        if cursor.fetchone():
            return " Book is currently checked out."

        
        cursor.execute("""
            SELECT SUM(Fine_amt) AS total
            FROM FINE JOIN LOAN USING(Loan_id)
            WHERE Card_id = %s AND Paid = FALSE
        """, (card_id,))
        unpaid = cursor.fetchone()["total"]
        if unpaid and unpaid > 0:
            return f" Borrower has unpaid fines: ${unpaid:.2f}"

        
        cursor.execute("SELECT IFNULL(MAX(Loan_id),0)+1 AS next_id FROM LOAN")
        next_id = cursor.fetchone()["next_id"]

        today = date.today()
        due = today + timedelta(days=14)

        cursor.execute("""
            INSERT INTO LOAN (Loan_id, Isbn, Card_id, Date_out, Date_due, Date_in)
            VALUES (%s, %s, %s, %s, %s, NULL)
        """, (next_id, isbn, card_id, today, due))

        conn.commit()
        return f" SUCCESS  Book {isbn} checked out to {card_id}. Due {due}"

    except Exception as e:
        conn.rollback()
        return f" Checkout failed: {e}"

    finally:
        close_connection(conn, cursor)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m app.checkout <ISBN> <CARD_ID>")
    else:
        isbn = sys.argv[1]
        card_id = sys.argv[2]
        print(checkout_book(isbn, card_id))