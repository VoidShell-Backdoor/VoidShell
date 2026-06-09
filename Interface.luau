local Library = (Abysall.UILibrary == "Linoria" and "LinoriaLib" or "Obsidian")
local BaseUrl = "https://raw.githubusercontent.com/mstudio45/" .. Library .. "/refs/heads/main/"
local AbysallUrl = "https://raw.githubusercontent.com/bocaj111004/Abysall/refs/heads/main/"

return {
  Library = loadstring(game:HttpGet(BaseUrl .. "Library.lua"))(),
  SaveManager = loadstring(game:HttpGet(BaseUrl .. "addons/SaveManager.lua"))(),
  ThemeManager = loadstring(game:HttpGet(BaseUrl .. "addons/ThemeManager.lua"))(),

  ApplyInfoTab = loadstring(game:HttpGet(AbysallUrl .. "Components/InfoTab.luau"))(),
  ApplySettingsTab = loadstring(game:HttpGet(AbysallUrl .. "Components/SettingsTab.luau"))()
}
