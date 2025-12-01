import re
from mysql.connector import Error
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_connection, close_connection

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
    def create_borrower(name, ssn, address, fname, lname, email=None, phone=None):
        #Create a new borrower in the system.

        # Validate required fields
        is_valid, error_msg = BorrowerManager.validate_inputs(name, ssn, address)
        if not is_valid:
            print(f"[BORROWER] Validation failed: {error_msg}")
            return False, error_msg, None
        
        # Remove dashes from SSN for storage
        ssn_clean = ssn.replace('-', '')
        
        conn = get_connection()
        if not conn:
            print("[BORROWER] Failed to get database connection")
            return False, "Failed to connect to database", None
        
        try:
            # Check if SSN already exists
            if BorrowerManager.ssn_exists(conn, ssn_clean):
                print(f"[BORROWER] SSN {ssn} already exists")
                return False, f"A borrower with SSN {ssn} already exists in the system", None
            
            # Generate new card_id
            card_id = BorrowerManager.generate_card_id(conn)
            if not card_id:
                print("[BORROWER] Failed to generate card ID")
                return False, "Failed to generate card ID", None
            
            print(f"[BORROWER] Creating borrower: {name} (SSN: {ssn_clean}, Card ID: {card_id})")
            
            # Insert new borrower
            cursor = conn.cursor()
            query = """
                INSERT INTO BORROWER 
                (Card_id, Ssn, Bname, Fname, Lname, Email, Address, PhoneNumber)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (card_id, ssn_clean, name, fname, lname, email, address, phone))
            conn.commit()
            cursor.close()
            
            print(f"[BORROWER] Successfully created borrower with Card ID: {card_id}")
            return True, f"Borrower created successfully with Card ID: {card_id}", card_id
        
        except Error as e:
            print(f"[BORROWER] Database error: {str(e)}")
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

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python -m app.services.borrower_manager create <name> <ssn> <address> [fname] [lname] [email] [phone]")
        print("  python -m app.services.borrower_manager search <term>")
        print("\nExample:")
        print("  python -m app.services.borrower_manager create \"John Doe\" \"123-45-6789\" \"123 Main St\"")
        print("  python -m app.services.borrower_manager create \"John Doe\" \"123-45-6789\" \"123 Main St\" \"John\" \"Doe\" \"john@example.com\" \"555-1234\"")
        print("  python -m app.services.borrower_manager search \"John\"")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "create":
        if len(sys.argv) < 5:
            print("Usage: python -m app.services.borrower_manager create <name> <ssn> <address> [fname] [lname] [email] [phone]")
            sys.exit(1)
        
        name = sys.argv[2]
        ssn = sys.argv[3]
        address = sys.argv[4]
        fname = sys.argv[5] if len(sys.argv) > 5 else None
        lname = sys.argv[6] if len(sys.argv) > 6 else None
        email = sys.argv[7] if len(sys.argv) > 7 else None
        phone = sys.argv[8] if len(sys.argv) > 8 else None

        nameSplit = name.split(' ')
        fname = nameSplit[0]
        lname = nameSplit[1]
        
        success, message, card_id = BorrowerManager.create_borrower(name, ssn, address, fname, lname, email, phone)
        print(message)
        if success:
            print(f"Card ID: {card_id}")
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Please provide a search term.")
            sys.exit(1)
        
        term = " ".join(sys.argv[2:])
        results = BorrowerManager.search_borrowers(term)
        
        if not results:
            print(f"No borrowers found matching: {term!r}")
        else:
            # Print header
            print(f"\n{'Card ID':<10} {'Name':<25} {'SSN':<12} {'Email':<25} {'Phone':<12} {'Address':<30}")
            print("-" * 114)
            
            # Print results
            for row in results:
                card_id = row['Card_id'] or "N/A"
                name = row['Bname'][:24] if row['Bname'] else "N/A"
                ssn = row['Ssn'] or "N/A"
                email = row['Email'][:24] if row['Email'] else "N/A"
                phone = row['PhoneNumber'][:11] if row['PhoneNumber'] else "N/A"
                address = row['Address'][:29] if row['Address'] else "N/A"
                
                print(f"{card_id:<10} {name:<25} {ssn:<12} {email:<25} {phone:<12} {address:<30}")
            
            print(f"\nTotal: {len(results)} borrower(s) found")
    
    else:
        print("Unknown command:", cmd)
        print("Usage:")
        print("  python -m app.services.borrower_manager create <name> <ssn> <address> [fname] [lname] [email] [phone]")
        print("  python -m app.services.borrower_manager search <term>")