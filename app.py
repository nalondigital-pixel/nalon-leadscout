import os
import time
import requests
import pandas as pd

from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


OVERPASS_SERVERS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


CITIES = {
    "Johannesburg": (-26.35, 27.75, -25.90, 28.35),
    "Cape Town": (-34.35, 18.25, -33.70, 18.95),
    "Durban": (-30.15, 30.70, -29.65, 31.25),
    "Pretoria": (-25.95, 28.00, -25.55, 28.45),
    "Sandton": (-26.15, 27.95, -25.95, 28.15),
}


BUSINESS_CATEGORIES = {
    "Hairdresser": {"tag_key": "shop", "tag_value": "hairdresser"},
    "Beauty Salon": {"tag_key": "shop", "tag_value": "beauty"},
    "Car Repair": {"tag_key": "shop", "tag_value": "car_repair"},
    "Restaurant": {"tag_key": "amenity", "tag_value": "restaurant"},
    "Dentist": {"tag_key": "amenity", "tag_value": "dentist"},
    "Clinic": {"tag_key": "amenity", "tag_value": "clinic"},
    "Pharmacy": {"tag_key": "amenity", "tag_value": "pharmacy"},
    "Laundry": {"tag_key": "shop", "tag_value": "laundry"},
    "Bakery": {"tag_key": "shop", "tag_value": "bakery"},
    "Car Wash": {"tag_key": "amenity", "tag_value": "car_wash"},
}


OUTPUTS_FOLDER = "outputs"

FULL_LEADS_FILE = os.path.join(OUTPUTS_FOLDER, "latest_full_leads.csv")
EMAIL_READY_FILE = os.path.join(OUTPUTS_FOLDER, "latest_email_ready_leads.csv")
OUTREACH_FILE = os.path.join(OUTPUTS_FOLDER, "latest_outreach_messages.csv")


def build_query(tag_key, tag_value, bbox):
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


def fetch_businesses(city_name, category_name, tag_key, tag_value):
    bbox = CITIES[city_name]
    query = build_query(tag_key, tag_value, bbox)

    headers = {
        "User-Agent": "NalonLeadScoutWebApp/1.0"
    }

    print(f"Searching {category_name} in {city_name}...")

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

    return []


def get_tag(tags, possible_names):
    for name in possible_names:
        value = tags.get(name)
        if value:
            return value

    return ""


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def has_value(value):
    value = clean_text(value)
    return value != "" and value.lower() != "nan"


def create_outreach_message(business_name, category_name, city_name):
    if not business_name:
        business_name = "your business"

    if not category_name:
        category_name = "business"

    if not city_name:
        first_line = f"I came across {business_name} while checking local {category_name.lower()} businesses."
    else:
        first_line = f"I came across {business_name} while checking {category_name.lower()} businesses in {city_name}."

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


def clean_business(item, city_name, category_name):
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

    google_search_link = ""

    if name:
        google_search_link = f"https://www.google.com/search?q={name.replace(' ', '+')}+{city_name.replace(' ', '+')}"

    email_subject = f"Quick website idea for {name}" if name else "Quick website idea for your business"

    outreach_message = create_outreach_message(
        business_name=name,
        category_name=category_name,
        city_name=city_name
    )

    return {
        "business_name": name,
        "category": category_name,
        "city": city_name,
        "phone": phone,
        "email": email,
        "facebook": facebook,
        "website": website,
        "has_website": "Yes" if website else "No",
        "address": address,
        "latitude": latitude,
        "longitude": longitude,
        "maps_link": maps_link,
        "google_search_link": google_search_link,
        "lead_score": 0,
        "lead_quality": "",
        "recommended_contact_channel": "",
        "email_subject": email_subject,
        "outreach_message": outreach_message,
        "gmail_draft_status": "Not created",
        "outreach_status": "Not contacted",
        "date_contacted": "",
        "follow_up_date": "",
        "reply_status": "",
        "deal_status": "",
        "quoted_price": "",
        "notes": "",
    }


def calculate_score(row):
    score = 0

    if row["has_website"] == "No":
        score += 3

    if has_value(row.get("phone", "")):
        score += 3

    if has_value(row.get("email", "")):
        score += 3

    if has_value(row.get("facebook", "")):
        score += 2

    if has_value(row.get("address", "")):
        score += 1

    if has_value(row.get("maps_link", "")):
        score += 1

    if has_value(row.get("google_search_link", "")):
        score += 1

    return score


def calculate_quality(row):
    score = row.get("lead_score", 0)

    try:
        score = float(score)
    except ValueError:
        score = 0

    if score >= 9:
        return "High"

    if score >= 6:
        return "Medium"

    return "Low"


def recommended_contact_channel(row):
    if has_value(row.get("email", "")):
        return "Email"

    if has_value(row.get("phone", "")):
        return "Phone/WhatsApp"

    if has_value(row.get("facebook", "")):
        return "Facebook"

    return "Manual verification"


def remove_duplicates(df):
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


def find_leads(city_name, selected_category):
    all_leads = []

    if selected_category == "All Categories":
        categories_to_search = BUSINESS_CATEGORIES
    else:
        categories_to_search = {
            selected_category: BUSINESS_CATEGORIES[selected_category]
        }

    for category_name, category_data in categories_to_search.items():
        businesses = fetch_businesses(
            city_name=city_name,
            category_name=category_name,
            tag_key=category_data["tag_key"],
            tag_value=category_data["tag_value"]
        )

        print(f"Found {len(businesses)} raw results for {category_name} in {city_name}.")

        for business in businesses:
            cleaned = clean_business(
                item=business,
                city_name=city_name,
                category_name=category_name
            )

            if not cleaned["business_name"]:
                continue

            if cleaned["has_website"] == "No":
                all_leads.append(cleaned)

        time.sleep(1)

    df = pd.DataFrame(all_leads)

    if df.empty:
        return df

    df = remove_duplicates(df)

    df["lead_score"] = df.apply(calculate_score, axis=1)
    df["lead_quality"] = df.apply(calculate_quality, axis=1)
    df["recommended_contact_channel"] = df.apply(recommended_contact_channel, axis=1)

    df = df.sort_values(by="lead_score", ascending=False)

    return df


def save_outputs(df):
    os.makedirs(OUTPUTS_FOLDER, exist_ok=True)

    df.to_csv(FULL_LEADS_FILE, index=False)

    outreach_df = df.copy()
    outreach_df.to_csv(OUTREACH_FILE, index=False)

    email_ready_df = df.copy()

    if "email" in email_ready_df.columns:
        email_ready_df["email"] = email_ready_df["email"].apply(clean_text)
        email_ready_df = email_ready_df[email_ready_df["email"] != ""]
        email_ready_df = email_ready_df.drop_duplicates(subset=["email"])
    else:
        email_ready_df = pd.DataFrame()

    email_ready_df.to_csv(EMAIL_READY_FILE, index=False)

    return {
        "total_leads": len(df),
        "email_ready": len(email_ready_df),
        "high_quality": len(df[df["lead_quality"] == "High"]) if "lead_quality" in df.columns else 0,
        "medium_quality": len(df[df["lead_quality"] == "Medium"]) if "lead_quality" in df.columns else 0,
        "low_quality": len(df[df["lead_quality"] == "Low"]) if "lead_quality" in df.columns else 0,
        "with_phone": len(df[df["phone"].apply(has_value)]) if "phone" in df.columns else 0,
        "with_facebook": len(df[df["facebook"].apply(has_value)]) if "facebook" in df.columns else 0,
    }


def get_default_stats():
    return {
        "total_leads": 0,
        "email_ready": 0,
        "high_quality": 0,
        "medium_quality": 0,
        "low_quality": 0,
        "with_phone": 0,
        "with_facebook": 0,
    }


def render_home(
    request,
    leads=None,
    message="",
    selected_city="",
    selected_category="",
    download_ready=False,
    stats=None
):
    if leads is None:
        leads = []

    if stats is None:
        stats = get_default_stats()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "cities": list(CITIES.keys()),
            "categories": ["All Categories"] + list(BUSINESS_CATEGORIES.keys()),
            "leads": leads,
            "message": message,
            "selected_city": selected_city,
            "selected_category": selected_category,
            "download_ready": download_ready,
            "stats": stats,
        }
    )


@app.get("/")
def home(request: Request):
    return render_home(request=request)


@app.post("/find")
def find(
    request: Request,
    city: str = Form(...),
    category: str = Form(...)
):
    df = find_leads(city, category)

    if df.empty:
        return render_home(
            request=request,
            leads=[],
            message="No leads found. Try another city or category.",
            selected_city=city,
            selected_category=category,
            download_ready=False,
            stats=get_default_stats()
        )

    stats = save_outputs(df)

    leads = df.head(100).to_dict(orient="records")

    return render_home(
        request=request,
        leads=leads,
        message=f"Found {len(df)} leads. Showing first 100.",
        selected_city=city,
        selected_category=category,
        download_ready=True,
        stats=stats
    )


@app.get("/download/full")
def download_full_leads():
    if not os.path.exists(FULL_LEADS_FILE):
        return {"error": "No full leads CSV found. Please find leads first."}

    return FileResponse(
        FULL_LEADS_FILE,
        media_type="text/csv",
        filename="nalon_leadscout_full_leads.csv"
    )


@app.get("/download/email-ready")
def download_email_ready():
    if not os.path.exists(EMAIL_READY_FILE):
        return {"error": "No email-ready CSV found. Please find leads first."}

    return FileResponse(
        EMAIL_READY_FILE,
        media_type="text/csv",
        filename="nalon_leadscout_email_ready_leads.csv"
    )


@app.get("/download/outreach")
def download_outreach():
    if not os.path.exists(OUTREACH_FILE):
        return {"error": "No outreach CSV found. Please find leads first."}

    return FileResponse(
        OUTREACH_FILE,
        media_type="text/csv",
        filename="nalon_leadscout_outreach_messages.csv"
    )