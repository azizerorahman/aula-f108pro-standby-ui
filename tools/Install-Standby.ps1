param(
 [ValidateSet('Verify','Inspect','Install')][string]$Mode='Verify',
 [string]$PayloadDirectory=(Join-Path (Split-Path $PSScriptRoot -Parent) 'dist')
)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path $PSScriptRoot -Parent
Add-Type -Path (Join-Path $repoRoot 'src/transport/StandbyTransport.cs')
$fw=[IO.File]::ReadAllBytes((Join-Path $PayloadDirectory 'standby-mcu.bin'))
$spi=[IO.File]::ReadAllBytes((Join-Path $PayloadDirectory 'standby-graphics.bin'))
$summary=[StandbyTransport]::InspectPayloads($fw,$spi)
$tests=@([StandbyTransport]::SelfTest($fw,$spi))
if($Mode -eq 'Verify') {
 @{mode=$Mode;payload=$summary;tests=$tests;device_opened=$false}|ConvertTo-Json -Depth 5
 exit 0
}
if($env:OS -ne 'Windows_NT'){throw 'Device transport requires Windows'}
if(Get-Process DeviceDriver -ErrorAction SilentlyContinue){throw 'Close the AULA control app before opening the keyboard'}
$rows=@(Get-PnpDevice -PresentOnly | Where-Object {$_.InstanceId -like 'HID\VID_0C45&PID_800A&*' -and $_.Status -eq 'OK'})
$commands=@($rows | Where-Object {[StandbyTransport]::IsInterface($_.InstanceId,0xff13,0x0107)})
$data=@($rows | Where-Object {[StandbyTransport]::IsInterface($_.InstanceId,0xff68,0x0107)})
if($commands.Count -ne 1 -or $data.Count -ne 1){throw 'Expected exactly one CH revision-0107 command/data pair. Other revisions require an independent compatibility review.'}
[StandbyTransport]::Preflight($commands[0].InstanceId,$data[0].InstanceId,0x0107)
if($Mode -eq 'Inspect'){
 @{mode=$Mode;revision='0107';interfaces_match=$true;flash_writes=0}|ConvertTo-Json
 exit 0
}
$runDirectory=Join-Path $repoRoot ('private/install-'+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null
$receipt=Join-Path $runDirectory 'result.json'
[StandbyTransport]::Progress=[Action[StandbyTransport+Evidence]]{param($e)
 Write-Host ($e.phase+' | MCU packets: '+$e.mcu_packets+' | graphics pages: '+$e.graphics_pages)
}
try{
 $null=[StandbyTransport]::ProgramMcu($commands[0].InstanceId,$fw)
 Start-Sleep -Milliseconds 1500
 $null=[StandbyTransport]::ProgramGraphics($commands[0].InstanceId,$data[0].InstanceId,$spi)
 $result=@{status='transfer_complete_physical_check_pending';transfer=[StandbyTransport]::Current}
 [IO.File]::WriteAllText($receipt,($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 Write-Host 'Transfer complete. Check typing, clock, knob, effects and reconnect persistence on the keyboard.'
}catch{
 $result=@{status='failed';error=$_.Exception.Message;transfer=[StandbyTransport]::Current}
 [IO.File]::WriteAllText($receipt,($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
 throw
}
