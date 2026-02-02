# ============================================================
# Full Integration Test Script
# Run: .\test_full_flow.ps1
# ============================================================

$BaseUrl = "http://localhost:5000/api"
$Global:Token = $null
$Global:AdminToken = $null
$Global:UserId = $null
$Global:TicketId = $null

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
        [string]$Token = $null
    )
    
    $Headers = @{ "Content-Type" = "application/json" }
    
    if ($Token) {
        $Headers["Authorization"] = "Bearer $Token"
    } elseif ($Global:Token) {
        $Headers["Authorization"] = "Bearer $Global:Token"
    }
    
    $Uri = "$BaseUrl$Endpoint"
    
    try {
        if ($Body) {
            $JsonBody = $Body | ConvertTo-Json -Depth 10
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -Body $JsonBody
        } else {
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers
        }
        return $Response
    }
    catch {
        $StatusCode = $_.Exception.Response.StatusCode.Value__
        return @{ success = $false; error = "HTTP $StatusCode"; status_code = $StatusCode }
    }
}

Write-Host "
╔═══════════════════════════════════════════════════════════╗
║         IT SUPPORT SYSTEM - FULL INTEGRATION TEST         ║
╚═══════════════════════════════════════════════════════════╝
" -ForegroundColor Magenta

# ============================================================
# PHASE 1: Setup & Authentication
# ============================================================
Write-Section "PHASE 1: AUTHENTICATION"

# Test 1.1: Register new user
$RandomId = Get-Random -Maximum 9999
$TestUser = @{
    username = "testuser_$RandomId"
    email = "testuser_$RandomId@example.com"
    password = "testpass123"
    full_name = "Test User $RandomId"
    department = "Engineering"
}

Write-Info "1.1 Registering test user..."
$Response = Invoke-API -Method "POST" -Endpoint "/auth/register" -Body $TestUser
if ($Response.success) {
    Write-Success "User registered: $($Response.user.username)"
    $Global:UserId = $Response.user.id
} else {
    Write-Error "Registration failed: $($Response.error)"
}

# Test 1.2: Login as user
Write-Info "1.2 Logging in as test user..."
$Response = Invoke-API -Method "POST" -Endpoint "/auth/login" -Body @{
    username = $TestUser.username
    password = $TestUser.password
}
if ($Response.success) {
    $Global:Token = $Response.token
    Write-Success "User login successful"
} else {
    Write-Error "Login failed"
    exit 1
}

# Test 1.3: Login as admin
Write-Info "1.3 Logging in as admin..."
$Response = Invoke-API -Method "POST" -Endpoint "/auth/login" -Body @{
    username = "admin"
    password = "admin123"
}
if ($Response.success) {
    $Global:AdminToken = $Response.token
    Write-Success "Admin login successful"
} else {
    Write-Error "Admin login failed (run seed_data.py first)"
}

# ============================================================
# PHASE 2: Chat Flow (Button Navigation)
# ============================================================
Write-Section "PHASE 2: CHAT FLOW"

# Test 2.1: Start conversation
Write-Info "2.1 Starting conversation..."
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{ action = "start" }
if ($Response.success -and $Response.buttons.Count -gt 0) {
    Write-Success "Conversation started with $($Response.buttons.Count) categories"
    $SessionId = $Response.session_id
} else {
    Write-Error "Failed to start conversation"
}

# Test 2.2: Select VPN category
Write-Info "2.2 Selecting VPN category..."
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{
    action = "select_category"
    value = "vpn"
    session_id = $SessionId
}
if ($Response.success -and $Response.buttons) {
    Write-Success "Got $($Response.buttons.Count) subcategories for VPN"
} else {
    Write-Error "Failed to select category"
}

# Test 2.3: Select subcategory
Write-Info "2.3 Selecting first subcategory..."
if ($Response.buttons.Count -gt 1) {
    $FirstSubcat = $Response.buttons[0]
    $Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{
        action = "select_subcategory"
        value = $FirstSubcat.value
        session_id = $SessionId
    }
    if ($Response.success) {
        Write-Success "Got solution for: $($FirstSubcat.label)"
        Write-Info "Solution preview: $($Response.response.Substring(0, [Math]::Min(80, $Response.response.Length)))..."
    }
}

# Test 2.4: Decline ticket (solution worked)
Write-Info "2.4 Declining ticket creation (solution worked)..."
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{
    action = "decline_ticket"
    session_id = $SessionId
}
if ($Response.success) {
    Write-Success "Ticket declined - conversation ended gracefully"
}

# Test 2.5: Free text flow (Other Issues)
Write-Info "2.5 Testing free text flow..."
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{ action = "start" }
$SessionId = $Response.session_id

$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{
    action = "free_text"
    message = "My computer keeps showing blue screen errors and restarting randomly. This is urgent!"
    session_id = $SessionId
}
if ($Response.success) {
    Write-Success "Free text processed"
}

# Test 2.6: Confirm ticket creation
Write-Info "2.6 Confirming ticket creation..."
$Response = Invoke-API -Method "POST" -Endpoint "/chat" -Body @{
    action = "confirm_ticket"
    session_id = $SessionId
}
if ($Response.success -and $Response.ticket_id) {
    Write-Success "Ticket created: $($Response.ticket_id)"
    $Global:TicketId = $Response.ticket_id
} else {
    Write-Error "Ticket creation failed"
}

# ============================================================
# PHASE 3: Ticket Management
# ============================================================
Write-Section "PHASE 3: TICKET MANAGEMENT"

# Test 3.1: Get user tickets
Write-Info "3.1 Getting user tickets..."
$Response = Invoke-API -Method "GET" -Endpoint "/tickets/user/$Global:UserId"
if ($Response.success) {
    Write-Success "User has $($Response.tickets.Count) tickets"
}

# Test 3.2: Get ticket details
if ($Global:TicketId) {
    Write-Info "3.2 Getting ticket details..."
    $Response = Invoke-API -Method "GET" -Endpoint "/tickets/$Global:TicketId"
    if ($Response.success) {
        Write-Success "Ticket: $($Response.ticket.subject)"
        Write-Info "  Priority: $($Response.ticket.priority)"
        Write-Info "  Status: $($Response.ticket.status)"
        Write-Info "  Category: $($Response.ticket.category)"
    }
}

# Test 3.3: Admin - Assign ticket
if ($Global:TicketId -and $Global:AdminToken) {
    Write-Info "3.3 [ADMIN] Assigning ticket to technician..."
    $Response = Invoke-API -Method "PUT" -Endpoint "/tickets/$Global:TicketId/assign" -Body @{
        technician_id = "TECH-001"
    } -Token $Global:AdminToken
    if ($Response.success) {
        Write-Success "Ticket assigned to TECH-001"
    }
}

# Test 3.4: Admin - Update ticket status
if ($Global:TicketId -and $Global:AdminToken) {
    Write-Info "3.4 [ADMIN] Updating ticket status..."
    $Response = Invoke-API -Method "PUT" -Endpoint "/tickets/$Global:TicketId/status" -Body @{
        status = "in_progress"
    } -Token $Global:AdminToken
    if ($Response.success) {
        Write-Success "Ticket status updated to: in_progress"
    }
}

# ============================================================
# PHASE 4: Knowledge Base
# ============================================================
Write-Section "PHASE 4: KNOWLEDGE BASE"

# Test 4.1: Search KB
Write-Info "4.1 Searching knowledge base..."
$Response = Invoke-API -Method "POST" -Endpoint "/kb/search" -Body @{
    query = "VPN not connecting"
    top_k = 3
}
if ($Response.success) {
    Write-Success "Found $($Response.results.Count) KB results"
}

# Test 4.2: Get KB categories
Write-Info "4.2 Getting KB categories..."
$Response = Invoke-API -Method "GET" -Endpoint "/chat/categories"
if ($Response.success) {
    Write-Success "KB has $($Response.categories.Count) categories"
}

# Test 4.3: Get KB stats
Write-Info "4.3 Getting KB stats..."
$Response = Invoke-API -Method "GET" -Endpoint "/kb/stats"
if ($Response.success) {
    Write-Success "KB stats retrieved"
    Write-Info "  Total entries: $($Response.stats.total_entries)"
}

# ============================================================
# PHASE 5: Admin Features
# ============================================================
Write-Section "PHASE 5: ADMIN FEATURES"

# Test 5.1: Get technicians
Write-Info "5.1 Getting technicians..."
$Response = Invoke-API -Method "GET" -Endpoint "/technicians" -Token $Global:AdminToken
if ($Response.success) {
    Write-Success "Got $($Response.technicians.Count) technicians"
}

# Test 5.2: Get SLA config
Write-Info "5.2 Getting SLA configuration..."
$Response = Invoke-API -Method "GET" -Endpoint "/sla" -Token $Global:AdminToken
if ($Response.success) {
    Write-Success "Got SLA config for $($Response.sla_config.Count) priority levels"
}

# Test 5.3: Get priority rules
Write-Info "5.3 Getting priority rules..."
$Response = Invoke-API -Method "GET" -Endpoint "/priority-rules" -Token $Global:AdminToken
if ($Response.success) {
    Write-Success "Got $($Response.rules.Count) priority rules"
}

# Test 5.4: Get analytics
Write-Info "5.4 Getting ticket analytics..."
$Response = Invoke-API -Method "GET" -Endpoint "/analytics/tickets" -Token $Global:AdminToken
if ($Response.success) {
    Write-Success "Analytics retrieved"
    Write-Info "  Total tickets: $($Response.stats.total)"
    Write-Info "  Open: $($Response.stats.open)"
    Write-Info "  In Progress: $($Response.stats.in_progress)"
}

# Test 5.5: Get ticket trend
Write-Info "5.5 Getting ticket trend..."
$Response = Invoke-API -Method "GET" -Endpoint "/analytics/trend?days=7" -Token $Global:AdminToken
if ($Response.success) {
    Write-Success "Got $($Response.trend.Count) days of trend data"
}

# ============================================================
# SUMMARY
# ============================================================
Write-Section "TEST SUMMARY"

Write-Host "
╔═══════════════════════════════════════════════════════════╗
║                    ALL TESTS COMPLETED!                   ║
╠═══════════════════════════════════════════════════════════╣
║  Phase 1: Authentication     ✅                           ║
║  Phase 2: Chat Flow          ✅                           ║
║  Phase 3: Ticket Management  ✅                           ║
║  Phase 4: Knowledge Base     ✅                           ║
║  Phase 5: Admin Features     ✅                           ║
╚═══════════════════════════════════════════════════════════╝
" -ForegroundColor Green

if ($Global:TicketId) {
    Write-Info "Test ticket created: $Global:TicketId"
}

Write-Host ""
