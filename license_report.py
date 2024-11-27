from pathlib import Path
from collections import defaultdict
from typing import Dict, List, NamedTuple
from dataclasses import dataclass


@dataclass
class DirectoryStats:
    with_license: List[Path] = None
    without_license: List[Path] = None
    extension_counts: Dict[str, int] = None
    lines_by_extension: Dict[str, Dict[str, int]] = (
        None  # ext -> {'with': lines, 'without': lines}
    )
    subdirs: Dict[Path, "DirectoryStats"] = None

    def __post_init__(self):
        self.with_license = []
        self.without_license = []
        self.extension_counts = defaultdict(int)
        self.lines_by_extension = defaultdict(lambda: {"with": 0, "without": 0})
        self.subdirs = {}

    def aggregate_stats(self):
        """Return aggregated stats including all subdirectories."""
        total_with = self.with_license.copy()
        total_without = self.without_license.copy()
        total_extensions = defaultdict(int, self.extension_counts)
        total_lines = defaultdict(lambda: {"with": 0, "without": 0})

        # Add current directory's lines
        for ext, counts in self.lines_by_extension.items():
            total_lines[ext]["with"] += counts["with"]
            total_lines[ext]["without"] += counts["without"]

        # Add subdirectories' lines
        for subdir_stats in self.subdirs.values():
            sub_with, sub_without, sub_extensions, sub_lines = (
                subdir_stats.aggregate_stats()
            )
            total_with.extend(sub_with)
            total_without.extend(sub_without)
            for ext, count in sub_extensions.items():
                total_extensions[ext] += count
            for ext, counts in sub_lines.items():
                total_lines[ext]["with"] += counts["with"]
                total_lines[ext]["without"] += counts["without"]

        return total_with, total_without, total_extensions, total_lines


def count_lines(file_path: Path) -> int:
    """Count number of lines in a file, skipping empty lines."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except (UnicodeDecodeError, IOError):
        return 0


def find_files_missing_license(
    root_dir=".", exclude_dirs=None, exclude_file_types=None
):
    """Find files that don't contain both MIT and Sundsvall license text."""
    LICENSE_TEXTS = [
        ["MIT license", "MIT License"],
        ["Sundsvalls Kommun", "Sundsvalls kommun"],
    ]
    stats_by_dir = {}
    root_path = Path(root_dir)

    # Create DirectoryStats objects for all directories
    for path in root_path.rglob("*"):
        if path.is_dir():
            if exclude_dirs and any(
                excluded in path.parts for excluded in exclude_dirs
            ):
                continue
            stats_by_dir[path] = DirectoryStats()
            if path.parent in stats_by_dir:
                stats_by_dir[path.parent].subdirs[path] = stats_by_dir[path]

    # Add root directory if not already present
    if root_path not in stats_by_dir:
        stats_by_dir[root_path] = DirectoryStats()

    # Process all files
    for file_path in root_path.rglob("*"):
        if file_path.is_dir():
            continue
        if exclude_dirs and any(
            excluded in file_path.parts for excluded in exclude_dirs
        ):
            continue
        if exclude_file_types and any(
            file_path.name.endswith(ext) for ext in exclude_file_types
        ):
            continue

        dir_path = file_path.parent
        extension = file_path.suffix or "no_extension"
        stats_by_dir[dir_path].extension_counts[extension] += 1

        try:
            if file_path.stat().st_size > 1_000_000:  # Skip files larger than 1MB
                continue

            line_count = count_lines(file_path)
            with file_path.open("r", encoding="utf-8") as f:
                content = f.read()
                has_all_licenses = all(
                    any(text in content for text in license_texts)
                    for license_texts in LICENSE_TEXTS
                )
                if has_all_licenses:
                    stats_by_dir[dir_path].with_license.append(file_path)
                    stats_by_dir[dir_path].lines_by_extension[extension]["with"] += (
                        line_count
                    )
                else:
                    stats_by_dir[dir_path].without_license.append(file_path)
                    stats_by_dir[dir_path].lines_by_extension[extension]["without"] += (
                        line_count
                    )
        except (UnicodeDecodeError, IOError):
            continue

    return stats_by_dir


def print_directory_report(stats_by_dir, min_total_lines=0):
    """Print a formatted report of directory statistics."""
    # Keep track of printed directories to avoid printing subdirs of 0% or 100% coverage dirs
    zero_coverage_dirs = set()
    full_coverage_dirs = set()
    
    for dir_path, stats in sorted(stats_by_dir.items()):
        with_license, without_license, extension_counts, lines_by_ext = stats.aggregate_stats()
        
        # Skip if this is a subdirectory of an already printed 0% or 100% coverage directory
        parent = dir_path.parent
        if any(parent.is_relative_to(d) for d in zero_coverage_dirs) or \
           any(parent.is_relative_to(d) for d in full_coverage_dirs):
            continue

        # Calculate total lines
        total_lines = sum(
            lines_by_ext[ext]['with'] + lines_by_ext[ext]['without']
            for ext in lines_by_ext
        )
        
        # Skip directories with fewer lines than minimum
        if total_lines < min_total_lines:
            continue
        
        # Skip empty directories
        if not (with_license or without_license):
            continue

        print(f"\n{dir_path}/")
        
        # Print table header
        print("  {:<10} {:>8} {:>10} {:>8} {:>12} {:>12} {:>8}".format(
            "Extension", "MIT", "Total", "Files%", "MIT Lines", "Tot Lines", "Lines%"
        ))
        print("  " + "-" * 70)

        total_lines_covered = 0
        total_lines = 0
        
        for ext in sorted(extension_counts.keys()):
            with_count = sum(1 for f in with_license if f.suffix == ext or (not f.suffix and ext == 'no_extension'))
            total = extension_counts[ext]
            files_coverage = (with_count / total * 100) if total > 0 else 0
            
            lines_with = lines_by_ext[ext]['with']
            lines_without = lines_by_ext[ext]['without']
            total_ext_lines = lines_with + lines_without
            lines_coverage = (lines_with / total_ext_lines * 100) if total_ext_lines > 0 else 0
            
            total_lines_covered += lines_with
            total_lines += total_ext_lines
            
            print("  {:<10} {:>8} {:>10} {:>7.1f}% {:>12} {:>12} {:>7.1f}%".format(
                ext, with_count, total, files_coverage,
                lines_with, total_ext_lines, lines_coverage
            ))

        # Print totals
        print("  " + "-" * 70)
        total_files_coverage = (len(with_license) / (len(with_license) + len(without_license)) * 100) if (len(with_license) + len(without_license)) > 0 else 0
        total_lines_coverage = (total_lines_covered / total_lines * 100) if total_lines > 0 else 0
        print("  {:<10} {:>8} {:>10} {:>7.1f}% {:>12} {:>12} {:>7.1f}%".format(
            "Total", len(with_license), len(with_license) + len(without_license),
            total_files_coverage, total_lines_covered, total_lines, total_lines_coverage
        ))

        # Track directories with 0% or 100% coverage to skip their subdirectories
        if total_lines_coverage == 0:
            zero_coverage_dirs.add(dir_path)
        elif total_lines_coverage == 100:
            full_coverage_dirs.add(dir_path)


if __name__ == "__main__":
    exclude_dirs = ["node_modules", "venv", ".git"]
    exclude_file_types = [".png", ".jpg", ".woff2", ".md"]

    stats = find_files_missing_license(
        exclude_dirs=exclude_dirs,
        exclude_file_types=exclude_file_types,
    )

    print_directory_report(stats, min_total_lines=1000)
