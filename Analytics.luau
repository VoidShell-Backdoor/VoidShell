local function CloneReference(Object)
    if Abysall.Environment.cloneref then
        return Abysall.Environment.cloneref(Object)
    else
        return Object
    end
end

local Services = setmetatable({}, {
    __index = function(self, Name)
        return CloneReference(game:GetService(Name))
    end
})

if Abysall.Environment.identifyexecutor and Abysall.Environment.request then
    local Player = Services.Players.LocalPlayer
    local Data = {
        Account = Player.Name,
        Executor = Abysall.Environment.identifyexecutor(),
        Executions = tonumber(Abysall.TotalExecutions),
        GameName = Services.MarketplaceService:GetProductInfo(game.PlaceId).Name,
        PlaceId = tostring(game.PlaceId)
    }

    task.spawn(function()
        pcall(function()
            Abysall.Environment.request({
                Url = "http://93.115.101.180:10577/send",
                Method = "POST",
                Headers = {
                    ["content-type"] = "application/json"
                },
                Body = Services.HttpService:JSONEncode(Data)
            })
        end)
    end)
end
