import csv
import os
import re
import sys

def normalize_book_authors(input_path, output_path=None):
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    # Default output: book_author.csv in same directory as input
    if output_path is None:
        base_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(base_dir, "book_author.csv")

    # These must match your MySQL column names exactly
    fieldnames = ["Author_id", "Isbn"]

    seen_pairs = set()
    total_rows = 0
    written_rows = 0
    skipped_dupes = 0
    skipped_empty = 0

    with open(input_path, newline="", encoding="utf-8") as f_in, \
         open(output_path, "w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            total_rows += 1

            # Try to be flexible with header names
            raw_author_id = (
                row.get("Author_id")
                or row.get("author_id")
                or row.get("AUTHOR_ID")
                or row.get("authorId")
                or ""
            )
            raw_isbn = (
                row.get("Isbn")
                or row.get("isbn")
                or row.get("ISBN")
                or ""
            )

            author_id = raw_author_id.strip()
            # Clean ISBN: remove spaces/hyphens and other non-alphanumeric
            isbn = re.sub(r"[^0-9Xx]", "", raw_isbn).upper().strip()

            # Skip rows with missing key fields
            if not author_id or not isbn:
                skipped_empty += 1
                continue

            key = (author_id, isbn)
            if key in seen_pairs:
                skipped_dupes += 1
                continue

            seen_pairs.add(key)

            writer.writerow({
                "Author_id": author_id,
                "Isbn": isbn,
            })
            written_rows += 1

    print(f"Input file:        {input_path}")
    print(f"Output file:       {output_path}")
    print(f"Total input rows:  {total_rows}")
    print(f"Written rows:      {written_rows}")
    print(f"Skipped duplicates:{skipped_dupes}")
    print(f"Skipped empty key: {skipped_empty}")


def main():
    input_path = input("Enter path to book_authors CSV (e.g. book_authors.csv): ").strip()
    if not input_path:
        print("No path provided. Exiting.")
        sys.exit(1)

    normalize_book_authors(input_path)


if __name__ == "__main__":
    main()
