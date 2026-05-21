import pandas as pd


def main():
    input_file = "free_business_leads_no_website.csv"
    output_file = "top_50_leads_for_outreach.csv"

    df = pd.read_csv(input_file)

    # Make sure lead_score exists
    if "lead_score" not in df.columns:
        print("Error: lead_score column not found.")
        return

    # Remove rows without business names
    df = df[df["business_name"].notna()]
    df = df[df["business_name"].astype(str).str.strip() != ""]

    # Sort by best leads first
    df = df.sort_values(by="lead_score", ascending=False)

    # Keep only the top 50
    df = df.head(50)

    # Add manual workflow columns
    df["verified"] = "No"
    df["contact_method"] = ""
    df["notes"] = ""

    df.to_csv(output_file, index=False)

    print(f"Done. Created {output_file}")
    print(f"Rows saved: {len(df)}")


if __name__ == "__main__":
    main()