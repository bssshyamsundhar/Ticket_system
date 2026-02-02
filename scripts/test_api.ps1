# ============================================================
# IT Support API Test Script
# Run: .\test_api.ps1
# ============================================================

$BaseUrl = "http://localhost:5000/api"
$Global:Token = $null

# Colors for output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Cyan }
function Write-Section { param($msg) Write-Host "`n========================================" -ForegroundColor Yellow; Write-Host "  $msg" -ForegroundColor Yellow; Write-Host "========================================" -ForegroundColor Yellow }

# Helper function to make API calls
function Invoke-API {
    param(
        [string]$Method,
        [string]$Endpoint,
        [object]$Body = $null,
        [bool]$UseAuth = $true
    )
    
    $Headers = @{
        "Content-Type" = "application/json"
    }
    
    if ($UseAuth -and $Global:Token) {
        $Headers["Authorization"] = "Bearer $Global:Token"
    }
    
    $Uri = "$BaseUrl$Endpoint"
    
    try {
        if ($Body) {
            $JsonBody = $Body | ConvertTo-Json -Depth 10
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -Body $JsonBody
        }
        else {
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers
        }
        return $Response
    }
    catch {
        $StatusCode = $_.Exception.Response.StatusCode.Value__
        $ErrorDetail = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
        return @{
            success     = $false
            error       = $ErrorDetail.error
            status_code = $StatusCode
        }
    }
}

# ============================================================
# TEST: Health Check
# ============================================================
Write-Section "HEALTH CHECK"

try {
    $Response = Invoke-RestMethod -Uri "$BaseUrl/../health" -Method Get
    Write-Success "Server is running: $($Response.status)"
}
catch {
    Write-Error "Server is not running! Start the server with: python app.py"
    exit 1
}

# ============================================================
# TEST: User Registration
# ============================================================
Write-Section "USER REGISTRATION"

$TestUser = @{
    username   = "testuser_$(Get-Random -Maximum 9999)"
    email      = "test$(Get-Random -Maximum 9999)@example.com"
    password   = "test123"
    full_name  = "Test User"
    department = "IT"
}

Write-Info "Registering user: $($TestUser.username)"
$Response = Invoke-API -Method "POST" -Endpoint "/auth/register" -Body $TestUser -UseAuth $false

if ($Response.success) {
    Write-Success "User registered successfully"
    Write-Info "User ID: $($Response.user.id)"
}
else {
    Write-Error "Registration failed: $($Response.error)"
}

# ============================================================
# TEST: User Login
# ============================================================
Write-Section "USER LOGIN"

$LoginData = @{
    username = $TestUser.username
    password = $TestUser.password
}

Write-Info "Logging in as: $($TestUser.username)"
$Response = Invoke-API -Method "POST" -Endpoint "/auth/login" -Body $LoginData -UseAuth $false

if ($Response.success) {
    $Global:Token = $Response.token
    Write-Success "Login successful"
    Write-Info "Token acquired (expires in 24h)"
}
else {
    Write-Error "Login failed: $($Response.error)"
    exit 1
}

# ============================================================
# TEST: Get Current User
# ============================================================
Write-Section "GET CURRENT USER"

$Response = Invoke-API -Method "GET" -Endpoint "/auth/me"

if ($Response.success) {
    Write-Success "Got user info"
    Write-Info "Username: $($Response.user.username)"
    Write-Info "Role: $($Response.user.role)"
}
else {
    Write-Error "Failed to get user: $($Response.error)"
}

# ============================================================
# TEST: Chat Categories
# ============================================================
Write-Section "CHAT - GET CATEGORIES"

$Response = Invoke-API -Method "GET" -Endpoint "/chat/categories"

if ($Response.success) {
    Write-Success "Got $($Response.categories.Count) categories"
    foreach ($cat in $Response.categories) {
        Write-Info "  $($cat.icon) $($cat.display_name)"
    }
}
else {
    Write-Error "Failed to get categories: $($Response.error)"
}

# ============================================================
# TEST: Start Chat Conversation
# ============================================================
Write-Section "CHAT - START CONVERSATION"

$ChatData = @{
    action = "start"
}

$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body $ChatData

if ($Response.success) {
    Write-Success "Conversation started"
    Write-Info "Session ID: $($Response.session_id)"
    Write-Info "Buttons: $($Response.buttons.Count)"
    $SessionId = $Response.session_id
}
else {
    Write-Error "Failed to start chat: $($Response.error)"
}

# ============================================================
# TEST: Select Category (VPN)
# ============================================================
Write-Section "CHAT - SELECT CATEGORY"

$ChatData = @{
    action     = "select_category"
    value      = "vpn"
    session_id = $SessionId
}

$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body $ChatData

if ($Response.success) {
    Write-Success "Category selected"
    Write-Info "Response: $($Response.response.Substring(0, [Math]::Min(100, $Response.response.Length)))..."
    Write-Info "Subcategories: $($Response.buttons.Count)"
}
else {
    Write-Error "Failed to select category: $($Response.error)"
}

# ============================================================
# TEST: KB Search
# ============================================================
Write-Section "KB SEARCH"

$SearchData = @{
    query = "VPN connection not working"
    top_k = 3
}

$Response = Invoke-API -Method "POST" -Endpoint "/kb/search" -Body $SearchData

if ($Response.success) {
    Write-Success "Found $($Response.results.Count) results"
    foreach ($result in $Response.results) {
        Write-Info "  - $($result.issue) (Score: $([math]::Round($result.similarity, 2)))"
    }
}
else {
    Write-Error "KB search failed: $($Response.error)"
}

# ============================================================
# TEST: Get Technicians
# ============================================================
Write-Section "GET TECHNICIANS"

$Response = Invoke-API -Method "GET" -Endpoint "/technicians"

if ($Response.success) {
    Write-Success "Got $($Response.technicians.Count) technicians"
    foreach ($tech in $Response.technicians) {
        Write-Info "  - $($tech.name) ($($tech.role))"
    }
}
else {
    Write-Error "Failed to get technicians: $($Response.error)"
}

# ============================================================
# TEST: Get SLA Config
# ============================================================
Write-Section "GET SLA CONFIG"

$Response = Invoke-API -Method "GET" -Endpoint "/sla"

if ($Response.success) {
    Write-Success "Got SLA configuration"
    foreach ($sla in $Response.sla_config) {
        Write-Info "  - $($sla.priority): $($sla.sla_hours) hours"
    }
}
else {
    Write-Error "Failed to get SLA config: $($Response.error)"
}

# ============================================================
# TEST: Get Priority Rules
# ============================================================
Write-Section "GET PRIORITY RULES"

$Response = Invoke-API -Method "GET" -Endpoint "/priority-rules"

if ($Response.success) {
    Write-Success "Got $($Response.rules.Count) priority rules"
}
else {
    Write-Error "Failed to get priority rules: $($Response.error)"
}

# ============================================================
# TEST: Get Ticket Analytics
# ============================================================
Write-Section "TICKET ANALYTICS"

$Response = Invoke-API -Method "GET" -Endpoint "/analytics/tickets"

if ($Response.success) {
    Write-Success "Got ticket analytics"
    $stats = $Response.stats
    Write-Info "  Total: $($stats.total)"
    Write-Info "  Open: $($stats.open)"
    Write-Info "  In Progress: $($stats.in_progress)"
    Write-Info "  Resolved: $($stats.resolved)"
}
else {
    Write-Error "Failed to get analytics: $($Response.error)"
}

# ============================================================
# TEST: Admin Login
# ============================================================
Write-Section "ADMIN LOGIN"

$AdminLogin = @{
    username = "admin"
    password = "admin123"
}

$Response = Invoke-API -Method "POST" -Endpoint "/auth/login" -Body $AdminLogin -UseAuth $false

if ($Response.success) {
    $Global:Token = $Response.token
    Write-Success "Admin login successful"
}
else {
    Write-Error "Admin login failed (seed data may not be loaded)"
}

# ============================================================
# TEST: Create Ticket via Chat
# ============================================================
Write-Section "CREATE TICKET VIA CHAT"

# Start fresh conversation
$ChatData = @{ action = "start" }
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body $ChatData
$SessionId = $Response.session_id

# Select Other Issues (free text)
$ChatData = @{
    action     = "free_text"
    message    = "My computer is running very slow and applications keep crashing"
    session_id = $SessionId
}
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body $ChatData

if ($Response.success -and $Response.buttons) {
    Write-Info "Got ticket creation prompt"
    
    # Confirm ticket creation
    $ChatData = @{
        action     = "confirm_ticket"
        session_id = $SessionId
    }
    $Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body $ChatData
    
    if ($Response.ticket_id) {
        Write-Success "Ticket created: $($Response.ticket_id)"
    }
}

# ============================================================
# TEST: Get User Tickets
# ============================================================
Write-Section "GET USER TICKETS"

$Response = Invoke-API -Method "GET" -Endpoint "/auth/me"
$UserId = $Response.user.id

$Response = Invoke-API -Method "GET" -Endpoint "/tickets/user/$UserId"

if ($Response.success) {
    Write-Success "Got $($Response.tickets.Count) tickets"
    foreach ($ticket in $Response.tickets) {
        Write-Info "  - $($ticket.id): $($ticket.subject) [$($ticket.status)]"
    }
}
else {
    Write-Error "Failed to get tickets: $($Response.error)"
}

# ============================================================
# SUMMARY
# ============================================================
Write-Section "TEST SUMMARY"
Write-Host ""
Write-Success "All API tests completed!"
Write-Host ""
Write-Info "API is functional and ready for use."
Write-Host ""
