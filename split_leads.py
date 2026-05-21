import pandas as pd


def save_file(df, filename):
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} leads to {filename}")


def main():
    input_file = "free_business_leads_no_website.csv"

    df = pd.read_csv(input_file)

    # Remove empty business names
    df = df[df["business_name"].notna()]
    df = df[df["business_name"].astype(str).str.strip() != ""]

    # Sort by best leads first
    df = df.sort_values(by="lead_score", ascending=False)

    # Save top general lists
    save_file(df.head(50), "top_50_best_leads.csv")
    save_file(df.head(100), "top_100_best_leads.csv")
    save_file(df.head(500), "top_500_best_leads.csv")

    # Save by city
    for city in df["city"].dropna().unique():
        city_df = df[df["city"] == city]
        filename = f"leads_{city.lower().replace(' ', '_')}.csv"
        save_file(city_df, filename)

    # Save by category
    for category in df["category"].dropna().unique():
        category_df = df[df["category"] == category]
        filename = f"leads_{category.lower().replace(' ', '_')}.csv"
        save_file(category_df, filename)

    # Save strongest leads with some contact/location data
    strong_df = df[
        (df["phone"].notna() & (df["phone"].astype(str).str.strip() != "")) |
        (df["email"].notna() & (df["email"].astype(str).str.strip() != "")) |
        (df["facebook"].notna() & (df["facebook"].astype(str).str.strip() != ""))
    ]

    save_file(strong_df, "strong_leads_with_contact_data.csv")


if __name__ == "__main__":
    main()
    