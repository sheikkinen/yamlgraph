# FR-945 REQ-YG-635 read-only LAN host inventory.
# Contract: pure ASCII, no interpolation of caller-controlled text,
# non-admin, read-only, emits ONE JSON document on stdout.
# Built-in Windows groups referenced by SID (S-1-5-32-580 Remote
# Management Users) so Finnish/other-locale installs work.
$ErrorActionPreference = 'Stop'
$startedAt = (Get-Date).ToUniversalTime().ToString("o")

$errors = New-Object System.Collections.ArrayList
function Add-InvError($fld, $msg) {
    $null = $errors.Add(@{ field = $fld; message = $msg })
}

# --- admin check (recon MUST run non-admin; parent recon.py refuses if true) ---
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# --- SID-based Remote Management Users membership ---
$rmuMember = $false
try {
    $rmuSid = 'S-1-5-32-580'
    $me = ([Security.Principal.WindowsIdentity]::GetCurrent()).User
    $rmuMembers = Get-LocalGroupMember -SID $rmuSid -ErrorAction Stop
    foreach ($m in $rmuMembers) {
        if ($m.SID -and ($m.SID.Value -eq $me.Value)) { $rmuMember = $true; break }
    }
} catch {
    Add-InvError 'remote_management_users_member' $_.Exception.Message
}

# --- OS + machine identity ---
$computerName = $env:COMPUTERNAME
$osVersion = [Environment]::OSVersion.VersionString

$manufacturer = ''
$model = ''
$totalMem = 0
$logicalProc = 0
try {
    $cs = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
    $manufacturer = [string]$cs.Manufacturer
    $model = [string]$cs.Model
    $totalMem = [int64]$cs.TotalPhysicalMemory
    $logicalProc = [int]$cs.NumberOfLogicalProcessors
} catch { Add-InvError 'computer_system' $_.Exception.Message }

# --- CPU ---
$cpu = @{ name = ''; cores = 0; logical_processors = 0; max_clock_mhz = 0 }
try {
    $p = Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -First 1
    $cpu.name = [string]$p.Name
    $cpu.cores = [int]$p.NumberOfCores
    $cpu.logical_processors = [int]$p.NumberOfLogicalProcessors
    $cpu.max_clock_mhz = [int]$p.MaxClockSpeed
} catch { Add-InvError 'cpu' $_.Exception.Message }

# --- GPUs ---
$gpus = @()
try {
    $vids = Get-CimInstance Win32_VideoController -ErrorAction Stop
    foreach ($v in $vids) {
        $gpus += @{
            name = [string]$v.Name
            adapter_ram_bytes = if ($v.AdapterRAM) { [int64]$v.AdapterRAM } else { $null }
            driver_version = [string]$v.DriverVersion
        }
    }
} catch { Add-InvError 'gpus' $_.Exception.Message }

# --- Disks ---
$disks = @()
try {
    $drives = Get-PSDrive -PSProvider FileSystem -ErrorAction Stop
    foreach ($d in $drives) {
        $free = 0
        $used = 0
        if ($d.Free) { $free = [int64]$d.Free }
        if ($d.Used) { $used = [int64]$d.Used }
        $disks += @{
            drive = [string]$d.Name
            free_bytes = $free
            used_bytes = $used
        }
    }
} catch { Add-InvError 'disks' $_.Exception.Message }

# --- Python native ---
$pythonNative = $null
try {
    $pyver = & python --version 2>&1
    if ($LASTEXITCODE -eq 0) { $pythonNative = [string]$pyver }
} catch { Add-InvError 'python_native' $_.Exception.Message }

# --- py launcher ---
$pyLauncher = @()
try {
    $lst = & py --list 2>&1
    if ($LASTEXITCODE -eq 0) {
        foreach ($line in $lst) {
            $s = [string]$line
            if ($s.Trim().Length -gt 0) { $pyLauncher += $s }
        }
    }
} catch { Add-InvError 'py_launcher' $_.Exception.Message }

# --- WSL ---
$wsl = $null
try {
    $wslRaw = & wsl --status 2>&1
    if ($LASTEXITCODE -eq 0) {
        $defDistro = $null
        $defVer = $null
        foreach ($ln in $wslRaw) {
            $sl = [string]$ln
            if ($sl -match 'Default Distribution:\s*(\S+)') { $defDistro = $Matches[1] }
            if ($sl -match 'Default Version:\s*(\d+)') { $defVer = [int]$Matches[1] }
        }
        $wsl = @{
            default_distribution = $defDistro
            default_version = $defVer
            raw = ($wslRaw -join "`n")
        }
    }
} catch { Add-InvError 'wsl' $_.Exception.Message }

# --- OpenSSH server capability ---
$sshState = 'Unknown'
try {
    $cap = Get-WindowsCapability -Online -Name 'OpenSSH.Server*' -ErrorAction Stop | Select-Object -First 1
    if ($cap) {
        if ($cap.State -eq 'Installed') { $sshState = 'Installed' }
        elseif ($cap.State -eq 'NotPresent') { $sshState = 'NotPresent' }
        else { $sshState = 'Unknown' }
    }
} catch { Add-InvError 'openssh_server_state' $_.Exception.Message }

$sshdService = $null
try {
    $svc = Get-Service -Name sshd -ErrorAction Stop
    $sshdService = @{
        name = [string]$svc.Name
        status = [string]$svc.Status
        start_type = [string]$svc.StartType
    }
} catch {
    # sshd not installed is a normal state, not an error
}

# --- LM Studio ---
$lmsCliPresent = $false
try {
    $cmd = Get-Command lms -ErrorAction Stop
    if ($cmd) { $lmsCliPresent = $true }
} catch {
    # missing lms.exe is a normal state
}

$lmsService = $null
try {
    $svc = Get-Service -Name '*LM*Studio*' -ErrorAction Stop | Select-Object -First 1
    if ($svc) {
        $lmsService = @{
            name = [string]$svc.Name
            status = [string]$svc.Status
            start_type = [string]$svc.StartType
        }
    }
} catch {
    # normal absence
}

# --- Listening ports (dedup by port+process) ---
$ports = @()
$seen = New-Object System.Collections.Generic.HashSet[string]
try {
    $conns = Get-NetTCPConnection -State Listen -ErrorAction Stop
    foreach ($c in $conns) {
        $procName = $null
        try {
            $pr = Get-Process -Id $c.OwningProcess -ErrorAction Stop
            $procName = [string]$pr.ProcessName
        } catch {}
        $key = "$($c.LocalPort)|$procName"
        if ($seen.Add($key)) {
            $ports += @{
                local_address = [string]$c.LocalAddress
                local_port = [int]$c.LocalPort
                process_name = $procName
            }
        }
    }
} catch { Add-InvError 'listening_ports' $_.Exception.Message }

$endedAt = (Get-Date).ToUniversalTime().ToString("o")

# --- Assemble ---
$out = [ordered]@{
    computer_name = [string]$computerName
    os_version = [string]$osVersion
    manufacturer = $manufacturer
    model = $model
    total_memory_bytes = $totalMem
    logical_processors = $logicalProc
    cpu = $cpu
    gpus = $gpus
    disks = $disks
    python_native = $pythonNative
    py_launcher = $pyLauncher
    wsl = $wsl
    openssh_server_state = $sshState
    sshd_service = $sshdService
    lm_studio_cli_present = $lmsCliPresent
    lm_studio_service = $lmsService
    listening_ports = $ports
    admin = [bool]$admin
    remote_management_users_member = [bool]$rmuMember
    probe_started_at = $startedAt
    probe_ended_at = $endedAt
    errors = @($errors)
}

# ONE JSON document; -Compress avoids formatting drift across PS versions.
$out | ConvertTo-Json -Depth 8 -Compress
