$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw 'Create the virtual environment first. See README.md.'
}
& $projectPython -B -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
