# Requires Windows PowerShell 5.1, not a normal non-admin terminal for setup/run actions.
[CmdletBinding(SupportsShouldProcess=$true)]
param(
 [ValidateSet('Preflight','EnableHyperV','CreateBase','PrepareBase','SealBase','Inspect')][string]$Action='Preflight',
 [string]$IsoPath,
 [string]$OfflineKit='C:\Users\Aaron\Documents\TDefense-Sandbox\OfflineKit',
 [string]$TargetOrigin='https://example.com',
 [PSCredential]$GuestCredential,
 [string[]]$PublicEgressAddress,
 [switch]$UseLocalAI
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$projectRoot=Split-Path $PSScriptRoot -Parent
$stateRoot=Join-Path $projectRoot 'work\disposable-vm'
$baseVM='TDefense-Clean-Base'
$switchName='TDefense-Isolated'
$hostAddress='192.168.253.1'
$guestAddress='192.168.253.2'
$python=Join-Path $projectRoot '.venv\Scripts\python.exe'
$baseDisk=Join-Path $stateRoot 'base\Windows.vhdx'
$manifest=Join-Path $stateRoot 'sealed-base.json'
function Is-Admin {
 $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
 return ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Assert-Host {
 if ($PSVersionTable.PSEdition -ne 'Desktop') { throw 'Use Windows PowerShell 5.1 (powershell.exe), not PowerShell 7, for Hyper-V/PowerShell Direct actions.' }
 if (-not (Is-Admin)) { throw 'Run Windows PowerShell as Administrator for this action. Preflight works without elevation.' }
 if (-not (Get-Command New-VM -ErrorAction SilentlyContinue)) { throw 'Hyper-V module is unavailable. Run EnableHyperV, reboot when ready, then retry.' }
 Import-Module Hyper-V
}
function Assert-Base {
 $vm=Get-VM -Name $baseVM
 if ($vm.Notes -ne 'TDefense-owned-clean-base-v1' -or $vm.Generation -ne 2) { throw 'Base ownership/type mismatch.' }
 $disks=@(Get-VMHardDiskDrive -VMName $baseVM)
 if ($disks.Count -ne 1 -or [IO.Path]::GetFullPath($disks[0].Path) -ne [IO.Path]::GetFullPath($baseDisk)) { throw 'Base disk ownership mismatch.' }
 if (Get-VMNetworkAdapter -VMName $baseVM | Where-Object SwitchName) { throw 'Base must have no connected adapters.' }
}
function Assert-Acls([string]$Name) {
 $rules=@(Get-VMNetworkAdapterExtendedAcl -VMName $Name)
 if ($rules.Count -ne 5) { throw 'Unexpected adapter rule count.' }
 $expected=@(@(1,'Outbound','0.0.0.0/0'),@(2,'Outbound','::/0'),@(3,'Inbound','0.0.0.0/0'),@(4,'Inbound','::/0'))
 foreach ($e in $expected) {
  $rule=@($rules | Where-Object Weight -eq $e[0])
  if ($rule.Count -ne 1 -or [string]$rule[0].Action -ne 'Deny' -or [string]$rule[0].Direction -ne $e[1] -or [string]$rule[0].RemoteIPAddress -ne $e[2] -or $rule[0].Stateful) { throw 'Deny rule readback mismatch.' }
  if ([string]$rule[0].LocalIPAddress -notin @('','Any','*','0.0.0.0/0','::/0') -or [string]$rule[0].RemotePort -notin @('','Any','*','0-65535') -or [string]$rule[0].LocalPort -notin @('','Any','*','0-65535') -or [string]$rule[0].Protocol -notin @('','Any','*','256')) { throw 'Deny rule is unexpectedly restricted.' }
 }
 $allow=@($rules | Where-Object Weight -eq 100)
 if ($allow.Count -ne 1 -or [string]$allow[0].Action -ne 'Allow' -or [string]$allow[0].Direction -ne 'Outbound' -or [string]$allow[0].RemoteIPAddress -notin @($hostAddress,"$hostAddress/32") -or [string]$allow[0].RemotePort -ne '18080' -or [string]$allow[0].Protocol -notin @('TCP','6') -or -not $allow[0].Stateful -or $allow[0].IdleSessionTimeout -ne 90) { throw 'Proxy allow rule readback mismatch.' }
}
function Guest-Session([string]$Name) {
 if (-not $GuestCredential) { $script:GuestCredential=Get-Credential -Message 'Local administrator account INSIDE the disposable Windows base (not your host account)' }
 $end=(Get-Date).AddSeconds(90)
 do {
  try { return New-PSSession -VMName $Name -Credential $GuestCredential -ErrorAction Stop }
  catch { if ((Get-Date) -ge $end) { throw 'Guest did not become available through PowerShell Direct within 90 seconds.' };Start-Sleep -Seconds 2 }
 } while ($true)
}
function Assert-ChildPath([string]$Path,[string]$Directory) {
 $resolved=[IO.Path]::GetFullPath($Path)
 $prefix=[IO.Path]::GetFullPath($Directory).TrimEnd('\')+'\'
 if (-not $resolved.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or $resolved -eq [IO.Path]::GetFullPath($baseDisk)) { throw 'Refusing an operation outside the generated job directory.' }
 if ((Get-Item -LiteralPath $Directory).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Job directory cannot be a junction/symlink.' }
}
if ($Action -eq 'Preflight') {
 $edition=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').EditionID
 [pscustomobject]@{Edition=$edition;Administrator=(Is-Admin);HyperVCmdlets=[bool](Get-Command New-VM -ErrorAction SilentlyContinue);OfflineKitPresent=(Test-Path -LiteralPath $OfflineKit);BasePresent=(Test-Path -LiteralPath $manifest);LiveReady=$false;Next='Enable Hyper-V as administrator; install Windows into an offline base VM; prepare and seal it; Inspect performs boundary tests on EVERY new job.'} | ConvertTo-Json
 return
}
if ($Action -eq 'EnableHyperV') {
 if (-not (Is-Admin)) { throw 'Hyper-V installation requires Windows PowerShell as Administrator.' }
 if ($PSCmdlet.ShouldProcess('Windows optional feature Microsoft-Hyper-V-All','Enable without rebooting automatically')) {
  Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All -NoRestart
  Write-Host 'Feature installation requested. Save your work and reboot manually before CreateBase.'
 }
 return
}
Assert-Host
Set-Location -LiteralPath $projectRoot
if (-not $PSCmdlet.ShouldProcess('T-Defense dedicated VM resources',$Action)) { return }
if ($Action -eq 'CreateBase') {
 if (-not $IsoPath -or -not (Test-Path -LiteralPath $IsoPath -PathType Leaf) -or [IO.Path]::GetExtension($IsoPath) -ne '.iso') { throw 'Supply a Windows installation ISO using -IsoPath. No OS media is downloaded automatically.' }
 if ((Get-VM -Name $baseVM -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath $baseDisk)) { throw 'Base resources already exist; refusing to overwrite.' }
 New-Item -ItemType Directory -Path (Split-Path $baseDisk) -Force | Out-Null
 New-VM -Name $baseVM -Generation 2 -MemoryStartupBytes 8GB -NewVHDPath $baseDisk -NewVHDSizeBytes 64GB -Path (Split-Path $baseDisk) | Out-Null
 Disconnect-VMNetworkAdapter -VMName $baseVM
 Set-VM -Name $baseVM -Notes 'TDefense-owned-clean-base-v1' -AutomaticStartAction Nothing -AutomaticStopAction TurnOff -CheckpointType Disabled
 Set-VMProcessor -VMName $baseVM -Count 4
 Set-VMKeyProtector -VMName $baseVM -NewLocalKeyProtector
 Enable-VMTPM -VMName $baseVM
 $dvd=Add-VMDvdDrive -VMName $baseVM -Path ([IO.Path]::GetFullPath($IsoPath)) -PassThru
 Set-VMFirmware -VMName $baseVM -FirstBootDevice $dvd -EnableSecureBoot On
 Start-VM -Name $baseVM
 Write-Host "Open Hyper-V Manager -> $baseVM -> Connect. Install Windows using a disposable local administrator account. Keep it disconnected and do not sign into personal accounts. Then run PrepareBase."
 return
}
if ($Action -eq 'PrepareBase') {
 Assert-Base
 if (Test-Path -LiteralPath $manifest) { throw 'Base is already sealed; do not modify it while child disks may exist.' }
 if (-not (Test-Path -LiteralPath $OfflineKit -PathType Container)) { throw 'OfflineKit not found.' }
 $vm=Get-VM -Name $baseVM
 if ((Get-VMNetworkAdapter -VMName $baseVM | Where-Object SwitchName)) { throw 'Disconnect all base adapters before preparation.' }
 if ($vm.State -eq 'Off') { Start-VM -Name $baseVM | Out-Null }
 $session=Guest-Session $baseVM
 try {
  Invoke-Command -Session $session -ScriptBlock {
   if ((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').InstallationType -eq 'Server Core') { throw 'This VM uses Server Core. Install Windows Server with Desktop Experience before preparing this base.' }
   New-Item -ItemType Directory -Path 'C:\TDefense' -Force | Out-Null
  }
  Copy-Item -LiteralPath $OfflineKit -Destination 'C:\TDefense\OfflineKit' -ToSession $session -Recurse
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Initialize-Guest.ps1') -Destination 'C:\TDefense\Initialize-Guest.ps1' -ToSession $session
  Invoke-Command -Session $session -ArgumentList ([bool]$UseLocalAI) -ScriptBlock {param($AI);& 'C:\TDefense\Initialize-Guest.ps1' -IncludeAI:$AI}
 } finally { Remove-PSSession $session }
 Write-Host 'PrepareBase finished. Run SealBase next. Installers/models are reused in each disposable clone.'
 return
}
if ($Action -eq 'SealBase') {
 Assert-Base
 if (Test-Path -LiteralPath $manifest) { throw 'A sealed manifest already exists. No base is overwritten.' }
 $session=Guest-Session $baseVM
 try {
  Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'readiness.py') -Destination 'C:\TDefense\readiness-check.py' -ToSession $session
  $ok=Invoke-Command -Session $session -ScriptBlock {
   if ((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').InstallationType -eq 'Server Core') { throw 'This VM uses Server Core. Reinstall with Desktop Experience before sealing it.' }
   if (-not (Test-Path 'C:\TDefense\prepared.json')) { throw 'Run PrepareBase first.' }
   if (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue) { throw 'Base must remain offline.' }
   if (Get-Command Get-BitLockerVolume -ErrorAction SilentlyContinue) {
    $bitlocker=Get-BitLockerVolume -MountPoint C: -ErrorAction Stop
    if ([string]$bitlocker.VolumeStatus -ne 'FullyDecrypted') { throw 'Base must be fully decrypted; TPM-bound encrypted disks cannot be cloned this way.' }
   } elseif (Get-Command Get-WindowsFeature -ErrorAction SilentlyContinue) {
    if ((Get-WindowsFeature -Name BitLocker).Installed) { throw 'Cannot verify encryption state of this base.' }
   } else { throw 'Cannot verify base encryption state.' }
   $env:PLAYWRIGHT_BROWSERS_PATH='C:\TDefense\Browsers'
   # Execute a script file: PS5.1 strips embedded quotes from Python -c arguments.
   $previousPreference=$ErrorActionPreference
   try {
    $ErrorActionPreference='Continue'
    $probeOutput=@(& 'C:\TDefense\venv\Scripts\python.exe' 'C:\TDefense\readiness-check.py' 2>&1)
    $probeExit=$LASTEXITCODE
   } finally { $ErrorActionPreference=$previousPreference }
   $diagnostic=($probeOutput -join "`n")
   if ($diagnostic.Length -gt 8192) { throw 'Offline browser readiness returned oversized diagnostics.' }
   if ($probeExit -ne 0) { throw "Offline browser readiness failed. $diagnostic" }
   try { $probe=$diagnostic | ConvertFrom-Json } catch { throw 'Offline browser readiness returned invalid JSON.' }
   if ($probe.ok -isnot [bool] -or $probe.ok -ne $true) { throw 'Offline browser readiness did not confirm success.' }
   return $true
  }
  if (-not $ok) { throw 'Base verification failed.' }
 } finally { Remove-PSSession $session }
 Stop-VM -Name $baseVM -Force
 if ((Get-VM -Name $baseVM).State -ne 'Off') { throw 'Base is not shut down.' }
 $disk=Get-VHD -Path $baseDisk
 if ($disk.VhdType -eq 'Differencing' -or $disk.Attached) { throw 'Base must be a detached standalone disk.' }
 $hash=(Get-FileHash -LiteralPath $baseDisk -Algorithm SHA256).Hash
 @{version=1;path=$baseDisk;sha256=$hash} | ConvertTo-Json | Set-Content -LiteralPath $manifest -Encoding UTF8
 Write-Host 'Clean offline base sealed. Do not start or edit the base while disposable children exist.'
 return
}
# Inspect is separate from the existing localhost-only app/investigator.py.
if ($Action -ne 'Inspect') { throw 'Unsupported action.' }
if (-not (Test-Path -LiteralPath $manifest)) { throw 'No sealed base. Complete CreateBase, PrepareBase, and SealBase first.' }
# Validate the destination before creating host resources. No network access occurs here.
$origin=$TargetOrigin | & $python -m vm_kit.checks origin
if ($LASTEXITCODE -ne 0) { throw 'Use an origin-only public http(s) destination, without a path or query.' }
Assert-Base
$seal=Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
if ($seal.path -ne $baseDisk -or (Get-FileHash -LiteralPath $baseDisk -Algorithm SHA256).Hash -ne $seal.sha256 -or (Get-VM -Name $baseVM).State -ne 'Off') { throw 'Base identity changed or base is running; no inspection allowed.' }
$mutex=[Threading.Mutex]::new($false,'Global\TDefenseDisposableVM')
if (-not $mutex.WaitOne(0)) { $mutex.Dispose();throw 'Another disposable inspection is running.' }
$jobId=[Guid]::NewGuid().ToString('N')
$jobVM='TDefense-Job-'+$jobId
$jobDir=Join-Path $stateRoot ('jobs\'+$jobId)
$child=Join-Path $jobDir 'job.vhdx'
$firewall='TDefense-Job-'+$jobId
$session=$null;$proxy=$null;$canary=$null;$vmCreated=$false;$cleanupFailed=$false
$validated=$null
try {
 New-Item -ItemType Directory -Path $jobDir | Out-Null
 $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
 & icacls.exe $jobDir /inheritance:r /grant:r "${sid}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
 if ($LASTEXITCODE -ne 0) { throw 'Cannot protect temporary session files.' }
 $switchOwner=Join-Path $stateRoot 'switch-owner.json'
 $switch=Get-VMSwitch -Name $switchName -ErrorAction SilentlyContinue
 if (-not $switch) {
  # Refuse overlapping local IPv4 networks, including VPN routes. No NAT/default route is created.
  $conflict=Get-NetRoute -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -ne '0.0.0.0/0' -and $_.DestinationPrefix -ne '255.255.255.255/32' } | ForEach-Object {
   $prefix=$_.DestinationPrefix
   $value=& $python -m vm_kit.checks route-overlaps $prefix
   if ($LASTEXITCODE -ne 0 -or $value -notin @('True','False')) { throw 'Cannot validate local route overlap; no switch will be created.' }
   if ($value -eq 'True') { $prefix }
  }
  if ($conflict) { throw 'Dedicated VM subnet overlaps an existing route; select/review another subnet before proceeding.' }
  $switch=New-VMSwitch -Name $switchName -SwitchType Internal
  New-NetIPAddress -InterfaceAlias "vEthernet ($switchName)" -IPAddress $hostAddress -PrefixLength 30 | Out-Null
  @{id=[string]$switch.Id;address=$hostAddress} | ConvertTo-Json | Set-Content -LiteralPath $switchOwner -Encoding UTF8
 }
 if (-not (Test-Path -LiteralPath $switchOwner)) { throw 'Existing switch lacks T-Defense ownership record.' }
 $owner=Get-Content -LiteralPath $switchOwner -Raw | ConvertFrom-Json
 if ([string]$switch.Id -ne $owner.id -or $owner.address -ne $hostAddress) { throw 'Switch ownership mismatch.' }
 if ($switch.SwitchType -ne 'Internal') { throw 'Unexpected virtual switch type.' }
 if (@(Get-VM | Get-VMNetworkAdapter | Where-Object SwitchName -eq $switchName).Count -ne 0) { throw 'Dedicated switch is already used by another VM; inspect leftovers before continuing.' }
 if (-not (Get-NetIPAddress -InterfaceAlias "vEthernet ($switchName)" -AddressFamily IPv4 | Where-Object IPAddress -eq $hostAddress)) { throw 'Unexpected switch address.' }
 New-VHD -Path $child -ParentPath $baseDisk -Differencing | Out-Null
 New-VM -Name $jobVM -Generation 2 -MemoryStartupBytes 8GB -VHDPath $child -Path $jobDir | Out-Null
 $vmCreated=$true
 Set-VM -Name $jobVM -AutomaticStartAction Nothing -AutomaticStopAction TurnOff -CheckpointType Disabled
 Set-VMProcessor -VMName $jobVM -Count 4
 Set-VMKeyProtector -VMName $jobVM -NewLocalKeyProtector
 Enable-VMTPM -VMName $jobVM
 Set-VMFirmware -VMName $jobVM -EnableSecureBoot On
 Set-VMNetworkAdapter -VMName $jobVM -MacAddressSpoofing Off -DhcpGuard On -RouterGuard On
 # Hypervisor rules are applied while the VM is still OFF and disconnected.
 Add-VMNetworkAdapterExtendedAcl -VMName $jobVM -Direction Outbound -Action Deny -RemoteIPAddress '0.0.0.0/0' -Weight 1
 Add-VMNetworkAdapterExtendedAcl -VMName $jobVM -Direction Outbound -Action Deny -RemoteIPAddress '::/0' -Weight 2
 Add-VMNetworkAdapterExtendedAcl -VMName $jobVM -Direction Inbound -Action Deny -RemoteIPAddress '0.0.0.0/0' -Weight 3
 Add-VMNetworkAdapterExtendedAcl -VMName $jobVM -Direction Inbound -Action Deny -RemoteIPAddress '::/0' -Weight 4
 Add-VMNetworkAdapterExtendedAcl -VMName $jobVM -Direction Outbound -Action Allow -RemoteIPAddress $hostAddress -RemotePort '18080' -Protocol TCP -Weight 100 -Stateful $true -IdleSessionTimeout 90
 Assert-Acls $jobVM
 Connect-VMNetworkAdapter -VMName $jobVM -SwitchName $switchName
 Start-VM -Name $jobVM | Out-Null
 $session=Guest-Session $jobVM
 Invoke-Command -Session $session -ArgumentList $guestAddress -ScriptBlock {
  param($GuestAddress)
  $adapters=@(Get-NetAdapter -Physical)
  if ($adapters.Count -ne 1) { throw 'Expected exactly one guest adapter.' }
  $nic=$adapters[0]
  Disable-NetAdapterBinding -InterfaceAlias $nic.Name -ComponentID ms_tcpip6 | Out-Null
  Set-NetIPInterface -InterfaceIndex $nic.ifIndex -AddressFamily IPv4 -Dhcp Disabled
  Get-NetIPAddress -InterfaceIndex $nic.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue | Remove-NetIPAddress -Confirm:$false
  New-NetIPAddress -InterfaceIndex $nic.ifIndex -IPAddress $GuestAddress -PrefixLength 30 | Out-Null
  Set-DnsClientServerAddress -InterfaceIndex $nic.ifIndex -ResetServerAddresses
  if (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue) { throw 'Guest unexpectedly has a default route.' }
  New-Item -ItemType Directory -Path 'C:\TDefense\Run' -Force | Out-Null
 }
 Copy-Item -LiteralPath $PSScriptRoot -Destination 'C:\TDefense\Run\vm_kit' -ToSession $session -Recurse
 # Windows PowerShell/.NET uses a byte buffer for GetBytes.
 $bytes=New-Object byte[] 32;$rng=[Security.Cryptography.RandomNumberGenerator]::Create();$rng.GetBytes($bytes);$rng.Dispose();$token=[Convert]::ToBase64String($bytes)
 $denied=@(Get-NetIPAddress -AddressFamily IPv4 | ForEach-Object { $_.IPAddress+'/32' }) + @(Get-NetRoute -AddressFamily IPv4 | Where-Object DestinationPrefix -ne '0.0.0.0/0' | ForEach-Object DestinationPrefix)
 if (-not $PublicEgressAddress) {
  # Detect the primary NAT/VPN public endpoint, so DNS cannot hairpin into the host/router.
  $PublicEgressAddress=@((Invoke-RestMethod -Uri 'https://api.ipify.org?format=json' -TimeoutSec 10).ip)
 }
 foreach ($address in $PublicEgressAddress) {
  $checked=$address | & $python -m vm_kit.checks public-ip
  if ($LASTEXITCODE -ne 0) { throw 'Cannot determine a valid public egress IPv4; no browsing allowed.' }
  $denied+=([string]$checked+'/32')
 }
 $resultPath=Join-Path $jobDir 'result.json'
 $startPath=Join-Path $jobDir 'start.signal'
 $configPath=Join-Path $jobDir 'proxy-session.json'
 @{bind=$hostAddress;token=$token;denied=$denied;result_path=$resultPath;start_path=$startPath} | ConvertTo-Json -Compress | Set-Content -LiteralPath $configPath -Encoding Ascii
 $proxy=Start-Process -FilePath $python -ArgumentList '-m vm_kit.broker' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardInput $configPath -RedirectStandardOutput (Join-Path $jobDir 'proxy.stdout') -RedirectStandardError (Join-Path $jobDir 'proxy.stderr') -PassThru
 New-NetFirewallRule -Name $firewall -DisplayName $firewall -Direction Inbound -Action Allow -InterfaceAlias "vEthernet ($switchName)" -RemoteAddress $guestAddress -LocalAddress $hostAddress -Protocol TCP -LocalPort 18080,18081 -Profile Any | Out-Null
 $canary=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Parse($hostAddress),18081);$canary.Start()
 $boundary=Invoke-Command -Session $session -ArgumentList $hostAddress,$token,($PublicEgressAddress -join ',') -ScriptBlock {
  param($ProxyHost,$Token,$Egress)
  function Connects([string]$Address,[int]$Port) {
   $client=[Net.Sockets.TcpClient]::new()
   try { $task=$client.ConnectAsync($Address,$Port);return ($task.Wait(1500) -and $client.Connected) } catch { return $false } finally { $client.Dispose() }
  }
  $ready=$false
  for ($i=0;$i -lt 10 -and -not $ready;$i++) { $ready=Connects $ProxyHost 18080;if (-not $ready) { Start-Sleep -Milliseconds 250 } }
  if (-not $ready) { throw 'Broker is not reachable; no website will be visited.' }
  # 18081 is deliberately listening on the host: a successful connection is a boundary failure.
  foreach ($test in @(@($ProxyHost,18081),@($ProxyHost,8000),@('192.168.1.1',443),@('169.254.169.254',80),@('1.1.1.1',443))) {
   if (Connects $test[0] $test[1]) { throw 'Direct network isolation failed; inspection blocked.' }
  }
  function Proxy-Code([string]$Destination) {
   $client=[Net.Sockets.TcpClient]::new()
   try {
    $client.Connect($ProxyHost,18080);$stream=$client.GetStream();$stream.ReadTimeout=6000;$stream.WriteTimeout=3000
    $auth=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('tdefense:'+$Token))
    $request="CONNECT ${Destination}:443 HTTP/1.1`r`nProxy-Authorization: Basic $auth`r`n`r`n"
    $bytes=[Text.Encoding]::ASCII.GetBytes($request);$stream.Write($bytes,0,$bytes.Length)
    $line=''
    for ($n=0;$n -lt 256;$n++) { $ch=$stream.ReadByte();if ($ch -lt 0 -or $ch -eq 10) { break };$line+=[char]$ch }
    return $line
   } finally { $client.Dispose() }
  }
  # Pre-start forwarding MUST be denied even for a public website.
  if ((Proxy-Code 'example.com') -notlike 'HTTP/1.1 403*') { throw 'Broker released egress before Direct session closed.' }
  foreach ($address in @('127.0.0.1','169.254.169.254','192.168.1.1','224.0.0.1','[::1]')+($Egress -split ',')) {
   if ((Proxy-Code $address) -notlike 'HTTP/1.1 403*') { throw 'Proxy private/special/egress-address rejection failed.' }
  }
  return $true
 }
 if (-not $boundary -or $proxy.HasExited) { throw 'Network boundary is not ready.' }
 $config=@{target_origin=[string]$origin;proxy="http://${hostAddress}:18080";token=$token;use_local_ai=[bool]$UseLocalAI;public_egress=$PublicEgressAddress} | ConvertTo-Json -Compress
 # Launch the trusted worker while the clean guest has not visited any site.
 Invoke-Command -Session $session -ArgumentList $config,([bool]$UseLocalAI) -ScriptBlock {
  param($Config,$AI)
  $env:TDEFENSE_DISPOSABLE_GUEST='1';$env:PLAYWRIGHT_BROWSERS_PATH='C:\TDefense\Browsers'
  if ($AI) {
   $env:OLLAMA_HOST='127.0.0.1:11434';$env:OLLAMA_MODELS='C:\TDefense\Models'
   $ollama=Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
   Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden | Out-Null
   Start-Sleep -Seconds 2
  }
  $Config | Set-Content -LiteralPath 'C:\TDefense\job.json' -Encoding Ascii
  Start-Process -FilePath 'C:\TDefense\venv\Scripts\python.exe' -ArgumentList '-m vm_kit.worker' -WorkingDirectory 'C:\TDefense\Run' -WindowStyle Hidden -RedirectStandardInput 'C:\TDefense\job.json' -RedirectStandardOutput 'C:\TDefense\worker.stdout' -RedirectStandardError 'C:\TDefense\worker.stderr' | Out-Null
 }
 Remove-PSSession $session;$session=$null
 # No PowerShell remoting/deserialization channel remains during untrusted browsing.
 New-Item -ItemType File -Path $startPath | Out-Null
 $end=(Get-Date).AddSeconds(90)
 while (-not (Test-Path -LiteralPath $resultPath)) {
  if ($proxy.HasExited -or (Get-Date) -ge $end) { throw 'No bounded report received before the host deadline.' }
  Start-Sleep -Milliseconds 250
 }
 if ((Get-Item -LiteralPath $resultPath).Length -gt 65536) { throw 'Result exceeds host transport limit.' }
 $raw=Get-Content -LiteralPath $resultPath -Raw
 $validated=$raw | & $python -m vm_kit.report
 if ($LASTEXITCODE -ne 0) { throw 'Guest result failed strict validation.' }
 # Do not emit a report until disposal has completed successfully.
} finally {
 if ($session) { Remove-PSSession $session -ErrorAction SilentlyContinue }
 if ($vmCreated -or (Get-VM -Name $jobVM -ErrorAction SilentlyContinue)) {
  try { Disconnect-VMNetworkAdapter -VMName $jobVM -ErrorAction Stop } catch { $cleanupFailed=$true }
  # Always attempt power-off even when disconnection fails.
  try { Stop-VM -Name $jobVM -TurnOff -Force -ErrorAction Stop } catch { $cleanupFailed=$true }
  try {
   $remainingVM=Get-VM -Name $jobVM -ErrorAction SilentlyContinue
   if ($remainingVM -and $remainingVM.State -ne 'Off') { throw 'Disposable guest remains running.' }
   if ($remainingVM) { Remove-VM -Name $jobVM -Force -ErrorAction Stop }
   if (Get-VM -Name $jobVM -ErrorAction SilentlyContinue) { throw 'Disposable guest remains registered.' }
  } catch { $cleanupFailed=$true }
 }
 if ($proxy) {
  try {
   if (-not $proxy.HasExited) { Stop-Process -Id $proxy.Id -Force -ErrorAction Stop;$proxy.WaitForExit(5000) | Out-Null }
   if (-not $proxy.HasExited) { throw 'Egress broker remains running.' }
  } catch { $cleanupFailed=$true }
 }
 if ($canary) { $canary.Stop() }
 Remove-NetFirewallRule -Name $firewall -ErrorAction SilentlyContinue
 if (Test-Path -LiteralPath $child) {
  Assert-ChildPath $child $jobDir
  if (-not $cleanupFailed) { Remove-Item -LiteralPath $child -Force }
 }
 foreach ($name in @('proxy-session.json','proxy.stdout','proxy.stderr','result.json','result.part','start.signal')) {
  $item=Join-Path $jobDir $name
  if (Test-Path -LiteralPath $item) { Assert-ChildPath $item $jobDir;Remove-Item -LiteralPath $item -Force }
 }
 $mutex.ReleaseMutex();$mutex.Dispose()
 if ($cleanupFailed) { Write-Warning 'Disposable cleanup was not fully verified; no successful report will be emitted. Inspect Hyper-V before reuse.' }
}
if ($cleanupFailed) { throw 'Disposable cleanup failed. Network was disconnected where possible; inspect Hyper-V before another job.' }
Write-Output $validated
