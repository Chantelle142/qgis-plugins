# Field Tools: QGIS plugins

QGIS plugin repository for Create Field Grid and future field tools.

## Install in QGIS (once)

1. In QGIS, open **Plugins → Manage and Install Plugins…**
2. Go to the **Settings** tab and click **Add…** next to *Plugin repositories*.
3. Name: `Field Tools`
   URL: `https://chantelle142.github.io/qgis-plugins/plugins.xml`
   Click **OK**.
4. Go to the **All** tab, search for the plugin (for example **Create Field Grid**) and click **Install Plugin**.

QGIS checks for new versions when it starts. Updates appear under **Upgradeable** in the Plugin Manager.

## Plugins

| Plugin | What it does |
|---|---|
| **Create Field Grid** | Creates numbered soil sampling points by dividing each field into square grid cells of a chosen area. |

## How this repository works

This repository only holds the released plugins. It is published with GitHub Pages, and QGIS reads `plugins.xml`.

- Each plugin has a folder holding its release zips, named `<plugin_id>.<version>.zip`.
- `plugins.xml` lists the newest version of each plugin. Don't edit it by hand: `scripts/build_plugins_xml.py` rebuilds it from the zips, and a workflow runs that script whenever a zip is added.
- To roll a plugin back, delete its newest zip. People who already upgraded keep that version until a higher one is released.
- Releases normally arrive from each plugin's own source repository by its Release workflow.
