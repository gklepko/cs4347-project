from mysql.connector import Error
from database import get_connection, close_connection
from typing import List, Dict


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