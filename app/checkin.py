from app.db.database import get_connection, close_connection
from datetime import date

def search_active_loans(query: str):
    """
    Returns all currently checked-out loans where the ISBN,
    Card_id, or Borrower Name matches the search substring.
    """
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
        print(f"[CHECKIN SEARCH ERROR] {e}")
        return []
    finally:
        close_connection(conn, cursor)


def checkin_loans(loan_ids):
    """
    Marks the given loan IDs as returned (sets Date_in to today).
    """
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


# CLI Tester (like checkout.py)
if __name__ == "__main__":
    import sys

    # No args -> show usage
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python -m app.checkin search <term>")
        print("  python -m app.checkin in <loan_id1> [loan_id2] ...")
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "search":
        if len(sys.argv) < 3:
            print("Please provide a search term.")
            sys.exit(1)

        term = " ".join(sys.argv[2:])
        print(f"Searching active loans for: {term!r}")
        rows = search_active_loans(term)

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

    elif cmd == "in":
        if len(sys.argv) < 3:
            print("Please provide at least one Loan_id to check in.")
            sys.exit(1)

        try:
            loan_ids = [int(x) for x in sys.argv[2:]]
        except ValueError:
            print("All Loan_id values must be integers.")
            sys.exit(1)

        print(checkin_loans(loan_ids))

    else:
        print("Unknown command:", cmd)
        print("Usage:")
        print("  python -m app.checkin search <term>")
        print("  python -m app.checkin in <loan_id1> [loan_id2] ...")
