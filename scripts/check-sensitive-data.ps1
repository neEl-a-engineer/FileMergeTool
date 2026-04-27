param(
    [ValidateSet("push", "release", "history")]
    [string]$Mode = "push",
    [string]$ProjectRoot,
    [string]$ConfigPath,
    [string]$HistoryRange,
    [string[]]$TargetPath,
    [switch]$FailOnWarning
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Finding {
    param(
        [string]$Severity,
        [string]$Source,
        [string]$Path,
        [string]$RuleName,
        [string]$LineText,
        [Nullable[int]]$LineNumber = $null,
        [string]$Commit = ""
    )

    $prefix = "[{0}] {1}" -f $Severity.ToUpperInvariant(), $Source
    $detail = if ($Path) { $Path } else { "(history)" }
    if ($LineNumber) {
        $detail = "{0}:{1}" -f $detail, $LineNumber
    }
    if ($Commit) {
        $detail = "{0} @ {1}" -f $detail, $Commit
    }

    $snippet = $LineText
    if ($snippet.Length -gt 160) {
        $snippet = $snippet.Substring(0, 160) + "..."
    }

    $color = switch ($Severity.ToLowerInvariant()) {
        "error" { "Red" }
        "warning" { "Yellow" }
        default { "Gray" }
    }

    Write-Host "$prefix $detail" -ForegroundColor $color
    Write-Host ("       rule: {0}" -f $RuleName) -ForegroundColor $color
    if ($snippet) {
        Write-Host ("       text: {0}" -f $snippet) -ForegroundColor DarkGray
    }
}

function Invoke-Git {
    param(
        [string[]]$Arguments,
        [switch]$AllowFailure
    )

    Push-Location $script:ResolvedProjectRoot
    try {
        $output = & git @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if (($exitCode -ne 0) -and (-not $AllowFailure)) {
        $joinedArgs = $Arguments -join " "
        $message = ($output | Out-String).Trim()
        throw "git $joinedArgs failed. $message"
    }

    return @($output)
}

function Resolve-ProjectRoot {
    param([string]$Candidate)

    if ($Candidate) {
        return (Resolve-Path -LiteralPath $Candidate).Path
    }

    try {
        $repoRoot = (& git rev-parse --show-toplevel 2>$null)
        if ($LASTEXITCODE -eq 0 -and $repoRoot) {
            return ($repoRoot | Select-Object -First 1).Trim()
        }
    }
    catch {
    }

    return (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

function Resolve-ConfigPath {
    param([string]$Candidate)

    $candidates = @()
    if ($Candidate) {
        $candidates += $Candidate
    }
    $candidates += (Join-Path $script:ResolvedProjectRoot "sensitive-scan.config.json")
    $candidates += (Join-Path $PSScriptRoot "sensitive-scan.config.json")

    foreach ($path in $candidates) {
        if ($path -and (Test-Path -LiteralPath $path -PathType Leaf)) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }

    throw "sensitive-scan.config.json not found. Add it to the project root or pass -ConfigPath."
}

function Load-Config {
    param([string]$Path)

    $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    return $raw | ConvertFrom-Json
}

function Get-OptionalPropertyValue {
    param(
        [object]$InputObject,
        [string]$PropertyName
    )

    if ($null -eq $InputObject) {
        return $null
    }

    $property = $InputObject.PSObject.Properties[$PropertyName]
    if ($null -eq $property) {
        return $null
    }

    return $property.Value
}

function Get-ConfigValue {
    param(
        [object]$InputObject,
        [string[]]$PropertyNames,
        $DefaultValue = $null
    )

    foreach ($propertyName in @($PropertyNames)) {
        $value = Get-OptionalPropertyValue -InputObject $InputObject -PropertyName $propertyName
        if ($null -ne $value) {
            return $value
        }
    }

    return $DefaultValue
}

function Normalize-RelativePath {
    param(
        [string]$Path,
        [string]$BasePath = $script:ResolvedProjectRoot
    )

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $resolvedBase = [System.IO.Path]::GetFullPath($BasePath)
    $baseWithSlash = $resolvedBase.TrimEnd('\') + '\'

    if ($fullPath.StartsWith($baseWithSlash, [System.StringComparison]::OrdinalIgnoreCase)) {
        $relative = $fullPath.Substring($baseWithSlash.Length)
    }
    elseif ($fullPath.Equals($resolvedBase, [System.StringComparison]::OrdinalIgnoreCase)) {
        $relative = "."
    }
    else {
        $relative = $fullPath
    }

    return $relative.Replace('\', '/')
}

function Test-PathRuleMatch {
    param(
        [string]$RelativePath,
        [object[]]$Rules
    )

    $normalized = $RelativePath.Replace('\', '/')

    foreach ($ruleItem in @($Rules)) {
        if ($null -eq $ruleItem) {
            continue
        }

        $rule = if ($ruleItem -is [string]) {
            [string]$ruleItem
        }
        elseif ($null -ne (Get-OptionalPropertyValue -InputObject $ruleItem -PropertyName "path")) {
            [string](Get-OptionalPropertyValue -InputObject $ruleItem -PropertyName "path")
        }
        else {
            continue
        }

        $rule = $rule.Replace('\', '/')
        if ([string]::IsNullOrWhiteSpace($rule)) {
            continue
        }

        if ($rule.Contains('*') -or $rule.Contains('?')) {
            if ($normalized -like $rule) {
                return $true
            }
            continue
        }

        if ($rule.EndsWith('/')) {
            if ($normalized.StartsWith($rule, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
            continue
        }

        if (
            $normalized.Equals($rule, [System.StringComparison]::OrdinalIgnoreCase) -or
            $normalized.StartsWith($rule + '/', [System.StringComparison]::OrdinalIgnoreCase)
        ) {
            return $true
        }
    }

    return $false
}

function Test-ExtensionExcluded {
    param([string]$RelativePath)

    $extension = [System.IO.Path]::GetExtension($RelativePath)
    if ([string]::IsNullOrWhiteSpace($extension)) {
        return $false
    }

    foreach ($item in @($script:ContentSkipExtensions)) {
        if ($extension.Equals([string]$item, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Test-PushAllowedPath {
    param([string]$RelativePath)

    if (@($script:PushBlockedExtensionAllowPaths).Count -eq 0) {
        return $false
    }

    return Test-PathRuleMatch -RelativePath $RelativePath -Rules $script:PushBlockedExtensionAllowPaths
}

function Test-PushDisallowedExtension {
    param([string]$RelativePath)

    $extension = [System.IO.Path]::GetExtension($RelativePath)
    if ([string]::IsNullOrWhiteSpace($extension)) {
        return $false
    }

    foreach ($item in @($script:PushBlockedExtensions)) {
        if ($extension.Equals([string]$item, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }

    return $false
}

function Test-PushTrackedPath {
    param(
        [string]$RelativePath,
        [string]$Source,
        [string]$Commit = ""
    )

    if (Test-PathRuleMatch -RelativePath $RelativePath -Rules $script:GlobalSkipPaths) {
        return
    }

    if (Test-PushAllowedPath -RelativePath $RelativePath) {
        return
    }

    if (Test-PushDisallowedExtension -RelativePath $RelativePath) {
        Add-RecordedFinding -Severity "error" -Source $Source -Path $RelativePath -RuleName "disallowed push extension" -LineText $RelativePath -Commit $Commit
    }
}

function Test-AllowedPattern {
    param([string]$Line)

    foreach ($rule in $script:AllowedPatternRules) {
        if ($rule.Regex.IsMatch($Line)) {
            return $true
        }
    }

    return $false
}

function New-RegexRules {
    param([object[]]$Items)

    $rules = @()

    foreach ($item in @($Items)) {
        $pattern = [string](Get-OptionalPropertyValue -InputObject $item -PropertyName "pattern")
        if ($null -eq $item -or [string]::IsNullOrWhiteSpace($pattern)) {
            continue
        }

        $rules += [pscustomobject]@{
            Name    = [string](Get-OptionalPropertyValue -InputObject $item -PropertyName "name")
            Pattern = $pattern
            Reason  = [string](Get-OptionalPropertyValue -InputObject $item -PropertyName "reason")
            Regex   = [regex]::new($pattern)
        }
    }

    return $rules
}

function Add-RecordedFinding {
    param(
        [string]$Severity,
        [string]$Source,
        [string]$Path,
        [string]$RuleName,
        [string]$LineText,
        [Nullable[int]]$LineNumber = $null,
        [string]$Commit = ""
    )

    $entry = [pscustomobject]@{
        Severity   = $Severity
        Source     = $Source
        Path       = $Path
        RuleName   = $RuleName
        LineText   = $LineText
        LineNumber = $LineNumber
        Commit     = $Commit
    }

    $script:Findings.Add($entry) | Out-Null
    Write-Finding -Severity $Severity -Source $Source -Path $Path -RuleName $RuleName -LineText $LineText -LineNumber $LineNumber -Commit $Commit
}

function Test-RiskyFilename {
    param(
        [string]$RelativePath,
        [string]$Source,
        [string]$Commit = ""
    )

    $leaf = Split-Path -Leaf $RelativePath
    foreach ($pattern in @($script:GlobalErrorFilenames)) {
        if (($leaf -like [string]$pattern) -or ($RelativePath -like [string]$pattern)) {
            Add-RecordedFinding -Severity "error" -Source $Source -Path $RelativePath -RuleName "tracked risky filename" -LineText $leaf -Commit $Commit
        }
    }
}

function Scan-Line {
    param(
        [string]$Line,
        [string]$RelativePath,
        [string]$Source,
        [Nullable[int]]$LineNumber = $null,
        [string]$Commit = ""
    )

    if (Test-PathRuleMatch -RelativePath $RelativePath -Rules $script:ContentAllowPaths) {
        return
    }

    if (Test-AllowedPattern -Line $Line) {
        return
    }

    foreach ($rule in $script:ErrorRules) {
        if ($rule.Regex.IsMatch($Line)) {
            Add-RecordedFinding -Severity "error" -Source $Source -Path $RelativePath -RuleName $rule.Name -LineText $Line -LineNumber $LineNumber -Commit $Commit
        }
    }

    foreach ($rule in $script:WarningRules) {
        if ($rule.Regex.IsMatch($Line)) {
            Add-RecordedFinding -Severity "warning" -Source $Source -Path $RelativePath -RuleName $rule.Name -LineText $Line -LineNumber $LineNumber -Commit $Commit
        }
    }
}

function Scan-File {
    param(
        [string]$FullPath,
        [string]$Source,
        [string]$BasePath = $script:ResolvedProjectRoot
    )

    $relativePath = Normalize-RelativePath -Path $FullPath -BasePath $BasePath

    if (Test-PathRuleMatch -RelativePath $relativePath -Rules $script:GlobalSkipPaths) {
        return
    }

    if (Test-ExtensionExcluded -RelativePath $relativePath) {
        return
    }

    Test-RiskyFilename -RelativePath $relativePath -Source $Source

    try {
        $content = Get-Content -LiteralPath $FullPath -Raw -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        try {
            $content = Get-Content -LiteralPath $FullPath -Raw -ErrorAction Stop
        }
        catch {
            Write-Info ("skip unreadable file: {0}" -f $relativePath)
            return
        }
    }

    if ($content.Contains([char]0)) {
        Write-Info ("skip binary-like file: {0}" -f $relativePath)
        return
    }

    $lines = [regex]::Split($content, "`r?`n")
    for ($index = 0; $index -lt $lines.Count; $index++) {
        Scan-Line -Line $lines[$index] -RelativePath $relativePath -Source $Source -LineNumber ($index + 1)
    }
}

function Get-ProjectFilesFromTargets {
    param([object[]]$Targets)

    $files = New-Object System.Collections.Generic.List[string]

    foreach ($target in @($Targets)) {
        if ($null -eq $target) {
            continue
        }

        $pathText = if ($target -is [string]) {
            [string]$target
        }
        elseif ($null -ne (Get-OptionalPropertyValue -InputObject $target -PropertyName "path")) {
            [string](Get-OptionalPropertyValue -InputObject $target -PropertyName "path")
        }
        else {
            continue
        }

        if ([string]::IsNullOrWhiteSpace($pathText)) {
            continue
        }

        $fullPath = if ([System.IO.Path]::IsPathRooted($pathText)) {
            $pathText
        }
        else {
            Join-Path $script:ResolvedProjectRoot $pathText
        }

        if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
            $files.Add((Resolve-Path -LiteralPath $fullPath).Path) | Out-Null
            continue
        }

        if (Test-Path -LiteralPath $fullPath -PathType Container) {
            Get-ChildItem -LiteralPath $fullPath -File -Recurse | ForEach-Object {
                $files.Add($_.FullName) | Out-Null
            }
            continue
        }

        Write-Info ("target not found: {0}" -f $pathText)
    }

    return @($files | Sort-Object -Unique)
}

function Scan-ReleaseTargets {
    param([object[]]$Targets)

    foreach ($target in @($Targets)) {
        if ($null -eq $target) {
            continue
        }

        $pathText = if ($target -is [string]) {
            [string]$target
        }
        elseif ($null -ne (Get-OptionalPropertyValue -InputObject $target -PropertyName "path")) {
            [string](Get-OptionalPropertyValue -InputObject $target -PropertyName "path")
        }
        else {
            continue
        }

        if ([string]::IsNullOrWhiteSpace($pathText)) {
            continue
        }

        $fullPath = if ([System.IO.Path]::IsPathRooted($pathText)) {
            $pathText
        }
        else {
            Join-Path $script:ResolvedProjectRoot $pathText
        }

        if (Test-Path -LiteralPath $fullPath -PathType Leaf) {
            $resolvedFile = (Resolve-Path -LiteralPath $fullPath).Path
            $basePath = Split-Path -Parent $resolvedFile
            Scan-File -FullPath $resolvedFile -Source "release" -BasePath $basePath
            continue
        }

        if (Test-Path -LiteralPath $fullPath -PathType Container) {
            $resolvedDirectory = (Resolve-Path -LiteralPath $fullPath).Path
            Get-ChildItem -LiteralPath $resolvedDirectory -File -Recurse | ForEach-Object {
                Scan-File -FullPath $_.FullName -Source "release" -BasePath $resolvedDirectory
            }
            continue
        }

        Write-Info ("target not found: {0}" -f $pathText)
    }
}

function Scan-GitPatch {
    param(
        [string[]]$Lines,
        [string]$Source
    )

    $currentCommit = ""
    $currentPath = ""

    foreach ($rawLine in @($Lines)) {
        $line = [string]$rawLine

        if ($line -like "commit:*") {
            $currentCommit = $line.Substring(7).Trim()
            continue
        }

        if ($line -like "+++ b/*") {
            $currentPath = $line.Substring(6).Trim()
            if (-not (Test-PathRuleMatch -RelativePath $currentPath -Rules $script:GlobalSkipPaths)) {
                Test-RiskyFilename -RelativePath $currentPath -Source $Source -Commit $currentCommit
            }
            continue
        }

        if ($line.StartsWith("+++ ")) {
            continue
        }

        if (-not $line.StartsWith("+")) {
            continue
        }

        if (-not $currentPath) {
            continue
        }

        if (Test-PathRuleMatch -RelativePath $currentPath -Rules $script:GlobalSkipPaths) {
            continue
        }

        if (Test-ExtensionExcluded -RelativePath $currentPath) {
            continue
        }

        $addedLine = $line.Substring(1)
        Scan-Line -Line $addedLine -RelativePath $currentPath -Source $Source -Commit $currentCommit
    }
}

function Scan-GitChangedPaths {
    param(
        [string]$Range,
        [string]$Source
    )

    $arguments = @("diff", "--name-only", "--diff-filter=ACMR", "--relative")
    if ($Range) {
        $arguments += @($Range, "--")
    }

    $changedPaths = Invoke-Git -Arguments $arguments
    foreach ($item in @($changedPaths)) {
        $relativePath = ([string]$item).Trim()
        if ([string]::IsNullOrWhiteSpace($relativePath)) {
            continue
        }

        Test-PushTrackedPath -RelativePath $relativePath -Source $Source
        if (-not (Test-PathRuleMatch -RelativePath $relativePath -Rules $script:GlobalSkipPaths)) {
            Test-RiskyFilename -RelativePath $relativePath -Source $Source
        }
    }
}

function Resolve-HistoryLogArguments {
    param([string]$Range)

    if ($Range -eq "--all") {
        return @("log", "--all", "--no-color", "--format=commit:%H", "--patch")
    }

    if ($Range -match '^HEAD~(\d+)\.\.HEAD$') {
        try {
            $countOutput = Invoke-Git -Arguments @("rev-list", "--count", "HEAD")
            $commitCount = [int](([string]($countOutput | Select-Object -First 1)).Trim())
            $requestedDepth = [int]$Matches[1]
            if ($commitCount -le $requestedDepth) {
                Write-Info ("history range expanded to --all because repo only has {0} commits" -f $commitCount)
                return @("log", "--all", "--no-color", "--format=commit:%H", "--patch")
            }
        }
        catch {
        }
    }

    return @("log", "--no-color", "--format=commit:%H", "--patch", $Range, "--")
}

function Try-Get-UpstreamReference {
    Push-Location $script:ResolvedProjectRoot
    try {
        $upstreamOutput = & git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
        if ($LASTEXITCODE -eq 0 -and $upstreamOutput) {
            return ([string]($upstreamOutput | Select-Object -First 1)).Trim()
        }
    }
    finally {
        Pop-Location
    }

    return ""
}

function Resolve-PushHistorySpec {
    $useUnpushedHistory = $true
    if ($null -ne $script:PushConfig) {
        $useUnpushedHistory = [bool]$script:PushPreferUpstreamUnpushedRange
    }

    if ($useUnpushedHistory) {
        $upstreamReference = Try-Get-UpstreamReference
        if ($upstreamReference) {
            return [pscustomobject]@{
                Label  = "unpushed commit range"
                Range  = "$upstreamReference..HEAD"
                Source = "push-unpushed-history"
            }
        }

        Write-Info "no upstream tracking branch found; using fallback history range if configured"
    }

    $fallbackRange = $HistoryRange
    if ((-not $fallbackRange) -and $script:PushFallbackHistoryRange) {
        $fallbackRange = [string]$script:PushFallbackHistoryRange
    }

    if ($fallbackRange) {
        return [pscustomobject]@{
            Label  = "fallback history range"
            Range  = $fallbackRange
            Source = "push-history-fallback"
        }
    }

    return $null
}

function Run-PushMode {
    Write-Info "running push mode"

    $stagedFiles = Invoke-Git -Arguments @("diff", "--cached", "--name-only", "--diff-filter=ACMR", "--relative")
    foreach ($file in @($stagedFiles)) {
        $relativePath = ([string]$file).Trim()
        if ([string]::IsNullOrWhiteSpace($relativePath)) {
            continue
        }
        if (-not (Test-PathRuleMatch -RelativePath $relativePath -Rules $script:GlobalSkipPaths)) {
            Test-PushTrackedPath -RelativePath $relativePath -Source "staged-file"
            Test-RiskyFilename -RelativePath $relativePath -Source "staged-file"
        }
    }

    $stagedDiff = Invoke-Git -Arguments @("diff", "--cached", "--no-color", "--unified=0", "--diff-filter=ACMR", "--relative")
    Scan-GitPatch -Lines $stagedDiff -Source "staged-diff"

    $additionalPaths = @($script:PushScanAdditionalPaths)

    foreach ($file in (Get-ProjectFilesFromTargets -Targets $additionalPaths)) {
        Scan-File -FullPath $file -Source "push-additional"
    }

    $pushHistorySpec = Resolve-PushHistorySpec
    if ($null -ne $pushHistorySpec) {
        Write-Info ("scanning {0}: {1}" -f $pushHistorySpec.Label, $pushHistorySpec.Range)
        try {
            Scan-GitChangedPaths -Range $pushHistorySpec.Range -Source $pushHistorySpec.Source
            $historyPatch = Invoke-Git -Arguments (Resolve-HistoryLogArguments -Range $pushHistorySpec.Range)
            Scan-GitPatch -Lines $historyPatch -Source $pushHistorySpec.Source
        }
        catch {
            Write-Info ("skip history range scan: {0}" -f $_.Exception.Message)
        }
    }
}

function Run-ReleaseMode {
    Write-Info "running release mode"

    $targets = if ($TargetPath -and @($TargetPath).Count -gt 0) {
        @($TargetPath)
    }
    elseif (@($script:ReleaseScanTargets).Count -gt 0) {
        @($script:ReleaseScanTargets)
    }
    else {
        @()
    }

    if (@($targets).Count -eq 0) {
        Write-Info "no release targets configured"
        return
    }

    Scan-ReleaseTargets -Targets $targets
}

function Run-HistoryMode {
    Write-Info "running history mode"

    $range = $HistoryRange
    if ((-not $range) -and $script:HistoryScanRange) {
        $range = [string]$script:HistoryScanRange
    }
    if (-not $range) {
        $range = "--all"
    }

    $historyPatch = Invoke-Git -Arguments (Resolve-HistoryLogArguments -Range $range)
    Scan-GitPatch -Lines $historyPatch -Source "history"
}

$script:ResolvedProjectRoot = Resolve-ProjectRoot -Candidate $ProjectRoot
$script:ResolvedConfigPath = Resolve-ConfigPath -Candidate $ConfigPath
$script:Config = Load-Config -Path $script:ResolvedConfigPath
$script:GlobalSkipPaths = @(
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("global_skip_paths", "exclude_paths") -DefaultValue @()
)
$script:ContentSkipExtensions = @(
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("content_skip_extensions", "exclude_extensions") -DefaultValue @()
)
$script:GlobalErrorFilenames = @(
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("global_error_filenames", "tracked_error_filenames") -DefaultValue @()
)
$script:ContentAllowPaths = @(
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("content_allow_paths", "allowed_paths") -DefaultValue @()
)
$script:ErrorRules = New-RegexRules -Items (
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("content_error_patterns", "error_patterns") -DefaultValue @()
)
$script:WarningRules = New-RegexRules -Items (
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("content_warning_patterns", "warning_patterns") -DefaultValue @()
)
$script:AllowedPatternRules = New-RegexRules -Items (
    Get-ConfigValue -InputObject $script:Config -PropertyNames @("content_allow_patterns", "allowed_patterns") -DefaultValue @()
)
$script:PushConfig = Get-ConfigValue -InputObject $script:Config -PropertyNames @("push") -DefaultValue $null
$script:PushPreferUpstreamUnpushedRange = if ($null -ne $script:PushConfig) {
    [bool](Get-ConfigValue -InputObject $script:PushConfig -PropertyNames @("prefer_upstream_unpushed_range", "use_unpushed_history") -DefaultValue $true)
} else {
    $true
}
$script:PushScanAdditionalPaths = if ($null -ne $script:PushConfig) {
    @(Get-ConfigValue -InputObject $script:PushConfig -PropertyNames @("scan_additional_paths", "additional_paths") -DefaultValue @())
} else {
    @()
}
$script:PushFallbackHistoryRange = if ($null -ne $script:PushConfig) {
    [string](Get-ConfigValue -InputObject $script:PushConfig -PropertyNames @("fallback_history_range", "history_range") -DefaultValue "")
} else {
    ""
}
$script:PushBlockedExtensions = if ($null -ne $script:PushConfig) {
    @(Get-ConfigValue -InputObject $script:PushConfig -PropertyNames @("blocked_extensions", "disallowed_extensions") -DefaultValue @())
} else {
    @()
}
$script:PushBlockedExtensionAllowPaths = if ($null -ne $script:PushConfig) {
    @(Get-ConfigValue -InputObject $script:PushConfig -PropertyNames @("blocked_extension_allow_paths", "allowed_paths") -DefaultValue @())
} else {
    @()
}
$script:ReleaseConfig = Get-ConfigValue -InputObject $script:Config -PropertyNames @("release") -DefaultValue $null
$script:ReleaseScanTargets = if ($null -ne $script:ReleaseConfig) {
    @(Get-ConfigValue -InputObject $script:ReleaseConfig -PropertyNames @("scan_targets", "targets") -DefaultValue @())
} else {
    @()
}
$script:HistoryConfig = Get-ConfigValue -InputObject $script:Config -PropertyNames @("history") -DefaultValue $null
$script:HistoryScanRange = if ($null -ne $script:HistoryConfig) {
    [string](Get-ConfigValue -InputObject $script:HistoryConfig -PropertyNames @("scan_range", "range") -DefaultValue "")
} else {
    ""
}
$script:Findings = New-Object System.Collections.Generic.List[object]

Write-Info ("project root: {0}" -f $script:ResolvedProjectRoot)
Write-Info ("config path: {0}" -f $script:ResolvedConfigPath)

switch ($Mode) {
    "push" { Run-PushMode }
    "release" { Run-ReleaseMode }
    "history" { Run-HistoryMode }
    default { throw "unsupported mode: $Mode" }
}

$errorCount = @($script:Findings | Where-Object { $_.Severity -eq "error" }).Count
$warningCount = @($script:Findings | Where-Object { $_.Severity -eq "warning" }).Count

Write-Host ""
Write-Host ("Summary: errors={0}, warnings={1}" -f $errorCount, $warningCount) -ForegroundColor White

if ($errorCount -gt 0) {
    exit 1
}

if ($FailOnWarning -and $warningCount -gt 0) {
    exit 1
}

exit 0

