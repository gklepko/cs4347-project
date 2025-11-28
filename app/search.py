import sys
from database import get_connection, close_connection
from typing import List, Dict

def search_books(query_str: str) -> List[Dict]:
    """
    Searches books by ISBN, Title, or Author.
    Returns list of dicts: {Isbn, Title, Authors, Status}
    """
    conn = get_connection()
    if not conn:
        return []

    # format for substring match
    q = f"%{query_str}%"
    
    # Join Book -> Book_Author -> Author. 
    # Left Join Loan to check if any copy is currently out (Date_in is NULL).
    sql = """
    SELECT 
        b.Isbn, 
        b.Title, 
        GROUP_CONCAT(a.Name SEPARATOR ', ') as Authors,
        CASE 
            WHEN SUM(CASE WHEN l.Date_in IS NULL AND l.Loan_id IS NOT NULL THEN 1 ELSE 0 END) > 0 
            THEN 'OUT' 
            ELSE 'IN' 
        END as Status
    FROM BOOK b
    LEFT JOIN BOOK_AUTHOR ba ON b.Isbn = ba.Isbn
    LEFT JOIN AUTHOR a ON ba.Author_id = a.Author_id
    LEFT JOIN LOAN l ON b.Isbn = l.Isbn
    WHERE b.Isbn LIKE %s OR b.Title LIKE %s OR a.Name LIKE %s
    GROUP BY b.Isbn, b.Title
    """
    
    results = []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (q, q, q))
        results = cursor.fetchall()
    except Exception as e:
        print(f"Error searching books: {e}")
    finally:
        close_connection(conn, cursor)
        
    return results

# Search FUNCTION TEST BLOCK (Runs only when executed directly)
if __name__ == "__main__":
    # Check if a command line argument was provided (e.g. python -m app.search "Harry")
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter search term: ").strip()

    if query:
        print(f"Searching for: '{query}'...")
        results = search_books(query)
        
        if not results:
            print("No results found.")
        else:
            print(f"\nFound {len(results)} result(s):")
            print(f"\n{'ISBN':<15} {'TITLE':<40} {'AUTHORS':<30} {'STATUS'}")
            print("-" * 95)
            for r in results:
                # Handle potential None values safely
                title = r.get('Title', 'Unknown')
                authors = r.get('Authors', 'Unknown')
                status = r.get('Status', 'UNKNOWN')
                isbn = r.get('Isbn', '')

                # Truncate long strings for cleaner display
                title_disp = (title[:37] + '..') if len(title) > 37 else title
                auth_disp = (authors[:27] + '..') if authors and len(authors) > 27 else (authors or "Unknown")
                
                print(f"{isbn:<15} {title_disp:<40} {auth_disp:<30} {status}")

