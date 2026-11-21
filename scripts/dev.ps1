param([switch] $LaboratoireSeul)
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    if ($LaboratoireSeul) {
        py -m http.server 8765 --bind 127.0.0.1 --directory app
    } else {
        py -3.12 -m tutor.server
    }
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
