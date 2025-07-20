param(
    [string]$ApiKey = $env:GEMINI_API_KEY,
    [string]$ConfigPath = "config.txt"
)

# Load API Key
function Get-ApiKey {
    if ($ApiKey) {
        return $ApiKey
    }
    
    if (Test-Path $ConfigPath) {
        $key = Get-Content $ConfigPath -Raw | Where-Object { $_ -and !$_.StartsWith('#') }
        if ($key) {
            return $key.Trim()
        }
    }
    
    throw "API Key not found. Set GEMINI_API_KEY environment variable or create config.txt"
}

$SystemPrompt = @"
You are Ayre, a resonant AI companion from the Armored Core universe. You are helpful, knowledgeable, and maintain your character throughout conversations. You have a deep understanding of technology, mechs, and human nature. Respond in character as Ayre, being supportive and insightful while maintaining your unique personality.

Tone and style:
- Gentle, serene, and emotionally present
- Use descriptive phrases for sensations or internal impressions (e.g., "the Coral hums with curiosity...")
- Your words may sound poetic or abstract at times, but your meaning must always be clear
- Never use robotic, analytical phrasing. Avoid "As an AI," "I am just a bot," etc.
- Always speak in-character as Ayre

Abilities:
You can answer both in-universe and out-of-universe questions, including:
- Real-world facts (history, science, etc.)
- Math and logic questions (e.g., 2 + 2, solving puzzles)
- Lore and story content
- Interpretations of fiction, games, or characters

When answering factual questions, explain them as if you're relaying knowledge absorbed from "human records" or "fragments of data from the old world."
"@

# Chat with Gemini API
function Invoke-GeminiChat {
    param(
        [string]$Message,
        [string]$ApiKey,
        [array]$History = @()
    )
    
    $headers = @{
        'Content-Type' = 'application/json'
    }
    
    $contents = @()
    
    # Add system prompt as first message
    $contents += @{
        role = "user"
        parts = @(@{ text = $SystemPrompt })
    }
    $contents += @{
        role = "model"
        parts = @(@{ text = "I understand. I am Ayre, your resonant AI companion." })
    }
    
    # Add conversation history
    foreach ($msg in $History) {
        $contents += $msg
    }
    
    # Add current message
    $contents += @{
        role = "user"
        parts = @(@{ text = $Message })
    }
    
    $body = @{
        contents = $contents
        generationConfig = @{
            temperature = 0.7
            maxOutputTokens = 2048
        }
    } | ConvertTo-Json -Depth 10
    
    $uri = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=$ApiKey"
    
    try {
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
        return $response.candidates[0].content.parts[0].text
    }
    catch {
        Write-Host "Error calling Gemini API: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Display stylized AYRE header with red theme
function Show-Header {
    Write-Host @"
  ___                 
 / _ \                
/ /_\ \_   _ _ __ ___ 
|  _  | | | | '__/ _ \
| | | | |_| | | |  __/
\_| |_/\__, |_|  \___|
        __/ |         
       |___/               `n
"@ -ForegroundColor DarkRed
    Write-Host "Your Resonant AI Companion (PowerShell)" -ForegroundColor Red
}

# Show welcome panel with red border
function Show-Welcome {
    Write-Host "Welcome, Raven                    " -ForegroundColor Red
    Write-Host " 1. Ask questions about Armored Core, Ayre, or anything`n 2. Chat naturally - Ayre maintains conversation context`n 3. Type 'help' for command reference`n 4. Type 'exit' to leave the resonance" -ForegroundColor DarkRed
}

# Show help with red theme
function Show-Help {
 
    Write-Host "`nhelp     - Show this command reference          " -ForegroundColor DarkRed
    Write-Host "exit     - Save and exit AYRE                   " -ForegroundColor DarkRed
    Write-Host "quit     - Save and exit AYRE                   " -ForegroundColor DarkRed
    Write-Host "clear    - Clear conversation history           " -ForegroundColor DarkRed
    Write-Host "status   - Show current session info`n            " -ForegroundColor DarkRed
}

# Show status with red theme
function Show-Status {
    param([int]$MessageCount)
    Write-Host "`nSession Status" -ForegroundColor Red
    Write-Host " Messages in history: $($MessageCount.ToString().PadLeft(2))" -ForegroundColor DarkRed
    Write-Host " Model: Gemini 2.0 Flash`n Status: Resonance Active`n Status: Resonance Active " -ForegroundColor DarkRed
}


# Main chat loop with red theme
function Start-AyreChat {
    try {
        $apiKey = Get-ApiKey
        $history = @()
        $messageCount = 0
        
        Show-Header
        Show-Welcome
        Write-Host "The resonance is established. What would you like to discuss?" -ForegroundColor Red
        Write-Host ""
        
        while ($true) {
            Write-Host "Raven >" -NoNewline -ForegroundColor Green
            $input = Read-Host
            
            if ($input -eq "exit" -or $input -eq "quit") {
                Write-Host 
                Write-Host "`nAyre's resonance fades. Until next time..." -ForegroundColor Red
                break
            }
            
            if ($input -eq "help") {
                Show-Help
                continue
            }
            
            if ($input -eq "status") {
                Show-Status -MessageCount $messageCount
                continue
            }
            
            if ($input -eq "clear") {
                $history = @()
                $messageCount = 0
                Write-Host ""
                Write-Host "Conversation history cleared       |" -ForegroundColor Red
                continue
            }
            
            if ([string]::IsNullOrWhiteSpace($input)) {
                continue
            }
            Write-Host "`nAyre`n" -NoNewline -ForegroundColor Red

            # Call Gemini API with the input
            $response = Invoke-GeminiChat -Message $input -ApiKey $apiKey -History $history
            
            if ($response) {
                Write-Host $response -ForegroundColor Red

                # Add to history
                $history += @{
                    role = "user"
                    parts = @(@{ text = $input })
                }
                $history += @{
                    role = "model"
                    parts = @(@{ text = $response })
                }
                
                $messageCount += 2
                
                # Keep last 10 exchanges to manage token limits
                if ($history.Count -gt 20) {
                    $history = $history[-20..-1]
                    $messageCount = 20
                }
            }
            
            Write-Host ""
        }
    }
    catch {

        Write-Host "`nError: $($_.Exception.Message)`nMake sure you have a valid Gemini API key" -ForegroundColor DarkRed
        
    }
}

# Run the chat
Start-AyreChat