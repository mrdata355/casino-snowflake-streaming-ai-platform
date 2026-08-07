# ruff: noqa: I001

import pathlib
from html.parser import HTMLParser


ROOT = pathlib.Path(__file__).resolve().parents[1]


class OpsReadyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.nav_targets = []
        self.jump_targets = []
        self.buttons = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "button":
            self.buttons.append(attrs)
            if attrs.get("data-view"):
                self.nav_targets.append(attrs["data-view"])
            if attrs.get("data-jump"):
                self.jump_targets.append(attrs["data-jump"])


def test_root_html_has_unique_ids_and_valid_view_targets():
    parser = OpsReadyParser()
    parser.feed((ROOT / "index.html").read_text())
    assert len(parser.ids) == len(set(parser.ids)), "Root OpsReady HTML contains duplicate IDs"
    ids = set(parser.ids)
    for target in parser.nav_targets + parser.jump_targets:
        assert target in ids, f"UI control points to missing view: {target}"


def test_primary_engineer_controls_are_wired_in_javascript():
    app = (ROOT / "app.js").read_text()
    simulators = (ROOT / "simulators.js").read_text()
    manager = (ROOT / "manager-evidence.js").read_text()
    expected = {
        "roleToggle": app,
        "gradeWeekly": app,
        "gradeMonthly": app,
        "gradeFinops": app,
        "generateTraining": app,
        "openControlFull": simulators,
        "captureLabScore": simulators,
        "closeSim": simulators,
        "runUiSelfTest": manager,
        "exportEvidence": manager,
        "assignTeamDrill": manager,
        "recalcCert": manager,
    }
    for control_id, source in expected.items():
        assert control_id in source, f"Expected control is not wired: {control_id}"


def test_v6_uses_scoped_controls_and_loads_live_sandbox():
    html = (ROOT / "simulators" / "v6-full-job-cycle-lab.html").read_text()
    engine = (ROOT / "simulators" / "v6-engine-v2.js").read_text()
    live = (ROOT / "simulators" / "v6-live-sandbox.js").read_text()
    assert "v6-engine-v2.js" in html
    assert "v6-live-sandbox.js" in html
    assert "task-code" in engine and "task-live" in engine
    assert "getElementById('code')" not in engine
    assert "/sessions" in live and "/execute" in live
