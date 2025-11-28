import re
from mysql.connector import Error
from database import get_connection, close_connection

class BorrowerManager:

    @staticmethod
    # Validate SSN format
    def validate_ssn(ssn):
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        return re.match(pattern, ssn) is not None
    
    @staticmethod
    def validate_inputs(name, ssn, address):
        # Validate required fields are not empty
        if not name or not name.strip():
            return False, "Name is required"
        
        if not ssn or not ssn.strip():
            return False, "SSN is required"
        
        if not address or not address.strip():
            return False, "Address is required"
        
        if not BorrowerManager.validate_ssn(ssn):
            return False, "SSN must be in format XXX-XX-XXXX"
        
        return True, ""
    
    @staticmethod
    def generate_card_id(conn):
        # Generate next card_id in format ID000XXX
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(CAST(SUBSTRING(Card_id, 3) AS UNSIGNED)) FROM BORROWER")
            result = cursor.fetchone()
            cursor.close()
            
            max_id = result[0] if result[0] else 0
            next_id = max_id + 1
            card_id = f"ID{next_id:06d}"
            return card_id
        except Error as e:
            print(f"[DB ERROR] Failed to generate card_id: {e}")
            return None
    
    @staticmethod
    def ssn_exists(conn, ssn):
        # Check if SSN already exists in database
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT Card_id FROM BORROWER WHERE Ssn = %s", (ssn,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None
        except Error as e:
            print(f"[DB ERROR] Failed to check SSN: {e}")
            return False
    
    @staticmethod
    def create_borrower(name, ssn, address, fname=None, lname=None, email=None, phone=None):
        """
        Create a new borrower in the system.
        
        Args:
            name: Full name (required)
            ssn: Social Security Number in format XXX-XX-XXXX (required)
            address: Address (required)
            fname: First name (optional)
            lname: Last name (optional)
            email: Email address (optional)
            phone: Phone number (optional)
        
        Returns:
            tuple: (success: bool, message: str, card_id: str or None)
        """

        # Validate required fields
        is_valid, error_msg = BorrowerManager.validate_inputs(name, ssn, address)
        if not is_valid:
            return False, error_msg, None
        
        conn = get_connection()
        if not conn:
            return False, "Failed to connect to database", None
        
        try:
            # Check if SSN already exists
            if BorrowerManager.ssn_exists(conn, ssn):
                return False, f"A borrower with SSN {ssn} already exists in the system", None
            
            # Generate new card_id
            card_id = BorrowerManager.generate_card_id(conn)
            if not card_id:
                return False, "Failed to generate card ID", None
            
            # Insert new borrower
            cursor = conn.cursor()
            query = """
                INSERT INTO BORROWER 
                (Card_id, Ssn, Bname, Fname, Lname, Email, Address, PhoneNumber)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (card_id, ssn, name, fname, lname, email, phone))
            conn.commit()
            cursor.close()
            
            return True, f"Borrower created successfully with Card ID: {card_id}", card_id
        
        except Error as e:
            conn.rollback()
            return False, f"Database error: {str(e)}", None
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_borrower(card_id):
        # Retrieve borrower information by card ID
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM BORROWER WHERE Card_id = %s", (card_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Error as e:
            print(f"[DB ERROR] Failed to retrieve borrower: {e}")
            return None
        finally:
            close_connection(conn)
    
    @staticmethod
    def search_borrowers(search_term):
        # Search borrowers by name or SSN
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT * FROM BORROWER 
                WHERE Bname LIKE %s OR Ssn LIKE %s OR Card_id LIKE %s
                ORDER BY Bname
            """
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"[DB ERROR] Failed to search borrowers: {e}")
            return []
        finally:
            close_connection(conn)