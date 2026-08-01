import re
from pathlib import Path


ROOT = Path(__file__).parents[2]
PUBLIC_HTML = (
    ROOT / "index.html",
    ROOT / "impressum.html",
    ROOT / "datenschutz.html",
    ROOT / "p" / "page.html",
)


def test_locale_scripts_use_versioned_urls():
    for path in PUBLIC_HTML:
        html = path.read_text(encoding="utf-8")
        locale_scripts = re.findall(
            r'src="[^"]*(?:locale|legal-locale)[^"]*\.js[^"]*"',
            html,
        )
        assert locale_scripts, f"no locale scripts found in {path.name}"
        assert all("?v=" in script for script in locale_scripts)
