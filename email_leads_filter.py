import pandas as pd


INPUT_FILE = "outreach_messages.csv"
OUTPUT_FILE = "email_ready_leads.csv"


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def main():
    print("Reading outreach messages...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} outreach rows.")

    if "email" not in df.columns:
        print("No email column found.")
        return

    df["email"] = df["email"].apply(clean_text)

    # Keep only rows that have an email address
    email_df = df[df["email"] != ""]

    # Remove duplicate emails
    email_df = email_df.drop_duplicates(subset=["email"])

    # Sort by lead score if available
    if "lead_score" in email_df.columns:
        email_df = email_df.sort_values(by="lead_score", ascending=False)

    # Add draft status column
    email_df["gmail_draft_status"] = "Not created"

    email_df.to_csv(OUTPUT_FILE, index=False)

    print("--------------------------------")
    print(f"Done. Created {OUTPUT_FILE}")
    print(f"Email-ready leads: {len(email_df)}")
    print("--------------------------------")


if __name__ == "__main__":
    main()