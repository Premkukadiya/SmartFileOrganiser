"""
Report Generator for Smart File Organizer.

Generates summary reports in JSON, CSV, and HTML formats with
styled tables, charts, and comprehensive file analysis data.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("smart_organizer.reporter")


def generate_json_report(
    scan_summary: dict,
    duplicate_summary: Optional[dict] = None,
    metadata_list: Optional[list] = None,
    organize_results: Optional[dict] = None,
    output_path: str = "report.json",
) -> str:
    """
    Generate a comprehensive JSON report.

    Args:
        scan_summary: Scan results summary.
        duplicate_summary: Duplicate detection summary.
        metadata_list: List of extracted metadata dicts.
        organize_results: Organization results.
        output_path: Output file path.

    Returns:
        Path to the generated report.
    """
    report = {
        "report_metadata": {
            "generated_at": datetime.now().isoformat(),
            "tool": "Smart File Organizer v1.0.0",
            "report_type": "json",
        },
        "scan_summary": scan_summary,
    }

    if duplicate_summary:
        report["duplicate_summary"] = duplicate_summary
    if metadata_list:
        report["file_metadata"] = metadata_list
    if organize_results:
        report["organization_results"] = organize_results

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"JSON report generated: {output}")
    return str(output)


def generate_csv_report(
    scan_summary: dict,
    duplicate_summary: Optional[dict] = None,
    output_path: str = "report.csv",
) -> str:
    """
    Generate a CSV report with file listings.

    Args:
        scan_summary: Scan results summary.
        duplicate_summary: Duplicate detection summary.
        output_path: Output file path.

    Returns:
        Path to the generated report.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Summary section
        writer.writerow(["SCAN SUMMARY"])
        writer.writerow(["Total Files", scan_summary.get("total_files", 0)])
        writer.writerow(["Total Size", scan_summary.get("total_size_human", "0 B")])
        writer.writerow([])

        # Category breakdown
        writer.writerow(["CATEGORY BREAKDOWN"])
        writer.writerow(["Category", "Count", "Size"])
        for cat, data in scan_summary.get("categories", {}).items():
            writer.writerow([cat, data.get("count", 0), data.get("size_human", "0 B")])
        writer.writerow([])

        # Extension counts
        writer.writerow(["EXTENSION COUNTS"])
        writer.writerow(["Extension", "Count"])
        for ext, count in scan_summary.get("extension_counts", {}).items():
            writer.writerow([ext, count])
        writer.writerow([])

        # Duplicate summary
        if duplicate_summary:
            writer.writerow(["DUPLICATE SUMMARY"])
            writer.writerow(["Duplicate Groups", duplicate_summary.get("total_duplicate_groups", 0)])
            writer.writerow(["Duplicate Files", duplicate_summary.get("total_duplicate_files", 0)])
            writer.writerow(["Space Recoverable", duplicate_summary.get("total_space_recoverable_human", "0 B")])

    logger.info(f"CSV report generated: {output}")
    return str(output)


def generate_html_report(
    scan_summary: dict,
    duplicate_summary: Optional[dict] = None,
    metadata_list: Optional[list] = None,
    organize_results: Optional[dict] = None,
    output_path: str = "report.html",
) -> str:
    """
    Generate a beautiful, styled HTML report.

    Args:
        scan_summary: Scan results summary.
        duplicate_summary: Duplicate detection summary.
        metadata_list: List of extracted metadata dicts.
        organize_results: Organization results.
        output_path: Output file path.

    Returns:
        Path to the generated report.
    """
    total_files = scan_summary.get("total_files", 0)
    total_size = scan_summary.get("total_size_human", "0 B")
    categories = scan_summary.get("categories", {})
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Category colors
    cat_colors = {
        "Documents": "#3b82f6", "Images": "#a855f7", "Code": "#22c55e",
        "Archives": "#f59e0b", "Media": "#ef4444", "Data": "#06b6d4", "Other": "#6b7280",
    }

    # Build category rows
    cat_rows = ""
    cat_bars = ""
    max_count = max((d.get("count", 0) for d in categories.values()), default=1)

    for cat, data in sorted(categories.items(), key=lambda x: x[1].get("count", 0), reverse=True):
        color = cat_colors.get(cat, "#6b7280")
        count = data.get("count", 0)
        size = data.get("size_human", "0 B")
        pct = round(count / total_files * 100, 1) if total_files > 0 else 0
        bar_width = round(count / max_count * 100) if max_count > 0 else 0

        cat_rows += f"""
            <tr>
                <td><span class="badge" style="background:{color}">{cat}</span></td>
                <td>{count}</td>
                <td>{size}</td>
                <td>{pct}%</td>
            </tr>"""

        cat_bars += f"""
            <div class="bar-row">
                <span class="bar-label">{cat}</span>
                <div class="bar-track">
                    <div class="bar-fill" style="width:{bar_width}%;background:{color}"></div>
                </div>
                <span class="bar-value">{count}</span>
            </div>"""

    # Duplicate section
    dup_section = ""
    if duplicate_summary and duplicate_summary.get("total_duplicate_groups", 0) > 0:
        dup_section = f"""
        <div class="section">
            <h2>🔍 Duplicate Files</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" style="color:#ef4444">{duplicate_summary.get('total_duplicate_groups', 0)}</div>
                    <div class="stat-label">Duplicate Groups</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#f59e0b">{duplicate_summary.get('total_duplicate_files', 0)}</div>
                    <div class="stat-label">Duplicate Files</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#22c55e">{duplicate_summary.get('total_space_recoverable_human', '0 B')}</div>
                    <div class="stat-label">Space Recoverable</div>
                </div>
            </div>
        </div>"""

    # Metadata section
    meta_section = ""
    if metadata_list:
        meta_rows = ""
        for meta in metadata_list:
            mtype = meta.get("type", "unknown")
            detail = ""
            if mtype == "csv":
                detail = f"Rows: {meta.get('row_count', 'N/A')}, Cols: {meta.get('column_count', 'N/A')}"
            elif mtype == "image":
                detail = f"{meta.get('dimensions', 'N/A')}, {meta.get('format', 'N/A')}"
            elif mtype == "text":
                detail = f"Lines: {meta.get('line_count', 'N/A')}, Words: {meta.get('word_count', 'N/A')}"

            meta_rows += f"""
                <tr>
                    <td>{meta.get('filename', 'N/A')}</td>
                    <td><span class="badge" style="background:#6366f1">{mtype}</span></td>
                    <td>{meta.get('file_size_human', 'N/A')}</td>
                    <td>{detail}</td>
                </tr>"""

        meta_section = f"""
        <div class="section">
            <h2>📋 File Metadata</h2>
            <table>
                <thead><tr><th>File</th><th>Type</th><th>Size</th><th>Details</th></tr></thead>
                <tbody>{meta_rows}</tbody>
            </table>
        </div>"""

    # Organization section
    org_section = ""
    if organize_results:
        org_section = f"""
        <div class="section">
            <h2>📂 Organization Results</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" style="color:#22c55e">{organize_results.get('processed', 0)}</div>
                    <div class="stat-label">Files Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#f59e0b">{organize_results.get('skipped', 0)}</div>
                    <div class="stat-label">Files Skipped</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#ef4444">{organize_results.get('errors', 0)}</div>
                    <div class="stat-label">Errors</div>
                </div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Smart File Organizer Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(168,85,247,0.15));
            border-radius: 20px;
            border: 1px solid rgba(99,102,241,0.2);
            margin-bottom: 2rem;
        }}
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00ffff, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}
        .header .subtitle {{ color: #94a3b8; font-size: 0.95rem; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin: 1.5rem 0;
        }}
        .stat-card {{
            background: rgba(30,30,60,0.6);
            border: 1px solid rgba(99,102,241,0.15);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: 700;
            color: #00ffff;
        }}
        .stat-label {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin-top: 0.3rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .section {{
            background: rgba(20,20,45,0.5);
            border: 1px solid rgba(99,102,241,0.1);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
        }}
        .section h2 {{
            font-size: 1.3rem;
            margin-bottom: 1.2rem;
            color: #c4b5fd;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 0.8rem 1rem;
            background: rgba(99,102,241,0.1);
            color: #a5b4fc;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        th:first-child {{ border-radius: 8px 0 0 8px; }}
        th:last-child {{ border-radius: 0 8px 8px 0; }}
        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid rgba(99,102,241,0.08);
            font-size: 0.9rem;
        }}
        tr:hover td {{ background: rgba(99,102,241,0.05); }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            color: white;
        }}
        .bar-row {{
            display: flex;
            align-items: center;
            margin-bottom: 0.7rem;
            gap: 1rem;
        }}
        .bar-label {{
            min-width: 100px;
            font-size: 0.85rem;
            color: #cbd5e1;
        }}
        .bar-track {{
            flex: 1;
            height: 24px;
            background: rgba(30,30,60,0.8);
            border-radius: 12px;
            overflow: hidden;
        }}
        .bar-fill {{
            height: 100%;
            border-radius: 12px;
            transition: width 0.6s ease;
            min-width: 4px;
        }}
        .bar-value {{
            min-width: 40px;
            text-align: right;
            font-weight: 600;
            font-size: 0.9rem;
            color: #e2e8f0;
        }}
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #64748b;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 Smart File Organizer</h1>
            <p class="subtitle">Analysis Report • {timestamp}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_files}</div>
                <div class="stat-label">Total Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_size}</div>
                <div class="stat-label">Total Size</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(categories)}</div>
                <div class="stat-label">Categories</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(scan_summary.get('extension_counts', {}))}</div>
                <div class="stat-label">Extensions</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Category Breakdown</h2>
            <table>
                <thead>
                    <tr><th>Category</th><th>Count</th><th>Size</th><th>Share</th></tr>
                </thead>
                <tbody>{cat_rows}</tbody>
            </table>
        </div>

        <div class="section">
            <h2>📈 Distribution Chart</h2>
            {cat_bars}
        </div>

        {dup_section}
        {meta_section}
        {org_section}

        <div class="footer">
            Generated by Smart File Organizer v1.0.0 • {timestamp}
        </div>
    </div>
</body>
</html>"""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"HTML report generated: {output}")
    return str(output)


def generate_report(
    scan_summary: dict,
    duplicate_summary: Optional[dict] = None,
    metadata_list: Optional[list] = None,
    organize_results: Optional[dict] = None,
    format: str = "json",
    output_path: Optional[str] = None,
) -> str:
    """
    Generate a report in the specified format.

    Args:
        scan_summary: Scan results summary.
        duplicate_summary: Duplicate detection summary.
        metadata_list: List of extracted metadata dicts.
        organize_results: Organization results.
        format: Report format ('json', 'csv', or 'html').
        output_path: Output file path (auto-generated if None).

    Returns:
        Path to the generated report.
    """
    if output_path is None:
        output_path = f"report.{format}"

    if format == "json":
        return generate_json_report(scan_summary, duplicate_summary,
                                    metadata_list, organize_results, output_path)
    elif format == "csv":
        return generate_csv_report(scan_summary, duplicate_summary, output_path)
    elif format == "html":
        return generate_html_report(scan_summary, duplicate_summary,
                                    metadata_list, organize_results, output_path)
    else:
        logger.error(f"Unsupported report format: {format}")
        raise ValueError(f"Unsupported format: {format}. Use 'json', 'csv', or 'html'.")
