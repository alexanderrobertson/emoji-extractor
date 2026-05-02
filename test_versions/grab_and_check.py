import concurrent.futures
import re
import requests
import time
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.panel import Panel
from rich import print as rprint

# Configuration
BASE_URL = 'https://unicode.org/Public/emoji/{version}/emoji-test.txt'
UNICODE_VERSIONS = [
    "4.0", "5.0", "11.0", "12.0", "12.1", "13.0", "13.1", 
    "14.0", "15.0", "15.1", "16.0"
]

console = Console()

def fetch_file(version):
    url = BASE_URL.format(version=version)
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return version, response.text
    except Exception as e:
        return version, f"Error: {e}"

def parse_emoji_test(content):
    """Parses emoji-test.txt format (Version 4.0+)"""
    emoji = {}
    current_group = "None"
    current_subgroup = "None"
    
    for line in content.splitlines():
        line = line.strip()
        if not line: continue
        
        if line.startswith("# group:"):
            current_group = line.split(":", 1)[1].strip()
            continue
        if line.startswith("# subgroup:"):
            current_subgroup = line.split(":", 1)[1].strip()
            continue
        if line.startswith("#") and not line.startswith("# Version:"):
            continue
            
        if ";" in line and "#" in line:
            parts = line.split(";", 1)
            codepoints = parts[0].strip()
            # Normalize codepoints (some versions have extra spaces)
            codepoints = " ".join(codepoints.split())
            
            rest = parts[1].split("#", 1)
            status = rest[0].strip()
            
            # The part after # usually starts with emoji char then version then name
            # Example: 😀 E1.0 grinning face
            comment = rest[1].strip()
            # Regex to match Version then Name
            match = re.search(r'E\d+\.\d+\s+(.*)', comment)
            if match:
                name = match.group(1).strip()
            else:
                name = comment # Fallback
                
            emoji[codepoints] = {
                "status": status,
                "name": name,
                "group": current_group,
                "subgroup": current_subgroup,
                "raw_line": line
            }
    return emoji

def compare_versions(v1_name, v1_data, v2_name, v2_data):
    added = []
    removed = []
    changed = []
    
    v1_keys = set(v1_data.keys())
    v2_keys = set(v2_data.keys())
    
    # Added
    for k in (v2_keys - v1_keys):
        added.append((k, v2_data[k]))
        
    # Removed
    for k in (v1_keys - v2_keys):
        removed.append((k, v1_data[k]))
        
    # Metadata Changed
    for k in (v1_keys & v2_keys):
        m1 = v1_data[k]
        m2 = v2_data[k]
        
        if m1["status"] != m2["status"] or m1["name"] != m2["name"]:
            changed.append((k, m1, m2))
            
    return {
        "v1": v1_name,
        "v2": v2_name,
        "added": added,
        "removed": removed,
        "changed": changed,
        "total_v2": len(v2_data)
    }

def main():
    console.print(Panel.fit("[bold blue]Emoji Version Comparison Tool[/bold blue]"))
    
    # 1. Download files in parallel
    version_contents = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Downloading versions...", total=len(UNICODE_VERSIONS))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_version = {executor.submit(fetch_file, v): v for v in UNICODE_VERSIONS}
            for future in concurrent.futures.as_completed(future_to_version):
                v, content = future.result()
                if content.startswith("Error:"):
                    console.print(f"[red]Failed to download version {v}: {content}[/red]")
                else:
                    version_contents[v] = content
                progress.advance(task)

    # 2. Parse files in parallel
    parsed_data = {}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Parsing data...", total=len(version_contents))
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_version = {executor.submit(parse_emoji_test, content): v for v, content in version_contents.items()}
            for future in concurrent.futures.as_completed(future_to_version):
                v = future_to_version[future]
                parsed_data[v] = future.result()
                progress.advance(task)

    # 3. Compare consecutive versions
    # Sort versions based on their order in UNICODE_VERSIONS
    sorted_versions = [v for v in UNICODE_VERSIONS if v in parsed_data]
    comparisons = []
    
    for i in range(len(sorted_versions) - 1):
        v1 = sorted_versions[i]
        v2 = sorted_versions[i+1]
        comparisons.append(compare_versions(v1, parsed_data[v1], v2, parsed_data[v2]))

    # 4. Display and Save Results
    table = Table(title="Emoji Version Evolution (emoji-test.txt 4.0+)", show_header=True, header_style="bold magenta")
    table.add_column("Version", style="dim")
    table.add_column("Total", justify="right")
    table.add_column("Added", style="green", justify="right")
    table.add_column("Removed", style="red", justify="right")
    table.add_column("Modified", style="yellow", justify="right")

    first_v = sorted_versions[0]
    table.add_row(first_v, str(len(parsed_data[first_v])), "-", "-", "-")

    all_seen_emoji = set(parsed_data[first_v].keys())
    
    for comp in comparisons:
        table.add_row(
            comp["v2"],
            str(comp["total_v2"]),
            str(len(comp["added"])),
            str(len(comp["removed"])),
            str(len(comp["changed"]))
        )
        all_seen_emoji.update(parsed_data[comp["v2"]].keys())

    # Show and save summary to file
    summary_file = "emoji_evolution.md"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("# Emoji Version Evolution Summary (4.0+)\n\n")
        capture_console = Console(record=True, width=100)
        capture_console.print(table)
        f.write("```text\n")
        f.write(capture_console.export_text())
        f.write("```\n")
    
    # Save Detailed Log
    mod_file = "emoji_modifications.md"
    with open(mod_file, "w", encoding="utf-8") as f:
        f.write("# Emoji Detailed Modifications Log (4.0+)\n\n")
        f.write(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for comp in comparisons:
            f.write(f"## {comp['v1']} → {comp['v2']}\n")
            f.write(f"- **Total emoji in {comp['v2']}:** {comp['total_v2']}\n")
            f.write(f"- **Added:** {len(comp['added'])}\n")
            f.write(f"- **Removed:** {len(comp['removed'])}\n")
            f.write(f"- **Metadata Changed:** {len(comp['changed'])}\n\n")
            
            for section, items in [("Added emoji", comp['added']), ("Removed emoji", comp['removed'])]:
                if items:
                    f.write(f"### {section}\n")
                    f.write("| Codepoints | Name | Status |\n")
                    f.write("| :--- | :--- | :--- |\n")
                    for cp, data in sorted(items):
                        f.write(f"| `{cp}` | {data['name']} | {data['status']} |\n")
                    f.write("\n")
            
            if comp['changed']:
                f.write("### Metadata Changes\n")
                f.write("| Codepoints | Old Name/Status | New Name/Status |\n")
                f.write("| :--- | :--- | :--- |\n")
                for cp, m1, m2 in sorted(comp['changed']):
                    old = f"{m1['name']} ({m1['status']})"
                    new = f"{m2['name']} ({m2['status']})"
                    f.write(f"| `{cp}` | {old} | {new} |\n")
                f.write("\n")
            
            f.write("---\n\n")
            
    # Reliability Analysis
    latest_v = sorted_versions[-1]
    latest_emoji = set(parsed_data[latest_v].keys())
    missing_from_latest = all_seen_emoji - latest_emoji
    
    rprint(f"\n[bold]Reliability Check (4.0+ Target: {latest_v})[/bold]")
    rprint(f"Total unique emoji ever seen (v4.0+): [cyan]{len(all_seen_emoji)}[/cyan]")
    rprint(f"Total emoji in target: [cyan]{len(latest_emoji)}[/cyan]")
    
    if not missing_from_latest:
        rprint("[bold green]SUCCESS:[/bold green] The target version contains ALL emoji from v4.0 onwards.")
    else:
        rprint(f"[bold yellow]WARNING:[/bold yellow] Missing [red]{len(missing_from_latest)}[/red] emoji.")
        for cp in sorted(list(missing_from_latest))[:15]:
            rprint(f" - {cp}")

if __name__ == "__main__":
    main()
