import pandas as pd


INPUT_FILE = "outreach_messages_v2.csv"
OUTPUT_FILE = "email_ready_leads_v2.csv"


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def main():
    print("Reading upgraded outreach messages...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} outreach rows.")

    if "email" not in df.columns:
        print("No email column found.")
        return

    df["email"] = df["email"].apply(clean_text)

    # Keep only rows with email
    email_df = df[df["email"] != ""]

    # Remove duplicate emails
    email_df = email_df.drop_duplicates(subset=["email"])

    # Prefer high-quality leads first
    if "lead_quality" in email_df.columns:
        quality_order = {"High": 1, "Medium": 2, "Low": 3}
        email_df["quality_rank"] = email_df["lead_quality"].map(quality_order).fillna(4)
        email_df = email_df.sort_values(by="quality_rank", ascending=True)
        email_df = email_df.drop(columns=["quality_rank"])

    # Then sort by lead score if available
    if "lead_score" in email_df.columns:
        email_df = email_df.sort_values(by="lead_score", ascending=False)

    email_df.to_csv(OUTPUT_FILE, index=False)

    print("--------------------------------")
    print(f"Done. Created {OUTPUT_FILE}")
    print(f"Email-ready leads: {len(email_df)}")
    print("--------------------------------")


if __name__ == "__main__":
    main()