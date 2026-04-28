const form = document.querySelector("#job-form");
const kindInput = document.querySelector("#kind");
const settingName = document.querySelector("#setting-name");
const outputFolderName = document.querySelector("#output-folder-name");
const imageOutputOptions = document.querySelector("#image-output-options");
const outputDir = document.querySelector("#output-dir");
const rootPath = document.querySelector("#root-path");
const excludeDirs = document.querySelector("#exclude-dirs");
const excludeExts = document.querySelector("#exclude-exts");
const excludeDirPatterns = document.querySelector("#exclude-dir-patterns");
const excludeFiles = document.querySelector("#exclude-files");
const excludeFilePatterns = document.querySelector("#exclude-file-patterns");
const extensionSelectionPanel = document.querySelector("#extension-selection-panel");
const selectedExtensionChips = document.querySelector("#selected-extension-chips");
const additionalExts = document.querySelector("#additional-exts");
const additionalMarkers = document.querySelector("#additional-markers");
const additionalMarkerPatterns = document.querySelector("#additional-marker-patterns");
const globalMarkers = document.querySelector("#global-markers");
const globalMarkerPatterns = document.querySelector("#global-marker-patterns");
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
const helpPanel = document.querySelector("#help-panel");
const historyList = document.querySelector("#history-list");
const historyPreviewPanel = document.querySelector("#history-preview-panel");
const historyPreviewTitle = document.querySelector("#history-preview-title");
const historyPreviewContent = document.querySelector("#history-preview-content");
const refreshHistory = document.querySelector("#refresh-history");
const helpSubtabBar = document.querySelector("#help-subtab-bar");
const helpContent = document.querySelector("#help-content");
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

const textExtensionGroups = [
  {
    key: "plain-text",
    label: { ja: "純テキスト系", en: "Plain text" },
    extensions: [".txt", ".md", ".log", ".rst"],
  },
  {
    key: "structured-text",
    label: { ja: "構造テキスト系", en: "Structured text" },
    extensions: [".json", ".xml", ".csv", ".tsv"],
  },
  {
    key: "config",
    label: { ja: "設定 / 構成系", en: "Config / setup" },
    extensions: [".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".gitignore"],
  },
  {
    key: "web",
    label: { ja: "Web系", en: "Web stack" },
    extensions: [".html", ".css", ".js", ".jsx", ".ts", ".tsx"],
  },
  {
    key: "command-script",
    label: { ja: "コマンドスクリプト系", en: "Command scripts" },
    extensions: [".sh", ".ps1", ".bat", ".cmd"],
  },
  {
    key: "programming",
    label: { ja: "プログラミング言語系", en: "Programming languages" },
    extensions: [".py", ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".rb", ".kt", ".swift", ".sql"],
  },
];

function flattenExtensionGroups(groups) {
  return groups.flatMap((group) => group.extensions);
}

const extensionOptionsByKind = {
  "text-merge": flattenExtensionGroups(textExtensionGroups),
  "mail-merge": [".msg"],
  "powerpoint-merge": [".ppt", ".pptm", ".pps", ".ppsm", ".ppsx", ".pot", ".potm", ".potx", ".pptx"],
  "excel-merge": [".csv", ".ods", ".tsv", ".xls", ".xlsb", ".xlsm", ".xlsx", ".xlt", ".xltm", ".xltx"],
  "word-merge": [".doc", ".docm", ".docx", ".dot", ".dotm", ".dotx", ".odt", ".rtf"],
  "pdf-merge": [".pdf"],
  "image-merge": [".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"],
};

const extensionGroupsByKind = {
  "text-merge": textExtensionGroups,
};

const helpSections = {
  quickstart: {
    label: { ja: "はじめに", en: "Quick start" },
    title: { ja: "まずはここから", en: "Start here" },
    lead: {
      ja: "最初は 1 つのタブと 1 つのフォルダに絞ると、流れをつかみやすいです。ここでは最短で成果物まで辿る道筋をまとめています。",
      en: "If this is your first run, keep it small: one tool, one folder, one clear output. This gives you a quick feel for the workflow.",
    },
    cards: [
      {
        title: { ja: "最初の3ステップ", en: "Three-step start" },
        steps: {
          ja: [
            "上のタブで、やりたいマージ機能を選びます。",
            "収集対象ルートフォルダと、必要なら出力フォルダ名や除外条件を整えます。",
            "実行後は右下の実行結果と、履歴タブの出力ファイルを確認します。",
          ],
          en: [
            "Choose the merge tool from the top tab bar.",
            "Set the collection root, then adjust the output folder name and filters if needed.",
            "Run the job, then check the result panel and the outputs in History.",
          ],
        },
      },
      {
        title: { ja: "最初の試運転に向く組み合わせ", en: "Good first-run combinations" },
        items: {
          ja: [
            "構成リスト: フォルダ構成を JSON で俯瞰したい時。",
            "テキスト: Markdown やソースコードを AI に読みやすい JSON にしたい時。",
            "PDF / Word / PowerPoint: 元ファイルの結合に加えて、本文系のマージ JSON も欲しい時。",
          ],
          en: [
            "File list: when you want a JSON overview of a directory tree.",
            "Text: when you want Markdown or source files in an AI-friendly JSON format.",
            "PDF / Word / PowerPoint: when you want both merged files and text-oriented merge JSON outputs.",
          ],
        },
      },
      {
        title: { ja: "実行後に見る場所", en: "Where to look after a run" },
        items: {
          ja: [
            "実行結果: 成功 / 失敗、警告、出力件数を素早く確認できます。",
            "履歴: 出力ファイルごとにプレビューや保存を行えます。",
            "集計 JSON: スキップ理由やエラー理由まで含めて、その回の結果を追えます。",
          ],
          en: [
            "Result panel: quickly check success, failure, warnings, and output count.",
            "History: preview or download each generated artifact.",
            "Summary JSON: inspect skipped items and errors for the full run.",
          ],
        },
      },
    ],
  },
  tools: {
    label: { ja: "機能別", en: "Tool guide" },
    title: { ja: "機能ごとの向き不向き", en: "What each tool is best at" },
    lead: {
      ja: "同じフォルダでも、どのタブを使うかで得られる成果物が変わります。まずは目的から逆算して選ぶのが近道です。",
      en: "The same folder can produce very different outputs depending on the active tool. Pick the tab that best matches your goal.",
    },
    cards: [
      {
        title: { ja: "構成リスト / テキスト / メール", en: "File list / Text / Mail" },
        items: {
          ja: [
            "構成リスト: まず全体構造だけ見たい時の入口。",
            "テキスト: 拡張子を絞りながら、本文を lines 配列で保持したい時。",
            "メール: .msg を件名、差出人、宛先、本文、添付名つきで AI 向け JSON にしたい時。",
          ],
          en: [
            "File list: best as the first overview of a folder tree.",
            "Text: best when you want explicit extension selection and line-based content capture.",
            "Mail: best for turning .msg files into JSON with subject, sender, recipients, body, and attachments.",
          ],
        },
      },
      {
        title: { ja: "Office / PDF", en: "Office / PDF" },
        items: {
          ja: [
            "PowerPoint / PDF / Word: 元ファイルの結合に加えて、本文系マージ JSON を作ります。",
            "Excel: 機密分類つきで、数式版 / 値版の XLSX と JSON をまとめて出力します。",
            "PowerPoint / PDF / Office のプレビューは、サーバー側の既定アプリで実体を開きます。",
          ],
          en: [
            "PowerPoint / PDF / Word produce both merged files and text-oriented merge JSON outputs.",
            "Excel produces formula/value variants for both XLSX and JSON, with confidential split support.",
            "Office and PDF previews open the saved file using the server machine's default app.",
          ],
        },
      },
      {
        title: { ja: "画像", en: "Images" },
        items: {
          ja: [
            "HTML / PPTX / 両方から出力形式を選べます。",
            "人が確認しやすい見た目を重視したい時は HTML、レビュー資料にしたい時は PPTX が扱いやすいです。",
            "履歴タブからは HTML の保存と、PPTX の既定アプリ起動を使い分けられます。",
          ],
          en: [
            "Choose HTML, PPTX, or both as the output format.",
            "HTML is best for quick visual review; PPTX is useful when the result needs to travel as slides.",
            "History lets you download HTML artifacts or open PPTX files with the default app.",
          ],
        },
      },
    ],
  },
  settingsGuide: {
    label: { ja: "設定のコツ", en: "Settings" },
    title: { ja: "設定で迷いやすいポイント", en: "Settings that matter most" },
    lead: {
      ja: "このツールは、何を集めるか・何を除外するか・どう機密分類するかで挙動が大きく変わります。よく効く設定だけ先に押さえると楽です。",
      en: "This tool's behavior changes a lot based on what you collect, what you exclude, and how you classify confidential files. These are the settings worth learning first.",
    },
    cards: [
      {
        title: { ja: "収集対象拡張子", en: "Collected extensions" },
        items: {
          ja: [
            "構成リスト以外は、除外拡張子ではなく収集対象拡張子を選ぶ形です。",
            "テキストタブでは分類ごとに拡張子を選べて、候補にないものだけ追加拡張子へ入れます。",
            "収集対象に入っていても、内部的に読めない形式は集計 JSON に理由つきで残ります。",
          ],
          en: [
            "Every merge tool except File list uses collected extensions instead of excluded extensions.",
            "Text merge groups common extensions by category, and extra ones go into Additional extensions.",
            "If a selected extension cannot be read by the current runtime, the summary JSON records that reason.",
          ],
        },
      },
      {
        title: { ja: "除外ルールと正規表現", en: "Exclusions and regex" },
        items: {
          ja: [
            "除外フォルダ名と除外ファイル名は、通常文字列なら完全一致、正規表現なら case-sensitive に評価します。",
            "追加機密判定文字列は、通常文字列なら部分一致、正規表現なら case-sensitive に評価します。",
            "保存済み設定にしておくと、毎回打ち直さずに同じルールを再利用できます。",
          ],
          en: [
            "Excluded folder/file literals are exact matches; regex rules are evaluated case-sensitively.",
            "Sensitive marker literals use partial matches; regex markers are also case-sensitive.",
            "Saved presets are the easiest way to reuse the same rules across repeated runs.",
          ],
        },
      },
      {
        title: { ja: "設定保存の使い方", en: "Preset workflow" },
        items: {
          ja: [
            "同名保存は上書きではなく、(2), (3) のように採番して追加保存されます。",
            "設定一覧はモーダルで開き、読込と削除をそこから行えます。",
            "よく使うルートフォルダと判定ルールの組み合わせは、機能ごとに分けて持っておくと整理しやすいです。",
          ],
          en: [
            "Saving with the same name creates numbered copies instead of overwriting the original.",
            "The preset list opens in a modal where you can load or delete entries.",
            "It helps to keep separate presets for each merge tool and data source pattern.",
          ],
        },
      },
    ],
  },
  outputs: {
    label: { ja: "出力と履歴", en: "Outputs" },
    title: { ja: "出力ファイルの読み方", en: "Reading the outputs" },
    lead: {
      ja: "実行が終わると、その回専用の履歴フォルダへ成果物がまとまります。ファイル名と履歴タブを合わせて見ると、何が生成されたかが追いやすいです。",
      en: "Each run gets its own history folder. Once you know the naming pattern, the History tab becomes much easier to scan.",
    },
    cards: [
      {
        title: { ja: "命名ルール", en: "Naming pattern" },
        items: {
          ja: [
            "履歴フォルダは `80_workspace/history/{yyyymmdd_hhmmss}_{指定フォルダ名}` です。",
            "機密ファイルは必ず `機密_` で始まります。",
            "出力ファイルは `指定フォルダ名_..._マージ`、集計は `指定フォルダ名_集計.json` に揃います。",
          ],
          en: [
            "History folders use `80_workspace/history/{yyyymmdd_hhmmss}_{folder-name}`.",
            "Confidential outputs always start with `機密_`.",
            "Merge outputs follow `{folder-name}_..._マージ`, and summaries use `{folder-name}_集計.json`.",
          ],
        },
      },
      {
        title: { ja: "履歴タブでできること", en: "What History can do" },
        items: {
          ja: [
            "JSON 出力は画面内プレビューと保存を分けて使えます。",
            "PDF / Office はサーバー側の既定アプリで開くプレビューと、保存を分けて使えます。",
            "履歴カードを開くと、出力フォルダやエラー概要、生成ファイルの一覧まで確認できます。",
          ],
          en: [
            "JSON outputs support in-app preview and download separately.",
            "PDF and Office outputs support server-side open actions plus download.",
            "Expanding a history entry reveals the folder, error summary, and generated artifacts.",
          ],
        },
      },
      {
        title: { ja: "集計 JSON の見どころ", en: "What to read in the summary JSON" },
        items: {
          ja: [
            "対象件数、機密件数、スキップ件数、エラー件数を 1 ファイルで追えます。",
            "どの入力ファイルが merged / skipped / error だったかが一覧で残ります。",
            "内部的に読めなかったファイルも、理由つきで追跡できます。",
          ],
          en: [
            "One file shows scanned, confidential, skipped, and errored counts.",
            "Each source file records whether it was merged, skipped, or failed.",
            "Reader limitations are preserved as explicit skip reasons.",
          ],
        },
      },
    ],
  },
  prompts: {
    label: { ja: "AIプロンプト例", en: "AI prompts" },
    title: { ja: "そのまま使いやすいプロンプト例", en: "Prompt examples you can reuse" },
    lead: {
      ja: "マージ JSON を AI に渡す時は、まず要約、次に観点指定、最後に深掘り、の順に聞くと安定します。ここではすぐ使える叩き台を置いています。",
      en: "When you hand merge JSON to an AI, the smoothest flow is summary first, then targeted questions, then deeper analysis. These are ready-to-use starting points.",
    },
    cards: [
      {
        title: { ja: "テキストマージ JSON 向け", en: "For text merge JSON" },
        body: {
          ja: "仕様書やソースコードをまとめた JSON を読み込ませる時の入口です。",
          en: "Use this when you've merged source files, markdown, or docs into a single JSON artifact.",
        },
        code: {
          ja: "このマージJSONを読んで、まず全体構成を3段階で要約してください。\\n1. フォルダ/ファイル構成の要点\\n2. 重要そうなファイルの候補\\n3. 次に深掘りすべき論点\\n\\n引用する時は、相対パスと lines の位置が分かるように示してください。",
          en: "Read this merge JSON and summarize it in three layers:\\n1. Key points in the folder/file structure\\n2. Candidate files that look important\\n3. What should be examined next\\n\\nWhen you quote, include the relative path and enough line context to find the passage again.",
        },
      },
      {
        title: { ja: "PowerPoint / PDF / Word の本文系 JSON 向け", en: "For PowerPoint / PDF / Word merge JSON" },
        body: {
          ja: "人が読む資料を AI に下読みさせたい時の素直な聞き方です。",
          en: "A good prompt when you want the AI to pre-read presentation or document material for you.",
        },
        code: {
          ja: "このマージJSONを対象に、ファイルごとに次を整理してください。\\n- 何の資料か\\n- 各スライド / ページ / 文書の要点\\n- 重複している説明\\n- 人間が最終確認すべき曖昧な点\\n\\n事実と推測を分けて書いてください。",
          en: "Using this merge JSON, organize the following for each file:\\n- What the material is about\\n- Key points by slide / page / document\\n- Repeated explanations\\n- Ambiguous areas a human should review\\n\\nPlease separate facts from inference.",
        },
      },
      {
        title: { ja: "Excel の数式版 / 値版 JSON 向け", en: "For Excel formula/value JSON" },
        body: {
          ja: "数式ロジックと結果の両方を見る時に相性がいい聞き方です。",
          en: "Useful when you want to compare spreadsheet logic with the calculated values.",
        },
        code: {
          ja: "数式版JSONと値版JSONを見比べて、次を整理してください。\\n- 主要なシートの役割\\n- 重要な計算ロジック\\n- 値として見ると目立つ変化や異常値\\n- 数式の意図が読み取りにくいセル群\\n\\n最後に、レビュー優先度の高いシートを上位3つ挙げてください。",
          en: "Compare the formula JSON and the value JSON, then summarize:\\n- The role of the main sheets\\n- Important calculation logic\\n- Notable changes or outliers in the values\\n- Cells or ranges where the formula intent is hard to read\\n\\nFinish by listing the top three sheets that deserve detailed review.",
        },
      },
    ],
  },
};

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
    tabHelp: "使い方",
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
    excludeDirPatterns: "除外フォルダ正規表現",
    excludeFiles: "除外ファイル名",
    excludeFilePatterns: "除外ファイル名正規表現",
    selectedExts: "収集対象拡張子",
    additionalExts: "追加拡張子",
    extensionSelectAll: "全選択",
    extensionClearAll: "全解除",
    additionalMarkers: "追加機密分類判定文字列",
    additionalMarkerPatterns: "追加機密分類判定正規表現",
    imageOutputFormat: "画像出力形式",
    imageFormatHtml: "HTML",
    imageFormatPptx: "PPTX",
    imageFormatBoth: "両方",
    saveSetting: "設定を保存",
    runJob: "実行",
    settingsTitle: "全体設定",
    globalMarkers: "全体機密分類判定文字列",
    globalMarkerPatterns: "全体機密分類判定正規表現",
    language: "言語",
    restartServer: "サーバーを再起動",
    saveGlobalSettings: "全体設定を保存",
    historyTitle: "履歴",
    refreshHistory: "更新",
    helpTitle: "使い方",
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
    copyPrompt: "コピー",
    copiedPrompt: "コピー済み",
    copyFailed: "コピー失敗",
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
    tabHelp: "Guide",
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
    excludeDirPatterns: "Excluded folder regex",
    excludeFiles: "Excluded file names",
    excludeFilePatterns: "Excluded file name regex",
    selectedExts: "Collected extensions",
    additionalExts: "Additional extensions",
    extensionSelectAll: "Select all",
    extensionClearAll: "Clear",
    additionalMarkers: "Additional sensitive markers",
    additionalMarkerPatterns: "Additional sensitive regex",
    imageOutputFormat: "Image output format",
    imageFormatHtml: "HTML",
    imageFormatPptx: "PPTX",
    imageFormatBoth: "Both",
    saveSetting: "Save setting",
    runJob: "Run",
    settingsTitle: "Global Settings",
    globalMarkers: "Global sensitive markers",
    globalMarkerPatterns: "Global sensitive regex",
    language: "Language",
    restartServer: "Restart server",
    saveGlobalSettings: "Save global settings",
    historyTitle: "History",
    refreshHistory: "Refresh",
    helpTitle: "Guide",
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
    copyPrompt: "Copy",
    copiedPrompt: "Copied",
    copyFailed: "Copy failed",
  },
};

let activeKind = "file-list";
let language = "ja";
let activeHelpSection = "quickstart";
let savedSettingsCache = [];
let currentJobStatus = { status: "idle", warnings: [], output_paths: [] };
let pendingDeletePresetName = null;
const extensionStateByKind = {};

function splitList(value) {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function joinList(value) {
  return (value || []).join(", ");
}

function normalizeExtension(value) {
  const trimmed = String(value || "").trim();
  if (!trimmed) return "";
  return trimmed.startsWith(".") ? trimmed : `.${trimmed}`;
}

function normalizeExtensionList(values) {
  const normalized = [];
  const seen = new Set();
  for (const value of values || []) {
    const extension = normalizeExtension(value);
    if (!extension || seen.has(extension)) continue;
    seen.add(extension);
    normalized.push(extension);
  }
  return normalized;
}

function defaultSelectedExtensions(kind) {
  return [...(extensionOptionsByKind[kind] || [])];
}

function currentSelectedExtensions() {
  return [...selectedExtensionChips.querySelectorAll(".extension-chip.is-selected")].map((button) => button.dataset.ext);
}

function currentAdditionalExtensions() {
  return normalizeExtensionList(splitList(additionalExts.value));
}

function ensureExtensionState(kind) {
  if (!extensionStateByKind[kind]) {
    extensionStateByKind[kind] = {
      selectedExtensions: defaultSelectedExtensions(kind),
      additionalExtensions: [],
    };
  }
  return extensionStateByKind[kind];
}

function saveExtensionState(kind) {
  if (!kind || kind === "file-list" || kind === "history" || kind === "settings") {
    return;
  }
  extensionStateByKind[kind] = {
    selectedExtensions: currentSelectedExtensions(),
    additionalExtensions: currentAdditionalExtensions(),
  };
}

function loadExtensionState(kind) {
  const state = ensureExtensionState(kind);
  renderExtensionChips(kind, state.selectedExtensions);
  additionalExts.value = joinList(state.additionalExtensions);
}

function renderExtensionChips(kind, selectedValues) {
  selectedExtensionChips.innerHTML = "";
  const selectedSet = new Set(normalizeExtensionList(selectedValues));

  const groups = extensionGroupsByKind[kind];
  selectedExtensionChips.classList.toggle("is-grouped", Boolean(groups?.length));
  if (groups?.length) {
    for (const group of groups) {
      selectedExtensionChips.append(createExtensionGroup(group, selectedSet));
    }
    return;
  }

  const flatGroup = document.createElement("div");
  flatGroup.className = "extension-chip-list";
  for (const extension of extensionOptionsByKind[kind] || []) {
    flatGroup.append(createExtensionChip(extension, selectedSet));
  }
  selectedExtensionChips.append(flatGroup);
}

function createExtensionGroup(group, selectedSet) {
  const section = document.createElement("section");
  section.className = "extension-group";
  section.dataset.groupKey = group.key;

  const header = document.createElement("div");
  header.className = "extension-group-header";

  const title = document.createElement("p");
  title.className = "extension-group-title";
  title.textContent = group.label?.[language] || group.key;

  const actions = document.createElement("div");
  actions.className = "extension-group-actions";

  const selectAll = document.createElement("button");
  selectAll.type = "button";
  selectAll.className = "extension-group-action";
  selectAll.textContent = translations[language].extensionSelectAll;
  selectAll.addEventListener("click", () => {
    setGroupSelection(section, true);
  });

  const clearAll = document.createElement("button");
  clearAll.type = "button";
  clearAll.className = "extension-group-action";
  clearAll.textContent = translations[language].extensionClearAll;
  clearAll.addEventListener("click", () => {
    setGroupSelection(section, false);
  });

  actions.append(selectAll, clearAll);
  header.append(title, actions);

  const chips = document.createElement("div");
  chips.className = "extension-chip-list";
  for (const extension of group.extensions) {
    chips.append(createExtensionChip(extension, selectedSet));
  }

  section.append(header, chips);
  return section;
}

function createExtensionChip(extension, selectedSet) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "extension-chip";
  button.dataset.ext = extension;
  button.textContent = extension;
  button.classList.toggle("is-selected", selectedSet.has(extension));
  button.addEventListener("click", () => {
    button.classList.toggle("is-selected");
  });
  return button;
}

function setGroupSelection(groupElement, shouldSelect) {
  for (const chip of groupElement.querySelectorAll(".extension-chip")) {
    chip.classList.toggle("is-selected", shouldSelect);
  }
}

function localizedValue(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value[language] ?? value.ja ?? value.en ?? "";
  }
  return value ?? "";
}

function renderHelpPanel() {
  renderHelpTabs();
  renderHelpSection();
}

function renderHelpTabs() {
  helpSubtabBar.innerHTML = "";
  Object.entries(helpSections).forEach(([key, section]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "help-subtab-button";
    button.dataset.helpSection = key;
    button.textContent = localizedValue(section.label);
    button.classList.toggle("is-active", key === activeHelpSection);
    button.setAttribute("aria-selected", key === activeHelpSection ? "true" : "false");
    button.addEventListener("click", () => {
      activeHelpSection = key;
      renderHelpPanel();
    });
    helpSubtabBar.append(button);
  });
}

function renderHelpSection() {
  const section = helpSections[activeHelpSection] || helpSections.quickstart;
  helpContent.innerHTML = "";

  const header = document.createElement("header");
  header.className = "help-section-header";

  const title = document.createElement("h3");
  title.className = "help-section-title";
  title.textContent = localizedValue(section.title);

  const lead = document.createElement("p");
  lead.className = "help-section-lead";
  lead.textContent = localizedValue(section.lead);

  header.append(title, lead);
  helpContent.append(header);

  const grid = document.createElement("div");
  grid.className = "help-card-grid";

  for (const card of section.cards || []) {
    grid.append(createHelpCard(card));
  }

  helpContent.append(grid);
}

function createHelpCard(card) {
  const article = document.createElement("article");
  article.className = "help-card";

  const title = document.createElement("h4");
  title.className = "help-card-title";
  title.textContent = localizedValue(card.title);
  article.append(title);

  const body = localizedValue(card.body);
  if (body) {
    const paragraph = document.createElement("p");
    paragraph.className = "help-card-body";
    paragraph.textContent = body;
    article.append(paragraph);
  }

  const steps = localizedValue(card.steps);
  if (Array.isArray(steps) && steps.length > 0) {
    article.append(createHelpList(steps, true));
  }

  const items = localizedValue(card.items);
  if (Array.isArray(items) && items.length > 0) {
    article.append(createHelpList(items, false));
  }

  const code = localizedValue(card.code);
  if (code) {
    const actions = document.createElement("div");
    actions.className = "help-card-actions";

    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "secondary-button help-copy-button";
    copy.textContent = translations[language].copyPrompt;
    copy.addEventListener("click", async () => {
      const original = copy.textContent;
      try {
        await navigator.clipboard.writeText(code);
        copy.textContent = translations[language].copiedPrompt;
      } catch {
        copy.textContent = translations[language].copyFailed;
      }
      window.setTimeout(() => {
        copy.textContent = original;
      }, 1400);
    });
    actions.append(copy);

    const pre = document.createElement("pre");
    pre.className = "help-code";
    pre.textContent = code.replace(/\\n/g, "\n");

    article.append(actions, pre);
  }

  return article;
}

function createHelpList(items, ordered = false) {
  const list = document.createElement(ordered ? "ol" : "ul");
  list.className = ordered ? "help-step-list" : "help-list";
  for (const item of items) {
    const entry = document.createElement("li");
    entry.textContent = item;
    list.append(entry);
  }
  return list;
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

function sensitivityPatternsForRequest() {
  return [...new Set([...splitList(globalMarkerPatterns.value), ...splitList(additionalMarkerPatterns.value)])];
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
  saveExtensionState(activeKind);
  return {
    name: settingName.value.trim(),
    kind: activeKind,
    outputFolderName: outputFolderName.value.trim(),
    outputDir: outputDir.value.trim(),
    rootPath: rootPath.value.trim(),
    excludeDirs: splitList(excludeDirs.value),
    excludeExts: splitList(excludeExts.value),
    excludeDirPatterns: splitList(excludeDirPatterns.value),
    excludeFiles: splitList(excludeFiles.value),
    excludeFilePatterns: splitList(excludeFilePatterns.value),
    selectedExtensions: activeKind === "file-list" ? [] : currentSelectedExtensions(),
    additionalExtensions: activeKind === "file-list" ? [] : currentAdditionalExtensions(),
    additionalMarkers: splitList(additionalMarkers.value),
    additionalMarkerPatterns: splitList(additionalMarkerPatterns.value),
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
  excludeExts.value = joinList(state.excludeExts || state.excludeExtensions || []);
  excludeDirPatterns.value = joinList(state.excludeDirPatterns);
  excludeFiles.value = joinList(state.excludeFiles);
  excludeFilePatterns.value = joinList(state.excludeFilePatterns);
  additionalMarkers.value = joinList(state.additionalMarkers);
  additionalMarkerPatterns.value = joinList(state.additionalMarkerPatterns);
  extensionStateByKind[kind] = {
    selectedExtensions: normalizeExtensionList(state.selectedExtensions?.length ? state.selectedExtensions : defaultSelectedExtensions(kind)),
    additionalExtensions: normalizeExtensionList(state.additionalExtensions || []),
  };
  loadExtensionState(kind);
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
    globalMarkerPatterns.value = joinList(settings.globalMarkerPatterns || []);
  } catch {
    try {
      const settings = JSON.parse(localStorage.getItem(globalSettingsKey) || "{}");
      language = settings.language || "ja";
      globalMarkers.value = joinList(settings.globalMarkers || ["機密", "極秘"]);
      globalMarkerPatterns.value = joinList(settings.globalMarkerPatterns || []);
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
    globalMarkerPatterns: splitList(globalMarkerPatterns.value),
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
  renderHelpPanel();
  updateActiveKindLabel();
  if (activeKind !== "file-list" && activeKind !== "history" && activeKind !== "settings") {
    saveExtensionState(activeKind);
    loadExtensionState(activeKind);
  }
}

function setActiveKind(kind) {
  if (kind === "settings") {
    saveExtensionState(activeKind);
    jobPanel.classList.add("is-hidden");
    historyPanel.classList.add("is-hidden");
    helpPanel.classList.add("is-hidden");
    settingsPanel.classList.remove("is-hidden");
  } else if (kind === "history") {
    saveExtensionState(activeKind);
    jobPanel.classList.add("is-hidden");
    settingsPanel.classList.add("is-hidden");
    helpPanel.classList.add("is-hidden");
    historyPanel.classList.remove("is-hidden");
    fetchHistory();
  } else if (kind === "help") {
    saveExtensionState(activeKind);
    jobPanel.classList.add("is-hidden");
    settingsPanel.classList.add("is-hidden");
    historyPanel.classList.add("is-hidden");
    helpPanel.classList.remove("is-hidden");
    renderHelpPanel();
  } else {
    const previousKind = activeKind;
    const currentFolderName = outputFolderName.value.trim();
    saveExtensionState(previousKind);
    activeKind = kind;
    kindInput.value = kind;
    jobPanel.classList.remove("is-hidden");
    settingsPanel.classList.add("is-hidden");
    historyPanel.classList.add("is-hidden");
    helpPanel.classList.add("is-hidden");
    imageOutputOptions.classList.toggle("is-hidden", kind !== "image-merge");
    excludeExts.closest(".field").classList.toggle("is-hidden", kind !== "file-list");
    extensionSelectionPanel.classList.toggle("is-hidden", kind === "file-list");
    if (kind !== "file-list") {
      loadExtensionState(kind);
    }
    if (!currentFolderName || currentFolderName === kinds[previousKind].stem) {
      outputFolderName.value = kinds[kind].stem;
    }
    updateActiveKindLabel();
  }

  for (const button of tabButtons) {
    button.classList.toggle("is-active", button.dataset.kind === kind);
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
    exclude_extensions: activeKind === "file-list" ? splitList(excludeExts.value) : [],
    selected_extensions: activeKind === "file-list" ? [] : currentSelectedExtensions(),
    additional_extensions: activeKind === "file-list" ? [] : currentAdditionalExtensions(),
    exclude_dirs: splitList(excludeDirs.value),
    exclude_dir_patterns: splitList(excludeDirPatterns.value),
    exclude_files: splitList(excludeFiles.value),
    exclude_file_patterns: splitList(excludeFilePatterns.value),
    additional_sensitive_markers: sensitivityMarkersForRequest(),
    additional_sensitive_patterns: sensitivityPatternsForRequest(),
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
    if (kind !== "settings" && kind !== "history" && kind !== "help" && !outputFolderName.value.trim()) {
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
  renderHelpPanel();
  setActiveKind(activeKind);
  updateJobStatusCard({ status: "idle" });
  checkHealth();
}

initialize();
