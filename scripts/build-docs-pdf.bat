@echo off
setlocal enabledelayedexpansion

:: Default parameters
set "DocsDir=docs"
set "BuildDir=docs\_build"

:: Parse arguments if provided
if not "%~1"=="" set "DocsDir=%~1"
if not "%~2"=="" set "BuildDir=%~2"

:: Resolve paths
set "ScriptDir=%~dp0"
:: Remove trailing backslash
set "ScriptDir=%ScriptDir:~0,-1%"
for %%I in ("%ScriptDir%\..") do set "RepoRoot=%%~fI"

set "DocsPath=%RepoRoot%\%DocsDir%"
set "BuildPath=%RepoRoot%\%BuildDir%"

:: Resolve Python interpreter
set "PythonExe="
set "PythonArgs="

if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set "PythonExe=%VIRTUAL_ENV%\Scripts\python.exe"
    )
)

if "%PythonExe%"=="" (
    if exist "%RepoRoot%\venv\Scripts\python.exe" (
        set "PythonExe=%RepoRoot%\venv\Scripts\python.exe"
    )
)

if "%PythonExe%"=="" (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PythonExe=py"
        set "PythonArgs=-3"
    )
)

if "%PythonExe%"=="" (
    where python >nul 2>nul
    if not errorlevel 1 (
        set "PythonExe=python"
    )
)

if "%PythonExe%"=="" (
    echo [ERROR] No Python interpreter found. Activate the project's venv or install Python launcher.
    exit /b 1
)

if not exist "%DocsPath%\" (
    echo [ERROR] Docs directory not found: %DocsPath%
    exit /b 1
)

echo Cleaning Sphinx autosummary cache...
if exist "%DocsPath%\_autosummary\" (
    rmdir /s /q "%DocsPath%\_autosummary"
)

echo Building Sphinx PDF from %DocsPath%
echo Using Python: %PythonExe%

:: Check for TeX toolchain
where pdflatex >nul 2>nul
if not errorlevel 1 (
    echo [INFO] Generating LaTeX sources...
    "%PythonExe%" %PythonArgs% -m sphinx -M latex "%DocsPath%" "%BuildPath%"
    if errorlevel 1 (
        echo [ERROR] Sphinx LaTeX source generation failed!
        exit /b 1
    )

    echo [INFO] Compiling PDF using pdflatex...
    cd /d "%BuildPath%\latex"
    for %%f in (*.tex) do pdflatex -interaction=nonstopmode "%%f"

    if errorlevel 1 (
        echo [WARNING] pdflatex encountered some warnings/errors, but PDF may still rely on second pass.
    )

    :: Build index if idx exists
    for %%f in (*.idx) do makeindex -s python.ist "%%f"

    :: Second pass
    for %%f in (*.tex) do pdflatex -interaction=nonstopmode "%%f"

    :: Third pass to resolve cross-references generated in the 2nd pass
    for %%f in (*.tex) do pdflatex -interaction=nonstopmode "%%f"

    cd /d "%ScriptDir%\.."
    echo [SUCCESS] PDF build complete. Output is under %BuildPath%\latex
    exit /b 0
)

echo [WARNING] No TeX toolchain detected (pdflatex). Generating LaTeX sources instead.
"%PythonExe%" %PythonArgs% -m sphinx -M latex "%DocsPath%" "%BuildPath%"
if errorlevel 1 (
    echo [ERROR] Sphinx LaTeX source generation failed!
    exit /b 1
)
echo [INFO] LaTeX sources generated under %BuildPath%\latex. Install MiKTeX or TeX Live to compile PDF.
exit /b 0
