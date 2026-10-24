param([string[]]$TestPaths = @(
    'tests/api/test_reading_quiz_answers.py',
    'tests/reading/test_reading_captions.py::test_refresh_document_archives_outgoing_units',
    'deeptutor/learning/tests/test_guided_mastery_updates.py::test_hinted_qualitative_pass_does_not_display_full_mastery'
))

# Run from the isolated checkout with its own uv CPython environment.
$ErrorActionPreference = 'Stop'
$names = @('SystemRoot', 'WINDIR', 'ComSpec', 'PYTHONUTF8', 'DEEPTUTOR_HOME')
$prior = @{}
foreach ($name in $names) { $prior[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
$testHome = Join-Path ([IO.Path]::GetTempPath()) ('deeptutor-offline-' + [guid]::NewGuid())
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $windowsDirectory = [Environment]::GetFolderPath('Windows')
    if (!(Test-Path -LiteralPath $windowsDirectory)) { throw 'Cannot locate Windows directory' }
    $env:SystemRoot = $windowsDirectory
    $env:WINDIR = $windowsDirectory
    $env:ComSpec = Join-Path $windowsDirectory 'System32/cmd.exe'
    $env:PYTHONUTF8 = '1'
    $env:DEEPTUTOR_HOME = $testHome
    $python = Join-Path (Get-Location) '.venv/Scripts/python.exe'
    & $python -c "import sys, asyncio, _overlapped; assert sys.version_info[:2] == (3, 12); print(sys.executable)"
    if ($LASTEXITCODE) { throw 'CPython 3.12 / asyncio preflight failed' }
    & $python -m pytest @TestPaths -q
    $result = $LASTEXITCODE
} finally {
    Pop-Location
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $prior[$name], 'Process') }
}
exit $result
