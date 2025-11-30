import csv
import os
import sys

def normalize_books(input_path, output_path=None):
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    # Default output: book.csv
    if output_path is None:
        base_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(base_dir, "book.csv")

    fieldnames = ["Isbn", "Title"]

    print(f"Processing {input_path}...")

    with open(input_path, newline="", encoding="utf-8", errors="replace") as f_in, \
         open(output_path, "w", newline="", encoding="utf-8") as f_out:

        sample = f_in.read(2048)
        f_in.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = 'excel-tab'

        reader = csv.DictReader(f_in, dialect=dialect)
        
        # Verify headers exist
        if not reader.fieldnames:
             print("Error: Could not read headers.")
             return

        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        seen_isbns = set()
        count = 0
        skipped = 0

        for row in reader:
            # 1. Get Title
            title = row.get("Title") or row.get("title") or ""
            title = title.strip()

            # 2. Get ISBN (Prioritize ISBN10)
            raw_isbn = (row.get("ISBN10") or row.get("isbn10") or 
                        row.get("ISBN13") or row.get("isbn13") or 
                        row.get("ISBN") or row.get("isbn") or "")
            
            # Clean ISBN: remove hyphens, spaces, keep only alphanumeric
            isbn = "".join(filter(str.isalnum, raw_isbn)).upper()
            
            # Truncate to 10 chars if it's long (database Isbn is VARCHAR(10))
            if len(isbn) > 10:
                isbn = isbn[:10]

            if isbn and title:
                if isbn not in seen_isbns:
                    seen_isbns.add(isbn)
                    writer.writerow({
                        "Isbn": isbn,
                        "Title": title
                    })
                    count += 1
                else:
                    skipped += 1
            else:
                skipped += 1

    print(f"Done! Created '{output_path}'.")
    print(f"Imported: {count} books.")
    print(f"Skipped:  {skipped} duplicates or empty rows.")

def main():
    print("Enter path to raw books file (e.g. normalization/csv/books.csv):")
    path = input().strip()
    if path:
        normalize_books(path)

if __name__ == "__main__":
    main()

