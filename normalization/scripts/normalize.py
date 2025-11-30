import csv
import re
from collections import OrderedDict

# === Utility Functions ===

def clean_isbn(isbn):
    # Clean and validate ISBN, preserving leading zeros
    if not isbn or isbn.strip() == '':
        return None
    
    # Remove any whitespace and hyphens
    isbn = isbn.strip().replace('-', '').replace(' ', '')
    
    # Keep only digits and 'X' (for ISBN-10)                
    return isbn.zfill(10)[:10] if isbn else None                             # Update to keep exactly 10 characters

def normalize_name(name):
    # Normalize name to Title Case
    if not name:
        return ""
    
     # Handle special cases like "O'Brien", "McDonald"
    words = name.strip().split()
    normalized = []
    for word in words:
        if "'" in word:
            parts = word.split("'")
            normalized.append("'".join([p.capitalize() for p in parts]))
        else:
            normalized.append(word.capitalize())
    return " ".join(normalized)

def parse_authors(author_string):
    # Parse multiple authors from a single string
    if not author_string or author_string.strip() == '':
        return []
    
    # Common separators: comma, semicolon, ampersand, "and"
    # Replace various separators with comma
    author_string = re.sub(r'\s+and\s+', ',', author_string, flags=re.IGNORECASE)
    author_string = author_string.replace(';', ',')
    author_string = author_string.replace('&', ',')
    
    # Split by comma and clean up
    authors = [normalize_name(a.strip()) for a in author_string.split(',')]
    # Remove empty strings
    authors = [a for a in authors if a]
    return authors


# === Normalization Functions ===

def normalize_books(input_file='books.csv', output_dir='normalized_output'):
    """
    Normalize books.csv into:
    - book.csv (Isbn, Title)
    - authors.csv (Author_id, Name)
    - book_authors.csv (Author_id, Isbn)
    """
    
    books = []
    authors_dict = OrderedDict()  # {author_name: author_id}
    book_authors = []
    author_id_counter = 1

    print(f"\nReading {input_file}...")

    try:
        # books.csv uses tab delimiters
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')                                # Update delimiter to tab

            for row in reader:
                # Use ISBN10 as primary identifier (10 characters as specified)
                isbn = clean_isbn(row.get('ISBN10', ''))
                
                # If ISBN10 is not available or invalid, skip this book
                if not isbn:
                    print(f"Warning: Skipping book with missing ISBN10: {row.get('Title', 'Unknown')}")
                    continue
                
                title = row.get('Title', '').strip()
                if not title:
                    print(f"Warning: Book with ISBN " + isbn + " has no title")
                    continue

                # Normalize title (capitalize first letter of each word)
                title = ' '.join(
                    word.capitalize() if word.lower() not in ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'] or i == 0
                    else word.lower()
                    for i, word in enumerate(title.split())
                )

                # Add to books list
                books.append({'Isbn': isbn, 'Title': title})

                # Parse authors
                author_string = row.get('Author', '')
                authors = parse_authors(author_string)
                
                if not authors:
                    print(f"Warning: Book '{title}' has no authors listed")
                    authors = ['Unknown Author']

                # Process each author
                for author_name in authors:
                    # Add author to dictionary if not already present
                    if author_name not in authors_dict:
                        authors_dict[author_name] = author_id_counter
                        author_id_counter += 1
                    
                    # Create book_authors entry
                    author_id = f"A{authors_dict[author_name]:04d}"                         # Update Zero-padded Author_id
                    book_authors.append({'Author_id': author_id, 'Isbn': isbn})

        print(f"Processed {len(books)} books and {len(authors_dict)} unique authors.")
    
    except FileNotFoundError:
        print("Error: " + input_file + " not found!")
        return
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    # Write book.csv
    with open('book.csv', 'w', newline = '', encoding = 'utf-8') as f:
        writer = csv.DictWriter(f, fieldnames = ['Isbn', 'Title'])
        writer.writeheader()
        writer.writerows(books)
    print(f"Created book.csv")

     # Write authors.csv
    authors_list = [{'Author_id': f"A{aid:04d}", 'Name': name} for name, aid in authors_dict.items()]    # Update Zero-padded Author_id
    with open('authors.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Author_id', 'Name'])
        writer.writeheader()
        writer.writerows(authors_list)
    print(f"Created authors.csv")
    
    # Write book_authors.csv
    with open('book_authors.csv', 'w', newline = '', encoding = 'utf-8') as f:
        writer = csv.DictWriter(f, fieldnames = ['Author_id', 'Isbn'])
        writer.writeheader()
        writer.writerows(book_authors)
    print("Created book_authors.csv")


def normalize_borrowers(input_file='borrowers.csv', output_dir='normalized_output'):
    """
    Normalize borrowers.csv into:
    - borrower.csv (Card_id, Ssn, Bname, Address, Phone)
    """
    borrowers = []

    print(f"\nReading {input_file}...")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                card_id = row.get('ID0000id', '').strip()
                ssn = row.get('ssn', '').strip()
                first_name = normalize_name(row.get('first_name', ''))
                last_name = normalize_name(row.get('last_name', ''))
                
                # Combine first and last names into bname
                bname = (first_name + " " + last_name).strip()
                
                # Combine address, city, state into single Address field
                address_parts = []
                if row.get('address', '').strip():
                    address_parts.append(row.get('address', '').strip())
                if row.get('city', '').strip():
                    address_parts.append(row.get('city', '').strip())
                if row.get('state', '').strip():
                    address_parts.append(row.get('state', '').strip())
                address = ', '.join(address_parts)

                phone = row.get('phone', '').strip()

                borrowers.append({
                    'Card_id': card_id,
                    'Ssn': ssn,
                    'Bname': bname,
                    'Address': address,
                    'Phone': phone
                })

        print(f"Processed {len(borrowers)} borrowers.")

    except FileNotFoundError:
        print("Error: " + input_file + " not found!")
        return
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    with open('borrower.csv', 'w', newline = '', encoding = 'utf-8') as f:
        writer = csv.DictWriter(f, fieldnames = ['Card_id', 'Ssn', 'Bname', 'Address', 'Phone'])
        writer.writeheader()
        writer.writerows(borrowers)
    print("Created borrower.csv")


# === Main ===

def main():
    # Main function to run the normalization process
    print("=" * 30)
    print("Library Database Normalization Script")
    print("=" * 30)

    # Normalize books data
    normalize_books('books.csv')
    # Normalize borrowers data
    normalize_borrowers('borrowers.csv')

    print("\n" + "=" * 30)
    print("Normalization complete!")
    print("=" * 30)
    
    print("Generated files:")
    print("  1. book.csv")
    print("  2. authors.csv")
    print("  3. book_authors.csv")
    print("  4. borrower.csv")


if __name__ == "__main__":
    main()
