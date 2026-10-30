"""Takes the README screenshots of Portarr in one language: `python shots.py en|fr`.

It drives the real interface in headless Chromium against the fake servers of tests/fake_arr.py (see run.sh),
playing the situations a user goes through. Nothing here touches a real instance.
"""
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

LANG = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8765")
OUT = Path(os.environ.get("OUT", "/out")) / LANG
WIDTH, HEIGHT, SCALE = 1180, 760, 1.5
TALL = 960  # the list of instances needs more room than the other screens

# Instance names are the same in both languages; the ports are those started by run.sh.
INSTANCES = [("Radarr HD", 7001), ("Radarr 4K", 7002), ("Sonarr TV", 7003), ("Lidarr Music", 7005),
             ("Whisparr", 7007), ("Prowlarr main", 7009), ("Prowlarr new", 7010)]

TEXT = {
    "en": dict(locale="en-US", trash="TRaSH Guides", other="Another instance", indexers="Indexers", done="Done", backup_now="Back up now", restore="Restore…", sched="Scheduled backups", sched_save="Save the schedule"),
    "fr": dict(locale="fr-FR", trash="TRaSH Guides", other="Une autre instance", indexers="Indexeurs", done="Terminé", backup_now="Sauvegarder maintenant", restore="Restaurer…", sched="Sauvegardes planifiées", sched_save="Enregistrer la planification"),
}[LANG]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=SCALE,
                                  locale=TEXT["locale"], color_scheme="light")
        # the language switch and the theme are remembered in localStorage: set them before the app starts
        ctx.add_init_script(f"localStorage.setItem('portarr-lang', '{LANG}'); localStorage.setItem('portarr-theme', 'light');")
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())  # the "apply?" confirmation
        page.set_default_timeout(30000)

        for name, port in INSTANCES:  # what a user does first, only faster
            r = page.request.post(f"{BASE}/api/instances", data={"name": name, "url": f"http://127.0.0.1:{port}", "api_key": "demo-key"})
            assert r.ok, r.text()

        def tab(i: int) -> None:
            page.locator("#tabs button").nth(i).click()

        def target(name: str) -> None:
            page.locator("#view select").nth(0).select_option(label=name)
            page.wait_for_timeout(500)  # the page rebuilds itself for the new target

        def scroll_to(selector: str, offset: int = 110, **kw) -> None:
            page.locator(selector, **kw).first.evaluate(
                "(el, off) => { const c = document.querySelector('.content');"
                " c.scrollTop = el.getBoundingClientRect().top - c.getBoundingClientRect().top + c.scrollTop - off; }", offset)
            page.wait_for_timeout(200)

        def shot(name: str, height: int = HEIGHT) -> None:
            page.set_viewport_size({"width": WIDTH, "height": height})
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            page.screenshot(path=str(OUT / f"{name}.png"))
            page.set_viewport_size({"width": WIDTH, "height": HEIGHT})
            print(f"[{LANG}] {name}")

        # 1. the instances, each in its application's colour
        page.goto(BASE)
        page.wait_for_selector("text=Prowlarr new")
        shot("01-instances", TALL)

        # 2. export: the configuration loads by itself, tick what to include
        tab(1)
        page.wait_for_selector("#view details.section")
        shot("02-export")

        # 3. import from the TRaSH Guides: pick a profile, adjust the format groups
        tab(2)
        page.wait_for_selector("#view select")
        target("Radarr 4K (Radarr)")
        page.locator(".seg button", has_text=TEXT["trash"]).click()
        page.wait_for_selector("optgroup", state="attached")
        page.locator("#view select").filter(has=page.locator("optgroup")).select_option(label="HD Bluray + WEB")
        page.wait_for_selector("#view details.section")
        # the same panel offers a set of quality sizes and a naming scheme (their ids are those of the guides)
        page.locator("#view select").filter(has=page.locator("option[value='aed34b9f60ee115dfa7918b742336277']")).select_option("aed34b9f60ee115dfa7918b742336277")
        page.locator("#view select").filter(has=page.locator("option[value='plex-tmdb']")).select_option("plex-tmdb")
        page.wait_for_timeout(500)
        scroll_to(".seg", offset=95)
        shot("03-trash-profile", TALL)

        # 4. review every change before anything is written
        page.evaluate("document.querySelector('.content').scrollTop = 0")
        page.locator(".seg button", has_text=TEXT["other"]).click()
        page.locator("#actionbar button.primary").click()
        page.wait_for_selector(".flow")
        page.wait_for_timeout(400)
        shot("04-review")

        # 5. apply: the summary and the backup of the target
        page.locator("#actionbar button.primary").click()
        page.wait_for_selector(f"h2:text-is('{TEXT['done']}')")
        page.wait_for_timeout(400)
        shot("05-done")

        # 6. Prowlarr: an indexer that needs secrets is created disabled
        page.locator("#actionbar button.primary").click()  # new import
        page.wait_for_selector("#view select")
        target("Prowlarr new (Prowlarr)")
        page.locator(".seg button", has_text=TEXT["other"]).click()
        page.locator("#actionbar button.primary").click()
        page.wait_for_selector(".flow")
        page.wait_for_timeout(500)
        scroll_to("#view details.section > summary", offset=150, has_text=re.compile(rf"^\s*{TEXT['indexers']}\s*\d"))  # the title is followed by its "2 / 2" counter
        shot("06-prowlarr-secrets")

        # 7. a full backup of an instance, and the choices to restore it
        tab(3)
        page.wait_for_selector("#view select")
        page.locator("#view select").first.select_option(label="Radarr 4K (Radarr)")
        page.locator("#view button.primary", has_text=TEXT["backup_now"]).click()
        page.wait_for_selector("#view table")
        page.locator("#view button", has_text=TEXT["restore"]).first.click()
        page.wait_for_selector(".danger-zone")
        page.wait_for_timeout(400)
        scroll_to("#view table", offset=130)  # the list and the restore panel under it
        shot("07-full-backup", 1100)  # tall enough to show the whole restore panel

        # 8. scheduled backups: every night, for the two Radarr instances
        page.wait_for_timeout(4200)  # let the "backup saved" notice go away: the next picture has its own
        card = page.locator("#view .card", has_text=TEXT["sched"])
        for i in range(3):  # "back up automatically", then the first two instances
            card.locator("input[type=checkbox]").nth(i).check()
        card.locator("button", has_text=TEXT["sched_save"]).click()
        page.wait_for_selector(".toast")
        page.wait_for_timeout(600)
        scroll_to("#view .card:has(h3)", offset=95, has_text=TEXT["sched"])
        shot("08-scheduled-backups", TALL)

        browser.close()


main()
