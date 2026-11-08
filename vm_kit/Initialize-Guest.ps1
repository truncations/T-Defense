# Runs inside a newly installed, network-disconnected Windows base VM only.
[CmdletBinding()]
param([switch]$IncludeAI)
$ErrorActionPreference='Stop'
$guestRoot='C:\TDefense'
$kit='C:\TDefense\OfflineKit'
if (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue) { throw 'Base preparation requires no default network route.' }
$installer=@(Get-ChildItem -LiteralPath $kit -Filter 'python-3.14*-amd64.exe' -File)
if ($installer.Count -ne 1) { throw 'Exactly one pinned Python 3.14 installer is required.' }
$p=Start-Process -FilePath $installer[0].FullName -ArgumentList '/quiet InstallAllUsers=0 PrependPath=0 Include_test=0 Include_launcher=0 Shortcuts=0' -WindowStyle Hidden -Wait -PassThru
if ($p.ExitCode -ne 0) { throw 'Python installer failed.' }
$python=Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'
& $python -m venv "$guestRoot\venv"
if ($LASTEXITCODE -ne 0) { throw 'venv creation failed.' }
& "$guestRoot\venv\Scripts\python.exe" -m pip install --no-index --find-links "$kit\wheels" -r "$kit\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw 'Offline package installation failed.' }
Copy-Item -LiteralPath "$kit\chromium" -Destination "$guestRoot\Browsers" -Recurse
if ($IncludeAI) {
    $p=Start-Process -FilePath "$kit\OllamaSetup.exe" -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' -WindowStyle Hidden -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw 'Ollama installation failed.' }
    Copy-Item -LiteralPath "$kit\ollama-models" -Destination "$guestRoot\Models" -Recurse
}
# No clean base is approved automatically. The host separately verifies and seals it.
@{python="$guestRoot\venv\Scripts\python.exe";browsers="$guestRoot\Browsers";aiInstalled=[bool]$IncludeAI} | ConvertTo-Json | Set-Content "$guestRoot\prepared.json" -Encoding UTF8
Write-Output 'Offline base preparation finished. Shut it down and seal it on the host.'
