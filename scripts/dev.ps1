$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    py -m http.server 8765 --bind 127.0.0.1 --directory app
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
