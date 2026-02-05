# NYC Apartments Scraper

A small, pluggable pipeline that fetches apartment-like listings around a NYC location,
normalizes them to a common model, filters by distance/price/beds, and outputs them in
a human-friendly format.

The initial provider uses NYC Open Data (Housing New York / affordable housing datasets)
as a stand‑in for real apartment listings. The architecture is modular so you can add
more providers later. A RentCast-backed provider is also included for real rental listings.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# Copy and edit env vars (do NOT commit .env)
cp .env.example .env  # On Windows: copy .env.example .env

# Set your RentCast API key in .env
# RENTCAST_API_KEY=your-real-key-here

# Run a search using the RentCast provider (example)
python -m nyc_apartments.cli search \
  --center-address "Times Square, New York, NY" \
  --radius-km 3 \
  --provider rentcast_rental_listings \
  --output table
```

## Notes

- NYC Open Data provider does not expose exact rents, so price filters may not apply
  to that provider. The `Apartment` model still has `price` for future providers.
- The RentCast provider requires a valid `RENTCAST_API_KEY` in your environment.
- Add your own providers under `src/nyc_apartments/providers/` and plug them into the
  common `BaseProvider` interface.
