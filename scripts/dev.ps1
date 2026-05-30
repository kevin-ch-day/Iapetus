param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("setup","test","probe","labels","snapshot")]
    [string]$Action,
    [string[]]$Args = @()
)

$ErrorActionPreference = "Stop"

function Invoke-Setup {
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -U pip
    python -m pip install -e .
}

function Invoke-Test {
    .\.venv\Scripts\Activate.ps1
    python -m pytest
}

function Invoke-Probe {
    .\.venv\Scripts\Activate.ps1
    python -m iapetus.cli probe
}

function Invoke-Labels {
    .\.venv\Scripts\Activate.ps1
    python -m iapetus.cli labels demo
}

function Invoke-Snapshot {
    .\.venv\Scripts\Activate.ps1
    python -m iapetus.cli snapshot demo @Args
}

switch ($Action) {
    "setup" { Invoke-Setup }
    "test" { Invoke-Test }
    "probe" { Invoke-Probe }
    "labels" { Invoke-Labels }
    "snapshot" { Invoke-Snapshot }
    default { throw "Unknown action: $Action" }
}
