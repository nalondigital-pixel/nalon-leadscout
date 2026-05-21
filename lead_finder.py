import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY. Add it inside your .env file.")


def search_places(query):
    """
    This function searches Google Places for businesses matching our query.
    Example query: 'dentists in Johannesburg'
    """
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": (
            "places.id,"
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.internationalPhoneNumber,"
            "places.websiteUri,"
            "places.rating,"
            "places.userRatingCount,"
            "places.googleMapsUri,"
            "places.primaryTypeDisplayName"
        ),
    }

    payload = {
        "textQuery": query,
        "maxResultCount": 20,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print("Error:", response.status_code)
        print(response.text)
        return []

    data = response.json()
    return data.get("places", [])


def calculate_lead_score(place):
    """
    This gives every business a simple score.
    Higher score = better lead.
    """
    score = 0

    website = place.get("websiteUri")
    phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")
    rating = place.get("rating", 0)
    reviews = place.get("userRatingCount", 0)

    if not website:
        score += 3

    if phone:
        score += 2

    if rating >= 4.0:
        score += 1

    if rating >= 4.3:
        score += 1

    if reviews >= 10:
        score += 1

    if reviews >= 50:
        score += 2

    if reviews >= 100:
        score += 2

    return score


def clean_place(place, search_query):
    """
    This converts raw Google data into a clean row for our spreadsheet.
    """
    name = place.get("displayName", {}).get("text", "")
    phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber", "")
    website = place.get("websiteUri", "")

    return {
        "search_query": search_query,
        "business_name": name,
        "category": place.get("primaryTypeDisplayName", {}).get("text", ""),
        "address": place.get("formattedAddress", ""),
        "phone": phone,
        "website": website,
        "has_website": "Yes" if website else "No",
        "rating": place.get("rating", ""),
        "review_count": place.get("userRatingCount", 0),
        "google_maps_link": place.get("googleMapsUri", ""),
        "lead_score": calculate_lead_score(place),
        "status": "Not contacted",
    }


def main():
    searches = [
        "dentists in Johannesburg South Africa",
        "salons in Johannesburg South Africa",
        "mechanics in Pretoria South Africa",
        "plumbers in Cape Town South Africa",
        "restaurants in Durban South Africa",
        "car rental in Johannesburg South Africa",
        "lodges in Harare Zimbabwe",
        "construction companies in Bulawayo Zimbabwe",
    ]

    all_leads = []

    for query in searches:
        print(f"Searching: {query}")

        places = search_places(query)

        for place in places:
            cleaned = clean_place(place, query)

            if cleaned["has_website"] == "No" and cleaned["phone"]:
                all_leads.append(cleaned)

    df = pd.DataFrame(all_leads)

    if df.empty:
        print("No leads found.")
        return

    df = df.sort_values(by="lead_score", ascending=False)

    output_file = "business_leads_no_website.csv"
    df.to_csv(output_file, index=False)

    print(f"Done. Saved {len(df)} leads to {output_file}")


if __name__ == "__main__":
    main()