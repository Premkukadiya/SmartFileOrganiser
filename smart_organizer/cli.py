"""
CLI Interface for Smart File Organizer.

Built with Click, provides commands for scanning, organizing,
deduplicating, reporting, and undoing file operations.
"""

import sys
import logging
from pathlib import Path

import click

from . import __version__
from .config import load_config
from .scanner import scan_directory, get_scan_summary, print_scan_summary
from .deduplicator import find_duplicates, get_duplicate_summary, remove_duplicates, print_duplicate_report
from .organizer import organize_files, undo_organize, print_organize_summary
from .extractor import extract_metadata, print_extraction_summary
from .reporter import generate_report
from .utils import setup_logging

logger = logging.getLogger("smart_organizer.cli")

BANNER = """
+------------------------------------------------------+
|        Smart File Organizer v{version}               |
|    Scan - Organize - Deduplicate - Report            |
+------------------------------------------------------+
""".format(version=__version__)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="Smart File Organizer")
@click.pass_context
def cli(ctx):
    """Smart File Organizer - Automated file scanning, organization, and reporting."""
    if ctx.invoked_subcommand is None:
        click.echo(click.style(BANNER, fg="cyan"))
        click.echo("Use --help to see available commands.\n")
        click.echo("Commands:")
        click.echo(click.style("  scan     ", fg="green") + "Scan and classify files in a directory")
        click.echo(click.style("  organize ", fg="green") + "Organize files into structured folders")
        click.echo(click.style("  dedupe   ", fg="green") + "Find and remove duplicate files")
        click.echo(click.style("  report   ", fg="green") + "Generate analysis reports")
        click.echo(click.style("  undo     ", fg="green") + "Undo the last organize operation")
        click.echo()


@cli.command()
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="Target directory to scan.")
@click.option("--recursive/--no-recursive", default=True,
              help="Scan subdirectories recursively.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose debug output.")
@click.option("--config", "-c", type=click.Path(), default=None,
              help="Path to config YAML file.")
def scan(path: str, recursive: bool, verbose: bool, config: str):
    """Scan a directory and classify all files by type."""
    click.echo(click.style(BANNER, fg="cyan"))
    click.echo(click.style("[*] SCANNING FILES...\n", fg="yellow", bold=True))

    cfg = load_config(config)
    setup_logging(cfg.get("log_file", "organizer.log"), verbose)

    try:
        files = scan_directory(path, cfg, recursive)
        summary = get_scan_summary(files)
        print_scan_summary(summary)

        click.echo(click.style(f"[OK] Scan complete! Found {len(files)} files.", fg="green", bold=True))
    except (FileNotFoundError, NotADirectoryError) as e:
        click.echo(click.style(f"[ERROR] {e}", fg="red", bold=True))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"[ERROR] Unexpected error: {e}", fg="red", bold=True))
        logger.exception("Scan failed")
        sys.exit(1)


@cli.command()
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="Target directory to organize.")
@click.option("--output", "-o", default="Organized",
              help="Output directory for organized files.")
@click.option("--pattern", default="{date}_{original}",
              help="Rename pattern: {date}, {original}, {counter}.")
@click.option("--mode", type=click.Choice(["copy", "move"]), default="copy",
              help="Copy or move files.")
@click.option("--dry-run/--execute", default=True,
              help="Dry run (default) or execute changes.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose debug output.")
@click.option("--config", "-c", type=click.Path(), default=None,
              help="Path to config YAML file.")
def organize(path: str, output: str, pattern: str, mode: str,
             dry_run: bool, verbose: bool, config: str):
    """Organize files into a structured folder layout."""
    click.echo(click.style(BANNER, fg="cyan"))

    if dry_run:
        click.echo(click.style("[DRY RUN] No files will be moved\n", fg="yellow", bold=True))
    else:
        click.echo(click.style("[EXECUTE] Files will be organized\n", fg="red", bold=True))

    cfg = load_config(config)
    setup_logging(cfg.get("log_file", "organizer.log"), verbose)

    try:
        # Scan first
        click.echo(click.style("Step 1: Scanning files...", fg="cyan"))
        files = scan_directory(path, cfg)
        click.echo(click.style(f"  Found {len(files)} files\n", fg="green"))

        # Organize
        click.echo(click.style("Step 2: Organizing files...", fg="cyan"))
        results = organize_files(files, output, pattern, mode, dry_run)
        print_organize_summary(results, dry_run)

        if dry_run:
            click.echo(click.style("[TIP] Run with --execute to apply changes.", fg="yellow"))
        else:
            click.echo(click.style(f"[OK] Done! {results['processed']} files organized.", fg="green", bold=True))

    except Exception as e:
        click.echo(click.style(f"[ERROR] {e}", fg="red", bold=True))
        logger.exception("Organize failed")
        sys.exit(1)


@cli.command()
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="Target directory to scan for duplicates.")
@click.option("--dry-run/--execute", default=True,
              help="Dry run (default) or delete duplicates.")
@click.option("--keep", type=click.Choice(["oldest", "newest"]), default="oldest",
              help="Which duplicate to keep.")
@click.option("--algorithm", type=click.Choice(["sha256", "md5"]), default="sha256",
              help="Hash algorithm for comparison.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose debug output.")
@click.option("--config", "-c", type=click.Path(), default=None,
              help="Path to config YAML file.")
def dedupe(path: str, dry_run: bool, keep: str, algorithm: str,
           verbose: bool, config: str):
    """Find and optionally remove duplicate files."""
    click.echo(click.style(BANNER, fg="cyan"))
    click.echo(click.style("[*] DUPLICATE DETECTION\n", fg="yellow", bold=True))

    cfg = load_config(config)
    setup_logging(cfg.get("log_file", "organizer.log"), verbose)

    try:
        # Scan
        click.echo(click.style("Step 1: Scanning files...", fg="cyan"))
        files = scan_directory(path, cfg)
        click.echo(click.style(f"  Found {len(files)} files\n", fg="green"))

        # Find duplicates
        click.echo(click.style("Step 2: Computing hashes...", fg="cyan"))
        duplicates = find_duplicates(files, algorithm)
        summary = get_duplicate_summary(duplicates)
        print_duplicate_report(duplicates, summary)

        if not duplicates:
            click.echo(click.style("[OK] No duplicates found!", fg="green", bold=True))
            return

        # Remove duplicates
        if dry_run:
            click.echo(click.style("Step 3: Dry run — showing what would be deleted...", fg="cyan"))
        else:
            click.echo(click.style("Step 3: Removing duplicates...", fg="red"))

        deleted = remove_duplicates(duplicates, dry_run, keep)
        click.echo()

        if dry_run:
            click.echo(click.style(f"[TIP] {len(deleted)} files would be deleted. "
                                   f"Run with --execute to delete.", fg="yellow"))
        else:
            click.echo(click.style(f"[OK] Deleted {len(deleted)} duplicate files. "
                                   f"Saved {summary['total_space_recoverable_human']}!", fg="green", bold=True))

    except Exception as e:
        click.echo(click.style(f"[ERROR] {e}", fg="red", bold=True))
        logger.exception("Dedupe failed")
        sys.exit(1)


@cli.command()
@click.option("--path", "-p", required=True, type=click.Path(exists=True),
              help="Target directory to analyze.")
@click.option("--format", "-f", "report_format",
              type=click.Choice(["json", "csv", "html"]), default="json",
              help="Report output format.")
@click.option("--output", "-o", default=None,
              help="Output file path.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose debug output.")
@click.option("--config", "-c", type=click.Path(), default=None,
              help="Path to config YAML file.")
def report(path: str, report_format: str, output: str,
           verbose: bool, config: str):
    """Generate a comprehensive analysis report."""
    click.echo(click.style(BANNER, fg="cyan"))
    click.echo(click.style(f"[*] GENERATING {report_format.upper()} REPORT\n", fg="yellow", bold=True))

    cfg = load_config(config)
    setup_logging(cfg.get("log_file", "organizer.log"), verbose)

    try:
        # Scan
        click.echo(click.style("Step 1: Scanning files...", fg="cyan"))
        files = scan_directory(path, cfg)
        scan_summary = get_scan_summary(files)
        click.echo(click.style(f"  Found {len(files)} files\n", fg="green"))

        # Find duplicates
        click.echo(click.style("Step 2: Detecting duplicates...", fg="cyan"))
        duplicates = find_duplicates(files, cfg.get("hash_algorithm", "sha256"))
        dup_summary = get_duplicate_summary(duplicates)
        click.echo(click.style(f"  Found {dup_summary['total_duplicate_groups']} duplicate groups\n", fg="green"))

        # Extract metadata
        click.echo(click.style("Step 3: Extracting metadata...", fg="cyan"))
        metadata_list = []
        extractable = [f for f in files if f.category in ("Data", "Images", "Documents", "Code")]
        for file_info in extractable[:20]:  # Limit to 20 files for report
            try:
                meta = extract_metadata(file_info.path, file_info.category)
                metadata_list.append(meta)
            except Exception as e:
                logger.warning(f"Could not extract metadata from {file_info.name}: {e}")
        click.echo(click.style(f"  Extracted metadata from {len(metadata_list)} files\n", fg="green"))

        # Generate report
        click.echo(click.style("Step 4: Generating report...", fg="cyan"))
        report_path = generate_report(
            scan_summary, dup_summary, metadata_list,
            format=report_format, output_path=output,
        )
        click.echo()
        click.echo(click.style(f"[OK] Report generated: {report_path}", fg="green", bold=True))

        if report_format == "html":
            click.echo(click.style(f"   Open in browser: file:///{Path(report_path).resolve()}", fg="cyan"))

    except Exception as e:
        click.echo(click.style(f"[ERROR] {e}", fg="red", bold=True))
        logger.exception("Report generation failed")
        sys.exit(1)


@cli.command()
@click.option("--manifest", "-m", default="Organized/manifest.json",
              help="Path to the manifest.json file.")
def undo(manifest: str):
    """Undo the last organize operation."""
    click.echo(click.style(BANNER, fg="cyan"))
    click.echo(click.style("[*] UNDOING LAST ORGANIZE OPERATION\n", fg="yellow", bold=True))

    setup_logging()

    try:
        manifest_path = Path(manifest)
        if not manifest_path.exists():
            click.echo(click.style(f"[ERROR] Manifest not found: {manifest}", fg="red"))
            click.echo(click.style("   No organize operation to undo.", fg="yellow"))
            sys.exit(1)

        results = undo_organize(manifest)

        click.echo()
        click.echo(click.style(f"  Restored: {results['restored']} files", fg="green"))
        click.echo(click.style(f"  Errors:   {results['errors']}", fg="red" if results['errors'] else "green"))

        if results['restored'] > 0:
            click.echo()
            click.echo(click.style("[OK] Undo complete!", fg="green", bold=True))
        else:
            click.echo()
            click.echo(click.style("[WARN] No files were restored.", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"[ERROR] {e}", fg="red", bold=True))
        logger.exception("Undo failed")
        sys.exit(1)


if __name__ == "__main__":
    cli()
