Set-Location (Join-Path $PSScriptRoot '..')
py -m http.server 8765 --bind 127.0.0.1 --directory app
