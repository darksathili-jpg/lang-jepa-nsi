Set-Location (Join-Path $PSScriptRoot '..')
py -m unittest discover -s tests -v
