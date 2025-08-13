import os
import re
import sys
from pathlib import Path


def parse_summary(summary_path):
    """Parse SUMMARY.md and extract linked markdown file paths"""
    pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    found_paths = set()
    ordered_paths = []

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    rel_path = match.group(1).strip()
                    if rel_path == "SUMMARY.md":  # Skip self-reference
                        continue
                    norm_path = Path(rel_path).resolve()
                    if norm_path not in found_paths:
                        found_paths.add(norm_path)
                        ordered_paths.append(norm_path)
    except FileNotFoundError:
        sys.stderr.write(f"Warning: SUMMARY.md not found. Proceeding without order.\n")

    return ordered_paths


def find_md_files(root_path):
    """Find all .md files recursively, returning absolute paths"""
    md_files = []
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith(".md"):
                full_path = Path(root) / file
                md_files.append(full_path.resolve())
    return md_files


def main():
    root_dir = Path.cwd()
    summary_file = root_dir / "SUMMARY.md"

    # Find and classify files
    all_md = find_md_files(root_dir)
    ordered = parse_summary(summary_file)
    summary_absolute = summary_file.resolve()

    # Split files into ordered, unordered, and summary
    ordered_set = set(ordered)
    all_md_set = set(all_md)

    final_ordered = [f for f in ordered if f in all_md_set]
    unordered = [f for f in all_md if f not in ordered_set and f != summary_absolute]
    final_ordered += sorted(unordered)

    # Process files in the determined order
    for path in final_ordered:
        print(f"## {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                print(f.read())
        except Exception as e:
            sys.stderr.write(f"Error reading {path}: {str(e)}\n")

    # Always process SUMMARY.md last
    if summary_absolute in all_md_set:
        print(f"## {summary_absolute}")
        print(open(summary_absolute, "r", encoding="utf-8").read())


if __name__ == "__main__":
    main()
