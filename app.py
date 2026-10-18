-- ============================================================
-- ВОРОТА (ПРОВЕРКА ДОСТУПА)
-- ============================================================
local function apiCall(method, path, body)
    local req = (syn and syn.request) or http_request or request
    if API_URL == "" then return nil, "noapi" end
    if not req then return nil, "norequest" end
    local ok, res = pcall(function()
        return req({
            Url = API_URL .. path, Method = method,
            Headers = { ["Content-Type"] = "application/json" },
            Body = body and HttpService:JSONEncode(body) or nil,
        })
    end)
    if not ok or type(res) ~= "table" then return nil, "network" end
    if res.StatusCode ~= 200 then return nil, "http" .. tostring(res.StatusCode) end
    local ok2, data = pcall(function() return HttpService:JSONDecode(res.Body) end)
    if not ok2 or type(data) ~= "table" then return nil, "badjson" end
    return data
end

local function showGate()
    local gui = Instance.new("ScreenGui")
    gui.Name = "FrostyGate"
    gui.ResetOnSpawn = false
    gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
    gui.Parent = PlayerGui

    local bg = Instance.new("Frame")
    bg.Size = UDim2.fromScale(1, 1)
    bg.BackgroundColor3 = Color3.fromRGB(10, 15, 30)
    bg.BackgroundTransparency = 0.1
    bg.Parent = gui

    local frame = Instance.new("Frame")
    frame.Size = UDim2.fromOffset(400, 350)
    frame.Position = UDim2.fromScale(0.5, 0.5)
    frame.AnchorPoint = Vector2.new(0.5, 0.5)
    frame.BackgroundColor3 = Color3.fromRGB(20, 30, 50)
    frame.Parent = gui
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 16)
    corner.Parent = frame
    local stroke = Instance.new("UIStroke")
    stroke.Color = Color3.fromRGB(130, 200, 255)
    stroke.Thickness = 2
    stroke.Parent = frame

    local title = Instance.new("TextLabel")
    title.Text = "❄️ Frosty Hub — Доступ"
    title.Size = UDim2.new(1, 0, 0, 40)
    title.BackgroundTransparency = 1
    title.TextColor3 = Color3.fromRGB(255, 255, 255)
    title.Font = Enum.Font.GothamBold
    title.TextSize = 20
    title.Parent = frame

    local statusLbl = Instance.new("TextLabel")
    statusLbl.Text = "Требуется Premium или привязка Discord"
    statusLbl.Size = UDim2.new(1, -40, 0, 20)
    statusLbl.Position = UDim2.new(0, 20, 0, 45)
    statusLbl.BackgroundTransparency = 1
    statusLbl.TextColor3 = Color3.fromRGB(180, 200, 230)
    statusLbl.Font = Enum.Font.Gotham
    statusLbl.TextSize = 12
    statusLbl.Parent = frame

    local keyBox = Instance.new("TextBox")
    keyBox.Size = UDim2.new(1, -40, 0, 35)
    keyBox.Position = UDim2.new(0, 20, 0, 80)
    keyBox.BackgroundColor3 = Color3.fromRGB(10, 15, 30)
    keyBox.TextColor3 = Color3.fromRGB(255, 255, 255)
    keyBox.PlaceholderText = "Введи ключ (FROSTY-...)"
    keyBox.PlaceholderColor3 = Color3.fromRGB(100, 120, 150)
    keyBox.Font = Enum.Font.Gotham
    keyBox.TextSize = 14
    keyBox.Parent = frame
    local kc = Instance.new("UICorner")
    kc.CornerRadius = UDim.new(0, 8)
    kc.Parent = keyBox
    local ks = Instance.new("UIStroke")
    ks.Color = Color3.fromRGB(80, 100, 140)
    ks.Parent = keyBox

    local activateBtn = Instance.new("TextButton")
    activateBtn.Size = UDim2.new(1, -40, 0, 35)
    activateBtn.Position = UDim2.new(0, 20, 0, 125)
    activateBtn.BackgroundColor3 = Color3.fromRGB(60, 130, 200)
    activateBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
    activateBtn.Font = Enum.Font.GothamBold
    activateBtn.TextSize = 14
    activateBtn.Text = "Активировать ключ"
    activateBtn.Parent = frame
    local ac = Instance.new("UICorner")
    ac.CornerRadius = UDim.new(0, 8)
    ac.Parent = activateBtn

    local line = Instance.new("Frame")
    line.Size = UDim2.new(1, -40, 0, 1)
    line.Position = UDim2.new(0, 20, 0, 175)
    line.BackgroundColor3 = Color3.fromRGB(60, 80, 110)
    line.BorderSizePixel = 0
    line.Parent = frame

    local orLbl = Instance.new("TextLabel")
    orLbl.Text = "или"
    orLbl.Size = UDim2.new(1, 0, 0, 20)
    orLbl.Position = UDim2.new(0, 0, 0, 180)
    orLbl.BackgroundTransparency = 1
    orLbl.TextColor3 = Color3.fromRGB(120, 140, 170)
    orLbl.Font = Enum.Font.Gotham
    orLbl.TextSize = 12
    orLbl.Parent = frame

    local discordBtn = Instance.new("TextButton")
    discordBtn.Size = UDim2.new(1, -40, 0, 35)
    discordBtn.Position = UDim2.new(0, 20, 0, 210)
    discordBtn.BackgroundColor3 = Color3.fromRGB(88, 101, 242)
    discordBtn.TextColor3 = Color3.fromRGB(255, 255, 255)
    discordBtn.Font = Enum.Font.GothamBold
    discordBtn.TextSize = 14
    discordBtn.Text = "🔗 Привязать Discord"
    discordBtn.Parent = frame
    local dc = Instance.new("UICorner")
    dc.CornerRadius = UDim.new(0, 8)
    dc.Parent = discordBtn

    local codeLbl = Instance.new("TextLabel")
    codeLbl.Size = UDim2.new(1, -40, 0, 30)
    codeLbl.Position = UDim2.new(0, 20, 0, 255)
    codeLbl.BackgroundTransparency = 1
    codeLbl.TextColor3 = Color3.fromRGB(130, 200, 255)
    codeLbl.Font = Enum.Font.Code
    codeLbl.TextSize = 14
    codeLbl.Text = ""
    codeLbl.Parent = frame

    activateBtn.MouseButton1Click:Connect(function()
        local key = keyBox.Text:match("^%s*(.-)%s*$"):upper()
        if key == "" then return end
        activateBtn.Text = "Проверка..."
        activateBtn.Active = false
        task.spawn(function()
            local d, err = apiCall("POST", "/premium/activate", { userId = LocalPlayer.UserId, key = key })
            activateBtn.Text = "Активировать ключ"
            activateBtn.Active = true
            if d and d.ok then
                statusLbl.Text = "✅ Ключ активирован! Загрузка..."
                statusLbl.TextColor3 = Color3.fromRGB(100, 255, 100)
                task.wait(1)
                gui:Destroy()
                _G.FrostyPremiumUnlocked = true
            else
                statusLbl.Text = "❌ " .. (d and d.error or "Ошибка активации")
                statusLbl.TextColor3 = Color3.fromRGB(255, 100, 100)
            end
        end)
    end)

    discordBtn.MouseButton1Click:Connect(function()
        discordBtn.Text = "Запрос кода..."
        discordBtn.Active = false
        task.spawn(function()
            local d, err = apiCall("POST", "/link/start", { userId = LocalPlayer.UserId, username = LocalPlayer.Name })
            if not d or not d.code then
                discordBtn.Text = "🔗 Привязать Discord"
                discordBtn.Active = true
                statusLbl.Text = "❌ Ошибка сервера"
                return
            end
            codeLbl.Text = "Код: " .. d.code
            statusLbl.Text = "Введи код в Discord: !link " .. d.code
            statusLbl.TextColor3 = Color3.fromRGB(255, 200, 100)
            local deadline = tick() + 300
            while tick() < deadline do
                task.wait(3)
                local s = apiCall("GET", "/link/status?code=" .. d.code)
                if s and s.status == "linked" then
                    local stat = apiCall("GET", "/status?userId=" .. LocalPlayer.UserId)
                    if stat and stat.premium then
                        statusLbl.Text = "✅ Discord привязан! Загрузка..."
                        statusLbl.TextColor3 = Color3.fromRGB(100, 255, 100)
                        task.wait(1)
                        gui:Destroy()
                        _G.FrostyPremiumUnlocked = true
                        return
                    else
                        statusLbl.Text = "⚠ Discord привязан, но премиума нет."
                        statusLbl.TextColor3 = Color3.fromRGB(255, 200, 100)
                        discordBtn.Text = "🔗 Привязать Discord"
                        discordBtn.Active = true
                        return
                    end
                end
            end
            discordBtn.Text = "🔗 Привязать Discord"
            discordBtn.Active = true
            statusLbl.Text = "⌛ Код истёк"
        end)
    end)
end

-- ============================================================
-- ЗАПУСК
-- ============================================================
task.spawn(function()
    local d, err = apiCall("GET", "/status?userId=" .. tostring(LocalPlayer.UserId))
    if d and d.premium then
        print("[Frosty] Premium найден, загрузка...")
        buildUI()
    else
        print("[Frosty] Premium не найден, показываем экран активации.")
        showGate()
        local startTime = tick()
        while not _G.FrostyPremiumUnlocked and tick() - startTime < 600 do
            task.wait(1)
        end
        if _G.FrostyPremiumUnlocked then
            buildUI()
        end
    end
end)
