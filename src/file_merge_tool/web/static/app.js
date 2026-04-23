const form = document.querySelector("#job-form");
const kindInput = document.querySelector("#kind");
const settingName = document.querySelector("#setting-name");
const outputStem = document.querySelector("#output-stem");
const outputExtension = document.querySelector("#output-extension");
const imageOutputOptions = document.querySelector("#image-output-options");
const outputDir = document.querySelector("#output-dir");
const rootPath = document.querySelector("#root-path");
const excludeDirs = document.querySelector("#exclude-dirs");
const excludeExts = document.querySelector("#exclude-exts");
const excludeFiles = document.querySelector("#exclude-files");
const additionalMarkers = document.querySelector("#additional-markers");
const globalMarkers = document.querySelector("#global-markers");
const savedSelect = document.querySelector("#saved-setting-select");
const loadSetting = document.querySelector("#load-setting");
const deleteSetting = document.querySelector("#delete-setting");
const saveSetting = document.querySelector("#save-setting");
const saveGlobalSettings = document.querySelector("#save-global-settings");
const jobPanel = document.querySelector("#job-panel");
const settingsPanel = document.querySelector("#settings-panel");
const historyPanel = document.querySelector("#history-panel");
const historyList = document.querySelector("#history-list");
const refreshHistory = document.querySelector("#refresh-history");
const activeKindLabel = document.querySelector("#active-kind-label");
const jobOutput = document.querySelector("#job-output");
const health = document.querySelector("#health");
const languageInputs = document.querySelectorAll("input[name='language']");
const imageOutputModeInputs = document.querySelectorAll("input[name='image-output-mode']");
const tabButtons = document.querySelectorAll(".tab-button");

const settingsKey = "fileMergeTool.savedSettings.v1";
const globalSettingsKey = "fileMergeTool.globalSettings.v1";

const kinds = {
  "file-list": { label: { ja: "構成リスト", en: "File list JSON" }, ext: "json", stem: "file-list" },
  "text-merge": { label: { ja: "テキスト", en: "Text merge JSON" }, ext: "json", stem: "text-merge" },
  "mail-merge": { label: { ja: "メール", en: "Mail merge JSON" }, ext: "json", stem: "mail-merge" },
  "powerpoint-merge": { label: { ja: "PowerPoint", en: "PowerPoint merge" }, ext: "pptx", stem: "merged" },
  "excel-merge": { label: { ja: "Excel", en: "Excel merge" }, ext: "xlsx", stem: "merged" },
  "word-merge": { label: { ja: "Word", en: "Word merge" }, ext: "docx", stem: "merged" },
  "pdf-merge": { label: { ja: "PDF", en: "PDF merge" }, ext: "pdf", stem: "merged" },
  "image-merge": { label: { ja: "画像", en: "Image merge" }, ext: "html", stem: "images" },
};

const genericExcludeExts = [".png", ".jpg", ".jpeg", ".gif", ".zip", ".exe", ".dll"];
const imageExcludeExts = [".zip", ".exe", ".dll"];

const translations = {
  ja: {
    eyebrow: "Local AI Artifact Salon",
    title: "File Merge Tool",
    tabFileList: "構成リスト",
    tabText: "テキスト",
    tabMail: "メール",
    tabPowerPoint: "PowerPoint",
    tabExcel: "Excel",
    tabWord: "Word",
    tabPdf: "PDF",
    tabImage: "画像",
    tabHistory: "履歴",
    tabSettings: "設定",
    savedEyebrow: "Preset",
    savedTitle: "保存済み設定",
    savedSelect: "設定一覧",
    loadSetting: "読込",
    deleteSetting: "削除",
    jobTitle: "実行設定",
    settingName: "設定名",
    outputStem: "出力ファイル名",
    outputDir: "履歴保存先",
    rootPath: "収集対象ルートフォルダ",
    excludeDirs: "除外フォルダ",
    excludeExts: "除外拡張子",
    excludeFiles: "除外ファイル名",
    additionalMarkers: "追加機密分類判定文字列",
    imageOutputFormat: "画像出力形式",
    imageFormatHtml: "HTML",
    imageFormatPptx: "PPTX",
    imageFormatBoth: "両方",
    saveSetting: "設定を保存",
    runJob: "実行",
    settingsTitle: "全体設定",
    globalMarkers: "全体機密分類判定文字列",
    language: "言語",
    saveGlobalSettings: "全体設定を保存",
    historyTitle: "履歴",
    refreshHistory: "更新",
    jobResult: "実行結果",
    noSavedSettings: "保存済み設定なし",
    noHistory: "履歴なし",
    noJob: "No job yet.",
    ready: "ready",
    offline: "offline",
    submitting: "Submitting job...",
    saved: "設定を保存しました。",
    deleted: "設定を削除しました。",
    globalSaved: "全体設定を保存しました。",
    settingNameRequired: "設定名を入力してください。",
  },
  en: {
    eyebrow: "Local AI Artifact Salon",
    title: "File Merge Tool",
    tabFileList: "File list",
    tabText: "Text",
    tabMail: "Mail",
    tabPowerPoint: "PowerPoint",
    tabExcel: "Excel",
    tabWord: "Word",
    tabPdf: "PDF",
    tabImage: "Images",
    tabHistory: "History",
    tabSettings: "Settings",
    savedEyebrow: "Preset",
    savedTitle: "Saved Settings",
    savedSelect: "Setting list",
    loadSetting: "Load",
    deleteSetting: "Delete",
    jobTitle: "Run Settings",
    settingName: "Setting name",
    outputStem: "Output file name",
    outputDir: "History folder",
    rootPath: "Collection root folder",
    excludeDirs: "Excluded folders",
    excludeExts: "Excluded extensions",
    excludeFiles: "Excluded file names",
    additionalMarkers: "Additional sensitive markers",
    imageOutputFormat: "Image output format",
    imageFormatHtml: "HTML",
    imageFormatPptx: "PPTX",
    imageFormatBoth: "Both",
    saveSetting: "Save setting",
    runJob: "Run",
    settingsTitle: "Global Settings",
    globalMarkers: "Global sensitive markers",
    language: "Language",
    saveGlobalSettings: "Save global settings",
    historyTitle: "History",
    refreshHistory: "Refresh",
    jobResult: "Job Result",
    noSavedSettings: "No saved settings",
    noHistory: "No history",
    noJob: "No job yet.",
    ready: "ready",
    offline: "offline",
    submitting: "Submitting job...",
    saved: "Setting saved.",
    deleted: "Setting deleted.",
    globalSaved: "Global settings saved.",
    settingNameRequired: "Enter a setting name.",
  },
};

let activeKind = "file-list";
let language = "ja";
let savedSettingsCache = [];

function splitList(value) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinList(value) {
  return (value || []).join(", ");
}

function outputName() {
  const stem = outputStem.value.trim() || kinds[activeKind].stem;
  return `${stem}.${primaryExtension()}`;
}

function selectedImageOutputMode() {
  const checked = document.querySelector("input[name='image-output-mode']:checked");
  return checked?.value || "html";
}

function selectedImageOutputFormats() {
  const mode = selectedImageOutputMode();
  return mode === "both" ? ["html", "pptx"] : [mode];
}

function sensitivityMarkersForRequest() {
  return [...new Set([...splitList(globalMarkers.value), ...splitList(additionalMarkers.value)])];
}

function primaryExtension() {
  if (activeKind !== "image-merge") {
    return kinds[activeKind].ext;
  }
  const mode = selectedImageOutputMode();
  return mode === "pptx" ? "pptx" : "html";
}

function extensionLabel() {
  if (activeKind !== "image-merge") {
    return `.${kinds[activeKind].ext}`;
  }
  const mode = selectedImageOutputMode();
  if (mode === "both") {
    return ".html / .pptx";
  }
  return `.${mode}`;
}

function setImageOutputMode(mode) {
  for (const input of imageOutputModeInputs) {
    input.checked = input.value === mode;
  }
  updateOutputExtension();
}

function updateOutputExtension() {
  outputExtension.textContent = extensionLabel();
}

function currentFormState() {
  return {
    name: settingName.value.trim(),
    kind: activeKind,
    outputStem: outputStem.value.trim(),
    outputDir: outputDir.value.trim(),
    rootPath: rootPath.value.trim(),
    excludeDirs: splitList(excludeDirs.value),
    excludeExts: splitList(excludeExts.value),
    excludeFiles: splitList(excludeFiles.value),
    additionalMarkers: splitList(additionalMarkers.value),
    imageOutputMode: selectedImageOutputMode(),
  };
}

function applyFormState(state) {
  const kind = state.kind && kinds[state.kind] ? state.kind : activeKind;
  setActiveKind(kind);
  settingName.value = state.name || "";
  outputStem.value = state.outputStem || kinds[kind].stem;
  outputDir.value = state.outputDir || "80_workspace\\history";
  rootPath.value = state.rootPath || "";
  excludeDirs.value = joinList(state.excludeDirs);
  excludeExts.value = joinList(state.excludeExts);
  excludeFiles.value = joinList(state.excludeFiles);
  additionalMarkers.value = joinList(state.additionalMarkers);
  setImageOutputMode(state.imageOutputMode || "html");
}

function renderSavedSettings() {
  savedSelect.innerHTML = "";
  if (savedSettingsCache.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = translations[language].noSavedSettings;
    savedSelect.append(option);
    return;
  }
  for (const item of savedSettingsCache) {
    const option = document.createElement("option");
    option.value = item.name;
    option.textContent = `${item.name} / ${kinds[item.kind]?.label[language] ?? item.kind}`;
    savedSelect.append(option);
  }
}

async function fetchSavedSettings() {
  try {
    const response = await fetch("/api/settings/presets");
    if (!response.ok) throw new Error("settings failed");
    const payload = await response.json();
    savedSettingsCache = payload.items || [];
  } catch {
    try {
      savedSettingsCache = JSON.parse(localStorage.getItem(settingsKey) || "[]");
    } catch {
      savedSettingsCache = [];
    }
  }
  renderSavedSettings();
}

async function saveCurrentSetting() {
  const state = currentFormState();
  if (!state.name) {
    jobOutput.textContent = translations[language].settingNameRequired;
    settingName.focus();
    return;
  }

  try {
    const response = await postJson("/api/settings/presets", state);
    savedSettingsCache = response.items || [];
  } catch {
    const next = savedSettingsCache.filter((item) => item.name !== state.name);
    next.unshift(state);
    savedSettingsCache = next;
    localStorage.setItem(settingsKey, JSON.stringify(next));
  }
  renderSavedSettings();
  savedSelect.value = state.name;
  jobOutput.textContent = translations[language].saved;
}

function loadSelectedSetting() {
  const selected = savedSettingsCache.find((item) => item.name === savedSelect.value);
  if (selected) {
    applyFormState(selected);
  }
}

async function deleteSelectedSetting() {
  const name = savedSelect.value;
  if (!name) return;
  try {
    const response = await fetch(`/api/settings/presets/${encodeURIComponent(name)}`, {
      method: "DELETE",
    });
    const payload = await response.json();
    savedSettingsCache = payload.items || [];
  } catch {
    savedSettingsCache = savedSettingsCache.filter((item) => item.name !== name);
    localStorage.setItem(settingsKey, JSON.stringify(savedSettingsCache));
  }
  renderSavedSettings();
  jobOutput.textContent = translations[language].deleted;
}

async function loadGlobalSettings() {
  try {
    const response = await fetch("/api/settings/global");
    if (!response.ok) throw new Error("global settings failed");
    const settings = await response.json();
    language = settings.language || "ja";
    globalMarkers.value = joinList(settings.globalMarkers || ["機密", "極秘"]);
  } catch {
    try {
      const settings = JSON.parse(localStorage.getItem(globalSettingsKey) || "{}");
      language = settings.language || "ja";
      globalMarkers.value = joinList(settings.globalMarkers || ["機密", "極秘"]);
    } catch {
      language = "ja";
    }
  }
  for (const input of languageInputs) {
    input.checked = input.value === language;
  }
  applyLanguage();
}

async function saveGlobal() {
  const payload = {
    language,
    globalMarkers: splitList(globalMarkers.value),
  };
  try {
    await fetch("/api/settings/global", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    localStorage.setItem(globalSettingsKey, JSON.stringify(payload));
  }
  jobOutput.textContent = translations[language].globalSaved;
}

function applyLanguage() {
  document.documentElement.lang = language;
  for (const node of document.querySelectorAll("[data-i18n]")) {
    const key = node.dataset.i18n;
    node.textContent = translations[language][key] ?? node.textContent;
  }
  if (jobOutput.textContent === translations.ja.noJob || jobOutput.textContent === translations.en.noJob) {
    jobOutput.textContent = translations[language].noJob;
  }
  renderSavedSettings();
  updateActiveKindLabel();
}

function setActiveKind(kind) {
  if (kind === "settings") {
    jobPanel.classList.add("is-hidden");
    historyPanel.classList.add("is-hidden");
    settingsPanel.classList.remove("is-hidden");
  } else if (kind === "history") {
    jobPanel.classList.add("is-hidden");
    settingsPanel.classList.add("is-hidden");
    historyPanel.classList.remove("is-hidden");
    fetchHistory();
  } else {
    const previousKind = activeKind;
    const currentStem = outputStem.value.trim();
    activeKind = kind;
    kindInput.value = kind;
    jobPanel.classList.remove("is-hidden");
    settingsPanel.classList.add("is-hidden");
    historyPanel.classList.add("is-hidden");
    imageOutputOptions.classList.toggle("is-hidden", kind !== "image-merge");
    adjustExcludeExtensionsForKind(previousKind, kind);
    updateOutputExtension();
    if (!currentStem || currentStem === kinds[previousKind].stem) {
      outputStem.value = kinds[kind].stem;
    }
    updateActiveKindLabel();
  }

  for (const button of tabButtons) {
    button.classList.toggle("is-active", button.dataset.kind === kind);
  }
}

function adjustExcludeExtensionsForKind(previousKind, nextKind) {
  const current = splitList(excludeExts.value);
  const currentText = joinList(current);
  if (nextKind === "image-merge" && currentText === joinList(genericExcludeExts)) {
    excludeExts.value = joinList(imageExcludeExts);
  }
  if (previousKind === "image-merge" && currentText === joinList(imageExcludeExts)) {
    excludeExts.value = joinList(genericExcludeExts);
  }
}

function updateActiveKindLabel() {
  activeKindLabel.textContent = kinds[activeKind].label[language];
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("bad status");
    health.textContent = translations[language].ready;
    health.classList.add("is-ok");
  } catch {
    health.textContent = translations[language].offline;
    health.classList.remove("is-ok");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  jobOutput.textContent = translations[language].submitting;

  const payload = {
    kind: activeKind,
    root_path: rootPath.value,
    output_name: outputName(),
    output_stem: outputStem.value.trim() || kinds[activeKind].stem,
    setting_name: settingName.value.trim(),
    image_output_formats: selectedImageOutputFormats(),
    exclude_dirs: splitList(excludeDirs.value),
    exclude_extensions: splitList(excludeExts.value),
    exclude_files: splitList(excludeFiles.value),
    additional_sensitive_markers: sensitivityMarkersForRequest(),
  };

  try {
    const created = await postJson("/api/jobs", payload);
    await pollJob(created.job_id);
    fetchHistory();
  } catch (error) {
    jobOutput.textContent = String(error);
  }
});

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

async function pollJob(jobId) {
  for (;;) {
    const response = await fetch(`/api/jobs/${jobId}`);
    const job = await response.json();
    jobOutput.textContent = JSON.stringify(job, null, 2);
    if (job.status === "completed" || job.status === "failed") {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 700));
  }
}

async function fetchHistory() {
  historyList.textContent = "Loading...";
  try {
    const response = await fetch("/api/history");
    if (!response.ok) throw new Error(await response.text());
    const payload = await response.json();
    renderHistory(payload.items || []);
  } catch (error) {
    historyList.textContent = String(error);
  }
}

function renderHistory(items) {
  historyList.innerHTML = "";
  if (items.length === 0) {
    historyList.textContent = translations[language].noHistory;
    return;
  }

  for (const item of items) {
    const row = document.createElement("article");
    row.className = "history-item";

    const body = document.createElement("div");
    body.className = "history-body";
    const title = document.createElement("h3");
    title.textContent = `${item.kind} / ${item.status}`;
    const meta = document.createElement("div");
    meta.className = "history-meta";
    const startedAt = document.createElement("p");
    startedAt.className = "history-started-at";
    startedAt.textContent = item.started_at ?? "-";
    const sourceRoot = document.createElement("p");
    sourceRoot.className = "history-source-root";
    sourceRoot.textContent = item.source_root ?? "-";
    meta.append(startedAt, sourceRoot);
    body.append(title, meta);

    const downloads = document.createElement("div");
    downloads.className = "history-downloads";
    const outputs = item.outputs || [];
    if (outputs.length === 0) {
      const empty = document.createElement("p");
      empty.className = "history-empty";
      empty.textContent = item.error || "-";
      downloads.append(empty);
    }
    outputs.forEach((output, index) => {
      const link = document.createElement("a");
      link.href = `/api/downloads/${item.job_id}/${index}`;
      link.textContent = output.download_name || `download-${index + 1}`;
      downloads.append(link);
    });

    row.append(body, downloads);
    historyList.append(row);
  }
}

for (const button of tabButtons) {
  button.addEventListener("click", () => {
    const kind = button.dataset.kind;
    if (!kind) return;
    setActiveKind(kind);
    if (kind !== "settings" && kind !== "history" && !outputStem.value.trim()) {
      outputStem.value = kinds[kind].stem;
    }
  });
}

for (const input of languageInputs) {
  input.addEventListener("change", () => {
    language = input.value;
    applyLanguage();
  });
}

for (const input of imageOutputModeInputs) {
  input.addEventListener("change", updateOutputExtension);
}

saveSetting.addEventListener("click", saveCurrentSetting);
loadSetting.addEventListener("click", loadSelectedSetting);
deleteSetting.addEventListener("click", deleteSelectedSetting);
saveGlobalSettings.addEventListener("click", saveGlobal);
refreshHistory.addEventListener("click", fetchHistory);

async function initialize() {
  await loadGlobalSettings();
  await fetchSavedSettings();
  setActiveKind(activeKind);
  checkHealth();
}

initialize();
