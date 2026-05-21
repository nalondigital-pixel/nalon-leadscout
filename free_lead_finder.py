import requests
import pandas as pd
import time


OVERPASS_SERVERS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


# Bounding boxes:
# Format: south, west, north, east
# These are rough areas around each city.
CITIES = {
    "Johannesburg": (-26.35, 27.75, -25.90, 28.35),
    "Cape Town": (-34.35, 18.25, -33.70, 18.95),
    "Durban": (-30.15, 30.70, -29.65, 31.25),
    "Pretoria": (-25.95, 28.00, -25.55, 28.45),
    "Sandton": (-26.15, 27.95, -25.95, 28.15),
}


BUSINESS_CATEGORIES = [
    {"category_name": "Hairdresser", "tag_key": "shop", "tag_value": "hairdresser"},
    {"category_name": "Beauty Salon", "tag_key": "shop", "tag_value": "beauty"},
    {"category_name": "Car Repair", "tag_key": "shop", "tag_value": "car_repair"},
    {"category_name": "Restaurant", "tag_key": "amenity", "tag_value": "restaurant"},
    {"category_name": "Dentist", "tag_key": "amenity", "tag_value": "dentist"},
    {"category_name": "Clinic", "tag_key": "amenity", "tag_value": "clinic"},
    {"category_name": "Pharmacy", "tag_key": "amenity", "tag_value": "pharmacy"},
    {"category_name": "Laundry", "tag_key": "shop", "tag_value": "laundry"},
    {"category_name": "Bakery", "tag_key": "shop", "tag_value": "bakery"},
    {"category_name": "Car Wash", "tag_key": "amenity", "tag_value": "car_wash"},
]


def build_query(tag_key, tag_value, bbox):
    """
    Builds an Overpass API query using coordinates instead of city names.

    This is more reliable because OpenStreetMap does not always find
    city administrative areas correctly by name.
    """

    south, west, north, east = bbox

    query = f"""
    [out:json][timeout:45];
    (
      node["{tag_key}"="{tag_value}"]({south},{west},{north},{east});
      way["{tag_key}"="{tag_value}"]({south},{west},{north},{east});
      relation["{tag_key}"="{tag_value}"]({south},{west},{north},{east});
    );
    out center tags 100;
    """

    return query


def fetch_businesses(city_name, category_name, tag_key, tag_value, bbox):
    """
    Fetches business data from free Overpass servers.

    If one server fails, it tries the next server.
    """

    print(f"Searching {category_name} businesses in {city_name}...")

    query = build_query(tag_key, tag_value, bbox)

    headers = {
        "User-Agent": "NalonDigitalLeadFinder/1.0"
    }

    for server in OVERPASS_SERVERS:
        try:
            response = requests.post(
                server,
                data={"data": query},
                headers=headers,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("elements", [])

            print(f"Server failed: {server}")
            print(f"Status code: {response.status_code}")

        except requests.exceptions.RequestException as error:
            print(f"Connection problem with {server}: {error}")

    print(f"Could not fetch {category_name} in {city_name}. Moving on...")
    return []


def get_tag(tags, possible_names):
    """
    OpenStreetMap uses different names for phone, website, and email.
    This function checks all possible names.
    """

    for name in possible_names:
        value = tags.get(name)
        if value:
            return value

    return ""


def clean_business(item, city_name, category_name):
    """
    Converts raw OpenStreetMap data into a clean spreadsheet row.
    """

    tags = item.get("tags", {})

    name = tags.get("name", "").strip()

    phone = get_tag(tags, [
        "phone",
        "contact:phone",
        "mobile",
        "contact:mobile",
        "telephone"
    ])

    email = get_tag(tags, [
        "email",
        "contact:email"
    ])

    website = get_tag(tags, [
        "website",
        "contact:website",
        "url"
    ])

    facebook = get_tag(tags, [
        "contact:facebook",
        "facebook"
    ])

    street = tags.get("addr:street", "")
    house_number = tags.get("addr:housenumber", "")
    suburb = tags.get("addr:suburb", "")
    postcode = tags.get("addr:postcode", "")

    address_parts = [
        house_number,
        street,
        suburb,
        city_name,
        postcode
    ]

    address = ", ".join([part for part in address_parts if part])

    latitude = item.get("lat")
    longitude = item.get("lon")

    if not latitude or not longitude:
        center = item.get("center", {})
        latitude = center.get("lat", "")
        longitude = center.get("lon", "")

    maps_link = ""

    if latitude and longitude:
        maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"

    google_search_link = f"https://www.google.com/search?q={name.replace(' ', '+')}+{city_name.replace(' ', '+')}"

    return {
        "business_name": name,
        "category": category_name,
        "city": city_name,
        "phone": phone,
        "email": email,
        "website": website,
        "facebook": facebook,
        "has_website": "Yes" if website else "No",
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "maps_link": maps_link,
        "google_search_link": google_search_link,
        "status": "Not contacted"
    }


def calculate_score(row):
    """
    Gives each business a lead score.

    Higher score = better lead.
    """

    score = 0

    if row["has_website"] == "No":
        score += 3

    if row["phone"]:
        score += 3

    if row["email"]:
        score += 2

    if row["facebook"]:
        score += 2

    if row["address"]:
        score += 1

    if row["maps_link"]:
        score += 1

    return score


def remove_duplicates(df):
    """
    Removes duplicate businesses.
    """

    if df.empty:
        return df

    df["duplicate_key"] = (
        df["business_name"].astype(str).str.lower().str.strip()
        + "_"
        + df["city"].astype(str).str.lower().str.strip()
    )

    df = df.drop_duplicates(subset=["duplicate_key"])
    df = df.drop(columns=["duplicate_key"])

    return df


def main():
    all_leads = []

    for city_name, bbox in CITIES.items():
        for category in BUSINESS_CATEGORIES:
            businesses = fetch_businesses(
                city_name=city_name,
                category_name=category["category_name"],
                tag_key=category["tag_key"],
                tag_value=category["tag_value"],
                bbox=bbox
            )

            print(f"Found {len(businesses)} raw results.")

            for business in businesses:
                cleaned = clean_business(
                    item=business,
                    city_name=city_name,
                    category_name=category["category_name"]
                )

                if not cleaned["business_name"]:
                    continue

                # IMPORTANT:
                # We are NOT requiring phone anymore.
                # OpenStreetMap often has missing phone numbers.
                # We collect no-website businesses first, then verify manually.
                if cleaned["has_website"] == "No":
                    all_leads.append(cleaned)

            time.sleep(2)

    df = pd.DataFrame(all_leads)

    if df.empty:
        print("--------------------------------")
        print("No leads found.")
        print("This means OpenStreetMap has poor data for these areas/categories.")
        print("Next step would be using another free source like business directories.")
        print("--------------------------------")
        return

    df = remove_duplicates(df)

    df["lead_score"] = df.apply(calculate_score, axis=1)

    df = df.sort_values(by="lead_score", ascending=False)

    output_file = "free_business_leads_no_website.csv"

    df.to_csv(output_file, index=False)

    print("--------------------------------")
    print(f"Done. Saved {len(df)} leads to {output_file}")
    print("--------------------------------")


if __name__ == "__main__":
    main()