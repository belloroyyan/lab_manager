import sys

def progress_bar(current, total, bar_len=30, extra=""):
    if total == 0:
        return

    percent = current / total
    filled = int(bar_len * percent)
    bar = "#" * filled + "-" * (bar_len - filled)

    sys.stdout.write(f"\r[{bar}] {percent*100:.1f}% {extra}")
    sys.stdout.flush()

    if current == total:
        print()