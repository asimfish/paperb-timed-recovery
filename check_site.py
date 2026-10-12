"""Verify static source hashes and links, optionally their deployed HTTP bytes."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
from urllib.request import urlopen


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if (tag == "a" and key == "href") or (tag == "img" and key == "src"):
                self.references.append(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = json.loads((root / "SOURCE_MANIFEST.json").read_text())
    entries = {x["path"]: x for x in manifest["files"]}
    for name, entry in entries.items():
        data = (root / name).read_bytes()
        assert len(data) == entry["bytes"]
        assert hashlib.sha256(data).hexdigest() == entry["sha256"], name
    assert (root / ".nojekyll").exists()
    local_refs = set()
    for name in ["index.html", "full-design.html"]:
        html = (root / name).read_text()
        assert "chatgpt.site" not in html
        p = References()
        p.feed(html)
        for ref in p.references:
            if not ref or ref.startswith("#") or urlsplit(ref).scheme:
                continue
            resolved = urljoin("https://example.invalid/paperb-timed-recovery/" + name, ref)
            path = unquote(urlsplit(resolved).path)
            assert path.startswith("/paperb-timed-recovery/"), ref
            relative = path.removeprefix("/paperb-timed-recovery/")
            assert relative in (set(entries) | {"SOURCE_MANIFEST.json"}), (ref, relative)
            local_refs.add(relative)
    main_html = (root / "index.html").read_text()
    assert 'id="current_method"' in main_html
    assert "51/180" in main_html and "51 / 129 / 0" in main_html
    assert "37 / 141 / 2" in main_html and 'id="anticipatory"' in main_html
    assert 'id="history_adaptation"' in main_html
    assert '57 / 123 / 0' in main_html and '66 / 114 / 0' in main_html
    assert '622 / 1176 / 2' in main_html and '11 / 16' in main_html
    http = []
    if args.base_url:
        assert args.base_url.endswith("/")
        for name in sorted(set(entries) | {"SOURCE_MANIFEST.json"}):
            with urlopen(urljoin(args.base_url, name), timeout=30) as response:
                data = response.read()
                assert response.status == 200, name
                assert hashlib.sha256(data).hexdigest() == hashlib.sha256((root / name).read_bytes()).hexdigest(), name
                http.append({"path": name, "status": response.status})
    print(json.dumps({"status": "PASS", "bound_files": len(entries),
                      "local_link_targets": len(local_refs), "http_artifacts": len(http),
                      "project_prefix_preserved": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
