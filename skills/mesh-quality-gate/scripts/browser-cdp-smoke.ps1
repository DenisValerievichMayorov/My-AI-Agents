# Browser CDP smoke — mesh-quality-gate
# Exit 0 = CDP :9222 looks like Chrome DevTools; Exit 1 = fail
param(
    [string]$CdpBase = "http://localhost:9222",
    [int]$TimeoutSec = 5
)

$ErrorActionPreference = "Stop"
$versionUrl = "$CdpBase/json/version"
$listUrl = "$CdpBase/json/list"

function Get-CdpJson {
    param([string]$Uri)
    Invoke-RestMethod -Uri $Uri -TimeoutSec $TimeoutSec
}

try {
    $resp = $null
    $used = $versionUrl
    try {
        $resp = Get-CdpJson -Uri $versionUrl
    } catch {
        # Some setups answer only /json/list
        $resp = Get-CdpJson -Uri $listUrl
        $used = $listUrl
    }

    $browser = $null
    if ($resp -is [System.Array]) {
        $n = $resp.Count
        Write-Output "VERIFY: browser-smoke GET $used → OK (tabs=$n)"
        if ($n -gt 0 -and $resp[0].title) {
            Write-Output "First tab title: $($resp[0].title)"
        }
        exit 0
    }

    if ($resp.Browser) { $browser = $resp.Browser }
    elseif ($resp.browser) { $browser = $resp.browser }

    if (-not $browser -and -not $resp.webSocketDebuggerUrl) {
        Write-Output "VERIFY: FAIL CDP smoke $used — response is not CDP (no Browser/webSocketDebuggerUrl)"
        Write-Output "Body: $(($resp | ConvertTo-Json -Compress -Depth 3))"
        exit 1
    }

    if (-not $browser) { $browser = "(CDP ok, Browser field empty)" }

    Write-Output "VERIFY: browser-smoke GET $used → OK"
    Write-Output "Browser: $browser"
    if ($resp.webSocketDebuggerUrl) {
        Write-Output "webSocketDebuggerUrl: $($resp.webSocketDebuggerUrl)"
    }
    if ($resp."Protocol-Version") {
        Write-Output "Protocol-Version: $($resp.'Protocol-Version')"
    }
    exit 0
}
catch {
    Write-Output "VERIFY: FAIL CDP smoke $versionUrl — $($_.Exception.Message)"
    Write-Output "Hint: start Chrome with remote debugging on 9222 (Denis profile). Do not chromium.launch() empty profile."
    exit 1
}
