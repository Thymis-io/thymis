# count which % of .md files in this directory tree have 10 or more words
import glob
import os
import re


# Color codes for flashy CLI output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_ascii_motivation(percentage):
    progress_bar_length = 20  # Total length of the progress bar
    filled_length = int(progress_bar_length * (percentage / 100))
    bar = f"{'#' * filled_length}{'-' * (progress_bar_length - filled_length)}"

    if percentage == 100:
        print(
            f"{Colors.OKGREEN}{Colors.BOLD}🎉 Perfect Score! All your docs are amazing! 🎉{Colors.ENDC}"
        )
    elif percentage >= 80:
        print(
            f"{Colors.OKGREEN}{Colors.BOLD}Amazing! Your docs are thriving!{Colors.ENDC}"
        )
    elif percentage >= 50:
        print(
            f"{Colors.OKCYAN}{Colors.BOLD}Good job! Keep pushing for more docs!{Colors.ENDC}"
        )
    else:
        print(
            f"{Colors.WARNING}{Colors.BOLD}Let's write more docs and boost that percentage!{Colors.ENDC}"
        )

    print(f"{Colors.HEADER}[{bar}] {percentage:.2f}%{Colors.ENDC}")


def count_docs_with_min_words(directory, min_words=10):
    count = 0
    total_files = 0
    filled_files = []
    unfilled_files = []

    # Use glob to find all .md files in the directory and subdirectories
    md_files = list(glob.glob(os.path.join(directory, "**", "*.md"), recursive=True))
    total_files = len(md_files)

    for idx, filepath in enumerate(md_files, start=1):
        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
                # Count words using regex to match word characters
                words = re.findall(r"\b\w+\b", content)
                if len(words) >= min_words:
                    count += 1
                    filled_files.append(filepath)
                else:
                    unfilled_files.append(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    print("\nFiles meeting the word count requirement:")
    for file in filled_files:
        print(f"  - {file}")

    print("\nFiles needing more words:")
    for file in unfilled_files:
        print(f"  - {file}")

    return count, total_files


if __name__ == "__main__":
    directory = os.path.dirname(os.path.abspath(__file__))
    min_words = 20  # Set the minimum number of words to check
    count, total_files = count_docs_with_min_words(directory, min_words)

    if total_files > 0:
        percentage = (count / total_files) * 100
        print_ascii_motivation(percentage)
        print(f"{Colors.HEADER}{Colors.BOLD}Docs Stats:{Colors.ENDC}")
        print(
            f"{Colors.OKBLUE}Total .md files: {Colors.BOLD}{total_files}{Colors.ENDC}"
        )
        print(
            f"{Colors.OKGREEN}Files with {min_words} or more words: {Colors.BOLD}{count}{Colors.ENDC}"
        )
        print(f"{Colors.OKCYAN}Percentage: {Colors.BOLD}{percentage:.2f}%{Colors.ENDC}")
    else:
        print(
            f"{Colors.FAIL}{Colors.BOLD}No .md files found in the directory.{Colors.ENDC}"
        )
        print(
            f"{Colors.WARNING}Percentage of .md files with {min_words} or more words: 0.00%{Colors.ENDC}"
        )
else:
    print(
        f"{Colors.FAIL}This script is intended to be run as a standalone program.{Colors.ENDC}"
    )
