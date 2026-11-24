import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

from validator import load_airports
from csv_loader import parse_files
from query import run_queries

STUDENT_ID = "241AMC029"
FIRST_NAME = "FahriYigit"
LAST_NAME = "Yoru"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE")
    source.add_argument("-d", metavar="FOLDER")
    source.add_argument("-j", metavar="FILE")

    parser.add_argument("-a", metavar="FILE")
    parser.add_argument("-o", metavar="FILE")
    parser.add_argument("-q", metavar="FILE")
    parser.add_argument("-r", metavar="FOLDER", default=".")

    try:
        args = parser.parse_args(argv)

        if (args.i or args.d) and not args.a:
            parser.error("-a is required with -i or -d")

        if args.j and args.o is not None:
            parser.error("-o cannot be used with -j")

    except SystemExit as exc:
        return exc.code

    try:
        if args.j:
            with open(args.j, encoding="utf-8") as file:
                db = json.load(file)

            if not isinstance(db, list) or not all(
                isinstance(record, dict) for record in db
            ):
                raise ValueError("Invalid database format")

        else:
            airports = load_airports(args.a)

            if args.i:
                paths = [args.i]
            else:
                folder = Path(args.d)

                paths = sorted(
                    str(path)
                    for path in folder.iterdir()
                    if path.is_file() and path.name.endswith(".csv")
                )

                if not paths:
                    raise ValueError("No CSV files found")

            output = Path(args.o or "db.json")
            log_path = output.parent / "errors.log"

            logger = logging.getLogger("flight_parser")
            logger.setLevel(logging.INFO)
            logger.propagate = False

            handler = logging.FileHandler(
                log_path, mode="w", encoding="utf-8"
            )

            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))

            logger.addHandler(handler)

            try:
                db, errors = parse_files(paths, airports)

                for error in errors:
                    logger.warning(error)

                with open(output, "w", encoding="utf-8") as file:
                    json.dump(db, file, indent=2, ensure_ascii=False)

            finally:
                logger.removeHandler(handler)
                handler.close()

        if args.q:
            with open(args.q, encoding="utf-8") as file:
                queries = json.load(file)

            if not isinstance(queries, dict):
                if not isinstance(queries, list) or not all(
                    isinstance(query, dict) for query in queries
                ):
                    raise ValueError("Invalid query file format")

            responses = run_queries(db, queries)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            filename = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_"
                f"{LAST_NAME}_{timestamp}.json"
            )

            response_path = Path(args.r) / filename

            with open(response_path, "w", encoding="utf-8") as file:
                json.dump(
                    responses, file, indent=2, ensure_ascii=False
                )

        return 0

    except (OSError, ValueError, TypeError, KeyError, OverflowError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
