#!/usr/bin/env python3
"""
Rebuild plugins.xml (the list QGIS reads) from the plugin zips in this repository.

Layout: one folder per plugin, holding that plugin's release zips:

    create_field_grid/create_field_grid.2.0.0.zip
    create_field_grid/create_field_grid.2.0.1.zip
    another_plugin/another_plugin.1.0.0.zip

For each folder the newest version is listed, with its details read from the
metadata.txt inside the zip. Older zips stay so a release can be rolled back by
deleting the newer zip. The plugin's icon is copied out of the zip next to it.

    python scripts/build_plugins_xml.py
"""

import argparse
import configparser
import os
import re
import sys
import zipfile
from xml.sax.saxutils import escape, quoteattr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://chantelle142.github.io/qgis-plugins"
ZIP_RE = re.compile(r"^(?P<id>[A-Za-z0-9_]+)\.(?P<version>\d+(?:\.\d+)*)\.zip$")


def version_key(v):
    return tuple(int(p) for p in v.split("."))


def full_version(v):
    """QGIS compares versions part by part; '3.99' is clearer as '3.99.0'."""
    parts = v.split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts)


def read_metadata(zf, plugin_id):
    name = "%s/metadata.txt" % plugin_id
    if name not in zf.namelist():
        raise ValueError("no %s inside the zip (the zip must contain the %s/ folder)"
                         % (name, plugin_id))
    cfg = configparser.ConfigParser(interpolation=None, strict=False)
    cfg.read_string(zf.read(name).decode("utf-8-sig"))
    return {k: v.strip() for k, v in cfg["general"].items()}


def cdata(text):
    return "<![CDATA[%s]]>" % (text or "").replace("]]>", "]]]]><![CDATA[>")


def plugin_entry(plugin_id, zip_name, meta, base_url):
    rel_zip = "%s/%s" % (plugin_id, zip_name)
    icon_url = ""
    if meta.get("icon"):
        icon_url = "%s/%s/%s" % (base_url, plugin_id, os.path.basename(meta["icon"]))
    tags = {
        "description": cdata(meta.get("description", "")),
        "about": cdata(meta.get("about", "")),
        "version": escape(meta["version"]),
        "qgis_minimum_version": escape(full_version(meta.get("qgisminimumversion", "3.0"))),
        "qgis_maximum_version": escape(full_version(meta.get("qgismaximumversion", "3.99"))),
        "homepage": cdata(meta.get("homepage", "")),
        "file_name": escape(zip_name),
        "icon": escape(icon_url),
        "author_name": cdata(meta.get("author", "")),
        "download_url": escape("%s/%s" % (base_url, rel_zip)),
        "experimental": "True" if meta.get("experimental", "").lower() in ("true", "yes", "1") else "False",
        "deprecated": "True" if meta.get("deprecated", "").lower() in ("true", "yes", "1") else "False",
        "tracker": cdata(meta.get("tracker", "")),
        "repository": cdata(meta.get("repository", "")),
        "tags": cdata(meta.get("tags", "")),
        "changelog": cdata(meta.get("changelog", "")),
    }
    body = "\n".join("    <%s>%s</%s>" % (k, v, k) for k, v in tags.items())
    return '  <pyqgis_plugin name=%s version=%s>\n%s\n  </pyqgis_plugin>' % (
        quoteattr(meta["name"]), quoteattr(meta["version"]), body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_URL)
    args = ap.parse_args()
    base_url = args.base_url.rstrip("/")

    entries, problems = [], []
    for plugin_id in sorted(os.listdir(ROOT)):
        folder = os.path.join(ROOT, plugin_id)
        if plugin_id.startswith(".") or plugin_id == "scripts" or not os.path.isdir(folder):
            continue
        zips = []
        for f in os.listdir(folder):
            m = ZIP_RE.match(f)
            if m and m.group("id") == plugin_id:
                zips.append((version_key(m.group("version")), f))
            elif f.endswith(".zip"):
                problems.append("%s/%s: name must be %s.<version>.zip" % (plugin_id, f, plugin_id))
        if not zips:
            continue
        _, zip_name = max(zips)
        try:
            with zipfile.ZipFile(os.path.join(folder, zip_name)) as zf:
                meta = read_metadata(zf, plugin_id)
                zip_version = ZIP_RE.match(zip_name).group("version")
                if meta.get("version") != zip_version:
                    raise ValueError("metadata.txt says version=%s but the file name says %s"
                                     % (meta.get("version"), zip_version))
                icon = meta.get("icon")
                if icon:
                    member = "%s/%s" % (plugin_id, icon)
                    if member in zf.namelist():
                        with open(os.path.join(folder, os.path.basename(icon)), "wb") as fh:
                            fh.write(zf.read(member))
                    else:
                        meta["icon"] = ""
        except (ValueError, KeyError, zipfile.BadZipFile) as e:
            problems.append("%s/%s: %s" % (plugin_id, zip_name, e))
            continue
        entries.append((meta["name"].lower(), plugin_entry(plugin_id, zip_name, meta, base_url)))
        print("Listed %s %s" % (plugin_id, meta["version"]))

    if problems:
        sys.exit("Not updating plugins.xml:\n  " + "\n  ".join(problems))

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<plugins>\n%s\n</plugins>\n'
           % "\n".join(e for _, e in sorted(entries)))
    with open(os.path.join(ROOT, "plugins.xml"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(xml)
    print("Wrote plugins.xml with %d plugin(s)" % len(entries))


if __name__ == "__main__":
    main()
