"use strict";

// ---------------------------------------------------------------- i18n
const I18N = {
  en: {
    tab_instances: "Instances", tab_export: "Export", tab_import: "Import", tab_backups: "Backups",
    theme_auto: "Theme: automatic", theme_light: "Theme: light", theme_dark: "Theme: dark",
    inst_hint: "Your Radarr, Sonarr, Lidarr, Whisparr and Prowlarr servers. API keys are stored on this server only and are never sent back to the browser.", inst_add: "Add instance", inst_edit: "Edit instance",
    name: "Name", url: "URL", url_hint: "Include the URL base if you use one, e.g. http://192.168.1.10:7878/radarr",
    api_key: "API key", api_key_keep: "(empty = keep current key)", api_key_where: "Found in Settings → General → Security",
    verify_ssl: "Verify the TLS certificate", save: "Test & save", cancel: "Cancel", test: "Test", edit: "Edit", delete: "Delete",
    delete_confirm: "Delete the instance “{0}”? (Nothing is changed on the server itself.)",
    connected: "Connected to {0} {1}", saved: "Saved",
    exp_hint: "Pick what to export from an instance. Everything is referenced by name so it can be imported on another instance.",
    imp_hint: "Import a bundle on an instance. You always get a preview first, and the target is backed up before anything is written.",
    instance: "Instance", refresh: "Refresh",
    loaded_from: "Loaded from {0} {1}", scored_cf_note: "Selecting a profile also selects what it depends on.",
    sec_customFormats: "Custom formats", sec_qualityProfiles: "Quality profiles", sec_qualityDefinitions: "Quality sizes",
    sec_naming: "Naming", sec_mediaManagement: "Media management",
    sec_metadataProfiles: "Metadata profiles", sec_appProfiles: "Sync profiles", sec_indexers: "Indexers", sec_indexerProxies: "Indexer proxies",
    note_conditions: "{0} condition(s)", note_profile: "{0} enabled qualities · {1} scored formats",
    note_sizes: "min {0} · preferred {1} · max {2} MB/min", note_metadata: "{0} album types · {1} secondary types · {2} statuses", note_sync: "RSS {0} · automatic {1} · interactive {2} · min. seeders {3}",
    note_indexer: "{0} · priority {1} · profile {2}", on: "on", off: "off",
    note_secrets: "Secrets are never exported: {0}", src_file: "A file or pasted JSON", src_instance: "Another instance",
    paste_ph: "…or paste here a Portarr export or TRaSH-Guides custom format JSON", overwrite: "Overwrite existing items that differ (custom formats, quality profiles, sync profiles, indexers…)",
    overwrite_hint: "Quality sizes, naming and media management are always updated when selected.", analysing: "Analysing…", apply_n: "Apply ({0})", applying: "Applying…",
    confirm_apply: "Apply {0} change(s) on “{1}”? A backup of its current state is saved first.",
    done: "Done", new_import: "New import", backup_saved: "Previous state of the target saved as", same_instance: "Source and target must differ",
    a_create: "new", a_update: "update", a_unchanged: "identical", a_skip: "skipped", s_ok: "done", s_error: "error",
    bk_hint: "Automatic snapshots of an instance taken just before each import. To roll back, import one of these files with “overwrite” enabled (items created by the import are not deleted).",
    bk_empty: "No backup yet.", date: "Date", size: "Size", file: "File",
    changes: "{0} change(s)", loading: "Loading…",
    exp_step1: "Instance", exp_step2: "Content", exp_step3: "File",
    exp_pick_title: "Instance to export from", exp_content_title: "What to include",
    exp_selected: "{0} item(s) selected", exp_no_secrets: "no API key or password is included", exp_none: "Select at least one item to export.",
    exp_loading_msg: "Loading the configuration…", download_file: "Download the file",
    exp_saved_title: "File saved", exp_saved_text: "{0} is in your browser's downloads folder. What now?",
    exp_next_keep: "Keep it as a backup, or reuse it on another instance of yours: Import → A file.",
    exp_next_share: "Send it to someone: it holds your configuration only, never an API key or a password.",
    exp_goto_import: "Go to Import",
    imp_step1: "Choose", imp_step2: "Review", imp_step3: "Done",
    imp_target_title: "Instance to configure", imp_target_hint: "The configuration is applied to this instance. Nothing changes before you confirm.",
    imp_source_title: "Configuration to apply",
    src_pasted: "pasted JSON", pick_file: "Choose a .json file", file_chosen: "File: {0}", or_paste: "or paste its content:",
    imp_need_file: "Choose a file, or paste its content, to continue.", imp_need_inst: "Choose the instance to copy from.",
    imp_ready: "Next, you review every change: nothing is written to {0} yet.", imp_review: "Review changes",
    rev_from: "From", rev_to: "To", rev_change: "Change", rev_back: "Back",
    rev_info: "{0} change(s) will be applied to {1}. A backup is saved first.",
    rev_nothing: "Nothing to apply: {0} already matches.", rev_pick: "Select at least one change to apply.",
    done_text: "{0} change(s) applied to {1}.", done_undo: "To undo: Import → A file, choose the backup below, and tick “overwrite”.",
    inst_empty_title: "No instance yet", inst_empty_cta: "Add your first Radarr, Sonarr, Lidarr, Whisparr or Prowlarr instance to get started.",
    update_available: "Version {0} is available", update_title: "You run v{0}. Click to see how to update.",
    inst_add_tile: "Add an instance", tls_off: "TLS certificate not verified", build_title: "Built from commit {0}",
    imp_no_same_app: "There is no other {0} instance to copy from. Add one in Instances, or use a file.",
    src_trash: "TRaSH Guides", trash_only: "The TRaSH Guides only cover Radarr and Sonarr: choose a Radarr or Sonarr target instance.",
    trash_loading: "Downloading the TRaSH Guides… (about 25 MB, first time only)", trash_profile: "Quality profile", trash_pick: "Choose a profile…",
    trash_required: "Required by the profile", trash_groups: "Optional format groups", trash_group_default: "recommended", trash_req: "required",
    trash_updated: "Guides downloaded on {0}", trash_refresh: "Update the guides", trash_count: "{0} formats selected", retry: "Retry",
    need_profile: "Choose a TRaSH profile first", trash_hint: "Scores come from the profile's score set. Ticked groups are the guides' recommendation; adjust freely, the preview comes next.",
  },
  fr: {
    tab_instances: "Instances", tab_export: "Export", tab_import: "Import", tab_backups: "Sauvegardes",
    theme_auto: "Thème : automatique", theme_light: "Thème : clair", theme_dark: "Thème : sombre",
    inst_hint: "Vos serveurs Radarr, Sonarr, Lidarr, Whisparr et Prowlarr. Les clés API restent sur ce serveur et ne sont jamais renvoyées au navigateur.", inst_add: "Ajouter", inst_edit: "Modifier l'instance",
    name: "Nom", url: "URL", url_hint: "Ajoutez l'URL Base si vous en utilisez une, ex. http://192.168.1.10:7878/radarr",
    api_key: "Clé API", api_key_keep: "(vide = conserver la clé actuelle)", api_key_where: "Dans Paramètres → Général → Sécurité",
    verify_ssl: "Vérifier le certificat TLS", save: "Tester et enregistrer", cancel: "Annuler", test: "Tester", edit: "Modifier", delete: "Supprimer",
    delete_confirm: "Supprimer l'instance « {0} » ? (Rien n'est modifié sur le serveur lui-même.)",
    connected: "Connecté à {0} {1}", saved: "Enregistré",
    exp_hint: "Choisissez ce qu'il faut exporter d'une instance. Tout est référencé par nom, ce qui permet de l'importer sur une autre instance.",
    imp_hint: "Importez un fichier sur une instance. Un aperçu est toujours affiché d'abord, et la cible est sauvegardée avant toute écriture.",
    instance: "Instance", refresh: "Actualiser",
    loaded_from: "Chargé depuis {0} {1}", scored_cf_note: "Cocher un profil coche aussi ce dont il dépend.",
    sec_customFormats: "Formats personnalisés", sec_qualityProfiles: "Profils de qualité", sec_qualityDefinitions: "Tailles par qualité",
    sec_naming: "Nommage", sec_mediaManagement: "Gestion des médias",
    sec_metadataProfiles: "Profils de métadonnées", sec_appProfiles: "Profils de synchronisation", sec_indexers: "Indexeurs", sec_indexerProxies: "Proxys d'indexeurs",
    note_conditions: "{0} condition(s)", note_profile: "{0} qualités actives · {1} formats notés",
    note_sizes: "min {0} · préféré {1} · max {2} Mo/min", note_metadata: "{0} types d'album · {1} types secondaires · {2} statuts", note_sync: "RSS {0} · automatique {1} · interactif {2} · seeders min. {3}",
    note_indexer: "{0} · priorité {1} · profil {2}", on: "oui", off: "non",
    note_secrets: "Les secrets ne sont jamais exportés : {0}", src_file: "Un fichier ou du JSON collé", src_instance: "Une autre instance",
    paste_ph: "…ou collez ici un export Portarr ou un JSON de format personnalisé TRaSH-Guides", overwrite: "Écraser les éléments existants qui diffèrent (formats personnalisés, profils de qualité, profils de synchronisation, indexeurs…)",
    overwrite_hint: "Les tailles par qualité, le nommage et la gestion des médias sont toujours mis à jour s'ils sont cochés.", analysing: "Analyse…", apply_n: "Appliquer ({0})", applying: "Application…",
    confirm_apply: "Appliquer {0} changement(s) sur « {1} » ? L'état actuel est d'abord sauvegardé.",
    done: "Terminé", new_import: "Nouvel import", backup_saved: "État précédent de la cible sauvegardé sous", same_instance: "La source et la cible doivent être différentes",
    a_create: "nouveau", a_update: "mise à jour", a_unchanged: "identique", a_skip: "ignoré", s_ok: "fait", s_error: "erreur",
    bk_hint: "Instantanés automatiques d'une instance pris juste avant chaque import. Pour revenir en arrière, importez l'un de ces fichiers avec « écraser » activé (les éléments créés par l'import ne sont pas supprimés).",
    bk_empty: "Aucune sauvegarde.", date: "Date", size: "Taille", file: "Fichier",
    changes: "{0} changement(s)", loading: "Chargement…",
    exp_step1: "Instance", exp_step2: "Contenu", exp_step3: "Fichier",
    exp_pick_title: "Instance à exporter", exp_content_title: "Ce qu'il faut inclure",
    exp_selected: "{0} élément(s) sélectionné(s)", exp_no_secrets: "aucune clé API ni mot de passe n'est inclus", exp_none: "Sélectionnez au moins un élément à exporter.",
    exp_loading_msg: "Chargement de la configuration…", download_file: "Télécharger le fichier",
    exp_saved_title: "Fichier enregistré", exp_saved_text: "{0} est dans le dossier de téléchargements de votre navigateur. Et maintenant ?",
    exp_next_keep: "Gardez-le comme sauvegarde, ou réutilisez-le sur une autre de vos instances : Import → Un fichier.",
    exp_next_share: "Envoyez-le à quelqu'un : il ne contient que votre configuration, jamais de clé API ni de mot de passe.",
    exp_goto_import: "Aller à l'Import",
    imp_step1: "Choisir", imp_step2: "Vérifier", imp_step3: "Terminé",
    imp_target_title: "Instance à configurer", imp_target_hint: "La configuration est appliquée à cette instance. Rien ne change avant votre confirmation.",
    imp_source_title: "Configuration à appliquer",
    src_pasted: "JSON collé", pick_file: "Choisir un fichier .json", file_chosen: "Fichier : {0}", or_paste: "ou collez son contenu :",
    imp_need_file: "Choisissez un fichier, ou collez son contenu, pour continuer.", imp_need_inst: "Choisissez l'instance à copier.",
    imp_ready: "Ensuite, vous vérifiez chaque changement : rien n'est encore écrit sur {0}.", imp_review: "Vérifier les changements",
    rev_from: "Depuis", rev_to: "Vers", rev_change: "Modifier", rev_back: "Retour",
    rev_info: "{0} changement(s) seront appliqués à {1}. Une sauvegarde est faite d'abord.",
    rev_nothing: "Rien à appliquer : {0} correspond déjà.", rev_pick: "Sélectionnez au moins un changement à appliquer.",
    done_text: "{0} changement(s) appliqué(s) à {1}.", done_undo: "Pour annuler : Import → Un fichier, choisissez la sauvegarde ci-dessous et cochez « écraser ».",
    inst_empty_title: "Aucune instance", inst_empty_cta: "Ajoutez votre première instance Radarr, Sonarr, Lidarr, Whisparr ou Prowlarr pour commencer.",
    update_available: "La version {0} est disponible", update_title: "Vous utilisez la v{0}. Cliquez pour voir comment mettre à jour.",
    inst_add_tile: "Ajouter une instance", tls_off: "certificat TLS non vérifié", build_title: "Construit depuis le commit {0}",
    imp_no_same_app: "Il n'y a pas d'autre instance {0} à copier. Ajoutez-en une dans Instances, ou utilisez un fichier.",
    src_trash: "TRaSH Guides", trash_only: "Les TRaSH Guides ne couvrent que Radarr et Sonarr : choisissez une instance cible Radarr ou Sonarr.",
    trash_loading: "Téléchargement des TRaSH Guides… (environ 25 Mo, la première fois seulement)", trash_profile: "Profil de qualité", trash_pick: "Choisir un profil…",
    trash_required: "Imposés par le profil", trash_groups: "Groupes de formats optionnels", trash_group_default: "recommandé", trash_req: "requis",
    trash_updated: "Guides téléchargés le {0}", trash_refresh: "Mettre à jour les guides", trash_count: "{0} formats sélectionnés", retry: "Réessayer",
    need_profile: "Choisissez d'abord un profil TRaSH", trash_hint: "Les scores viennent du jeu de scores du profil. Les groupes cochés sont la recommandation des guides ; ajustez librement, l'aperçu vient ensuite.",
  },
};
const LANGS = { fr: "Français", en: "English" };
// The browser's language by default; the FR | EN switch in the header overrides it and is remembered.
let lang = (navigator.language || "en").toLowerCase().startsWith("fr") ? "fr" : "en";
try { const saved = localStorage.getItem("portarr-lang"); if (saved in LANGS) lang = saved; } catch { /* storage can be blocked */ }
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

// replaceChildren() would print null and arrays as text; this keeps only real nodes and strings.
function fill(el, ...kids) {
  el.replaceChildren(...kids.flat(Infinity).filter((k) => k != null && k !== false).map((k) => (k.nodeType ? k : String(k))));
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
  back: '<path d="M19 12H5M12 19l-7-7 7-7"/>',
  up: '<path d="M12 19V5M5 12l7-7 7 7"/>',
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
  const langSwitch = h("div", { class: "langsw", role: "group", "aria-label": "Language" }, Object.entries(LANGS).map(([code, name]) =>
    h("button", { title: name, "aria-pressed": String(code === lang), onclick: () => setLang(code) }, code.toUpperCase())));
  document.getElementById("header").replaceChildren(
    h("a", { class: "brand", href: "/" }, logoMark(), h("span", null, "Portarr")), h("div", { class: "spacer" }), langSwitch, btn);
}

function setLang(code) {
  if (code === lang) return;
  lang = code;
  storage("set", "portarr-lang", code);
  document.documentElement.lang = code;
  renderHeader();
  paintVersion();
  render(); // rebuilds the current screen in the new language; choices already made are kept in S
}

// ---------------------------------------------------------------- state & shell
const S = {
  tab: "instances",
  instances: [],
  editing: null, // null | "new" | instance id
  version: null, // {version, commit}, from /api/version
  update: null, // {available, latest, current, url}, from /api/update
  exp: { id: "", bundle: null, sel: {}, error: null, saved: null },
  imp: { step: 1, mode: "file", text: "", fileName: "", sourceLabel: "", srcId: "", targetId: "", overwrite: false, bundle: null, plan: null, sel: {}, result: null,
    trash: { app: null, profiles: null, profileId: "", detail: null, selected: new Set(), error: null, fetchedAt: 0, open: new Map() } },
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

// The bottom bar is the one place for "what happens next": a short message and the next action(s).
const bar = {
  set(info, ...buttons) {
    const el = document.getElementById("actionbar");
    el.hidden = false;
    el.replaceChildren(h("div", { class: "msg grow" }, info), ...buttons.filter(Boolean));
  },
  clear() {
    const el = document.getElementById("actionbar");
    el.hidden = true;
    el.replaceChildren();
  },
};
function actionBtn(text, onclick, { primary = false, disabled = false, iconName = null } = {}) {
  return h("button", { class: primary ? "primary" : "", onclick, disabled }, iconName ? icon(iconName) : null, h("span", { class: "lbl" }, text));
}

// Progress indicator, shown in the toolbar zone. Steps already done can be clicked to go back.
function stepper(labels, current, goTo = {}) {
  return h("ol", { class: "steps" }, labels.map((label, i) => {
    const n = i + 1;
    const state = n < current ? "done" : n === current ? "current" : "todo";
    const inner = [h("span", { class: "dot" }, state === "done" ? icon("check") : String(n)), h("span", { class: "lbl" }, label)];
    return h("li", { class: `step ${state}`, "aria-current": state === "current" ? "step" : null },
      state === "done" && goTo[n] ? h("button", { onclick: goTo[n] }, inner) : h("span", { class: "stepin" }, inner));
  }));
}

async function loadInstances() {
  S.instances = await api("/api/instances");
}

function instanceSelect(value, onchange, exclude, app) {
  const opts = S.instances.filter((i) => i.id !== exclude && (!app || i.app === app));
  const sel = h("select", { onchange: (e) => onchange(e.target.value) },
    opts.map((i) => h("option", { value: i.id }, `${i.name} (${cap(i.app)})`)));
  sel.value = opts.some((i) => i.id === value) ? value : opts[0]?.id ?? "";
  return sel;
}

async function render() {
  renderTabs();
  tools.set([]);
  bar.clear();
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
  tools.set([]);
  bar.clear();
  return h("div", { class: "card empty" }, h("h3", null, t("inst_empty_title")), h("p", { class: "hint" }, t("inst_empty_cta")),
    h("button", { class: "primary", onclick: () => { S.tab = "instances"; S.editing = "new"; render(); } }, icon("plus"), " ", t("inst_add")));
}

// ---------------------------------------------------------------- instances
function viewInstances() {
  tools.set([]);
  const list = S.instances.length
    ? S.instances.map((i) => h("div", { class: "card" },
      h("div", { class: "row spread" },
        h("div", { class: "grow" },
          h("div", { class: "row" }, h("strong", { class: "name" }, i.name), h("span", { class: `badge b-${i.app}` }, cap(i.app))),
          h("div", { class: "hint", style: "margin:0" }, i.url, i.verify_ssl ? "" : ` · ${t("tls_off")}`)),
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
    : [];
  const addTile = h("button", { class: "addtile", onclick: () => { S.editing = "new"; render(); } }, icon("plus"), t("inst_add_tile"));

  return h("div", null, h("h2", null, t("tab_instances")), h("p", { class: "hint" }, t("inst_hint")), list,
    S.editing ? instanceForm() : S.instances.length ? addTile : needInstances());
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
  if (!S.instances.some((i) => i.id === e.id)) Object.assign(e, { id: S.instances[0].id, bundle: null, saved: null, error: null });
  const total = () => Object.values(e.sel).reduce((n, s) => n + s.size, 0);
  const statusBox = h("div"), treeBox = h("div"), savedBox = h("div", { style: "scroll-margin-bottom: 100px" }); // keep clear of the action bar

  function chrome() {
    tools.set([stepper([t("exp_step1"), t("exp_step2"), t("exp_step3")], e.saved ? 3 : e.bundle ? 2 : 1)]);
    const n = total();
    const info = e.bundle ? (n ? `${t("exp_selected", n)} · ${t("exp_no_secrets")}` : t("exp_none")) : e.error ? "" : t("exp_loading_msg");
    bar.set(info, actionBtn(t("download_file"), download, { primary: true, iconName: "download", disabled: !e.bundle || n === 0 }));
  }
  function showStatus() {
    fill(statusBox, 
      !e.bundle && !e.error ? h("p", { class: "hint" }, t("loading")) : null,
      e.error ? h("div", { class: "card" }, h("p", { class: "err", style: "margin:0 0 10px" }, e.error), h("button", { onclick: load }, t("retry"))) : null);
  }
  function showTree() {
    fill(treeBox, e.bundle ? h("div", null,
      h("h3", { style: "margin:18px 0 6px" }, t("exp_content_title")),
      h("p", { class: "hint" }, t("loaded_from", cap(e.bundle.source.app), e.bundle.source.version), " · ", t("scored_cf_note")),
      selectionTree(bundleRows(e.bundle), e.sel, { bundle: e.bundle, onChange: chrome })) : null);
  }
  function showSaved() {
    fill(savedBox, e.saved ? h("div", { class: "card note" },
      h("h3", null, "✓ ", t("exp_saved_title")),
      h("p", { class: "hint", style: "margin:0" }, t("exp_saved_text", e.saved)),
      h("ul", null, h("li", null, t("exp_next_keep")), h("li", null, t("exp_next_share"))),
      h("div", { style: "margin-top:12px" }, h("button", { onclick: () => { S.tab = "import"; render(); } }, t("exp_goto_import")))) : null);
  }
  function download() {
    const b = e.bundle;
    const name = `${b.source.app}-${slug(b.source.instanceName)}-${new Date().toISOString().slice(0, 10)}.json`;
    const a = h("a", { href: URL.createObjectURL(new Blob([JSON.stringify(filterBundle(b, e.sel), null, 2)], { type: "application/json" })), download: name });
    document.body.append(a); a.click(); a.remove();
    e.saved = name;
    showSaved();
    chrome();
    savedBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
  async function load() {
    const id = e.id;
    Object.assign(e, { bundle: null, error: null, saved: null });
    showStatus(); showTree(); showSaved(); chrome();
    try {
      const b = await api(`/api/instances/${id}/export`);
      if (e.id !== id) return; // the user picked another instance meanwhile
      e.bundle = b;
      const rows = bundleRows(b);
      e.sel = {};
      SECTIONS.forEach((s) => { if (rows[s]?.length) e.sel[s] = new Set(NOT_BY_DEFAULT.includes(s) ? [] : rows[s].map((r) => r.name)); });
    } catch (err) {
      if (e.id !== id) return;
      e.error = err.message;
    }
    showStatus(); showTree(); chrome();
  }

  const select = instanceSelect(e.id, (v) => { e.id = v; load(); });
  if (!e.bundle && !e.error) load(); else { showStatus(); showTree(); showSaved(); chrome(); }

  return h("div", null, h("h2", null, t("tab_export")), h("p", { class: "hint" }, t("exp_hint")),
    h("div", { class: "card" }, h("h3", null, t("exp_pick_title")),
      h("div", { class: "row" }, h("div", { class: "grow" }, select), h("button", { onclick: load }, icon("refresh"), " ", t("refresh")))),
    statusBox, treeBox, savedBox);
}

// ---------------------------------------------------------------- import
function planRows(plan) {
  const rows = {};
  for (const [section, items] of Object.entries(plan.sections)) {
    rows[section] = items.map((i) => ({ ...i, selectable: i.action === "create" || i.action === "update" }));
  }
  return rows;
}

const impSteps = () => [t("imp_step1"), t("imp_step2"), t("imp_step3")];

async function runPreview(m) {
  m.plan = await api(`/api/instances/${m.targetId}/import/preview`, { method: "POST", body: { bundle: m.bundle, overwrite: m.overwrite } });
  m.sel = {};
  for (const [s, items] of Object.entries(m.plan.sections)) {
    m.sel[s] = new Set(items.filter((i) => (i.action === "create" || i.action === "update") && !NOT_BY_DEFAULT.includes(s)).map((i) => i.name));
  }
}

// Import is three screens: 1. choose what and where, 2. review every change, 3. done.
function viewImport() {
  if (!S.instances.length) return needInstances();
  const m = S.imp;
  if (!S.instances.some((i) => i.id === m.targetId)) m.targetId = S.instances[0].id;
  if (m.result) return importResult();
  if (m.step === 2 && m.plan) return importReview();
  m.step = 1;
  return importSetup();
}

function importSetup() {
  const m = S.imp;
  const target = S.instances.find((i) => i.id === m.targetId);
  tools.set([stepper(impSteps(), 1)]);

  const targetSelect = instanceSelect(m.targetId, (v) => { m.targetId = v; if (m.srcId === v) m.srcId = ""; m.plan = null; render(); });
  const srcSelect = instanceSelect(m.srcId, (v) => { m.srcId = v; refresh(); }, m.targetId, target.app); // a bundle only fits the same application
  m.srcId = srcSelect.value; // keep the state in line with what the list shows

  // why the user cannot continue yet (null = ready)
  const why = () => {
    if (m.mode === "file") return m.text.trim() ? null : t("imp_need_file");
    if (m.mode === "instance") return m.srcId ? null : t("imp_need_inst");
    if (target.app !== "radarr" && target.app !== "sonarr") return t("trash_only");
    return m.trash.profileId ? null : t("need_profile");
  };
  function refresh() {
    const reason = why();
    bar.set(reason ?? t("imp_ready", target.name), actionBtn(t("imp_review"), go, { primary: true, disabled: !!reason, iconName: "search" }));
  }
  function go(ev) {
    return busy(ev.currentTarget, t("analysing"), async () => {
      let bundle, label;
      if (m.mode === "instance") {
        if (m.srcId === m.targetId) throw new Error(t("same_instance"));
        bundle = await api(`/api/instances/${m.srcId}/export`);
        label = S.instances.find((i) => i.id === m.srcId).name;
      } else if (m.mode === "trash") {
        bundle = await api(`/api/trash/${m.trash.app}/build`, { method: "POST", body: { profile_id: m.trash.profileId, formats: [...m.trash.selected] } });
        label = `TRaSH Guides · ${m.trash.detail?.profile.name ?? ""}`;
      } else {
        bundle = await api("/api/import/parse", { method: "POST", body: { text: m.text, app: target.app } });
        label = m.fileName || t("src_pasted");
      }
      m.bundle = bundle;
      m.sourceLabel = label;
      await runPreview(m);
      m.step = 2;
      render();
    });
  }

  const chosen = h("span", { class: "chosen" }, m.fileName ? t("file_chosen", m.fileName) : "");
  const text = h("textarea", { placeholder: t("paste_ph"), oninput: (ev) => { m.text = ev.target.value; m.fileName = ""; chosen.textContent = ""; refresh(); } });
  text.value = m.text;
  const file = h("input", { type: "file", accept: ".json,application/json", onchange: async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    m.text = await f.text();
    m.fileName = f.name;
    text.value = m.text;
    chosen.textContent = t("file_chosen", f.name);
    refresh();
  } });
  const fileBox = h("div", null,
    h("div", { class: "filepick" }, h("button", { onclick: () => file.click() }, icon("upload"), " ", t("pick_file")), file, chosen),
    h("div", { class: "hint", style: "margin:0 0 6px" }, t("or_paste")), text);
  const instBox = h("div", null, srcSelect.options.length
    ? h("label", { class: "field", style: "margin:0" }, h("span", null, t("instance")), srcSelect)
    : h("p", { class: "hint", style: "margin:0" }, t("imp_no_same_app", cap(target.app))));
  const trashBox = trashPanel(m, target.app, refresh);

  const panels = { file: fileBox, instance: instBox, trash: trashBox };
  const modes = h("div", { class: "seg" });
  const setMode = (mode) => {
    m.mode = mode;
    Object.entries(panels).forEach(([k, el]) => { el.hidden = k !== mode; });
    modes.replaceChildren(...[["file", "src_file"], ["instance", "src_instance"], ["trash", "src_trash"]].map(([k, label]) =>
      h("button", { class: mode === k ? "active" : "", onclick: () => setMode(k) }, t(label))));
    refresh();
  };

  const node = h("div", null, h("h2", null, t("tab_import")), h("p", { class: "hint" }, t("imp_hint")),
    h("div", { class: "card" }, h("h3", null, t("imp_target_title")),
      h("div", { class: "hint", style: "margin:0 0 10px" }, t("imp_target_hint")), targetSelect),
    h("div", { class: "card" }, h("h3", null, t("imp_source_title")), modes, fileBox, instBox, trashBox));
  setMode(m.mode);
  return node;
}

function importReview() {
  const m = S.imp;
  const target = S.instances.find((i) => i.id === m.targetId);
  const back = () => { m.step = 1; render(); };
  tools.set([stepper(impSteps(), 2, { 1: back })]);
  const count = () => Object.values(m.sel).reduce((n, s) => n + s.size, 0);
  const listBox = h("div");

  function chrome() {
    const n = count();
    const nothing = m.plan.summary.create + m.plan.summary.update === 0;
    bar.set(n ? t("rev_info", n, target.name) : nothing ? t("rev_nothing", target.name) : t("rev_pick"),
      actionBtn(t("rev_back"), back, { iconName: "back" }),
      actionBtn(t("apply_n", n), apply, { primary: true, disabled: n === 0, iconName: "check" }));
  }
  function showList() {
    const sum = m.plan.summary;
    fill(listBox, 
      (m.bundle.warnings ?? []).map((w) => h("div", { class: "warn", style: "margin:0 0 6px" }, `⚠ ${w}`)),
      h("div", { class: "summary" }, ["create", "update", "unchanged", "skip"].map((k) => h("span", { class: `badge b-${k}` }, `${sum[k]} ${t(`a_${k}`)}`))),
      selectionTree(planRows(m.plan), m.sel, { bundle: m.bundle, onChange: chrome }));
  }
  function apply(ev) {
    if (!confirm(t("confirm_apply", count(), target.name))) return;
    return busy(ev.currentTarget, t("applying"), async () => {
      const selection = Object.fromEntries(Object.entries(m.sel).map(([s, set]) => [s, [...set]]));
      m.result = await api(`/api/instances/${m.targetId}/import/apply`, { method: "POST", body: { bundle: m.bundle, selection, overwrite: m.overwrite } });
      render();
    });
  }
  const overwrite = h("input", { type: "checkbox", checked: m.overwrite, onchange: async (ev) => {
    m.overwrite = ev.target.checked;
    try { await runPreview(m); showList(); chrome(); } catch (err) { toast(err.message, "error"); }
  } });

  showList();
  chrome();
  return h("div", null, h("h2", null, t("tab_import")),
    h("div", { class: "card" },
      h("div", { class: "flow" },
        h("div", null, h("div", { class: "hint", style: "margin:0" }, t("rev_from")), h("strong", { class: "name" }, m.sourceLabel)),
        h("span", { class: "arrow" }, "→"),
        h("div", null, h("div", { class: "hint", style: "margin:0" }, t("rev_to")),
          h("span", { class: "end" }, h("strong", { class: "name" }, target.name), h("span", { class: `badge b-${target.app}` }, cap(target.app)))),
        h("div", { class: "grow" }), h("button", { onclick: back }, t("rev_change"))),
      h("label", { class: "row", style: "margin-top:14px;flex-wrap:nowrap;align-items:flex-start" }, overwrite, h("span", { class: "grow" }, t("overwrite"))),
      h("div", { class: "hint", style: "margin:6px 0 0" }, t("overwrite_hint"))),
    listBox);
}

const scoreBadge = (n) => h("span", { class: `badge ${n > 0 ? "b-create" : n < 0 ? "b-error" : ""}` }, n > 0 ? `+${n}` : String(n));

// Source "TRaSH Guides": pick one of the guides' quality profiles and which optional formats to bring along.
function trashPanel(m, app, onChange = () => {}) {
  const T = m.trash;
  const box = h("div");
  if (app !== "radarr" && app !== "sonarr") {
    box.append(h("p", { class: "hint", style: "margin:0" }, t("trash_only")));
    return box;
  }
  if (T.app !== app) Object.assign(T, { app, profiles: null, profileId: "", detail: null, selected: new Set(), error: null, open: new Map() });

  const load = async (force = false) => {
    T.error = null; T.profiles = null; draw();
    try {
      if (force) await api("/api/trash/refresh", { method: "POST" });
      const r = await api(`/api/trash/${app}/profiles`);
      T.profiles = r.profiles; T.fetchedAt = r.fetchedAt;
      if (T.profileId && !T.profiles.some((p) => p.id === T.profileId)) Object.assign(T, { profileId: "", detail: null });
    } catch (e) { T.error = e.message; }
    draw();
  };
  const pick = async (id) => {
    T.profileId = id; T.detail = null; T.selected = new Set(); T.open = new Map(); draw();
    if (!id) return;
    try {
      T.detail = await api(`/api/trash/${app}/profiles/${id}`);
      T.selected = new Set(T.detail.defaults);
    } catch (e) { toast(e.message, "error"); }
    draw();
  };

  // draw() rebuilds the panel on every tick, so what the user opened or closed is kept here, not in the DOM
  const remember = (key, el, byDefault) => {
    el.open = T.open.has(key) ? T.open.get(key) : byDefault;
    el.addEventListener("toggle", () => T.open.set(key, el.open));
    return el;
  };

  const formatRow = (f, locked) => h("li", null, h("label", null,
    h("input", { type: "checkbox", checked: locked || T.selected.has(f.trash_id), disabled: locked, onchange: (e) => {
      const group = T.detail.groups.find((g) => g.formats.some((x) => x.trash_id === f.trash_id));
      e.target.checked ? T.selected.add(f.trash_id) : T.selected.delete(f.trash_id);
      // using any format of a group means its required formats come along
      if (group) {
        const used = group.formats.some((x) => !x.required && T.selected.has(x.trash_id));
        group.formats.filter((x) => x.required).forEach((x) => (used ? T.selected.add(x.trash_id) : T.selected.delete(x.trash_id)));
      }
      draw();
    } }),
    h("span", { class: "name grow" }, f.name), f.required && !locked ? h("span", { class: "badge" }, t("trash_req")) : null, scoreBadge(f.score)));

  const groupBlock = (g) => {
    const ids = g.formats.map((f) => f.trash_id);
    const n = ids.filter((i) => T.selected.has(i)).length;
    const all = h("input", { type: "checkbox", checked: n === ids.length && n > 0, onclick: (e) => e.stopPropagation(), onchange: (e) => {
      ids.forEach((i) => (e.target.checked ? T.selected.add(i) : T.selected.delete(i)));
      draw();
    } });
    all.indeterminate = n > 0 && n < ids.length;
    return remember(g.trash_id, h("details", { class: "section card" },
      h("summary", null, all, h("span", { class: "grow" }, g.name), g.default ? h("span", { class: "badge b-create" }, t("trash_group_default")) : null,
        h("span", { class: "badge" }, `${n} / ${ids.length}`)),
      g.description ? h("div", { class: "detail", style: "margin-left:0" }, g.description) : null,
      h("ul", null, g.formats.map((f) => formatRow(f, false)))), g.default);
  };

  const draw = () => {
    if (T.error) {
      fill(box, h("p", { class: "err", style: "margin:0 0 10px" }, T.error), h("button", { onclick: () => load() }, t("retry")));
      return;
    }
    if (!T.profiles) { fill(box, h("p", { class: "hint", style: "margin:0" }, t("trash_loading"))); return; }
    const sel = h("select", { onchange: (e) => pick(e.target.value) }, h("option", { value: "" }, t("trash_pick")));
    for (const cat of [...new Set(T.profiles.map((p) => p.category))]) {
      sel.append(h("optgroup", { label: cat }, T.profiles.filter((p) => p.category === cat).map((p) => h("option", { value: p.id }, p.name))));
    }
    sel.value = T.profileId;
    const d = T.detail;
    fill(box, 
      h("label", { class: "field" }, h("span", null, t("trash_profile")), sel),
      h("div", { class: "row", style: "margin-bottom:12px" },
        h("span", { class: "hint grow", style: "margin:0" }, t("trash_updated", new Date(T.fetchedAt * 1000).toLocaleString(lang))),
        h("button", { onclick: () => load(true) }, t("trash_refresh"))),
      d ? h("div", null,
        d.profile.description ? h("p", { class: "hint" }, d.profile.description) : null,
        h("p", { class: "hint" }, t("trash_hint"), " ", t("trash_count", T.selected.size)),
        d.required.length ? remember("required", h("details", { class: "section card" }, h("summary", null, h("span", { class: "grow" }, t("trash_required")), h("span", { class: "badge" }, String(d.required.length))),
          h("ul", null, d.required.map((f) => formatRow(f, true)))), false) : null,
        d.groups.length ? h("h3", { style: "margin:14px 0 8px" }, t("trash_groups")) : null,
        d.groups.map(groupBlock)) : null);
    onChange(); // the caller's "can I continue?" depends on the chosen profile
  };
  if (!T.profiles) load();
  draw();
  return box;
}

function importResult() {
  const m = S.imp;
  const r = m.result;
  const target = S.instances.find((i) => i.id === m.targetId);
  tools.set([stepper(impSteps(), 4)]); // all three steps done
  const ok = Object.values(r.sections).flat().filter((i) => i.status === "ok").length;
  bar.set(t("done_text", ok, target.name), actionBtn(t("new_import"), () => {
    S.imp = { ...m, step: 1, bundle: null, plan: null, sel: {}, result: null, sourceLabel: "", text: "", fileName: "" };
    render();
  }, { primary: true, iconName: "plus" }));
  return h("div", null, h("h2", null, t("done")),
    h("div", { class: "summary" },
      h("span", { class: "badge b-ok" }, `${ok} ${t("s_ok")}`),
      r.summary.error ? h("span", { class: "badge b-error" }, `${r.summary.error} ${t("s_error")}`) : null),
    r.backup ? h("div", { class: "card note" },
      h("div", null, `${t("backup_saved")} `, h("a", { href: `/api/backups/${encodeURIComponent(r.backup)}` }, r.backup)),
      h("div", { class: "hint", style: "margin:6px 0 0" }, t("done_undo"))) : null,
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
          h("td", null, new Date(f.mtime * 1000).toLocaleString(lang)),
          h("td", null, `${Math.max(1, Math.round(f.size / 1024))} KB`)))))
      : h("p", { class: "hint" }, t("bk_empty")));
}

// Version and build, bottom of the sidebar: tells whether the NAS really runs the latest image.
function paintVersion() {
  const v = S.version;
  if (!v) return;
  const u = S.update;
  fill(document.getElementById("version"), h("strong", null, `Portarr v${v.version}`),
    v.commit ? h("span", { class: "build", title: t("build_title", v.commit) }, `build ${v.commit}`) : null,
    u?.available ? h("a", { class: "update", href: u.url, target: "_blank", rel: "noopener noreferrer", title: t("update_title", u.current) },
      icon("up"), t("update_available", u.latest)) : null);
}

// Both calls are conveniences, never blockers: a failure just leaves the sidebar as it is.
async function renderVersion() {
  try { S.version = await api("/api/version"); } catch { return; }
  paintVersion();
  try { S.update = await api("/api/update"); } catch { return; } // the server answers from its cache, or asks GitHub once
  paintVersion();
}

renderHeader();
renderVersion();
render();
