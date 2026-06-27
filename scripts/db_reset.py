"""Reset the local SQLite catalog and re-seed demo rows."""

from seed_demo_data import main

if __name__ == "__main__":
    main(reset=True)
