import os
import sys
import shutil
from glob import glob


def ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)


def find_first(patterns):
    for pattern in patterns:
        matches = glob(pattern)
        if matches:
            # Prefer the shortest filename match (usually correct part)
            matches.sort(key=lambda p: (len(os.path.basename(p)), p))
            return matches[0]
    return None


def main():
    # Build default source root using path join to avoid escaping issues
    default_src_root = os.path.join(
        'F:\\TOEIC Coach',
        'Content',
        "[sachtoeic.com]Jim's Toeic LC Audio",
    )

    src_root = sys.argv[1] if len(sys.argv) > 1 else default_src_root
    if not os.path.isdir(src_root):
        print(f"Source directory not found: {src_root}")
        sys.exit(1)

    dest_dir = os.path.join('static', 'audio')
    ensure_dir(dest_dir)

    expected = {
        'Part 1': 'part1_sample.mp3',
        'Part 2': 'part2_sample.mp3',
        'Part 3': 'part3_sample.mp3',
        'Part 4': 'part4_sample.mp3',
    }

    # Prefer TEST 01 files; fall back to any part file if TEST 01 not found
    results = {}
    for part_label, dest_name in expected.items():
        patterns = [
            os.path.join(src_root, f"*TEST 01*{part_label}*.mp3"),
            os.path.join(src_root, f"*Test 01*{part_label}*.mp3"),
            os.path.join(src_root, f"*TEST*{part_label}*.mp3"),
            os.path.join(src_root, f"*{part_label}*.mp3"),
        ]
        src_path = find_first(patterns)
        if not src_path:
            print(f"No file found for {part_label} using patterns: {patterns}")
            continue
        dest_path = os.path.join(dest_dir, dest_name)
        shutil.copy2(src_path, dest_path)
        results[part_label] = (src_path, dest_path)

    if not results:
        print("No audio files were copied.")
        sys.exit(2)

    print("Copied:")
    for part_label, (src, dest) in results.items():
        print(f"- {part_label}: {src} -> {dest}")


if __name__ == '__main__':
    main() 