#!/usr/bin/env python3

import csv
import os
import sys

def normalize_authors(input_path, output_path=None):
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    # Default output: author.csv in same directory as input
    if output_path is None:
        base_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(base_dir, "author.csv")

    fieldnames = ["author_id", "name", "fname", "lname"]

    with open(input_path, newline="", encoding="utf-8") as f_in, \
         open(output_path, "w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Get raw values (handle slight header-case variations just in case)
            raw_author_id = (row.get("Author_id") or
                             row.get("author_id") or
                             row.get("AUTHOR_ID") or "").strip()
            raw_name = (row.get("Name") or
                        row.get("name") or
                        row.get("NAME") or "").strip()

            author_id = raw_author_id
            name = raw_name

            fname = ""
            lname = ""

            # Only try to split if there is no dot in the full name
            if name and "." not in name:
                parts = [p for p in name.split() if p]

                if len(parts) == 1:
                    # Single name: treat as first name only
                    fname = parts[0]
                    lname = ""
                else:
                    # First token as fname, last token as lname
                    fname = parts[0]
                    lname = parts[-1]

            writer.writerow({
                "author_id": author_id,
                "name": name,
                "fname": fname,
                "lname": lname,
            })

    print(f"Normalized authors written to: {output_path}")


def main():
    input_path = input("Enter path to authors CSV (e.g. authors.csv): ").strip()
    if not input_path:
        print("No path provided. Exiting.")
        sys.exit(1)

    normalize_authors(input_path)


if __name__ == "__main__":
    main()
