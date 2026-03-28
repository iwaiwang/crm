$ErrorActionPreference = "SilentlyContinue"

function Write-Section($title) {
  Write-Host ""
  Write-Host ("================== " + $title + " ==================") -ForegroundColor Cyan
}

function Get-ProcessInfoById([int]$Pid) {
  Get-CimInstance Win32_Process |
    Where-Object { $_.ProcessId -eq $Pid } |
    Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine
}

function Show-PortSnapshot {
  $listeners = Get-NetTCPConnection -LocalPort 8002 -State Listen
  if (-not $listeners) {
    Write-Host "No process is listening on port 8002." -ForegroundColor Yellow
    return @()
  }

  $listeners |
    Select-Object LocalAddress, LocalPort, State, OwningProcess |
    Format-Table -AutoSize

  foreach ($listener in $listeners) {
    $pid = [int]$listener.OwningProcess
    Write-Host ""
    Write-Host ("[Listener] PID=" + $pid) -ForegroundColor Green

    $proc = Get-ProcessInfoById $pid
    if ($proc) {
      $proc | Format-List

      if ($proc.ParentProcessId) {
        Write-Host "[Parent]" -ForegroundColor DarkCyan
        $parent = Get-ProcessInfoById ([int]$proc.ParentProcessId)
        if ($parent) {
          $parent | Format-List
        } else {
          Write-Host "Parent process already exited or cannot be read." -ForegroundColor Yellow
        }
      }
    } else {
      Write-Host "This PID already exited. The TCP snapshot is stale." -ForegroundColor Yellow
    }
  }

  return $listeners
}

Write-Section "Current listener on 8002"
$initialListeners = Show-PortSnapshot

Write-Section "Watch for 10 seconds"
$history = @()
1..10 | ForEach-Object {
  $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
  $listeners = Get-NetTCPConnection -LocalPort 8002 -State Listen

  if (-not $listeners) {
    $history += [PSCustomObject]@{
      Time = $now
      PID = "-"
      LocalAddress = "-"
      Note = "NO_LISTENER"
    }
  } else {
    foreach ($listener in $listeners) {
      $pid = [int]$listener.OwningProcess
      $proc = Get-ProcessInfoById $pid
      $history += [PSCustomObject]@{
        Time = $now
        PID = $pid
        LocalAddress = $listener.LocalAddress
        Note = "LISTEN"
        Name = if ($proc) { $proc.Name } else { "<exited>" }
        ParentPID = if ($proc) { $proc.ParentProcessId } else { "" }
        CommandLine = if ($proc) { $proc.CommandLine } else { "" }
      }
    }
  }

  Start-Sleep -Seconds 1
}

$history | Select-Object Time, PID, LocalAddress, Note, Name, ParentPID | Format-Table -AutoSize

Write-Host ""
Write-Host "Command lines captured during sampling:" -ForegroundColor Cyan
$history |
  Where-Object { $_.PID -ne "-" } |
  Select-Object Time, PID, Name, ParentPID, CommandLine |
  Format-List

$pidChanges = $history |
  Where-Object { $_.PID -ne "-" } |
  Select-Object -ExpandProperty PID -Unique

Write-Section "Conclusion"
if (-not $pidChanges -or $pidChanges.Count -eq 0) {
  Write-Host "No listener was found on port 8002 during the 10 second watch." -ForegroundColor Yellow
} elseif ($pidChanges.Count -eq 1) {
  Write-Host ("PID stayed stable for 10 seconds: " + $pidChanges[0]) -ForegroundColor Green
} else {
  Write-Host ("PID changed during the 10 second watch: " + ($pidChanges -join ", ")) -ForegroundColor Red
  Write-Host "This usually means a process is restarting, a parent/child handoff is happening, or a new process took over the port." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "To kill a process manually, run:" -ForegroundColor Cyan
Write-Host "taskkill /F /PID <PID> /T"
