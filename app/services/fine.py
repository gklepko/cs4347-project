from mysql.connector import Error
from datetime import date, datetime
from decimal import Decimal
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import get_connection, close_connection


class FinesManager:
    """
    Automated library fines management system.
    Fines are assessed at $0.25/day for late books.
    Automatically calculates fines for any book overdue.
    """
    
    FINE_RATE_PER_DAY = Decimal('0.25')
    
    @staticmethod
    def calculate_days_late(due_date, return_date=None):
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
        
        if return_date is None:
            comparison_date = date.today()
        elif isinstance(return_date, str):
            comparison_date = datetime.strptime(return_date, '%Y-%m-%d').date()
        else:
            comparison_date = return_date
        
        days_late = (comparison_date - due_date).days
        return max(0, days_late)
    
    @staticmethod
    def calculate_fine_amount(days_late):
        return Decimal(days_late) * FinesManager.FINE_RATE_PER_DAY
    
    @staticmethod
    def update_fines():
        conn = get_connection()
        if not conn:
            return False, "Failed to connect to database", {}
        
        stats = {
            'new_fines': 0,
            'updated_fines': 0,
            'skipped_paid': 0,
            'total_processed': 0
        }
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Find all late loans
            # Case 1: Books returned late (Date_in > Date_due)
            # Case 2: Books still out and overdue (Date_in IS NULL AND Date_due < TODAY)
            query = """
                SELECT 
                    Loan_id,
                    Date_due,
                    Date_in
                FROM LOAN
                WHERE 
                    (Date_in IS NOT NULL AND Date_in > Date_due)
                    OR (Date_in IS NULL AND Date_due < CURDATE())
            """
            
            cursor.execute(query)
            late_loans = cursor.fetchall()
            stats['total_processed'] = len(late_loans)
            
            for loan in late_loans:
                loan_id = loan['Loan_id']
                due_date = loan['Date_due']
                date_in = loan['Date_in']
                
                # Calculate days late and fine amount
                days_late = FinesManager.calculate_days_late(due_date, date_in)
                fine_amount = FinesManager.calculate_fine_amount(days_late)
                
                # Check if fine already exists
                cursor.execute("SELECT Loan_id, Paid, Fine_amt FROM FINE WHERE Loan_id = %s", (loan_id,))
                existing_fine = cursor.fetchone()
                
                if existing_fine:
                    # Fine exists
                    if existing_fine['Paid']:
                        # Already paid, skip
                        stats['skipped_paid'] += 1
                    else:
                        # Not paid, update if amount changed
                        current_amount = Decimal(str(existing_fine['Fine_amt']))
                        if current_amount != fine_amount:
                            cursor.execute(
                                "UPDATE FINE SET Fine_amt = %s WHERE Loan_id = %s",
                                (fine_amount, loan_id)
                            )
                            stats['updated_fines'] += 1
                else:
                    # No fine exists, create new one
                    cursor.execute(
                        "INSERT INTO FINE (Loan_id, Fine_amt, Paid) VALUES (%s, %s, FALSE)",
                        (loan_id, fine_amount)
                    )
                    stats['new_fines'] += 1
            
            conn.commit()
            cursor.close()
            
            message = f"Fines updated: {stats['new_fines']} new, {stats['updated_fines']} updated, {stats['skipped_paid']} paid (skipped)"
            return True, message, stats
            
        except Error as e:
            conn.rollback()
            return False, f"Database error: {str(e)}", stats
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_borrower_fines(card_id, include_paid=False):
        conn = get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Build query based on whether to include paid fines
            paid_filter = "" if include_paid else "AND f.Paid = FALSE"
            
            query = f"""
                SELECT 
                    f.Loan_id,
                    f.Fine_amt,
                    f.Paid,
                    l.Isbn,
                    l.Date_out,
                    l.Date_due,
                    l.Date_in,
                    b.Title
                FROM FINE f
                JOIN LOAN l ON f.Loan_id = l.Loan_id
                JOIN BOOK b ON l.Isbn = b.Isbn
                WHERE l.Card_id = %s {paid_filter}
                ORDER BY l.Date_due DESC
            """
            
            cursor.execute(query, (card_id,))
            fines = cursor.fetchall()
            
            # Calculate totals
            total_fines = Decimal('0.00')
            unpaid_fines = Decimal('0.00')
            
            for fine in fines:
                fine_amt = Decimal(str(fine['Fine_amt']))
                total_fines += fine_amt
                if not fine['Paid']:
                    unpaid_fines += fine_amt
            
            cursor.close()
            
            return {
                'total_fines': total_fines,
                'unpaid_fines': unpaid_fines,
                'fines': fines
            }
            
        except Error as e:
            print(f"[FINES ERROR] Failed to get borrower fines: {e}")
            return None
        finally:
            close_connection(conn)
    
    @staticmethod
    def get_all_unpaid_fines():
        conn = get_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT 
                    br.Card_id,
                    br.Bname,
                    br.Email,
                    br.PhoneNumber,
                    SUM(f.Fine_amt) as Total_unpaid,
                    COUNT(f.Loan_id) as Num_fines
                FROM BORROWER br
                JOIN LOAN l ON br.Card_id = l.Card_id
                JOIN FINE f ON l.Loan_id = f.Loan_id
                WHERE f.Paid = FALSE
                GROUP BY br.Card_id, br.Bname, br.Email, br.PhoneNumber
                ORDER BY Total_unpaid DESC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Error as e:
            print(f"[FINES ERROR] Failed to get unpaid fines: {e}")
            return []
        finally:
            close_connection(conn)
    
    @staticmethod
    def pay_fines(card_id):
        conn = get_connection()
        if not conn:
            return False, "Failed to connect to database", None
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check for unreturned books with fines
            check_query = """
                SELECT f.Loan_id
                FROM FINE f
                JOIN LOAN l ON f.Loan_id = l.Loan_id
                WHERE l.Card_id = %s 
                    AND f.Paid = FALSE 
                    AND l.Date_in IS NULL
            """
            
            cursor.execute(check_query, (card_id,))
            unreturned = cursor.fetchall()
            
            if unreturned:
                return False, "Cannot pay fines: borrower has unreturned books with outstanding fines", None
            
            # Get total unpaid fines
            total_query = """
                SELECT SUM(f.Fine_amt) as Total_unpaid
                FROM FINE f
                JOIN LOAN l ON f.Loan_id = l.Loan_id
                WHERE l.Card_id = %s AND f.Paid = FALSE
            """
            
            cursor.execute(total_query, (card_id,))
            result = cursor.fetchone()
            
            if not result or result['Total_unpaid'] is None:
                return False, "No unpaid fines found for this borrower", Decimal('0.00')
            
            total_unpaid = Decimal(str(result['Total_unpaid']))
            
            # Mark all unpaid fines as paid
            update_query = """
                UPDATE FINE f
                JOIN LOAN l ON f.Loan_id = l.Loan_id
                SET f.Paid = TRUE
                WHERE l.Card_id = %s AND f.Paid = FALSE
            """
            
            cursor.execute(update_query, (card_id,))
            rows_updated = cursor.rowcount
            
            conn.commit()
            cursor.close()
            
            return True, f"Payment successful: ${total_unpaid} paid", total_unpaid
            
        except Error as e:
            conn.rollback()
            return False, f"Database error: {str(e)}", None
        finally:
            close_connection(conn)
    
    @staticmethod
    def has_unpaid_fines(card_id):
        conn = get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) as count
                FROM FINE f
                JOIN LOAN l ON f.Loan_id = l.Loan_id
                WHERE l.Card_id = %s AND f.Paid = FALSE
            """
            
            cursor.execute(query, (card_id,))
            result = cursor.fetchone()
            cursor.close()
            
            return result[0] > 0 if result else False
            
        except Error as e:
            print(f"[FINES ERROR] Failed to check unpaid fines: {e}")
            return False
        finally:
            close_connection(conn)


# Command-line interface for running fines operations
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Library Fines Management System')
    parser.add_argument('action', choices=['update', 'view-unpaid'],
                       help='Action to perform: update (calculate fines) or view-unpaid (show report)')
    
    args = parser.parse_args()
    
    if args.action == 'update':
        print("=" * 70)
        print(f"FINES UPDATE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        
        success, message, stats = FinesManager.update_fines()
        
        print()
        print("-" * 70)
        print("SUMMARY")
        print("-" * 70)
        
        if success:
            print(f"✓ Update completed successfully")
            print()
            print(f"Total loans processed: {stats['total_processed']}")
            print(f"New fines created:     {stats['new_fines']}")
            print(f"Existing fines updated: {stats['updated_fines']}")
            print(f"Paid fines (skipped):  {stats['skipped_paid']}")
        else:
            print(f"✗ Update failed: {message}")
        
        print()
        
        # Show current unpaid fines summary
        unpaid = FinesManager.get_all_unpaid_fines()
        
        if unpaid:
            total_unpaid_system = sum(Decimal(str(b['Total_unpaid'])) for b in unpaid)
            print(f"Borrowers with unpaid fines: {len(unpaid)}")
            print(f"Total unpaid fines in system: ${total_unpaid_system:.2f}")
        else:
            print("No unpaid fines in the system")
        
        print("=" * 70)
    
    elif args.action == 'view-unpaid':
        print("=" * 70)
        print("ALL UNPAID FINES")
        print("=" * 70)
        print()
        
        unpaid = FinesManager.get_all_unpaid_fines()
        
        if unpaid:
            print(f"Borrowers with unpaid fines: {len(unpaid)}")
            print()
            
            total_unpaid_system = sum(Decimal(str(b['Total_unpaid'])) for b in unpaid)
            print(f"Total unpaid fines in system: ${total_unpaid_system:.2f}")
            print()
            
            if len(unpaid) <= 20:
                print("All borrowers with unpaid fines:")
                for borrower in unpaid:
                    print(f"  • {borrower['Bname']:<30} ({borrower['Card_id']}): ${Decimal(str(borrower['Total_unpaid'])):>7.2f}")
            else:
                print("Top 20 borrowers by unpaid fines:")
                for borrower in unpaid[:20]:
                    print(f"  • {borrower['Bname']:<30} ({borrower['Card_id']}): ${Decimal(str(borrower['Total_unpaid'])):>7.2f}")
                print(f"  ... and {len(unpaid) - 20} more")
        else:
            print("No unpaid fines in the system")
        
        print()
        print("=" * 70)