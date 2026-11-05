import os
import sys
import csv
from collections import Counter

def inspect_dataset(file_path: str):
    print("=" * 70)
    print(f"INSPECTING KCC DATASET: {file_path}")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"File Size: {file_size_mb:.2f} MB")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print("Error: Empty file.")
            return

        print(f"Total Columns ({len(headers)}):")
        for idx, h in enumerate(headers):
            print(f"  {idx+1:2d}. {h}")

        row_count = 0
        null_counts = [0] * len(headers)
        column_values = [Counter() for _ in headers]
        sample_rows = []

        for row in reader:
            row_count += 1
            if len(sample_rows) < 5:
                sample_rows.append(row)

            for i, val in enumerate(row):
                if i < len(headers):
                    val_str = val.strip()
                    if not val_str or val_str.lower() in ("nan", "null", "none", "na", ""):
                        null_counts[i] += 1
                    else:
                        if len(column_values[i]) < 1000:
                            column_values[i][val_str] += 1

    print(f"\nTotal Rows Counted: {row_count:,}")
    print("\nColumn Null Counts & Top Values:")
    for i, h in enumerate(headers):
        null_pct = (null_counts[i] / row_count * 100) if row_count > 0 else 0
        print(f"\n[{i+1}] {h}")
        print(f"    Missing: {null_counts[i]:,} / {row_count:,} ({null_pct:.1f}%)")
        print(f"    Unique Sample Values ({len(column_values[i])}):")
        for val, cnt in column_values[i].most_common(5):
            print(f"      - {val[:60]}: {cnt:,}")

    print("\n" + "=" * 70)
    print("SAMPLE RECORD 1 (FULL DETAIL):")
    print("=" * 70)
    if sample_rows:
        for h, v in zip(headers, sample_rows[0]):
            print(f"{h}: {v}")

    print("\n" + "=" * 70)
    print("SAMPLE RECORD 2 (FULL DETAIL):")
    print("=" * 70)
    if len(sample_rows) > 1:
        for h, v in zip(headers, sample_rows[1]):
            print(f"{h}: {v}")

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/original/kcc_dataset.csv"
    inspect_dataset(path)
