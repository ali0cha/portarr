"""The English README is the main one; the French one must say the same, with the same commands."""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
EN = (ROOT / "README.md").read_text("utf-8")
FR = (ROOT / "README.fr.md").read_text("utf-8")


def headings(text: str) -> list[int]:
    # '#' lines outside code blocks: their depth gives the outline
    return [len(m.group(1)) for m in re.finditer(r"^(#{1,6}) ", re.sub(r"```.*?```", "", text, flags=re.S), re.M)]


def code_blocks(text: str) -> list[tuple[str, list[str]]]:
    """(language, lines) of every fenced block, comments removed: comments are the only translated part."""
    blocks = []
    for lang, body in re.findall(r"^[ \t]*```(\w*)\n(.*?)^[ \t]*```", text, flags=re.S | re.M):
        lines = []
        for line in body.splitlines():
            line = re.sub(r"\s+#.*$", "", line.strip())
            if line and not line.startswith("#"):
                lines.append(line)
        blocks.append((lang, lines))
    return blocks


def test_each_readme_links_to_the_other():
    assert "(README.fr.md)" in EN and "(README.md)" in FR


def test_same_outline():
    assert headings(EN) == headings(FR)


def test_same_tables():
    def shape(text: str) -> list[int]:
        return [len(re.findall(r"\|", line)) for line in text.splitlines() if line.startswith("|")]

    assert shape(EN) == shape(FR)


def test_commands_and_config_are_identical():
    en, fr = code_blocks(EN), code_blocks(FR)
    assert len(en) == len(fr) >= 4
    for (lang_en, a), (lang_fr, b) in zip(en, fr):
        assert (lang_en, a) == (lang_fr, b)


def test_local_links_point_to_files_that_exist():
    for text in (EN, FR):
        targets = re.findall(r"\]\(([^)\s]+)\)", text) + re.findall(r'src="([^"]+)"', text)
        local = [t for t in targets if not t.startswith(("http", "#", "mailto"))]
        assert local, "expected at least the logo and the screenshots"
        assert [t for t in local if not (ROOT / t).exists()] == []


def test_no_placeholder_left_behind():
    for text in (EN, FR):
        assert "YOUR_GITHUB_USER" not in text and "VOTRE_UTILISATEUR" not in text


SHOTS = ROOT / "docs" / "screenshots"


def shots_used(text: str, lang: str) -> list[str]:
    return sorted(re.findall(rf"docs/screenshots/{lang}/([\w.-]+\.png)", text))


def test_both_readmes_show_the_same_screenshots_in_their_own_language():
    assert shots_used(EN, "en") == shots_used(FR, "fr") != []
    assert not re.search(r"screenshots/fr/", EN) and not re.search(r"screenshots/en/", FR)  # no English image in the French page


def test_every_screenshot_is_used_and_stays_light():
    for lang, text in (("en", EN), ("fr", FR)):
        on_disk = sorted(p.name for p in (SHOTS / lang).glob("*.png"))
        assert on_disk == shots_used(text, lang), f"{lang}: unused or missing screenshots"
        too_big = [p.name for p in (SHOTS / lang).glob("*.png") if p.stat().st_size > 450_000]
        assert too_big == [], f"{too_big}: compress them (tools/screenshots/run.sh does it) to keep the repository light"
