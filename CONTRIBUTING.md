# Contributing

Use focused changes with an explanation of the user-visible behavior.

1. Create a Python environment and install requirements-dev.txt.
2. Run `python tools/render_ui.py`, `python tools/build_preview.py`, `python -m unittest discover -s tests -v` and `python tools/check_project.py`.
3. Inspect changed screens at 240 × 135 and at integer enlargement. Include before-and-after screen assets for visual changes.
4. Describe whether your evidence comes from the browser, CPU tests, a mocked transport or physical hardware.
5. Keep private logs, serials, machine paths, recordings, credentials and vendor binaries out of the commit.

Generated reference PNGs, graphics allocation and firmware pins must stay consistent. The artwork renderer writes build/rendered/ for comparison; it does not silently replace the reviewed assets or authorize a hardware update.

Firmware changes require the exact base hash, reviewed patch boundaries, asynchronous-transfer tests and honest hardware status. Do not remove compatibility checks to bypass an unknown device revision.

Use GitHub issues for reproducible bugs and feature proposals. A hardware report can name model/region, firmware revision and connection mode without including personal identifiers.
