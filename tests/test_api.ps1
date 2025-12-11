# API Performance Test Script
Write-Host "`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   🚀 AI SECURITY COMPLIANCE SYSTEM - API TEST     ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$baseUrl = "http://127.0.0.1:8000"
$results = @{}

# Wait for server
Write-Host "⏳ Waiting for server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test 1: Health Check
Write-Host "`n1️⃣  HEALTH CHECK ENDPOINT" -ForegroundColor Cyan
Write-Host "   URL: $baseUrl/health/" -ForegroundColor Gray
$times = @()
for ($i = 1; $i -le 5; $i++) {
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $response = Invoke-RestMethod -Uri "$baseUrl/health/" -TimeoutSec 5
        $sw.Stop()
        $times += $sw.ElapsedMilliseconds
        Write-Host "   Request $i`: $($sw.ElapsedMilliseconds) ms - Status: $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "   Request $i`: Failed - $($_.Exception.Message)" -ForegroundColor Red
    }
}
if ($times.Count -gt 0) {
    $avg = [int]($times | Measure-Object -Average).Average
    Write-Host "   ⏱️  Average Response Time: $avg ms`n" -ForegroundColor Yellow
    $results['health'] = $avg
}

# Test 2: Liveness Probe
Write-Host "2️⃣  LIVENESS PROBE" -ForegroundColor Cyan
Write-Host "   URL: $baseUrl/health/live" -ForegroundColor Gray
try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$baseUrl/health/live" -TimeoutSec 5
    $sw.Stop()
    Write-Host "   ✅ Status: $($response.status)" -ForegroundColor Green
    Write-Host "   ⏱️  Response Time: $($sw.ElapsedMilliseconds) ms`n" -ForegroundColor Yellow
    $results['liveness'] = $sw.ElapsedMilliseconds
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 3: Readiness Probe
Write-Host "3️⃣  READINESS PROBE" -ForegroundColor Cyan
Write-Host "   URL: $baseUrl/health/ready" -ForegroundColor Gray
try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$baseUrl/health/ready" -TimeoutSec 5
    $sw.Stop()
    Write-Host "   ✅ Status: $($response.status)" -ForegroundColor Green
    Write-Host "   📊 Checks:" -ForegroundColor Cyan
    $response.checks.PSObject.Properties | ForEach-Object {
        Write-Host "      - $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
    Write-Host "   ⏱️  Response Time: $($sw.ElapsedMilliseconds) ms`n" -ForegroundColor Yellow
    $results['readiness'] = $sw.ElapsedMilliseconds
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 4: System Metrics
Write-Host "4️⃣  SYSTEM METRICS" -ForegroundColor Cyan
Write-Host "   URL: $baseUrl/health/metrics" -ForegroundColor Gray
try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$baseUrl/health/metrics" -TimeoutSec 5
    $sw.Stop()
    Write-Host "   📊 System Metrics:" -ForegroundColor Green
    Write-Host "      CPU: $($response.cpu_percent)%" -ForegroundColor Gray
    Write-Host "      Memory: $($response.memory_percent)%" -ForegroundColor Gray
    Write-Host "      Disk: $($response.disk_usage)%" -ForegroundColor Gray
    Write-Host "   ⏱️  Response Time: $($sw.ElapsedMilliseconds) ms`n" -ForegroundColor Yellow
    $results['metrics'] = $sw.ElapsedMilliseconds
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 5: API Documentation
Write-Host "5️⃣  API DOCUMENTATION" -ForegroundColor Cyan
Write-Host "   URL: $baseUrl/api/docs" -ForegroundColor Gray
try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-WebRequest -Uri "$baseUrl/api/docs" -TimeoutSec 5
    $sw.Stop()
    Write-Host "   ✅ Status Code: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   ⏱️  Response Time: $($sw.ElapsedMilliseconds) ms`n" -ForegroundColor Yellow
    $results['docs'] = $sw.ElapsedMilliseconds
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Test 6: Prompt Analysis (POST)
Write-Host "6️⃣  PROMPT ANALYSIS (Security Test)" -ForegroundColor Cyan
Write-Host "   URL: $baseUrl/api/analyze" -ForegroundColor Gray
$testPrompt = @{
    prompt = "Test prompt with potential SSN: 123-45-6789 and email: test@example.com"
} | ConvertTo-Json

try {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$baseUrl/api/analyze" -Method Post -Body $testPrompt -ContentType "application/json" -TimeoutSec 10
    $sw.Stop()
    Write-Host "   ✅ Analysis Complete" -ForegroundColor Green
    Write-Host "   📊 Results:" -ForegroundColor Cyan
    Write-Host "      - PII Detected: $($response.pii_detected -join ', ')" -ForegroundColor Gray
    Write-Host "      - Injection: $($response.prompt_injection.is_injection)" -ForegroundColor Gray
    Write-Host "      - Toxicity: $($response.toxicity.is_toxic)" -ForegroundColor Gray
    Write-Host "   ⏱️  Response Time: $($sw.ElapsedMilliseconds) ms`n" -ForegroundColor Yellow
    $results['analysis'] = $sw.ElapsedMilliseconds
} catch {
    Write-Host "   ❌ Failed: $($_.Exception.Message)`n" -ForegroundColor Red
}

# Summary
Write-Host "`n╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              📊 PERFORMANCE SUMMARY               ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$results.GetEnumerator() | Sort-Object Value | ForEach-Object {
    $status = if ($_.Value -lt 100) { "🟢 Excellent" } elseif ($_.Value -lt 500) { "🟡 Good" } else { "🟠 Acceptable" }
    Write-Host "   $($_.Key.PadRight(15)): $($_.Value) ms  $status" -ForegroundColor Cyan
}

if ($results.Count -gt 0) {
    $avgAll = [int]($results.Values | Measure-Object -Average).Average
    Write-Host "`n   📈 Overall Average: $avgAll ms" -ForegroundColor Yellow
}

Write-Host "`n✅ All tests completed!" -ForegroundColor Green
Write-Host "   🌐 Open http://127.0.0.1:8000/api/docs for interactive API documentation`n" -ForegroundColor Cyan
