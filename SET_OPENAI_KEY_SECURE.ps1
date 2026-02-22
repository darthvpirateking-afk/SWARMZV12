param(
    [switch]$Status,
    [switch]$Clear,
    [switch]$Machine
)

function Get-PlainTextFromSecureString {
    param([Security.SecureString]$Secure)
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

if ($Status) {
    $userSet = -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'User'))
    $procSet = -not [string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)
    $machineSet = $false
    try {
        $machineSet = -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable('OPENAI_API_KEY', 'Machine'))
    }
    catch {}

    Write-Output "OPENAI_API_KEY User=$userSet Process=$procSet Machine=$machineSet"
    exit 0
}

if ($Clear) {
    [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $null, 'User')
    [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $null, 'Process')
    if ($Machine) {
        try {
            [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $null, 'Machine')
        }
        catch {
            Write-Warning 'Could not clear Machine scope. Run PowerShell as Administrator to clear it there.'
        }
    }
    Write-Output 'OPENAI_API_KEY cleared from User and Process scopes.'
    exit 0
}

$secureKey = Read-Host 'Enter OPENAI_API_KEY (input hidden)' -AsSecureString
$plainKey = Get-PlainTextFromSecureString -Secure $secureKey

if ([string]::IsNullOrWhiteSpace($plainKey)) {
    Write-Error 'No key entered. Aborting.'
    exit 1
}

[Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $plainKey, 'User')
$env:OPENAI_API_KEY = $plainKey

if ($Machine) {
    try {
        [Environment]::SetEnvironmentVariable('OPENAI_API_KEY', $plainKey, 'Machine')
    }
    catch {
        Write-Warning 'Could not write Machine scope. Run as Administrator if needed.'
    }
}

$plainKey = $null
$secureKey = $null

Write-Output 'OPENAI_API_KEY saved (User + current Process).'
Write-Output 'Use: ./SET_OPENAI_KEY_SECURE.ps1 -Status to verify without printing secrets.'
