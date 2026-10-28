"""The interface exists in French and English: keep the two tables in step."""
import re
from pathlib import Path

JS = (Path(__file__).parent.parent / "app" / "static" / "app.js").read_text("utf-8")
STRING = r'"((?:[^"\\]|\\.)*)"'


def table(lang: str) -> dict[str, str]:
    start = JS.index("const I18N = {")
    block = JS[start: JS.index("const LANGS", start)]
    body = block[block.index(f"\n  {lang}: {{"):]
    body = body[: body.index("\n  },")]
    return dict(re.findall(rf"\b([a-z][a-zA-Z0-9_]*): {STRING}", body))


EN, FR = table("en"), table("fr")
# keys built at run time, e.g. t(`a_${action}`)
DYNAMIC = (["a_" + a for a in ("create", "update", "unchanged", "skip")] + ["s_ok", "s_error", "on", "off"]
           + ["theme_" + t for t in ("auto", "light", "dark")] + ["tab_" + t for t in ("instances", "export", "import", "backups")]
           + ["sec_" + s for s in ("customFormats", "qualityProfiles", "qualityDefinitions", "naming", "mediaManagement",
                                   "appProfiles", "indexers", "indexerProxies", "metadataProfiles")]
           + ["src_file", "src_instance", "src_trash"])


def test_the_tables_were_read():
    assert len(EN) > 100 and len(FR) > 100


def test_both_languages_have_the_same_keys():
    assert sorted(set(EN) - set(FR)) == [], "missing in French"
    assert sorted(set(FR) - set(EN)) == [], "missing in English"


def test_every_key_used_in_the_code_exists():
    used = set(re.findall(r'\bt\(\s*"([a-zA-Z0-9_]+)"', JS)) | set(DYNAMIC)
    assert sorted(used - set(EN)) == []


def test_placeholders_match_between_languages():
    def slots(s: str) -> list[str]:
        return sorted(re.findall(r"\{\d+\}", s))

    common = EN.keys() & FR.keys()  # missing keys are reported by the test above
    assert {k: (slots(EN[k]), slots(FR[k])) for k in common if slots(EN[k]) != slots(FR[k])} == {}


def test_no_translation_is_left_empty_or_identical_by_accident():
    assert [k for k, v in {**EN, **FR}.items() if not v.strip()] == []
    # a few words are the same in both languages on purpose (product names, "Instance"...); long sentences are not
    same = [k for k in EN if EN[k] == FR[k] and len(EN[k]) > 25]
    assert same == [], f"untranslated: {same}"
