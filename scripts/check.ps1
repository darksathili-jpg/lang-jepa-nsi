$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    py -m unittest discover -s tests -v
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
