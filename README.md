# Nalon LeadScout

Nalon LeadScout is a Python automation tool that helps freelancers, web designers, digital marketers, and sales teams find local businesses with no listed websites.

The tool uses free OpenStreetMap data through the Overpass API to search businesses by city and category, detect missing websites, generate verification links, score leads, remove duplicates, and export a clean CSV file for outreach.

## Result

In testing, the tool generated 1,711 South African business leads with no listed websites.

## Features

- Search businesses by city and category
- Use free OpenStreetMap / Overpass API data
- Detect businesses with no listed website
- Generate Google Maps verification links
- Generate Google Search verification links
- Score leads based on available contact and location data
- Remove duplicate businesses
- Export results to CSV
- Handle failed Overpass servers using fallback servers

## Tech Stack

- Python
- Requests
- Pandas
- OpenStreetMap
- Overpass API
- CSV automation

## How It Works

1. Select cities and business categories.
2. Fetch public business data from OpenStreetMap.
3. Check whether each business has a listed website.
4. Generate Google Maps and Google Search verification links.
5. Score each lead.
6. Export the results to CSV.

## Use Case

A freelancer or agency can use this tool to find businesses without websites, verify the leads manually, and offer website design, SEO, digital marketing, POS systems, or other business services.

## Status

This is currently a local Python automation project. A web dashboard version is planned.