"use strict";

// ---------------------------------------------------------------- i18n
const I18N = {
  en: {
    tab_instances: "Instances", tab_export: "Export", tab_import: "Import", tab_backups: "Backups",
    theme_auto: "Theme: automatic", theme_light: "Theme: light", theme_dark: "Theme: dark",
    inst_hint: "Your Radarr, Sonarr, Lidarr, Whisparr and Prowlarr servers. API keys are stored on this server only and are never sent back to the browser.",
    inst_empty: "No instance yet.", inst_add: "Add instance", inst_edit: "Edit instance",
    name: "Name", url: "URL", url_hint: "Include the URL base if you use one, e.g. http://192.168.1.10:7878/radarr",
    api_key: "API key", api_key_keep: "(empty = keep current key)", api_key_where: "Found in Settings → General → Security",
    verify_ssl: "Verify the TLS certificate", save: "Test & save", cancel: "Cancel", test: "Test", edit: "Edit", delete: "Delete",
    delete_confirm: "Delete the instance “{0}”? (Nothing is changed on the server itself.)",
    connected: "Connected to {0} {1}", saved: "Saved",
    exp_hint: "Pick what to export from an instance. Everything is referenced by name so it can be imported on another instance.",
    imp_hint: "Import a bundle on an instance. You always get a preview first, and the target is backed up before anything is written.",
    instance: "Instance", load: "Load", download_short: "Download", refresh: "Refresh",
    loaded_from: "Loaded from {0} {1}", scored_cf_note: "Selecting a profile also selects what it depends on.",
    sec_customFormats: "Custom formats", sec_qualityProfiles: "Quality profiles", sec_qualityDefinitions: "Quality sizes",
    sec_naming: "Naming", sec_mediaManagement: "Media management",
    sec_metadataProfiles: "Metadata profiles", sec_appProfiles: "Sync profiles", sec_indexers: "Indexers", sec_indexerProxies: "Indexer proxies",
    note_conditions: "{0} condition(s)", note_profile: "{0} enabled qualities · {1} scored formats",
    note_sizes: "min {0} · preferred {1} · max {2} MB/min", note_metadata: "{0} album types · {1} secondary types · {2} statuses", note_sync: "RSS {0} · automatic {1} · interactive {2} · min. seeders {3}",
    note_indexer: "{0} · priority {1} · profile {2}", note_proxy: "{0}", on: "on", off: "off",
    note_secrets: "Secrets are never exported: {0}",
    source: "Source", src_file: "File / pasted JSON", src_instance: "Another instance", choose_file: "Choose a .json file",
    paste_ph: "…or paste here a Portarr export or TRaSH-Guides custom format JSON",
    target: "Target instance", overwrite: "Overwrite existing items that differ (custom formats, quality profiles, sync profiles, indexers…)",
    overwrite_hint: "Quality sizes, naming and media management are always updated when selected.",
    analyse: "Analyse", analysing: "Analysing…", apply_n: "Apply ({0})", applying: "Applying…",
    confirm_apply: "Apply {0} change(s) on “{1}”? A backup of its current state is saved first.",
    done: "Done", new_import: "New import", backup_saved: "Previous state of the target saved as",
    need_source: "Choose a source first", same_instance: "Source and target must differ",
    a_create: "new", a_update: "update", a_unchanged: "identical", a_skip: "skipped", s_ok: "done", s_error: "error",
    bk_hint: "Automatic snapshots of an instance taken just before each import. To roll back, import one of these files with “overwrite” enabled (items created by the import are not deleted).",
    bk_empty: "No backup yet.", date: "Date", size: "Size", file: "File",
    changes: "{0} change(s)", loading: "Loading…",
  },
  fr: {
    tab_instances: "Instances", tab_export: "Export", tab_import: "Import", tab_backups: "Sauvegardes",
    theme_auto: "Thème : automatique", theme_light: "Thème : clair", theme_dark: "Thème : sombre",
    inst_hint: "Vos serveurs Radarr, Sonarr, Lidarr, Whisparr et Prowlarr. Les clés API restent sur ce serveur et ne sont jamais renvoyées au navigateur.",
    inst_empty: "Aucune instance.", inst_add: "Ajouter", inst_edit: "Modifier l'instance",
    name: "Nom", url: "URL", url_hint: "Ajoutez l'URL Base si vous en utilisez une, ex. http://192.168.1.10:7878/radarr",
    api_key: "Clé API", api_key_keep: "(vide = conserver la clé actuelle)", api_key_where: "Dans Paramètres → Général → Sécurité",
    verify_ssl: "Vérifier le certificat TLS", save: "Tester et enregistrer", cancel: "Annuler", test: "Tester", edit: "Modifier", delete: "Supprimer",
    delete_confirm: "Supprimer l'instance « {0} » ? (Rien n'est modifié sur le serveur lui-même.)",
    connected: "Connecté à {0} {1}", saved: "Enregistré",
    exp_hint: "Choisissez ce qu'il faut exporter d'une instance. Tout est référencé par nom, ce qui permet de l'importer sur une autre instance.",
    imp_hint: "Importez un fichier sur une instance. Un aperçu est toujours affiché d'abord, et la cible est sauvegardée avant toute écriture.",
    instance: "Instance", load: "Charger", download_short: "Télécharger", refresh: "Actualiser",
    loaded_from: "Chargé depuis {0} {1}", scored_cf_note: "Cocher un profil coche aussi ce dont il dépend.",
    sec_customFormats: "Formats personnalisés", sec_qualityProfiles: "Profils de qualité", sec_qualityDefinitions: "Tailles par qualité",
    sec_naming: "Nommage", sec_mediaManagement: "Gestion des médias",
    sec_metadataProfiles: "Profils de métadonnées", sec_appProfiles: "Profils de synchronisation", sec_indexers: "Indexeurs", sec_indexerProxies: "Proxys d'indexeurs",
    note_conditions: "{0} condition(s)", note_profile: "{0} qualités actives · {1} formats notés",
    note_sizes: "min {0} · préféré {1} · max {2} Mo/min", note_metadata: "{0} types d'album · {1} types secondaires · {2} statuts", note_sync: "RSS {0} · automatique {1} · interactif {2} · seeders min. {3}",
    note_indexer: "{0} · priorité {1} · profil {2}", note_proxy: "{0}", on: "oui", off: "non",
    note_secrets: "Les secrets ne sont jamais exportés : {0}",
    source: "Source", src_file: "Fichier / JSON collé", src_instance: "Une autre instance", choose_file: "Choisir un fichier .json",
    paste_ph: "…ou collez ici un export Portarr ou un JSON de format personnalisé TRaSH-Guides",
    target: "Instance cible", overwrite: "Écraser les éléments existants qui diffèrent (formats personnalisés, profils de qualité, profils de synchronisation, indexeurs…)",
    overwrite_hint: "Les tailles par qualité, le nommage et la gestion des médias sont toujours mis à jour s'ils sont cochés.",
    analyse: "Analyser", analysing: "Analyse…", apply_n: "Appliquer ({0})", applying: "Application…",
    confirm_apply: "Appliquer {0} changement(s) sur « {1} » ? L'état actuel est d'abord sauvegardé.",
    done: "Terminé", new_import: "Nouvel import", backup_saved: "État précédent de la cible sauvegardé sous",
    need_source: "Choisissez d'abord une source", same_instance: "La source et la cible doivent être différentes",
    a_create: "nouveau", a_update: "mise à jour", a_unchanged: "identique", a_skip: "ignoré", s_ok: "fait", s_error: "erreur",
    bk_hint: "Instantanés automatiques d'une instance pris juste avant chaque import. Pour revenir en arrière, importez l'un de ces fichiers avec « écraser » activé (les éléments créés par l'import ne sont pas supprimés).",
    bk_empty: "Aucune sauvegarde.", date: "Date", size: "Taille", file: "Fichier",
    changes: "{0} changement(s)", loading: "Chargement…",
  },
};
const lang = (navigator.language || "en").toLowerCase().startsWith("fr") ? "fr" : "en";
document.documentElement.lang = lang;
const t = (k, ...args) => {
  let s = I18N[lang][k] ?? I18N.en[k] ?? k;
  args.forEach((v, i) => { s = s.replace(`{${i}}`, v); });
  return s;
};

// ---------------------------------------------------------------- helpers
// Names come from remote servers: always build DOM nodes, never innerHTML.
function h(tag, props, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "class") el.className = v;
    else if (k === "value" || k === "checked" || k === "disabled") el[k] = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : String(kid));
  return el;
}

// Feather-style line icons (static strings, parsed as SVG).
const ICONS = {
  server: '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><path d="M6 6h.01M6 18h.01"/>',
  upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M17 8l-5-5-5 5"/><path d="M12 3v12"/>',
  download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/>',
  archive: '<path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  refresh: '<path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.5 9a9 9 0 0 1 14.9-3.4L23 10M1 14l4.6 4.4A9 9 0 0 0 20.5 15"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.3-4.3"/>',
  check: '<path d="M20 6L9 17l-5-5"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  monitor: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>',
};
function icon(name) {
  const doc = new DOMParser().parseFromString(
    `<svg xmlns="http://www.w3.org/2000/svg" class="icon" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`, "image/svg+xml");
  return document.importNode(doc.documentElement, true);
}

// Same mark as logo.svg, drawn with currentColor so it sits on the coloured header.
function logoMark() {
  const doc = new DOMParser().parseFromString(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" aria-hidden="true">
       <circle cx="32" cy="32" r="30" fill="currentColor" fill-opacity=".22"/>
       <g fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">
         <path d="M15 24h31M39 17l7 7-7 7"/><path d="M49 41H18M25 34l-7 7 7 7"/></g></svg>`, "image/svg+xml");
  return document.importNode(doc.documentElement, true);
}

function toast(msg, kind = "") {
  const el = h("div", { class: `toast ${kind}` }, msg);
  document.getElementById("toasts").append(el);
  setTimeout(() => el.remove(), kind === "error" ? 9000 : 4000);
}

async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : `HTTP ${res.status}`);
  }
  return data;
}

// Runs fn while the button is disabled; toolbar buttons keep their icon and only swap the label.
async function busy(btn, label, fn) {
  const lbl = btn.querySelector(".lbl") || btn;
  const original = lbl.textContent;
  btn.disabled = true;
  if (label) lbl.textContent = label;
  try { return await fn(); } catch (e) { toast(e.message, "error"); } finally { btn.disabled = false; lbl.textContent = original; }
}

const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : "");
const slug = (s) => String(s).replace(/[^A-Za-z0-9._-]+/g, "_");
const SECTIONS = ["customFormats", "qualityProfiles", "metadataProfiles", "qualityDefinitions", "naming", "mediaManagement", "appProfiles", "indexerProxies", "indexers"];
const CONFIG_SECTIONS = ["naming", "mediaManagement"];
const NAME_KEY = { customFormats: "name", qualityProfiles: "name", qualityDefinitions: "quality", metadataProfiles: "name", appProfiles: "name", indexerProxies: "name", indexers: "name" };
const NOT_BY_DEFAULT = ["mediaManagement"]; // host-level settings: opt-in
const label = (section, name) => (CONFIG_SECTIONS.includes(section) ? t(`sec_${section}`) : name);
const onOff = (v) => t(v ? "on" : "off");

// ---------------------------------------------------------------- theme
const THEMES = ["auto", "light", "dark"];
const THEME_ICON = { auto: "monitor", light: "sun", dark: "moon" };
function storage(op, key, value) {
  try { return op === "get" ? localStorage.getItem(key) : localStorage.setItem(key, value); } catch { return null; }
}
function applyTheme(mode) {
  if (mode === "auto") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = mode;
}
let themeMode = THEMES.includes(storage("get", "portarr-theme")) ? storage("get", "portarr-theme") : "auto";
applyTheme(themeMode);

function renderHeader() {
  const btn = h("button", { class: "iconBtn", title: t(`theme_${themeMode}`), "aria-label": t(`theme_${themeMode}`), onclick: () => {
    themeMode = THEMES[(THEMES.indexOf(themeMode) + 1) % THEMES.length];
    storage("set", "portarr-theme", themeMode);
    applyTheme(themeMode);
    renderHeader();
  } }, icon(THEME_ICON[themeMode]));
  document.getElementById("header").replaceChildren(
    h("a", { class: "brand", href: "/" }, logoMark(), h("span", null, "Portarr")), h("div", { class: "spacer" }), btn);
}

// ---------------------------------------------------------------- state & shell
const S = {
  tab: "instances",
  instances: [],
  editing: null, // null | "new" | instance id
  exp: { id: "", bundle: null, sel: {} },
  imp: { mode: "file", text: "", srcId: "", targetId: "", overwrite: false, bundle: null, plan: null, sel: {}, result: null },
};

const TABS = [["instances", "server"], ["export", "upload"], ["import", "download"], ["backups", "archive"]];

function renderTabs() {
  document.getElementById("tabs").replaceChildren(...TABS.map(([id, ic]) =>
    h("button", { class: S.tab === id ? "active" : "", onclick: () => { S.tab = id; render(); } }, icon(ic), t(`tab_${id}`))));
}

const tools = { set: (list) => document.getElementById("toolbar").replaceChildren(...list.filter(Boolean)) };
function toolBtn(iconName, text, onclick, { primary = false, disabled = false } = {}) {
  return h("button", { class: `tool${primary ? " primary" : ""}`, title: text, onclick, disabled }, icon(iconName), h("span", { class: "lbl" }, text));
}
function setToolLabel(btn, text) {
  btn.querySelector(".lbl").textContent = text;
  btn.title = text;
}

async function loadInstances() {
  S.instances = await api("/api/instances");
}

function instanceSelect(value, onchange, exclude) {
  const opts = S.instances.filter((i) => i.id !== exclude);
  const sel = h("select", { onchange: (e) => onchange(e.target.value) },
    opts.map((i) => h("option", { value: i.id }, `${i.name} (${cap(i.app)})`)));
  sel.value = opts.some((i) => i.id === value) ? value : opts[0]?.id ?? "";
  return sel;
}

async function render() {
  renderTabs();
  tools.set([]);
  const view = document.getElementById("view");
  view.replaceChildren(h("p", { class: "hint" }, t("loading")));
  try {
    await loadInstances();
    const node = await { instances: viewInstances, export: viewExport, import: viewImport, backups: viewBackups }[S.tab]();
    view.replaceChildren(node);
  } catch (e) {
    view.replaceChildren(h("p", { class: "err", style: "margin:0" }, e.message));
  }
}

function needInstances() {
  tools.set([toolBtn("plus", t("inst_add"), () => { S.tab = "instances"; S.editing = "new"; render(); }, { primary: true })]);
  return h("div", { class: "card" }, h("p", { class: "hint", style: "margin:0" }, t("inst_empty")));
}

// ---------------------------------------------------------------- instances
function viewInstances() {
  tools.set([toolBtn("plus", t("inst_add"), () => { S.editing = "new"; render(); }, { primary: !S.editing, disabled: !!S.editing })]);
  const list = S.instances.length
    ? S.instances.map((i) => h("div", { class: "card" },
      h("div", { class: "row spread" },
        h("div", { class: "grow" },
          h("div", { class: "row" }, h("strong", { class: "name" }, i.name), h("span", { class: `badge b-${i.app}` }, cap(i.app))),
          h("div", { class: "hint", style: "margin:0" }, i.url, i.verify_ssl ? "" : " · TLS unverified")),
        h("div", { class: "row" },
          h("button", { onclick: (e) => busy(e.currentTarget, "…", async () => {
            const s = await api(`/api/instances/${i.id}/test`, { method: "POST" });
            toast(t("connected", cap(s.app), s.version), "ok");
          }) }, t("test")),
          h("button", { onclick: () => { S.editing = i.id; render(); } }, t("edit")),
          h("button", { class: "danger", onclick: async () => {
            if (!confirm(t("delete_confirm", i.name))) return;
            try { await api(`/api/instances/${i.id}`, { method: "DELETE" }); render(); } catch (e) { toast(e.message, "error"); }
          } }, t("delete"))))))
    : [h("p", { class: "hint" }, t("inst_empty"))];

  return h("div", null, h("h2", null, t("tab_instances")), h("p", { class: "hint" }, t("inst_hint")), list, S.editing ? instanceForm() : null);
}

function instanceForm() {
  const cur = S.instances.find((i) => i.id === S.editing);
  const name = h("input", { type: "text", value: cur?.name ?? "", placeholder: "Radarr 4K", autocomplete: "off" });
  const url = h("input", { type: "url", value: cur?.url ?? "", placeholder: "http://192.168.1.10:7878", autocomplete: "off" });
  const key = h("input", { type: "password", value: "", autocomplete: "off", placeholder: cur ? t("api_key_keep") : "" });
  const ssl = h("input", { type: "checkbox", checked: cur ? cur.verify_ssl : true });
  const save = h("button", { class: "primary", onclick: (e) => busy(e.currentTarget, "…", async () => {
    const body = { name: name.value, url: url.value, api_key: key.value, verify_ssl: ssl.checked };
    await api(cur ? `/api/instances/${cur.id}` : "/api/instances", { method: cur ? "PUT" : "POST", body });
    S.editing = null;
    toast(t("saved"), "ok");
    render();
  }) }, t("save"));
  return h("div", { class: "card" },
    h("h3", null, cur ? t("inst_edit") : t("inst_add")),
    h("label", { class: "field" }, h("span", null, t("name")), name),
    h("label", { class: "field" }, h("span", null, `${t("url")} — ${t("url_hint")}`), url),
    h("label", { class: "field" }, h("span", null, `${t("api_key")} — ${t("api_key_where")}`), key),
    h("label", { class: "row", style: "margin-bottom:14px" }, ssl, t("verify_ssl")),
    h("div", { class: "row" }, save, h("button", { onclick: () => { S.editing = null; render(); } }, t("cancel"))));
}

// ---------------------------------------------------------------- selection tree (shared by export & import)
/**
 * rows: {section: [{name, action?, status?, changes?, warnings?, error?, selectable, note?}]}
 * sel : {section: Set(name)}  (mutated)
 */
function selectionTree(rows, sel, { bundle, onChange = () => {}, readonly = false } = {}) {
  const boxes = {}; // section -> Map(name -> input)
  const headers = [];
  const refreshHeaders = () => headers.forEach((fn) => fn());

  const setBox = (section, name, checked) => {
    const box = boxes[section]?.get(name);
    if (!box || box.disabled) return;
    box.checked = checked;
    sel[section] ??= new Set();
    checked ? sel[section].add(name) : sel[section].delete(name);
  };

  const onToggle = (section, name, checked) => {
    setBox(section, name, checked);
    if (checked && bundle) {
      // pull in what the item depends on: custom formats scored by a profile, the sync profile of an indexer
      if (section === "qualityProfiles") {
        const p = bundle.qualityProfiles.find((x) => x.name === name);
        (p?.formatItems ?? []).forEach((fi) => setBox("customFormats", fi.name, true));
      } else if (section === "indexers") {
        const i = bundle.indexers.find((x) => x.name === name);
        if (i?.appProfile) setBox("appProfiles", i.appProfile, true);
      }
    }
    refreshHeaders();
    onChange();
  };

  const blocks = SECTIONS.filter((s) => rows[s]?.length).map((section) => {
    boxes[section] = new Map();
    const selectable = rows[section].filter((r) => r.selectable);
    const all = readonly ? null : h("input", { type: "checkbox", disabled: !selectable.length, onclick: (e) => e.stopPropagation(), onchange: (e) => {
      selectable.forEach((r) => setBox(section, r.name, e.target.checked));
      refreshHeaders();
      onChange();
    } });
    const count = readonly ? null : h("span", { class: "badge" });
    if (!readonly) {
      headers.push(() => {
        const n = (sel[section] ?? new Set()).size;
        all.checked = selectable.length > 0 && n === selectable.length;
        all.indeterminate = n > 0 && n < selectable.length;
        count.textContent = `${n} / ${rows[section].length}`;
      });
    }

    const items = rows[section].map((r) => {
      const box = readonly ? null : h("input", { type: "checkbox", checked: r.selectable && (sel[section]?.has(r.name) ?? false), disabled: !r.selectable,
        onchange: (e) => onToggle(section, r.name, e.target.checked) });
      if (box) boxes[section].set(r.name, box);
      const status = r.status ? h("span", { class: `badge b-${r.status}` }, t(`s_${r.status}`)) : null;
      const action = r.action ? h("span", { class: `badge b-${r.action}` }, t(`a_${r.action}`)) : null;
      return h("li", { class: r.selectable || readonly ? "" : "off" },
        h("label", null, box, h("span", { class: "name grow" }, label(section, r.name)), action, status),
        r.error ? h("div", { class: "err" }, r.error) : null,
        (r.warnings ?? []).map((w) => h("div", { class: "warn" }, `⚠ ${w}`)),
        r.changes?.length
          ? h("details", { class: "detail" }, h("summary", null, t("changes", r.changes.length)),
            h("ul", null, r.changes.map((c) => h("li", null, c))))
          : null,
        r.note ? h("div", { class: "detail" }, r.note) : null);
    });

    return h("details", { class: "section card", open: true },
      h("summary", null, all, h("span", { class: "grow" }, t(`sec_${section}`)), count),
      h("ul", null, items));
  });
  refreshHeaders();
  return h("div", null, blocks);
}

// ---------------------------------------------------------------- export
function bundleRows(bundle) {
  const rows = {};
  rows.customFormats = (bundle.customFormats ?? []).map((c) => ({ name: c.name, selectable: true, note: t("note_conditions", c.specifications.length) }));
  rows.qualityProfiles = (bundle.qualityProfiles ?? []).map((p) => ({
    name: p.name, selectable: true,
    note: t("note_profile", p.items.filter((i) => i.allowed).length, p.formatItems.length),
  }));
  rows.metadataProfiles = (bundle.metadataProfiles ?? []).map((p) => ({
    name: p.name, selectable: true, note: t("note_metadata", p.primaryAlbumTypes.length, p.secondaryAlbumTypes.length, p.releaseStatuses.length),
  }));
  rows.qualityDefinitions = (bundle.qualityDefinitions ?? []).map((d) => ({
    name: d.quality, selectable: true, note: t("note_sizes", d.minSize ?? "–", d.preferredSize ?? "–", d.maxSize ?? "∞"),
  }));
  CONFIG_SECTIONS.forEach((s) => { if (bundle[s]) rows[s] = [{ name: s, selectable: true }]; });
  rows.appProfiles = (bundle.appProfiles ?? []).map((p) => ({
    name: p.name, selectable: true,
    note: t("note_sync", onOff(p.enableRss), onOff(p.enableAutomaticSearch), onOff(p.enableInteractiveSearch), p.minimumSeeders),
  }));
  rows.indexerProxies = (bundle.indexerProxies ?? []).map((p) => ({
    name: p.name, selectable: true, note: [p.implementation, p.secretFields?.length ? t("note_secrets", p.secretFields.join(", ")) : null].filter(Boolean).join(" · "),
  }));
  rows.indexers = (bundle.indexers ?? []).map((i) => ({
    name: i.name, selectable: true,
    note: [t("note_indexer", i.definitionName || i.implementation, i.priority, i.appProfile ?? "–"), i.secretFields?.length ? t("note_secrets", i.secretFields.join(", ")) : null].filter(Boolean).join(" · "),
  }));
  return rows;
}

function filterBundle(bundle, sel) {
  const out = { ...bundle };
  for (const s of SECTIONS) {
    if (CONFIG_SECTIONS.includes(s)) { if (!sel[s]?.has(s)) delete out[s]; continue; }
    if (s in out) out[s] = out[s].filter((i) => sel[s]?.has(i[NAME_KEY[s]]));
  }
  return out;
}

function viewExport() {
  if (!S.instances.length) return needInstances();
  const e = S.exp;
  if (!S.instances.some((i) => i.id === e.id)) { e.id = S.instances[0].id; e.bundle = null; }
  const body = h("div");
  const total = () => Object.values(e.sel).reduce((n, s) => n + s.size, 0);

  const dl = toolBtn("download", t("download_short"), () => {
    const b = e.bundle;
    const json = JSON.stringify(filterBundle(b, e.sel), null, 2);
    const a = h("a", { href: URL.createObjectURL(new Blob([json], { type: "application/json" })),
      download: `${b.source.app}-${slug(b.source.instanceName)}-${new Date().toISOString().slice(0, 10)}.json` });
    document.body.append(a); a.click(); a.remove();
  }, { disabled: true });
  const update = () => { dl.disabled = !e.bundle || total() === 0; };

  const select = instanceSelect(e.id, (v) => { e.id = v; e.bundle = null; body.replaceChildren(); update(); });
  const load = toolBtn("refresh", t("load"), (ev) => busy(ev.currentTarget, t("loading"), async () => {
    e.id = select.value;
    e.bundle = await api(`/api/instances/${e.id}/export`);
    const rows = bundleRows(e.bundle);
    e.sel = {};
    SECTIONS.forEach((s) => { if (rows[s]?.length) e.sel[s] = new Set(NOT_BY_DEFAULT.includes(s) ? [] : rows[s].map((r) => r.name)); });
    showBundle();
  }), { primary: true });
  tools.set([load, dl]);

  const showBundle = () => {
    const b = e.bundle;
    body.replaceChildren(
      h("p", { class: "hint" }, t("loaded_from", cap(b.source.app), b.source.version), " · ", t("scored_cf_note")),
      selectionTree(bundleRows(b), e.sel, { bundle: b, onChange: update }));
    update();
  };
  if (e.bundle) showBundle();

  return h("div", null, h("h2", null, t("tab_export")), h("p", { class: "hint" }, t("exp_hint")),
    h("div", { class: "card" }, h("label", { class: "field", style: "margin:0" }, h("span", null, t("instance")), select)), body);
}

// ---------------------------------------------------------------- import
function planRows(plan) {
  const rows = {};
  for (const [section, items] of Object.entries(plan.sections)) {
    rows[section] = items.map((i) => ({ ...i, selectable: i.action === "create" || i.action === "update" }));
  }
  return rows;
}

function viewImport() {
  if (!S.instances.length) return needInstances();
  const m = S.imp;
  if (m.result) return importResult();
  if (!S.instances.some((i) => i.id === m.targetId)) m.targetId = S.instances[0].id;

  const out = h("div");
  const count = () => Object.values(m.sel).reduce((n, s) => n + s.size, 0);
  const apply = toolBtn("check", t("apply_n", 0), (ev) => {
    const target = S.instances.find((i) => i.id === m.targetId);
    if (!confirm(t("confirm_apply", count(), target.name))) return;
    return busy(ev.currentTarget, t("applying"), async () => {
      const selection = Object.fromEntries(Object.entries(m.sel).map(([s, set]) => [s, [...set]]));
      m.result = await api(`/api/instances/${m.targetId}/import/apply`, { method: "POST", body: { bundle: m.bundle, selection, overwrite: m.overwrite } });
      render();
    });
  }, { disabled: true });
  const updateApply = () => {
    setToolLabel(apply, t("apply_n", count()));
    apply.disabled = !m.plan || count() === 0;
  };

  const target = instanceSelect(m.targetId, (v) => { m.targetId = v; m.plan = null; render(); });
  const text = h("textarea", { placeholder: t("paste_ph"), oninput: (e) => { m.text = e.target.value; } });
  text.value = m.text;
  const file = h("input", { type: "file", accept: ".json,application/json", onchange: async (e) => {
    const f = e.target.files[0];
    if (f) { m.text = await f.text(); text.value = m.text; }
  } });
  const srcSelect = instanceSelect(m.srcId, (v) => { m.srcId = v; }, m.targetId);
  const fileBox = h("div", null, h("label", { class: "field" }, h("span", null, t("choose_file")), file), text);
  const instBox = h("div", null, h("label", { class: "field", style: "margin:0" }, h("span", null, t("instance")), srcSelect));
  const modes = h("div", { class: "seg" });
  const setMode = (mode) => {
    m.mode = mode;
    fileBox.hidden = mode !== "file";
    instBox.hidden = mode !== "instance";
    modes.replaceChildren(
      h("button", { class: mode === "file" ? "active" : "", onclick: () => setMode("file") }, t("src_file")),
      h("button", { class: mode === "instance" ? "active" : "", onclick: () => setMode("instance") }, t("src_instance")));
  };
  setMode(m.mode);

  const overwrite = h("input", { type: "checkbox", checked: m.overwrite, onchange: (e) => { m.overwrite = e.target.checked; if (m.bundle) analyse.click(); } });
  const analyse = toolBtn("search", t("analyse"), (ev) => busy(ev.currentTarget, t("analysing"), async () => {
    m.targetId = target.value;
    let bundle;
    if (m.mode === "instance") {
      m.srcId = srcSelect.value;
      if (!m.srcId) throw new Error(t("need_source"));
      if (m.srcId === m.targetId) throw new Error(t("same_instance"));
      bundle = await api(`/api/instances/${m.srcId}/export`);
    } else {
      if (!m.text.trim()) throw new Error(t("need_source"));
      bundle = await api("/api/import/parse", { method: "POST", body: { text: m.text } });
    }
    m.bundle = bundle;
    m.plan = await api(`/api/instances/${m.targetId}/import/preview`, { method: "POST", body: { bundle, overwrite: m.overwrite } });
    m.sel = {};
    for (const [s, items] of Object.entries(m.plan.sections)) {
      m.sel[s] = new Set(items.filter((i) => (i.action === "create" || i.action === "update") && !NOT_BY_DEFAULT.includes(s)).map((i) => i.name));
    }
    showPlan();
  }), { primary: true });
  tools.set([analyse, apply]);

  const showPlan = () => {
    const sum = m.plan.summary;
    out.replaceChildren(
      h("div", { class: "summary" },
        ["create", "update", "unchanged", "skip"].map((k) => h("span", { class: `badge b-${k}` }, `${sum[k]} ${t(`a_${k}`)}`))),
      selectionTree(planRows(m.plan), m.sel, { bundle: m.bundle, onChange: updateApply }));
    updateApply();
  };

  const node = h("div", null, h("h2", null, t("tab_import")), h("p", { class: "hint" }, t("imp_hint")),
    h("div", { class: "card" }, h("h3", null, `1. ${t("source")}`), modes, fileBox, instBox),
    h("div", { class: "card" }, h("h3", null, `2. ${t("target")}`), h("div", { class: "row" }, h("div", { class: "grow" }, target)),
      h("label", { class: "row", style: "margin-top:14px;flex-wrap:nowrap;align-items:flex-start" }, overwrite, h("span", { class: "grow" }, t("overwrite"))), h("div", { class: "hint", style: "margin:6px 0 0" }, t("overwrite_hint"))),
    out);
  if (m.plan) showPlan();
  return node;
}

function importResult() {
  const m = S.imp;
  const r = m.result;
  tools.set([toolBtn("plus", t("new_import"), () => { S.imp = { ...m, bundle: null, plan: null, sel: {}, result: null }; render(); }, { primary: true })]);
  const ok = Object.values(r.sections).flat().filter((i) => i.status === "ok").length;
  return h("div", null, h("h2", null, t("done")),
    h("div", { class: "summary" },
      h("span", { class: "badge b-ok" }, `${ok} ${t("s_ok")}`),
      r.summary.error ? h("span", { class: "badge b-error" }, `${r.summary.error} ${t("s_error")}`) : null),
    r.backup ? h("p", { class: "hint" }, `${t("backup_saved")} `, h("a", { href: `/api/backups/${encodeURIComponent(r.backup)}` }, r.backup)) : null,
    selectionTree(Object.fromEntries(Object.entries(r.sections).map(([s, items]) => [s,
      items.filter((i) => i.status).map((i) => ({ ...i, action: null, selectable: false }))])), {}, { readonly: true }));
}

// ---------------------------------------------------------------- backups
async function viewBackups() {
  tools.set([toolBtn("refresh", t("refresh"), () => render())]);
  const files = await api("/api/backups");
  return h("div", null, h("h2", null, t("tab_backups")), h("p", { class: "hint" }, t("bk_hint")),
    files.length
      ? h("div", { class: "card" }, h("table", null,
        h("tr", null, h("th", null, t("file")), h("th", null, t("date")), h("th", null, t("size"))),
        files.map((f) => h("tr", null,
          h("td", null, h("a", { href: `/api/backups/${encodeURIComponent(f.name)}`, download: f.name }, f.name)),
          h("td", null, new Date(f.mtime * 1000).toLocaleString()),
          h("td", null, `${Math.max(1, Math.round(f.size / 1024))} KB`)))))
      : h("p", { class: "hint" }, t("bk_empty")));
}

renderHeader();
render();
