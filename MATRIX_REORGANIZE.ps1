# NEXUSMON MATRIX Reorganization Protocol
# Transforms chaotic repository into clean matrix structure

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  🧠 NEXUSMON MATRIX REORGANIZATION PROTOCOL 🧠" -ForegroundColor Cyan
Write-Host "  ⚡ Establishing clean neural pathways... ⚡" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan

# Create MATRIX directory structure
$matrix_dirs = @(
    "matrix",
    "matrix/core",           # Core NEXUSMON organism files
    "matrix/protocols",      # Launcher scripts
    "matrix/tools",          # Utility scripts
    "matrix/runtime",        # Runtime engines
    "matrix/interfaces",     # UI/Web interfaces
    "matrix/archives",       # Legacy/backup files
    "matrix/deployment"      # Deployment configs
)

foreach ($dir in $matrix_dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  📁 Created: $dir" -ForegroundColor Green
    }
}

# Reorganization map
$moves = @{
    # NEXUSMON Core Organism → matrix/core/
    "nexusmon_organism.py" = "matrix/core/nexusmon_organism.py"
    "nexusmon_cognition.py" = "matrix/core/nexusmon_cognition.py"
    "nexusmon_mission_engine.py" = "matrix/core/nexusmon_mission_engine.py"
    "nexusmon_operator_rank.py" = "matrix/core/nexusmon_operator_rank.py"
    "nexusmon_performance.py" = "matrix/core/nexusmon_performance.py"
    "nexusmon_signal_modules.py" = "matrix/core/nexusmon_signal_modules.py"
    "nexusmon_artifact_vault.py" = "matrix/core/nexusmon_artifact_vault.py"
    "nexusmon_mentality.py" = "matrix/core/nexusmon_mentality.py"
    "nexusmon_plugins.py" = "matrix/core/nexusmon_plugins.py"
    "nexusmon_sensorium.py" = "matrix/core/nexusmon_sensorium.py"
    "nexusmon_forge.py" = "matrix/core/nexusmon_forge.py"
    "nexusmon_linguistics.py" = "matrix/core/nexusmon_linguistics.py"
    "nexusmon_nexus_vault.py" = "matrix/core/nexusmon_nexus_vault.py"
    
    # Launch Protocols → matrix/protocols/
    "RUN.ps1" = "matrix/protocols/NEXUSMON_AWAKEN.ps1"
    "RUN.cmd" = "matrix/protocols/NEXUSMON_AWAKEN.cmd"
    "RUN.sh" = "matrix/protocols/nexusmon_awaken.sh"
    "SWARMZ_UP.ps1" = "matrix/protocols/matrix_online.ps1"
    "SWARMZ_UP.cmd" = "matrix/protocols/matrix_online.cmd"
    "SWARMZ_DAEMON_UP.ps1" = "matrix/protocols/matrix_daemon.ps1"
    "SWARMZ_DAEMON_UP.cmd" = "matrix/protocols/matrix_daemon.cmd"
    "SWARMZ_ONE_BUTTON_START.ps1" = "matrix/protocols/one_jack_in.ps1"
    "SWARMZ_ONE_BUTTON_START.cmd" = "matrix/protocols/one_jack_in.cmd"
    
    # Diagnostic Protocols → matrix/protocols/diagnostics/
    "SWARMZ_DOCTOR.ps1" = "matrix/protocols/diagnostics/matrix_diagnostics.ps1"
    "SWARMZ_DOCTOR.cmd" = "matrix/protocols/diagnostics/matrix_diagnostics.cmd"
    "SWARMZ_SMOKE.ps1" = "matrix/protocols/diagnostics/smoke_test.ps1"
    "SWARMZ_SMOKE.cmd" = "matrix/protocols/diagnostics/smoke_test.cmd"
    "SWARMZ_SMOKE_TEST.ps1" = "matrix/protocols/diagnostics/full_smoke_test.ps1"
    "SWARMZ_SMOKE_TEST.cmd" = "matrix/protocols/diagnostics/full_smoke_test.cmd"
    "HEALTHCHECK.py" = "matrix/protocols/diagnostics/health_check.py"
    "self_check.py" = "matrix/protocols/diagnostics/self_check.py"
    
    # Deployment → matrix/deployment/
    "SWARMZ_ONE_BUTTON_DEPLOY.ps1" = "matrix/deployment/one_button_deploy.ps1"
    "SWARMZ_PROFILE.ps1" = "matrix/deployment/profile_config.ps1"
    "SWARMZ_PROFILE.cmd" = "matrix/deployment/profile_config.cmd"
    "SWARMZ_V5_LIVE_SETUP.ps1" = "matrix/deployment/live_setup_v5.ps1"
    "docker-compose.yml" = "matrix/deployment/docker-compose.yml"
    "Dockerfile" = "matrix/deployment/Dockerfile"
    "railway.json" = "matrix/deployment/railway.json"
    "railway.toml" = "matrix/deployment/railway.toml"
    "Procfile" = "matrix/deployment/Procfile"
    "render.yaml" = "matrix/deployment/render.yaml"
    
    # Tools → matrix/tools/
    "FIX_SWARMZ_LAUNCHERS.py" = "matrix/tools/fix_launchers.py"
    "CREATE_SWARMZ_APP_ICON.ps1" = "matrix/tools/create_app_icon.ps1"
    "PACK_EXE.ps1" = "matrix/tools/pack_executable.ps1"
    "APP_STORE_BUILD.cmd" = "matrix/tools/app_store_build.cmd"
    "ONE_BUTTON_SWARMZ_OWNERSHIP_PACK.py" = "matrix/tools/ownership_pack.py"
    "TOOLS_REPO_MAP.py" = "matrix/tools/repo_map.py"
    
    # Archives (legacy files) → matrix/archives/
    "SWARMZ_WSL_HOST_RECOVERY.ps1" = "matrix/archives/wsl_recovery.ps1"
    "SWARMZ_V5_WSL_LIBVIRT_BOOTSTRAP.ps1" = "matrix/archives/wsl_libvirt_bootstrap.ps1"
    "SWARMZ_HOLOGRAM_SERVICE.ps1" = "matrix/archives/hologram_service.ps1"
    "SWARMZ_MANUAL.ps1" = "matrix/archives/manual_mode.ps1"
    "SWARMZ_MANUAL.cmd" = "matrix/archives/manual_mode.cmd"
    "PHONE_MODE.ps1" = "matrix/archives/phone_mode.ps1"
    "PHONE_MODE.cmd" = "matrix/archives/phone_mode.cmd"
}

# Create subdirectories
New-Item -ItemType Directory -Path "matrix/protocols/diagnostics" -Force | Out-Null

# Execute moves
$moved = 0
foreach ($source in $moves.Keys) {
    if (Test-Path $source) {
        $dest = $moves[$source]
        $destDir = Split-Path $dest
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Move-Item -Path $source -Destination $dest -Force
        Write-Host "  ⚡ $source => $dest" -ForegroundColor Yellow
        $moved++
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✅ MATRIX REORGANIZATION COMPLETE ✅" -ForegroundColor Green
Write-Host "  📦 Files relocated: $moved" -ForegroundColor Green
Write-Host "  🧠 Neural pathways: OPTIMIZED" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Next: git add matrix/ ; git commit -m `"refactor: NEXUSMON MATRIX structure`"" -ForegroundColor Magenta

