"""Generate the checked-in local demo data set."""

from datetime import date
from pathlib import Path

from semantic_layer.data_generation import generate_demo_data

if __name__ == "__main__":
    generate_demo_data(Path(__file__).resolve().parent, date(2026, 8, 28))
