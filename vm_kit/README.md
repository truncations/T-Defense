# Disposable T-Defense VM runner — setup pending

This is a separate infrastructure kit. It does not replace the existing extension or localhost-only investigator, and it does not yet add a button/API to the application.

**Current machine status:** Professional edition; this Codex session is not an administrator; Hyper-V commands are unavailable; no Windows ISO or clean VHDX is available. The kit has software tests, not a demonstrated Hyper-V deployment. No real website was visited by this runner. Do not describe the network boundary as established until the deployment steps and per-job checks succeed.

## What it does

- Installs dependencies only once into a clean, offline Windows base.
- Uses a fresh Hyper-V differencing disk for each inspection. The base is SHA-256 checked and must remain off/unmodified.
- Runs one job at a time, with an 8 GB RAM / 4-vCPU guest, 90-second inspection deadline, and forced disposal afterward.
- Creates only a dedicated Internal virtual switch, `TDefense-Isolated` (192.168.253.0/30). No NAT, external switch or default guest route is created. Conflicting host routes cause setup to stop.
- Hyper-V adapter ACLs are applied/read back while the VM is off: deny IPv4/IPv6 traffic in both directions, except a stateful outbound TCP connection to the broker at 192.168.253.1:18080. The allow rule has higher priority. The guest cannot change these host/hypervisor rules.
- A short-lived authenticated host broker resolves/validates all IPv4 DNS answers and connects to the validated numeric address. It rejects nonpublic, multicast, special/reserved, local-route, host-interface and discovered/supplied public-egress addresses. IPv6-only sites and nonstandard ports are unsupported.
- Before browsing, the guest must reach the proxy and must fail to reach a deliberately listening host canary port, host backend port, LAN/router/metadata addresses and a direct public IP. It also tests public CONNECT and rejects private/special/egress destinations through the broker. Any failure stops inspection.
- PowerShell Direct copies trusted worker files and config before browsing; the session is then closed. Only afterward does the host release the worker to navigate. Results never use PowerShell remoting during untrusted browsing.
- An authenticated broker result endpoint enforces a 64 KiB body limit before JSON parsing, fixed schema, one result, and an atomic host-owned result file. No guest shared host folder is mounted. Host report rendering uses fixed templates.
- Cleanup separately attempts disconnection, force-off and removal even if an earlier operation fails. The child disk is deleted only from its checked job directory and only after successful VM teardown. Cleanup failure prevents reporting success.

**Limits:** the broker is a restricted host TCP transport, not a second firewall VM or TLS inspection service. HTTPS CONNECT is opaque; GET/HEAD/no-form/no-download restrictions are imposed by the trusted guest browser worker. A browser compromise could use permitted public-443 tunnels. Host networking, Hyper-V and the broker remain part of the trusted computing base. No sandbox is an absolute security guarantee. Host-side policy tests do not prove Windows switch enforcement.

Private/connected IPv4 routes, host addresses and the primary discovered public NAT/VPN address are blocked. Multi-WAN/additional public hairpin endpoints must all be supplied with `-PublicEgressAddress`; do not claim universal network isolation without reviewing that topology. Public-IPv4 DNS is resolved on the host, not in the guest. Normal DNS resolution can expose destination hostnames to the host's resolver.

## One-time setup

Use **Windows PowerShell 5.1 as Administrator**, not PowerShell 7. No script elevates itself or reboots automatically. Run from the repository root:

```powershell
cd 'C:\Users\Aaron\Documents\programming\T-Defense'
.\vm_kit\TDefense-VM.ps1 -Action Preflight
.\vm_kit\TDefense-VM.ps1 -Action EnableHyperV
```

Save your work and reboot manually if Windows requests it. The feature installation changes Windows optional features. It does not download or create the guest OS.

Obtain Windows x64 installation media from Microsoft. For an offline local-account development guest, consider **Windows Server 2025 Standard Evaluation (Desktop Experience)**, available as an evaluation ISO from [Microsoft Evaluation Center](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2025). Review Microsoft's current evaluation terms. Choose Desktop Experience, not Server Core. Windows 11 Pro/Enterprise also needs a valid installation/setup path; this kit does not bypass activation or account requirements. Do not use a disk containing personal accounts/data.

Create the base, substituting the actual downloaded filename:

```powershell
.\vm_kit\TDefense-VM.ps1 -Action CreateBase -IsoPath 'C:\Users\Aaron\Downloads\YOUR-WINDOWS-x64.iso'
```

Open Hyper-V Manager -> TDefense-Clean-Base -> Connect. Boot the installation DVD and install Windows on the empty VM disk. This does not install Windows over your host computer. Keep the VM network disconnected. Use a disposable local administrator account created for this VM; remember its credentials. Do not sign in to your real services or place user files inside it.

The existing OfflineKit is reused from `C:\Users\Aaron\Documents\TDefense-Sandbox\OfflineKit`. It must have the matching Python3.14 installer, pinned wheels/requirements, Chromium directory, and optionally Ollama installer/model files. There are no new package downloads in PrepareBase.

```powershell
.\vm_kit\TDefense-VM.ps1 -Action PrepareBase -UseLocalAI
```

Enter the local administrator credentials **inside the VM**, not your normal host credentials. This copies the offline kit through PowerShell Direct and installs it once. First preparation can take a while. Keep the same local VM account for future runs because Python/Ollama are installed for that account. Omit `-UseLocalAI` for a browser-only base; its reports explicitly say AI was not requested.

Then seal the base:

```powershell
.\vm_kit\TDefense-VM.ps1 -Action SealBase
```

Sealing requires an offline, fully decrypted boot disk (or a Server guest without BitLocker installed), a working offline Chromium check, and successful shutdown. It records the base hash in ignored `work/disposable-vm`. No automatic approval occurs after installers alone. Do not start or edit the sealed base while child disks exist. If the base is patched/rebuilt later, its approval must be renewed deliberately; this first cut refuses to overwrite an existing seal.

## Run an inspection after setup

Start with the benign public example:

```powershell
.\vm_kit\TDefense-VM.ps1 -Action Inspect -TargetOrigin 'https://example.com'
```

To request the optional model after browser/Windows verification:

```powershell
.\vm_kit\TDefense-VM.ps1 -Action Inspect -TargetOrigin 'https://example.com' -UseLocalAI
```

Public-egress discovery normally makes one fixed request to `https://api.ipify.org?format=json`. That service sees the host's public IP; no target URL or page data is sent. To avoid this lookup, or for multiple public egress addresses, supply them explicitly:

```powershell
.\vm_kit\TDefense-VM.ps1 -Action Inspect -TargetOrigin 'https://example.com' -PublicEgressAddress 'YOUR-PUBLIC-IPv4'
```

The script validates the address and denies it as a target. Discovery failure blocks inspection. Do not supply a guessed or incomplete address set. No inspection code calls VirusTotal or a cloud AI service.

The result is JSON with observations and a fixed-template summary. It never says the website is safe. Failures/unsupported checks are inconclusive. The command runs the fixed browser checks; it does not log into accounts, type canaries, click buttons or submit forms. Page scripts may still have side effects from ordinary GET navigation.

**Origin-only scope:** input must be `https://site.example` in shape, but use a real public host for live execution. Paths, queries, fragments, userinfo and nonstandard ports are rejected. A homepage check cannot establish what a particular /claim or personalized link does. Exact-link support requires a separate privacy/protocol change; nothing silently strips a requested path and pretends to inspect it.

## AI behavior

Ollama runs only inside the disposable guest, bound to its loopback interface, using the existing llama3.2:3b model with CPU-only options. It receives only fixed boolean observations and permitted template IDs, never page instructions, raw HTML or user message histories. Its JSON selection is validated against observed evidence. The host renders all evidence-backed templates even if the model omits one. Output never contains an AI-generated safety verdict.

If model startup, schema validation or the model request fails, the report is inconclusive with AI unavailable. Cold CPU inference may exceed the current bounded timeout; timing has NOT been verified on this machine. This is constrained evidence explanation, not an autonomous general-purpose browsing agent, malware scan, account-action simulator or comprehensive phishing classifier.

## Tests and verification status

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_vm_kit.py
.\.venv\Scripts\python.exe -m ruff check .
```

Tests use synthetic payloads, fake DNS and loopback sockets. They do not create VMs, alter firewall policy, install Windows features or visit hostile websites. PowerShell scripts are parsed and Preflight is executed without administrative changes. Full-project checks are recorded in PROGRESS.md.

Deployment acceptance still required: Hyper-V installation, Windows setup, base readiness, exact ACL representation/readback on this host, negative canary/direct/proxy destination probes, benign example.com browser run, fresh child disk on a second run, broker/VM removal after success and timeout, and local Ollama behavior. A later integration should call this through a narrow privileged broker/task with fixed executable paths and validated targets; never give the ordinary extension/backend arbitrary administrator command execution.

The handout's v0.6.0 app/sandbox_jobs.py/app/local_ai.py/sandbox-kit worker are absent from the current checkout/update ZIP. No extension button is wired to this kit yet; reconcile the actual source before integrating. Conversation analysis remains canceled/unimplemented.

## Implementation references

- [Hyper-V installation](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/get-started/install-hyper-v)
- [Differencing virtual disks](https://learn.microsoft.com/en-us/powershell/module/hyper-v/new-vhd)
- [Hyper-V extended ACLs](https://learn.microsoft.com/en-us/powershell/module/hyper-v/add-vmnetworkadapterextendedacl)
- [PowerShell Direct](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/powershell-direct)
- [Ollama structured output](https://ollama.com/blog/structured-outputs)


## SealBase File<string> error on Windows PowerShell5.1

The original inline Python readiness expression lost embedded quotes through native argument passing. The patched script copies vm_kit/readiness.py into the prepared guest and executes that file; it validates native exit status plus a bounded JSON Boolean success. Host origin/public-IP/route policy helpers also use module entry points rather than inline Python. Update the whole vm_kit source folder together.

Keep the prepared base running and rerun SealBase from elevated host Windows PowerShell. No recreation or PrepareBase rerun is required for this quote repair. A subsequent Server Core error requires Desktop Experience installation; a browser error now includes the bounded underlying diagnostic. Chromium sandbox requirements remain enabled, and failed checks never seal the base. Actual VM readiness/network enforcement still require user-host verification.
