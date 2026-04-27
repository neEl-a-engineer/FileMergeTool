const form = document.querySelector("#job-form");
const kindInput = document.querySelector("#kind");
const settingName = document.querySelector("#setting-name");
const outputFolderName = document.querySelector("#output-folder-name");
const imageOutputOptions = document.querySelector("#image-output-options");
const outputDir = document.querySelector("#output-dir");
const rootPath = document.querySelector("#root-path");
const excludeDirs = document.querySelector("#exclude-dirs");
const excludeExts = document.querySelector("#exclude-exts");
const excludeFiles = document.querySelector("#exclude-files");
const additionalMarkers = document.querySelector("#additional-markers");
const globalMarkers = document.querySelector("#global-markers");
const savedSettingsCount = document.querySelector("#saved-settings-count");
const openSavedSettings = document.querySelector("#open-saved-settings");
const savedSettingsDialog = document.querySelector("#saved-settings-dialog");
const savedSettingsList = document.querySelector("#saved-settings-list");
const closeSavedSettings = document.querySelector("#close-saved-settings");
const confirmDeleteDialog = document.querySelector("#confirm-delete-dialog");
const confirmDeleteMessage = document.querySelector("#confirm-delete-message");
const confirmDeleteCancel = document.querySelector("#confirm-delete-cancel");
const confirmDeleteAccept = document.querySelector("#confirm-delete-accept");
const saveSetting = document.querySelector("#save-setting");
const saveGlobalSettings = document.querySelector("#save-global-settings");
const restartServerButton = document.querySelector("#restart-server");
const jobPanel = document.querySelector("#job-panel");
const settingsPanel = document.querySelector("#settings-panel");
const historyPanel = document.querySelector("#history-panel");
const historyList = document.querySelector("#history-list");
const historyPreviewPanel = document.querySelector("#history-preview-panel");
const historyPreviewTitle = document.querySelector("#history-preview-title");
const historyPreviewContent = document.querySelector("#history-preview-content");
const refreshHistory = document.querySelector("#refresh-history");
const activeKindLabel = document.querySelector("#active-kind-label");
const jobStatusCard = document.querySelector("#job-status-card");
const jobStatusValue = document.querySelector("#job-status-value");
const jobStatusMessage = document.querySelector("#job-status-message");
const jobSummaryItems = document.querySelector("#job-summary-items");
const jobSummarySkipped = document.querySelector("#job-summary-skipped");
const jobSummaryWarnings = document.querySelector("#job-summary-warnings");
const jobSummaryOutputs = document.querySelector("#job-summary-outputs");
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
    savedCountNone: "保存済み設定はありません",
    savedCountSingle: "保存済み設定 1 件",
    savedCountMultiple: "保存済み設定 {count} 件",
    loadSetting: "読込",
    deleteSetting: "削除",
    closeDialog: "閉じる",
    deleteConfirmTitle: "設定を削除",
    deleteConfirmMessage: "「{name}」を削除します。元に戻せません。",
    cancelDelete: "キャンセル",
    confirmDelete: "削除する",
    jobTitle: "実行設定",
    settingName: "設定名",
    outputFolderName: "出力フォルダ名",
    historyRoot: "履歴保存ルート",
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
    restartServer: "サーバーを再起動",
    saveGlobalSettings: "全体設定を保存",
    historyTitle: "履歴",
    refreshHistory: "更新",
    jobResult: "実行結果",
    jobStatus: "実行ステータス",
    summaryItems: "対象",
    summarySkipped: "スキップ",
    summaryWarnings: "警告",
    summaryOutputs: "出力",
    statusIdle: "待機中",
    statusQueued: "待機中",
    statusRunning: "実行中",
    statusCompleted: "成功",
    statusFailed: "失敗",
    statusIdleMessage: "まだ実行していません。",
    statusQueuedMessage: "実行待ちです。",
    statusRunningMessage: "処理を進めています。",
    statusCompletedMessage: "実行が完了しました。",
    statusFailedMessage: "実行に失敗しました。",
    preview: "プレビュー",
    save: "保存",
    showOutputs: "出力を開く",
    hideOutputs: "出力を閉じる",
    previewOpened: "サーバー側で既定アプリを起動しました。",
    previewUnavailable: "この出力ではプレビューできません。",
    noSavedSettings: "保存済み設定なし",
    noHistory: "履歴なし",
    noJob: "No job yet.",
    ready: "ready",
    restarting: "restarting",
    offline: "offline",
    submitting: "Submitting job...",
    saved: "設定を保存しました。",
    savedAs: "設定を保存しました: {name}",
    deleted: "設定を削除しました。",
    globalSaved: "全体設定を保存しました。",
    settingNameRequired: "設定名を入力してください。",
    restartScheduled: "サーバー再起動を開始しました。復帰を待っています。",
    restartCompleted: "サーバーが再起動しました。",
    restartFailed: "サーバー再起動に失敗しました。",
    restartTimedOut: "サーバーの再起動完了を確認できませんでした。",
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
    savedCountNone: "No saved settings",
    savedCountSingle: "1 saved setting",
    savedCountMultiple: "{count} saved settings",
    loadSetting: "Load",
    deleteSetting: "Delete",
    closeDialog: "Close",
    deleteConfirmTitle: "Delete setting",
    deleteConfirmMessage: "Delete \"{name}\"? This cannot be undone.",
    cancelDelete: "Cancel",
    confirmDelete: "Delete",
    jobTitle: "Run Settings",
    settingName: "Setting name",
    outputFolderName: "Output folder name",
    historyRoot: "History root",
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
    restartServer: "Restart server",
    saveGlobalSettings: "Save global settings",
    historyTitle: "History",
    refreshHistory: "Refresh",
    jobResult: "Job Result",
    jobStatus: "Run status",
    summaryItems: "Items",
    summarySkipped: "Skipped",
    summaryWarnings: "Warnings",
    summaryOutputs: "Outputs",
    statusIdle: "Idle",
    statusQueued: "Queued",
    statusRunning: "Running",
    statusCompleted: "Success",
    statusFailed: "Failed",
    statusIdleMessage: "No job has been run yet.",
    statusQueuedMessage: "The job is waiting to start.",
    statusRunningMessage: "The job is running.",
    statusCompletedMessage: "The job completed successfully.",
    statusFailedMessage: "The job failed.",
    preview: "Preview",
    save: "Save",
    showOutputs: "Show outputs",
    hideOutputs: "Hide outputs",
    previewOpened: "Opened with the server machine's default app.",
    previewUnavailable: "Preview is not available for this output.",
    noSavedSettings: "No saved settings",
    noHistory: "No history",
    noJob: "No job yet.",
    ready: "ready",
    restarting: "restarting",
    offline: "offline",
    submitting: "Submitting job...",
    saved: "Setting saved.",
    savedAs: "Saved setting: {name}",
    deleted: "Setting deleted.",
    globalSaved: "Global settings saved.",
    settingNameRequired: "Enter a setting name.",
    restartScheduled: "Server restart requested. Waiting for it to come back.",
    restartCompleted: "Server restart completed.",
    restartFailed: "Server restart failed.",
    restartTimedOut: "Timed out while waiting for the server to restart.",
  },
};

let activeKind = "file-list";
let language = "ja";
let savedSettingsCache = [];
let currentJobStatus = { status: "idle", warnings: [], output_paths: [] };
let pendingDeletePresetName = null;

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
  const stem = outputFolderName.value.trim() || kinds[activeKind].stem;
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

function setImageOutputMode(mode) {
  for (const input of imageOutputModeInputs) {
    input.checked = input.value === mode;
  }
}

function currentFormState() {
  return {
    name: settingName.value.trim(),
    kind: activeKind,
    outputFolderName: outputFolderName.value.trim(),
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
  outputFolderName.value = state.outputFolderName || state.outputStem || kinds[kind].stem;
  outputDir.value = state.outputDir || "80_workspace\\history";
  rootPath.value = state.rootPath || "";
  excludeDirs.value = joinList(state.excludeDirs);
  excludeExts.value = joinList(state.excludeExts);
  excludeFiles.value = joinList(state.excludeFiles);
  additionalMarkers.value = joinList(state.additionalMarkers);
  setImageOutputMode(state.imageOutputMode || "html");
}

function renderSavedSettings() {
  savedSettingsCount.textContent = formatSavedSettingsCount(savedSettingsCache.length);
  openSavedSettings.disabled = false;
  savedSettingsList.innerHTML = "";
  if (savedSettingsCache.length === 0) {
    const empty = document.createElement("p");
    empty.className = "saved-settings-empty";
    empty.textContent = translations[language].noSavedSettings;
    savedSettingsList.append(empty);
    return;
  }
  for (const item of savedSettingsCache) {
    const row = document.createElement("article");
    row.className = "saved-setting-item";

    const body = document.createElement("div");
    body.className = "saved-setting-body";
    const name = document.createElement("p");
    name.className = "saved-setting-name";
    name.textContent = item.name || "-";
    const meta = document.createElement("p");
    meta.className = "saved-setting-meta";
    meta.textContent = buildSavedSettingMeta(item);
    body.append(name, meta);

    const actions = document.createElement("div");
    actions.className = "saved-setting-actions";
    const loadButton = document.createElement("button");
    loadButton.type = "button";
    loadButton.className = "secondary-button";
    loadButton.textContent = translations[language].loadSetting;
    loadButton.addEventListener("click", () => loadPreset(item));
    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "danger-button";
    deleteButton.textContent = translations[language].deleteSetting;
    deleteButton.addEventListener("click", () => promptDeletePreset(item.name));
    actions.append(loadButton, deleteButton);

    row.append(body, actions);
    savedSettingsList.append(row);
  }
}

function buildSavedSettingMeta(item) {
  const parts = [];
  if (item.kind) {
    parts.push(kinds[item.kind]?.label[language] ?? item.kind);
  }
  if (item.outputFolderName) {
    parts.push(item.outputFolderName);
  }
  if (item.rootPath) {
    parts.push(item.rootPath);
  }
  return parts.join(" • ");
}

function formatSavedSettingsCount(count) {
  if (count <= 0) {
    return translations[language].savedCountNone;
  }
  if (count === 1) {
    return translations[language].savedCountSingle;
  }
  return translateTemplate("savedCountMultiple", { count });
}

function nextPresetName(requestedName, existingItems) {
  const trimmed = String(requestedName || "").trim();
  const existingNames = new Set((existingItems || []).map((item) => item.name).filter(Boolean));
  if (!existingNames.has(trimmed)) {
    return trimmed;
  }
  let index = 2;
  while (existingNames.has(`${trimmed} (${index})`)) {
    index += 1;
  }
  return `${trimmed} (${index})`;
}

function translateTemplate(key, values) {
  let template = translations[language][key] || key;
  for (const [name, value] of Object.entries(values || {})) {
    template = template.replaceAll(`{${name}}`, String(value));
  }
  return template;
}

function showDialog(dialog) {
  if (!dialog) return;
  if (typeof dialog.showModal === "function") {
    if (!dialog.open) {
      dialog.showModal();
    }
    return;
  }
  dialog.setAttribute("open", "open");
}

function closeDialog(dialog) {
  if (!dialog) return;
  if (typeof dialog.close === "function") {
    dialog.close();
    return;
  }
  dialog.removeAttribute("open");
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

  let resolvedName = state.name;
  try {
    const response = await postJson("/api/settings/presets", state);
    savedSettingsCache = response.items || [];
    resolvedName = savedSettingsCache[0]?.name || state.name;
  } catch {
    resolvedName = nextPresetName(state.name, savedSettingsCache);
    const next = [{ ...state, name: resolvedName }, ...savedSettingsCache];
    savedSettingsCache = next;
    localStorage.setItem(settingsKey, JSON.stringify(next));
  }
  renderSavedSettings();
  settingName.value = resolvedName;
  jobOutput.textContent = translateTemplate("savedAs", { name: resolvedName });
}

function loadPreset(preset) {
  if (!preset) return;
  applyFormState(preset);
  closeDialog(savedSettingsDialog);
}

function promptDeletePreset(name) {
  if (!name) return;
  pendingDeletePresetName = name;
  confirmDeleteMessage.textContent = translateTemplate("deleteConfirmMessage", { name });
  showDialog(confirmDeleteDialog);
}

async function deletePresetByName(name) {
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

async function restartServer() {
  if (restartServerButton.disabled) {
    return;
  }
  restartServerButton.disabled = true;
  health.textContent = translations[language].restarting;
  health.classList.remove("is-ok");
  health.classList.add("is-busy");
  jobOutput.textContent = translations[language].restartScheduled;

  try {
    const response = await fetch("/api/system/restart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    await waitForServerReady();
    jobOutput.textContent = translations[language].restartCompleted;
    await fetchHistory();
  } catch (error) {
    health.textContent = translations[language].offline;
    health.classList.remove("is-busy");
    jobOutput.textContent = `${translations[language].restartFailed}\n${String(error)}`;
  } finally {
    restartServerButton.disabled = false;
  }
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
  updateJobStatusCard(currentJobStatus);
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
    const currentFolderName = outputFolderName.value.trim();
    activeKind = kind;
    kindInput.value = kind;
    jobPanel.classList.remove("is-hidden");
    settingsPanel.classList.add("is-hidden");
    historyPanel.classList.add("is-hidden");
    imageOutputOptions.classList.toggle("is-hidden", kind !== "image-merge");
    adjustExcludeExtensionsForKind(previousKind, kind);
    if (!currentFolderName || currentFolderName === kinds[previousKind].stem) {
      outputFolderName.value = kinds[kind].stem;
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
    health.classList.remove("is-busy");
    health.classList.add("is-ok");
  } catch {
    health.textContent = translations[language].offline;
    health.classList.remove("is-busy");
    health.classList.remove("is-ok");
  }
}

async function waitForServerReady() {
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    await new Promise((resolve) => setTimeout(resolve, 1500));
    try {
      const response = await fetch("/api/health", { cache: "no-store" });
      if (!response.ok) {
        continue;
      }
      health.textContent = translations[language].ready;
      health.classList.remove("is-busy");
      health.classList.add("is-ok");
      return;
    } catch {
      // Keep waiting while the server restarts.
    }
  }
  throw new Error(translations[language].restartTimedOut);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  jobOutput.textContent = translations[language].submitting;
  updateJobStatusCard({ status: "queued" });

  const payload = {
    kind: activeKind,
    root_path: rootPath.value,
    output_name: outputName(),
    output_stem: outputFolderName.value.trim() || kinds[activeKind].stem,
    output_folder_name: outputFolderName.value.trim() || kinds[activeKind].stem,
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
    updateJobStatusCard({ status: "failed", error: String(error), warnings: [], output_paths: [] });
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
    updateJobStatusCard(job);
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
    historyPreviewPanel.classList.add("is-hidden");
    return;
  }

  items.forEach((item, itemIndex) => {
    const outputs = item.outputs || [];
    const row = document.createElement("details");
    row.className = "history-item";
    if (itemIndex === 0 || item.status === "failed" || outputs.length === 0) {
      row.open = true;
    }

    const summary = document.createElement("summary");
    summary.className = "history-summary";

    const body = document.createElement("div");
    body.className = "history-body";
    const title = document.createElement("h3");
    title.textContent = item.output_folder_name || item.kind || "-";
    const meta = document.createElement("div");
    meta.className = "history-meta";
    meta.textContent = buildHistoryMeta(item, outputs.length);
    body.append(title, meta);

    const summaryActions = document.createElement("div");
    summaryActions.className = "history-summary-actions";
    const status = document.createElement("span");
    status.className = `history-status is-${item.status || "idle"}`;
    status.textContent = historyStatusLabel(item.status);
    const toggle = document.createElement("span");
    toggle.className = "history-toggle-indicator";
    toggle.title = row.open ? translations[language].hideOutputs : translations[language].showOutputs;
    toggle.setAttribute("aria-hidden", "true");
    toggle.append(createIconElement(chevronDownIcon()));
    row.addEventListener("toggle", () => {
      toggle.title = row.open ? translations[language].hideOutputs : translations[language].showOutputs;
    });
    summaryActions.append(status, toggle);

    summary.append(body, summaryActions);

    const detail = document.createElement("div");
    detail.className = "history-detail";
    const detailMeta = document.createElement("div");
    detailMeta.className = "history-detail-meta";
    if (item.source_root) {
      const sourceRoot = document.createElement("p");
      sourceRoot.className = "history-source-root";
      sourceRoot.textContent = item.source_root;
      sourceRoot.title = item.source_root;
      detailMeta.append(sourceRoot);
    }
    if (item.error) {
      const errorLine = document.createElement("p");
      errorLine.className = "history-error";
      errorLine.textContent = item.error;
      detailMeta.append(errorLine);
    }

    const downloads = document.createElement("div");
    downloads.className = "history-downloads";
    if (outputs.length === 0) {
      const empty = document.createElement("p");
      empty.className = "history-empty";
      empty.textContent = item.error || "-";
      downloads.append(empty);
    }
    outputs.forEach((output, index) => {
      downloads.append(createOutputRow(item, output, index));
    });

    detail.append(detailMeta, downloads);
    row.append(summary, detail);
    historyList.append(row);
  });
}

function createOutputRow(item, output, index) {
  const row = document.createElement("div");
  row.className = "history-output-row";

  const name = document.createElement("p");
  name.className = "history-output-name";
  name.textContent = output.download_name || `download-${index + 1}`;
  name.title = name.textContent;

  const actions = document.createElement("div");
  actions.className = "history-output-actions";

  if (output.preview_mode) {
    const previewButton = createIconButton({
      label: translations[language].preview,
      iconMarkup: previewIcon(),
      onClick: () => handlePreview(item.job_id, index, output),
    });
    actions.append(previewButton);
  }

  const saveLink = document.createElement("a");
  saveLink.className = "history-icon-button history-save-link";
  saveLink.href = `/api/downloads/${item.job_id}/${index}`;
  saveLink.title = translations[language].save;
  saveLink.setAttribute("aria-label", translations[language].save);
  saveLink.append(createIconElement(saveIcon()));
  actions.append(saveLink);

  row.append(name, actions);
  return row;
}

function createIconButton({ label, iconMarkup, onClick }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "history-icon-button";
  button.title = label;
  button.setAttribute("aria-label", label);
  button.append(createIconElement(iconMarkup));
  button.addEventListener("click", onClick);
  return button;
}

function createIconElement(markup) {
  const icon = document.createElement("span");
  icon.className = "history-icon";
  icon.innerHTML = markup;
  return icon;
}

function previewIcon() {
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M10.5 5a5.5 5.5 0 1 0 3.47 9.77l4.13 4.13 1.4-1.4-4.13-4.13A5.5 5.5 0 0 0 10.5 5Zm0 2a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7Z"></path>
    </svg>
  `;
}

function saveIcon() {
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M11 4h2v8.17l2.59-2.58L17 11l-5 5-5-5 1.41-1.41L11 12.17V4Zm-5 14h12v2H6v-2Z"></path>
    </svg>
  `;
}

function chevronDownIcon() {
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M7.41 8.59 12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41Z"></path>
    </svg>
  `;
}

function buildHistoryMeta(item, outputCount) {
  const parts = [];
  if (item.kind) {
    parts.push(item.kind);
  }
  if (item.started_at) {
    parts.push(item.started_at);
  }
  parts.push(`${outputCount} ${translations[language].summaryOutputs}`);
  return parts.join(" • ");
}

function historyStatusLabel(status) {
  const key = `status${capitalizeStatus(status)}`;
  return translations[language][key] || status || "-";
}

async function handlePreview(jobId, index, output) {
  if (output.preview_mode === "json") {
    try {
      const response = await fetch(`/api/history/${jobId}/outputs/${index}/preview`);
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      historyPreviewTitle.textContent = payload.name || "JSON Preview";
      historyPreviewContent.textContent = JSON.stringify(payload.content, null, 2);
      historyPreviewPanel.classList.remove("is-hidden");
    } catch (error) {
      historyPreviewTitle.textContent = "Preview";
      historyPreviewContent.textContent = String(error);
      historyPreviewPanel.classList.remove("is-hidden");
    }
    return;
  }

  if (output.preview_mode === "external") {
    try {
      const response = await fetch(`/api/history/${jobId}/outputs/${index}/open`, { method: "POST" });
      if (!response.ok) throw new Error(await response.text());
      const payload = await response.json();
      historyPreviewTitle.textContent = payload.name || "Preview";
      historyPreviewContent.textContent = translations[language].previewOpened;
      historyPreviewPanel.classList.remove("is-hidden");
    } catch (error) {
      historyPreviewTitle.textContent = "Preview";
      historyPreviewContent.textContent = String(error);
      historyPreviewPanel.classList.remove("is-hidden");
    }
    return;
  }

  historyPreviewTitle.textContent = "Preview";
  historyPreviewContent.textContent = translations[language].previewUnavailable;
  historyPreviewPanel.classList.remove("is-hidden");
}

function updateJobStatusCard(job) {
  currentJobStatus = {
    status: job?.status || "idle",
    error: job?.error || null,
    warnings: Array.isArray(job?.warnings) ? job.warnings : [],
    output_paths: Array.isArray(job?.output_paths) ? job.output_paths : [],
    item_count: typeof job?.item_count === "number" ? job.item_count : null,
    skipped_count: typeof job?.skipped_count === "number" ? job.skipped_count : null,
  };
  const status = currentJobStatus.status;
  const statusKey = `status${capitalizeStatus(status)}`;
  const messageKey = `${statusKey}Message`;
  const warningCount = currentJobStatus.warnings.length;
  const outputCount = currentJobStatus.output_paths.length;

  jobStatusCard.classList.remove("is-idle", "is-running", "is-success", "is-failed");
  if (status === "completed") {
    jobStatusCard.classList.add("is-success");
  } else if (status === "failed") {
    jobStatusCard.classList.add("is-failed");
  } else if (status === "running" || status === "queued") {
    jobStatusCard.classList.add("is-running");
  } else {
    jobStatusCard.classList.add("is-idle");
  }

  jobStatusValue.textContent = translations[language][statusKey] || status;
  if (status === "failed" && currentJobStatus.error) {
    jobStatusMessage.textContent = currentJobStatus.error;
  } else if (status === "completed" && warningCount > 0) {
    jobStatusMessage.textContent = `${translations[language].statusCompletedMessage} (${warningCount})`;
  } else {
    jobStatusMessage.textContent = translations[language][messageKey] || translations[language].statusIdleMessage;
  }

  jobSummaryItems.textContent = formatSummaryValue(currentJobStatus.item_count);
  jobSummarySkipped.textContent = formatSummaryValue(currentJobStatus.skipped_count);
  jobSummaryWarnings.textContent = formatSummaryValue(warningCount, true);
  jobSummaryOutputs.textContent = formatSummaryValue(outputCount, true);
}

function formatSummaryValue(value, zeroAllowed = false) {
  if (typeof value === "number") {
    return String(value);
  }
  return zeroAllowed ? "0" : "-";
}

function capitalizeStatus(status) {
  if (!status) return "Idle";
  return status.charAt(0).toUpperCase() + status.slice(1);
}

for (const button of tabButtons) {
  button.addEventListener("click", () => {
    const kind = button.dataset.kind;
    if (!kind) return;
    setActiveKind(kind);
    if (kind !== "settings" && kind !== "history" && !outputFolderName.value.trim()) {
      outputFolderName.value = kinds[kind].stem;
    }
  });
}

for (const input of languageInputs) {
  input.addEventListener("change", () => {
    language = input.value;
    applyLanguage();
  });
}

saveSetting.addEventListener("click", saveCurrentSetting);
openSavedSettings.addEventListener("click", () => showDialog(savedSettingsDialog));
closeSavedSettings.addEventListener("click", () => closeDialog(savedSettingsDialog));
confirmDeleteCancel.addEventListener("click", () => {
  pendingDeletePresetName = null;
  closeDialog(confirmDeleteDialog);
});
confirmDeleteAccept.addEventListener("click", async () => {
  const name = pendingDeletePresetName;
  pendingDeletePresetName = null;
  closeDialog(confirmDeleteDialog);
  await deletePresetByName(name);
});
saveGlobalSettings.addEventListener("click", saveGlobal);
restartServerButton.addEventListener("click", restartServer);
refreshHistory.addEventListener("click", fetchHistory);
savedSettingsDialog.addEventListener("click", (event) => {
  if (event.target === savedSettingsDialog) {
    closeDialog(savedSettingsDialog);
  }
});
confirmDeleteDialog.addEventListener("click", (event) => {
  if (event.target === confirmDeleteDialog) {
    pendingDeletePresetName = null;
    closeDialog(confirmDeleteDialog);
  }
});

async function initialize() {
  await loadGlobalSettings();
  await fetchSavedSettings();
  setActiveKind(activeKind);
  updateJobStatusCard({ status: "idle" });
  checkHealth();
}

initialize();
