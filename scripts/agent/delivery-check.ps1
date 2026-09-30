$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $ScriptDir "agent_tool.py") delivery-check @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
