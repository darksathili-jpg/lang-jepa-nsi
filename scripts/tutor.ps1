param(
    [ValidateSet('qwen', 'granite', 'smol')]
    [string] $Model,
    [ValidateRange(1, 16)]
    [int] $Threads = 2
)
$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    $tutorArgs = @('--threads', "$Threads")
    if ($Model) { $tutorArgs += @('--model', $Model) }
    py -3.12 -m tutor.server @tutorArgs
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
