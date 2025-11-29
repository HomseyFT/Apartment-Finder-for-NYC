from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Iterable, List

from rich.console import Console
from rich.table import Table

from .models import Apartment


def print_table(apartments: Iterable[Apartment]) -> None:
    apartments = list(apartments)
    console = Console()
    if not apartments:
        console.print("[bold yellow]No apartments found.[/bold yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Neighborhood", style="green")
    table.add_column("Address")
    table.add_column("Price", justify="right")
    table.add_column("Beds", justify="right")
    table.add_column("Baths", justify="right")
    table.add_column("URL", overflow="fold")

    for apt in apartments:
        table.add_row(
            apt.provider,
            apt.neighborhood or "-",
            apt.address,
            f"${apt.price:,}" if apt.price is not None else "-",
            str(apt.beds) if apt.beds is not None else "-",
            str(apt.baths) if apt.baths is not None else "-",
            str(apt.url) if apt.url is not None else "-",
        )

    console.print(table)


def to_json(apartments: Iterable[Apartment], *, indent: int = 2) -> str:
    payload: List[dict] = [apt.dict() for apt in apartments]
    return json.dumps(payload, indent=indent)


def to_csv(apartments: Iterable[Apartment]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "provider",
            "id",
            "neighborhood",
            "address",
            "city",
            "state",
            "zipcode",
            "price",
            "beds",
            "baths",
            "lat",
            "lon",
            "url",
        ],
    )
    writer.writeheader()

    for apt in apartments:
        writer.writerow(
            {
                "provider": apt.provider,
                "id": apt.id,
                "neighborhood": apt.neighborhood,
                "address": apt.address,
                "city": apt.city,
                "state": apt.state,
                "zipcode": apt.zipcode,
                "price": apt.price,
                "beds": apt.beds,
                "baths": apt.baths,
                "lat": apt.lat,
                "lon": apt.lon,
                "url": str(apt.url) if apt.url is not None else None,
            }
        )

    return output.getvalue()
