from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import typer

from .aggregator import run_aggregation
from .config import get_base_config, merge_cli_overrides
from .formatters import print_table, to_csv, to_json

app = typer.Typer(help="Search NYC apartment-like records via pluggable providers.")


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


@app.command()
def search(
    center_address: Optional[str] = typer.Option(
        None,
        "--center-address",
        help="Human-readable address used as center point (geocoded).",
    ),
    center_lat: Optional[float] = typer.Option(None, "--lat", help="Center latitude (decimal degrees)"),
    center_lon: Optional[float] = typer.Option(None, "--lon", help="Center longitude (decimal degrees)"),
    radius_km: float = typer.Option(3.0, "--radius-km", help="Search radius in kilometers"),
    min_price: Optional[int] = typer.Option(None, "--min-price", help="Minimum monthly rent in dollars"),
    max_price: Optional[int] = typer.Option(None, "--max-price", help="Maximum monthly rent in dollars"),
    min_beds: Optional[float] = typer.Option(None, "--min-beds", help="Minimum number of bedrooms"),
    max_beds: Optional[float] = typer.Option(None, "--max-beds", help="Maximum number of bedrooms"),
    provider: List[str] = typer.Option(
        [],
        "--provider",
        "-p",
        help="Provider(s) to enable by name (default: all discovered). Repeat for multiple.",
    ),
    output: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format: table | json | csv",
    ),
    limit: Optional[int] = typer.Option(None, "--limit", help="Maximum number of results to show"),
    save_json_path: Optional[Path] = typer.Option(
        None,
        "--save-json",
        help="Optional path to save the full result set as JSON.",
    ),
    sqlite_db: Optional[Path] = typer.Option(
        None,
        "--sqlite-db",
        help="Optional path to a SQLite DB for persistence/deduplication.",
    ),
    new_only: bool = typer.Option(
        False,
        "--new-only",
        help="With --sqlite-db, only show apartments not seen in previous runs.",
    ),
) -> None:
    """Run a search and print results according to the chosen output format."""

    base = get_base_config()

    overrides = dict(
        center_address=center_address,
        center_lat=center_lat,
        center_lon=center_lon,
        radius_km=radius_km,
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds,
        max_beds=max_beds,
        providers=provider or None,
        output_format=output,
        limit=limit,
    )

    config = merge_cli_overrides(base, **overrides)

    apartments = run_aggregation(config)

    # Optional SQLite-based dedupe/history
    if sqlite_db is not None:
        from .storage.sqlite_store import get_new_since_last_run, upsert_apartments

        db_path_str = str(sqlite_db)
        if new_only:
            apartments = get_new_since_last_run(db_path_str, apartments)
        else:
            upsert_apartments(db_path_str, apartments)

    # Optional JSON file export
    if save_json_path is not None:
        from .storage.json_store import save_to_json

        save_to_json(str(save_json_path), apartments)

    # Render to stdout
    output_lower = output.lower()
    if output_lower == "json":
        print(to_json(apartments))
    elif output_lower == "csv":
        print(to_csv(apartments), end="")
    else:
        print_table(apartments)


if __name__ == "__main__":  # pragma: no cover
    app()
