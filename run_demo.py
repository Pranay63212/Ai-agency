"""Run the unsold-estimate recovery demo.

    python run_demo.py --mock                      # no API key needed
    python run_demo.py                             # writes messages with Claude
    python run_demo.py --input client.csv --business "Cool Air HVAC" --sender Mike --phone "(214) 555-0100"
"""

import argparse
import csv
import os

from estimate_recovery.clean import clean, load_csv
from estimate_recovery.messages import write_all
from estimate_recovery.report import build_report

OUTPUT_FIELDS = [
    "customer_name", "phone", "email", "channels", "job_type", "quote_amount", "quote_date",
    "day_1_text", "day_4_email_subject", "day_4_email_body", "day_10_text",
]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default="sample_data/hvac_unsold_estimates.csv")
    p.add_argument("--out-dir", default="output")
    p.add_argument("--business", default="Comfort Pro HVAC")
    p.add_argument("--trade", default="HVAC")
    p.add_argument("--sender", default="Mike")
    p.add_argument("--phone", default="(214) 555-0100")
    p.add_argument("--close-rate", type=float, default=0.08, help="share of contacts expected to book")
    p.add_argument("--mock", action="store_true", help="use template messages instead of Claude")
    args = p.parse_args()

    business = {"name": args.business, "trade": args.trade, "sender": args.sender, "phone": args.phone}
    os.makedirs(args.out_dir, exist_ok=True)

    rows = load_csv(args.input)
    cleaned = clean(rows)
    print(f"Loaded {len(rows)} estimates: {len(cleaned.contacts)} ready, {len(cleaned.removed)} removed.")

    print("Writing follow-up messages...")
    contacts = write_all(cleaned.contacts, business, mock=args.mock)

    csv_path = os.path.join(args.out_dir, "follow_up_messages.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(contacts)

    report_path = os.path.join(args.out_dir, "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(build_report(contacts, cleaned.removed, business, args.close_rate, args.mock))

    print(f"Done.\n  Messages: {csv_path}\n  Report:   {report_path}")


if __name__ == "__main__":
    main()
