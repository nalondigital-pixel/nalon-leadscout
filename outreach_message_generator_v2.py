import pandas as pd
from datetime import date


INPUT_FILE = "free_business_leads_no_website.csv"
OUTPUT_FILE = "outreach_messages_v2.csv"


def clean_text(value):
    """
    Cleans empty values so they do not show as 'nan'.
    """
    if pd.isna(value):
        return ""

    return str(value).strip()


def has_value(value):
    """
    Checks if a field has useful data.
    """
    value = clean_text(value)
    return value != "" and value.lower() != "nan"


def create_email_subject(row):
    """
    Creates a professional subject line.
    """
    business_name = clean_text(row.get("business_name", ""))

    if business_name:
        return f"Quick website idea for {business_name}"

    return "Quick website idea for your business"


def create_outreach_message(row):
    """
    Creates a personalized outreach email.
    """
    business_name = clean_text(row.get("business_name", ""))
    category = clean_text(row.get("category", "business"))
    city = clean_text(row.get("city", ""))

    if not business_name:
        business_name = "your business"

    if not category:
        category = "business"

    category_text = category.lower()

    if city:
        first_line = f"I came across {business_name} while checking {category_text} businesses in {city}."
    else:
        first_line = f"I came across {business_name} while checking local {category_text} businesses."

    message = f"""Hi {business_name},

{first_line}

I noticed your business has a local listing, but I couldn’t find a website connected to it.

I help local businesses get simple 1-page websites with services, photos, WhatsApp/contact buttons, Google Maps, and a mobile-friendly layout.

I can create a quick sample for your business first, so you only decide after seeing it.

No worries if not interested — I won’t message again.

Regards,
Nalon Digital
nalondigital@gmail.com"""

    return message


def create_lead_quality(row):
    """
    Adds a simple quality label to each lead.
    """
    score = 0

    if has_value(row.get("email", "")):
        score += 3

    if has_value(row.get("phone", "")):
        score += 3

    if has_value(row.get("facebook", "")):
        score += 2

    if has_value(row.get("maps_link", "")):
        score += 1

    if has_value(row.get("google_search_link", "")):
        score += 1

    if "lead_score" in row and not pd.isna(row.get("lead_score", "")):
        try:
            original_score = float(row.get("lead_score", 0))
            if original_score >= 5:
                score += 2
        except ValueError:
            pass

    if score >= 8:
        return "High"
    elif score >= 5:
        return "Medium"
    else:
        return "Low"


def create_contact_channel(row):
    """
    Suggests the best contact method based on available data.
    """
    if has_value(row.get("email", "")):
        return "Email"

    if has_value(row.get("phone", "")):
        return "Phone/WhatsApp"

    if has_value(row.get("facebook", "")):
        return "Facebook"

    return "Manual verification needed"


def main():
    print("Reading leads file...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Loaded {len(df)} leads.")

    # Remove empty business names
    df = df[df["business_name"].notna()]
    df = df[df["business_name"].astype(str).str.strip() != ""]

    # Remove businesses that already have websites if the column exists
    if "has_website" in df.columns:
        df = df[df["has_website"].astype(str).str.lower().str.strip() == "no"]

    # Remove duplicate businesses
    df["duplicate_key"] = (
        df["business_name"].astype(str).str.lower().str.strip()
        + "_"
        + df["city"].astype(str).str.lower().str.strip()
    )

    df = df.drop_duplicates(subset=["duplicate_key"])
    df = df.drop(columns=["duplicate_key"])

    # Sort by lead score if available
    if "lead_score" in df.columns:
        df = df.sort_values(by="lead_score", ascending=False)

    # Create new outreach fields
    df["lead_quality"] = df.apply(create_lead_quality, axis=1)
    df["recommended_contact_channel"] = df.apply(create_contact_channel, axis=1)
    df["email_subject"] = df.apply(create_email_subject, axis=1)
    df["outreach_message"] = df.apply(create_outreach_message, axis=1)

    # Add tracking columns
    df["gmail_draft_status"] = "Not created"
    df["outreach_status"] = "Not contacted"
    df["date_contacted"] = ""
    df["follow_up_date"] = ""
    df["reply_status"] = ""
    df["deal_status"] = ""
    df["quoted_price"] = ""
    df["notes"] = ""
    df["last_updated"] = str(date.today())

    # Keep useful columns only
    columns_to_keep = [
        "business_name",
        "category",
        "city",
        "phone",
        "email",
        "facebook",
        "website",
        "has_website",
        "address",
        "maps_link",
        "google_search_link",
        "lead_score",
        "lead_quality",
        "recommended_contact_channel",
        "email_subject",
        "outreach_message",
        "gmail_draft_status",
        "outreach_status",
        "date_contacted",
        "follow_up_date",
        "reply_status",
        "deal_status",
        "quoted_price",
        "notes",
        "last_updated",
    ]

    available_columns = [col for col in columns_to_keep if col in df.columns]

    df = df[available_columns]

    df.to_csv(OUTPUT_FILE, index=False)

    print("--------------------------------")
    print(f"Done. Created {OUTPUT_FILE}")
    print(f"Total upgraded outreach messages created: {len(df)}")
    print("--------------------------------")


if __name__ == "__main__":
    main()