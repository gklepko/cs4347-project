import csv
import os
import re
import sys

def normalize_borrowers(input_path, output_path=None):
    if not os.path.isfile(input_path):
        print(f"Error: file not found: {input_path}")
        sys.exit(1)

    # Default output: borrower.csv in same directory as input
    if output_path is None:
        base_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(base_dir, "borrower.csv")

    fieldnames = [
        "card_id",
        "ssn",
        "bname",
        "fname",
        "lname",
        "email",
        "address",
        "phonenumber",
    ]

    with open(input_path, newline="", encoding="utf-8") as f_in, \
         open(output_path, "w", newline="", encoding="utf-8") as f_out:

        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Raw values from input CSV
            raw_card_id = (row.get("ID0000id") or "").strip()
            raw_ssn = row.get("ssn") or ""
            raw_fname = row.get("first_name") or ""
            raw_lname = row.get("last_name") or ""
            raw_email = row.get("email") or ""
            raw_street = row.get("address") or ""
            raw_city = row.get("city") or ""
            raw_state = row.get("state") or ""
            raw_phone = row.get("phone") or ""

            # card_id: keep as-is (trimmed)
            card_id = raw_card_id

            # ssn: digits only
            ssn = re.sub(r"\D", "", raw_ssn)

            # names
            fname = raw_fname.strip()
            lname = raw_lname.strip()
            bname = f"{fname} {lname}".strip()

            # email
            email = raw_email.strip()

            # address: "street, city, state" (skip empties)
            address_parts = [raw_street.strip(), raw_city.strip(), raw_state.strip()]
            address = ", ".join(p for p in address_parts if p)

            # phonenumber: digits only
            phonenumber = re.sub(r"\D", "", raw_phone)

            writer.writerow({
                "card_id": card_id,
                "ssn": ssn,
                "bname": bname,
                "fname": fname,
                "lname": lname,
                "email": email,
                "address": address,
                "phonenumber": phonenumber,
            })

    print(f"Normalized borrowers written to: {output_path}")


def main():
    path = input("Enter path to borrowers CSV (e.g. borrowers(1)(1).csv): ").strip()
    if not path:
        print("No path provided. Exiting.")
        sys.exit(1)

    normalize_borrowers(path)


if __name__ == "__main__":
    main()
