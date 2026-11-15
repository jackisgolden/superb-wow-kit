"""Audits the newest Forever release of every addon in addons.tsv.

Downloads each addon from its author's release and measures what it ships:
size on disk, image weight, code size, per-frame work, and release cadence.
Prints a table, and writes it to the GitHub job summary when run in CI.

Run from the repo root: python tests/audit.py
  --extra rows.tsv   also audit candidate rows that are not in the kit
  --pin              rewrite addons.tsv so each pin is the newest release

Fails when an addon has no Forever build or cannot be downloaded. Everything
else is reported as a flag, for a person to judge.
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

FLAVOR = "1.60.1"
INTERFACE = "16001"
AGENT = "addon-audit"
TSV = Path("addons.tsv")

DISK_BUDGET_MB = 50
RAW_IMAGE_BUDGET_MB = 10
LEFTOVER = re.compile(r"(test|backup|unused|\bold\b)|\.(psd|bak|orig|xcf)$", re.I)
ON_UPDATE = re.compile(r"""SetScript\(\s*["']OnUpdate["']""")
TICKER = re.compile(r"NewTicker\s*\(")
COMBAT_LOG = re.compile(r"COMBAT_LOG_EVENT")
PEER_NETWORK = re.compile(r"JoinChannelByName|JoinTemporaryChannel|JoinPermanentChannel")


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def newest(row):
    """The newest Forever release: download url, file name, pin, date, release count."""
    if row["source"] == "github":
        release = json.loads(get(f"https://api.github.com/repos/{row['id']}/releases/latest"))
        pattern = re.escape(row["file"]).replace(re.escape(row["pin"].lstrip("v")), ".*")
        asset = next(a for a in release["assets"] if re.fullmatch(pattern, a["name"]))
        return {
            "url": asset["browser_download_url"], "file": asset["name"], "pin": release["tag_name"],
            "date": release["published_at"][:10], "releases": None,
        }
    project = json.loads(get(f"https://api.cfwidget.com/{row['id']}"))
    files = [f for f in project["files"] if f["type"] == "release" and FLAVOR in f["versions"]]
    if not files:
        raise LookupError("no Forever release")
    files.sort(key=lambda f: f["uploaded_at"], reverse=True)
    file = files[0]
    pin = str(file["id"])
    name = urllib.parse.quote(file["name"])
    return {
        "url": f"https://mediafilez.forgecdn.net/files/{pin[:4]}/{int(pin[4:])}/{name}",
        "file": file["name"], "pin": pin, "date": file["uploaded_at"][:10], "releases": len(files),
    }


def loads_on_forever(folder):
    for toc in folder.glob("*.toc"):
        if re.search(r"[_-](Forever|Camelot)\.toc$", toc.name, re.I):
            return True
        for line in toc.read_text(errors="replace").splitlines():
            if line.lower().startswith("## interface:") and INTERFACE in line:
                return True
    return False


def is_library(path):
    return any(part.lower() in ("libs", "lib", "libraries", "thirdparty") for part in path.parts)


def raw_tga(path):
    with path.open("rb") as handle:
        header = handle.read(3)
    return len(header) == 3 and header[2] in (2, 3)


def measure(folders):
    stats = dict(disk=0, media=0, raw=0, lines=0, on_update=0, tickers=0,
                 combat_log=False, peer_network=False, leftovers=[], no_forever=[])
    for folder in folders:
        if not loads_on_forever(folder):
            stats["no_forever"].append(folder.name)
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            size = path.stat().st_size
            suffix = path.suffix.lower()
            stats["disk"] += size
            if suffix in (".tga", ".blp", ".png", ".jpg", ".ogg", ".mp3", ".wav", ".ttf", ".otf", ".m2"):
                stats["media"] += size
                if suffix == ".tga" and raw_tga(path):
                    stats["raw"] += size
            relative = path.relative_to(folder.parent)
            if is_library(relative):
                continue
            if LEFTOVER.search(path.name) and suffix not in (".toc", ".xml", ".txt", ".md"):
                stats["leftovers"].append(str(relative))
            if suffix == ".lua":
                text = path.read_text(errors="replace")
                stats["lines"] += text.count("\n")
                stats["on_update"] += len(ON_UPDATE.findall(text))
                stats["tickers"] += len(TICKER.findall(text))
                stats["combat_log"] |= bool(COMBAT_LOG.search(text))
                stats["peer_network"] |= bool(PEER_NETWORK.search(text))
    return stats


def flags(stats):
    found = []
    if stats["no_forever"]:
        found.append("no Forever build: " + ", ".join(stats["no_forever"]))
    if stats["disk"] > DISK_BUDGET_MB * 2**20:
        found.append(f"over {DISK_BUDGET_MB} MB")
    if stats["raw"] > RAW_IMAGE_BUDGET_MB * 2**20:
        found.append("uncompressed images")
    if stats["peer_network"]:
        found.append("joins a chat channel")
    if stats["combat_log"]:
        found.append("reads the combat log")
    if stats["leftovers"]:
        found.append(f"{len(stats['leftovers'])} leftover files")
    return found


def audit(row, today):
    release = newest(row)
    with tempfile.TemporaryDirectory() as work:
        zipfile.ZipFile(io.BytesIO(get(release["url"]))).extractall(work)
        wanted = row["folders"].split(",") if row.get("folders") else None
        folders = [d for d in sorted(Path(work).iterdir())
                   if d.is_dir() and (not wanted or d.name in wanted)]
        stats = measure(folders)
    age = (today - datetime.date.fromisoformat(release["date"])).days
    return release, stats, age


def mb(size):
    return f"{size / 2**20:.1f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra", type=Path)
    parser.add_argument("--pin", action="store_true")
    args = parser.parse_args()

    kit = list(csv.DictReader(TSV.open(newline=""), delimiter="\t"))
    extra = list(csv.DictReader(args.extra.open(newline=""), delimiter="\t")) if args.extra else []
    today = datetime.date.today()
    lines = [
        "| Addon | Release | Days old | Forever releases | Disk MB | Media MB | Raw TGA MB "
        "| Lua lines | OnUpdate | Tickers | Flags |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    failed, leftovers = [], {}
    for row in kit + extra:
        label = row["name"] + ("" if row in kit else " (candidate)")
        try:
            release, stats, age = audit(row, today)
        except Exception as error:
            failed.append(row["name"])
            lines.append(f"| {label} | FAILED: {error} | | | | | | | | | |")
            continue
        if stats["no_forever"]:
            failed.append(row["name"])
        if stats["leftovers"]:
            leftovers[row["name"]] = stats["leftovers"]
        if args.pin and row in kit:
            row["pin"], row["file"] = release["pin"], release["file"]
        lines.append("| " + " | ".join([
            label, release["file"], str(age), str(release["releases"] or ""),
            mb(stats["disk"]), mb(stats["media"]), mb(stats["raw"]), str(stats["lines"]),
            str(stats["on_update"]), str(stats["tickers"]), "; ".join(flags(stats)),
        ]) + " |")

    report = "\n".join(lines)
    for name, files in leftovers.items():
        report += f"\n\n{name} leftover files: " + ", ".join(files[:12])
    print(report)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write(report + "\n")
    if args.pin:
        with TSV.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(kit[0]), delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(kit)
    if failed:
        sys.exit("failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
