from mysql.connector import Error
from typing import List, Dict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_connection, close_connection


class BookSearchManager:
    # Manages book search and availability operations for the Book Search and Availability feature
    
    @staticmethod
    def search(query_str: str) -> List[Dict]:
        if not query_str or not query_str.strip():
            return []
        
        conn = get_connection()
        if not conn:
            return []

        # Format for substring match
        q = f"%{query_str}%"
        
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
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (q, q, q))
            results = cursor.fetchall()
            cursor.close()
        except Error as e:
            print(f"[DB ERROR] Error searching books: {e}")
        finally:
            close_connection(conn)
            
        return results

if __name__ == "__main__":
    # No args -> show usage
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python -m app.services.book_search <search_query>")
        print("\nExample:")
        print("  python -m app.services.book_search william")
        sys.exit(0)
    
    query = " ".join(sys.argv[1:])
    results = BookSearchManager.search(query)
    
    if not results:
        print(f"No books found matching: {query!r}")
    else:
        # Print header
        print(f"\n{'ISBN':<15} {'Title':<40} {'Author(s)':<30} {'Availability':<12}")
        print("-" * 97)
        
        # Print results
        for row in results:
            isbn = row['Isbn'] or "N/A"
            title = row['Title'][:39] if row['Title'] else "N/A"
            authors = row['Authors'] or "Unknown"
            status = row['Status']
            
            print(f"{isbn:<15} {title:<40} {authors:<30} {status:<12}")
        
        print(f"\nTotal: {len(results)} book(s) found")