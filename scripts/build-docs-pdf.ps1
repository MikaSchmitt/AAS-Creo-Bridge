param(
    [string]$DocsDir = "docs",
    [string]$BuildDir = "docs/_build"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$docsPath = Join-Path $repoRoot $DocsDir
$buildPath = Join-Path $repoRoot $BuildDir

# Resolve Python interpreter without requiring `python` on PATH.
$pythonExe = $null
$pythonArgs = @()

if ($env:VIRTUAL_ENV) {
    $activeVenvPython = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if (Test-Path $activeVenvPython) {
        $pythonExe = $activeVenvPython
    }
}

if (-not $pythonExe) {
    $repoVenvPython = Join-Path $repoRoot "venv\Scripts\python.exe"
    if (Test-Path $repoVenvPython) {
        $pythonExe = $repoVenvPython
    }
}

if (-not $pythonExe) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $pythonExe = $pyLauncher.Source
        $pythonArgs = @("-3")
    }
}

if (-not $pythonExe) {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $pythonExe = $pythonCommand.Source
    }
}

if (-not $pythonExe) {
    throw "No Python interpreter found. Activate the project's venv or install Python launcher (`py`)."
}

if (-not (Test-Path $docsPath)) {
    throw "Docs directory not found: $docsPath"
}

Write-Host "Building Sphinx PDF from $docsPath" -ForegroundColor Cyan
Write-Host "Using Python: $pythonExe" -ForegroundColor DarkCyan

# Compile directly to PDF when a TeX toolchain is available, otherwise emit LaTeX sources.
$hasLatexMk = $null -ne (Get-Command latexmk -ErrorAction SilentlyContinue)
$hasPdfLatex = $null -ne (Get-Command pdflatex -ErrorAction SilentlyContinue)

if ($hasLatexMk -or $hasPdfLatex) {
    & $pythonExe @pythonArgs -m sphinx -M latexpdf $docsPath $buildPath
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
    Write-Host "PDF build complete. Output is under $buildPath\latex" -ForegroundColor Green
    exit 0
}

Write-Warning "No TeX toolchain detected (latexmk/pdflatex). Generating LaTeX sources instead."
& $pythonExe @pythonArgs -m sphinx -M latex $docsPath $buildPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
Write-Host "LaTeX sources generated under $buildPath\latex. Install MiKTeX or TeX Live to compile PDF." -ForegroundColor Yellow

