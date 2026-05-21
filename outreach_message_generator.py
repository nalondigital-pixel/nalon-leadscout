import pandas as pd


INPUT_FILE = "free_business_leads_no_website.csv"
OUTPUT_FILE = "outreach_messages.csv"


def clean_text(value):
    """
    Makes sure empty values do not show as 'nan' in messages.
    """
    if pd.isna(value):
        return ""

    return str(value).strip()


def create_message(row):
    """
    Creates a friendly outreach message for each business.
    """

    business_name = clean_text(row.get("business_name", ""))
    category = clean_text(row.get("category", "business"))
    city = clean_text(row.get("city", ""))

    if not business_name:
        business_name = "your business"

    if not category:
        category = "business"

    if city:
        location_text = f"in {city}"
    else:
        location_text = "online"

    message = f"""Hi {business_name},

I came across your {category.lower()} business {location_text}.

I noticed your business has a local listing, but I could not find a website attached to it.

I help local businesses get a simple 1-page website with services, WhatsApp/contact buttons, photos, Google Maps location, and a clean mobile-friendly design.

I can create a quick sample for your business first.

No worries if not interested — I won’t message again.

Regards,
Nalon Digital"""

    return message


def create_email_subject(row):
    """
    Creates a simple email subject line.
    """

    business_name = clean_text(row.get("business_name", ""))

    if business_name:
        return f"Quick website idea for {business_name}"

    return "Quick website idea for your business"


def main():
    print("Reading leads file...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} leads.")

    # Remove leads without business names
    df = df[df["business_name"].notna()]
    df = df[df["business_name"].astype(str).str.strip() != ""]

    # Sort by best leads first if lead_score exists
    if "lead_score" in df.columns:
        df = df.sort_values(by="lead_score", ascending=False)

    # Create outreach fields
    df["email_subject"] = df.apply(create_email_subject, axis=1)
    df["outreach_message"] = df.apply(create_message, axis=1)

    # Add tracking columns
    df["outreach_status"] = "Not contacted"
    df["date_contacted"] = ""
    df["reply_status"] = ""
    df["notes"] = ""

    # Keep useful columns only
    columns_to_keep = [
        "business_name",
        "category",
        "city",
        "phone",
        "email",
        "facebook",
        "maps_link",
        "google_search_link",
        "lead_score",
        "email_subject",
        "outreach_message",
        "outreach_status",
        "date_contacted",
        "reply_status",
        "notes",
    ]

    available_columns = [col for col in columns_to_keep if col in df.columns]

    df = df[available_columns]

    df.to_csv(OUTPUT_FILE, index=False)

    print("--------------------------------")
    print(f"Done. Created {OUTPUT_FILE}")
    print(f"Total outreach messages created: {len(df)}")
    print("--------------------------------")


if __name__ == "__main__":
    main()