"""Runs the Superb WoW Kit addon in real Lua against a stubbed WoW API.

Needs: pip install lupa. Run from the repo root: python tests/test_kit.py
"""
import re
from pathlib import Path

from lupa import LuaRuntime

ADDON = Path("!ForeverKit")
TOC_FILES = [l.strip() for l in (ADDON / "!ForeverKit.toc").read_text().splitlines()
             if l.strip().endswith(".lua")]

STUBS = """
binds, saved, resets, cvars, messages, handler, saves = {}, 0, 0, {}, {}, nil, 0
inCombat, breakEditMode = false, false
function UnitNameUnmodified() return NAME, SURNAME end
function GetRealmName() return "Realm" end
function CreateFrame() return { RegisterEvent = function() end, SetScript = function(_, _, f) handler = f end } end
function SetBinding(k, a) binds[k] = a end
function SaveBindings() saved = saved + 1 end
function GetCurrentBindingSet() return 2 end
DEFAULT_BINDINGS = 0
function LoadBindings(n) assert(n == 0); resets = resets + 1; binds = {} end
function SetCVar(k, v) cvars[k] = v end
function print(m) messages[#messages + 1] = m end
function ReloadUI() end
screenWidth, screenHeight = 2133, 1200
function GetScreenWidth() return screenWidth end
function GetScreenHeight() return screenHeight end
macroList, slots, cursor, knownSpells = {}, {}, nil, { Exorcism = true }
keyActions = { ["2"] = "ACTIONBUTTON2", ["4"] = "ACTIONBUTTON4",
  ["SHIFT-2"] = "MULTIACTIONBAR1BUTTON2", ["CTRL-SHIFT-3"] = "MULTIACTIONBAR2BUTTON3" }
function GetBindingAction(k) return keyActions[k] or "" end
function GetMacroIndexByName(n) for i, m in ipairs(macroList) do if m.name == n then return i end end return 0 end
function CreateMacro(n, _, b, perChar) assert(perChar); macroList[#macroList + 1] = { name = n, body = b }; return #macroList end
function EditMacro(i, _, _, b) macroList[i].body = b end
function SetBindingMacro(k, n) binds[k] = "MACRO " .. n end
function PickupMacro(n) cursor = n end
C_Spell = { PickupSpell = function(n) if knownSpells[n] then cursor = n end end }
function GetCursorInfo() return cursor end
function ClearCursor() cursor = nil end
function PlaceAction(s) slots[s] = cursor; cursor = nil end
C_Timer = { After = function(_, f) f() end }
local function child(name)
  local c = { shown = true, hooks = {} }
  function c:GetName() return name end
  function c:Hide() self.shown = false end
  function c:HookScript(_, f) self.hooks[#self.hooks + 1] = f end
  function c:Show() self.shown = true; for _, f in ipairs(self.hooks) do f(self) end end
  return c
end
mapChildren = { child("LibDBIcon10_Questie"), child("DSPBuffsMinimapButton"), child("ForeverLayerHopMinimapBadge"),
  child("MinimapZoneTextButton"), child("QuestieFrameGroup"), child(nil) }
Minimap = { GetChildren = function() return (table.unpack or unpack)(mapChildren) end }
function InCombatLockdown() return inCombat end
SlashCmdList = {}
Enum = {
  EditModeSystem = { UnitFrame = 3, ChatFrame = 8, AuraFrame = 6 },
  EditModeAuraFrameSystemIndices = { BuffFrame = 1, DebuffFrame = 2 },
  EditModeChatFrameSetting = { WidthHundreds = 0, WidthTensAndOnes = 1, HeightHundreds = 2, HeightTensAndOnes = 3 },
  EditModeUnitFrameSystemIndices = { Party = 5 },
  EditModeUnitFrameSetting = { UseRaidStylePartyFrames = 9 },
  EditModeLayoutType = { Account = 1 },
}
local function preset()
  return { layoutName = "Modern", systems = { { system = 3, systemIndex = 5, settings = { { setting = 9, value = 0 } } },
    { system = 8, settings = { { setting = 0, value = 4 }, { setting = 1, value = 30 }, { setting = 2, value = 1 }, { setting = 3, value = 70 } } },
    { system = 6, systemIndex = 1, settings = {} }, { system = 6, systemIndex = 2, settings = {} } } }
end
EditModePresetLayoutManager = { GetCopyOfPresetLayouts = function() return { preset(), preset() } end }
layoutInfo = { activeLayout = 1, layouts = {} }
C_EditMode = {
  GetLayouts = function() if breakEditMode then error("nope") end return layoutInfo end,
  SaveLayouts = function(i) saves = saves + 1; layoutInfo = i; handler(nil, "EDIT_MODE_LAYOUTS_UPDATED") end,
}
"""

ADDONS = ("!ForeverKit", "EllesmereUI", "EllesmereUIBags", "FollowTheArrow", "EllesmereUIActionBars", "EllesmereUIMinimap", "EllesmereUIRaidFrames", "EllesmereUIUnitFrames", "Questie")


def login(name="Raba", surname="Canoosh", before="", personal="", installed=""):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(STUBS)
    lua.globals().NAME, lua.globals().SURNAME = name, surname
    lua.execute(before)
    for file in TOC_FILES:
        written = {"Personal.lua": personal, "Installed.lua": installed}
        lua.execute(written[file] if file in written else (ADDON / file).read_text())
    handler = lua.globals().handler
    for addon in ADDONS:
        handler(None, "ADDON_LOADED", addon)
    handler(None, "PLAYER_LOGIN", None)
    handler(None, "PLAYER_ENTERING_WORLD", None)
    return lua


AB = "EllesmereUIDB.profiles.Default.addons.EllesmereUIActionBars"


def test_bars_are_three_rows_of_twelve_and_a_faded_utility_block():
    e = login().eval
    bottoms = [e(f"{AB}.barPositions.{bar}.y") for bar in ("MainBar", "Bar2", "Bar3")]
    assert bottoms[0] == 38 and bottoms[1] - bottoms[0] == 47 and bottoms[2] - bottoms[1] == 47
    for bar in ("MainBar", "Bar2", "Bar3"):
        assert e(f"{AB}.barPositions.{bar}.x") == -281 and e(f"{AB}.barPositions.{bar}.relPoint") == "BOTTOM"
        assert e(f"{AB}.bars.{bar}.numIcons") == 12 and e(f"{AB}.bars.{bar}.numRows") == 1
        assert e(f"{AB}.bars.{bar}.buttonWidth") == 45 and e(f"{AB}.bars.{bar}.buttonPadding") == 2
    assert e(f"{AB}.bars.Bar5.numRows") == 3 and e(f"{AB}.barPositions.Bar5.y") == bottoms[0], "the block shares the row lines"
    assert e(f"{AB}.bars.Bar5.mouseoverAlpha") == 0.3 and e(f"{AB}.bars.Bar5.fadeMaxAlpha") == 1
    assert e(f"{AB}.bars.Bar5.barVisibility") == "always" and e(f"{AB}.bars.Bar5.mouseoverEnabled") is False, "mouseover mode rests at zero"
    assert e(f"{AB}.bars.Bar5.advancedFadeConditions.mouseover") is True
    for bar in ("Bar4", "Bar6", "Bar7", "Bar8", "MicroBar", "BagBar"):
        assert e(f"{AB}.bars.{bar}.alwaysHidden") is True
    assert e("EllesmereUIDB._capturedOnce_EAB") is True, "EllesmereUI must not copy the game's bar layout over this"


def test_xp_bar_is_ellesmereuis_and_sits_under_the_bottom_row():
    e = login().eval
    assert e(f"{AB}.useBlizzardDataBars") is False
    assert e(f"{AB}.bars.XPBar.width") == 562
    top = e(f"{AB}.barPositions.XPBar.y") + e(f"{AB}.bars.XPBar.height")
    assert e(f"{AB}.barPositions.XPBar.y") == 24 and top < e(f"{AB}.barPositions.MainBar.y")


def test_forever_command_reapplies_every_part():
    lua = login()
    lua.execute('SlashCmdList.FOREVERKIT("")')
    assert lua.eval("ForeverKitChar.version") is None and lua.eval("ForeverKitChar.seeded") is None


def test_binds_avoid_default_keys():
    lua = login()
    keys = list(lua.globals().binds)
    assert len(keys) == 30 and len({lua.globals().binds[k] for k in keys}) == 30
    assert all(re.fullmatch(r"(ALT|CTRL-SHIFT)-[0-9=-]|ALT-[QERFCV]", k) for k in keys), keys
    assert lua.eval("resets") == 0 and lua.eval("cvars.cameraFov") == 90


def test_party_preset_is_copied_then_saved_once():
    e = login().eval
    assert e("saves") == 1 and e("layoutInfo.activeLayout") == 3
    layout = "layoutInfo.layouts[1]"
    assert e(f"{layout}.layoutName") == "Forever Kit" and e(f"{layout}.layoutType") == 1
    assert e(f"{layout}.systems[1].settings[1].value") == 1
    assert e(f"{layout}.systems[1].anchorInfo.offsetX") == -480
    assert e("ForeverKitChar.partyPending") is None


def test_existing_custom_layout_is_edited_in_place():
    before = """layoutInfo = { activeLayout = 3, layouts = { { layoutName = "Mine",
      systems = { { system = 3, systemIndex = 5, settings = { { setting = 9, value = 0 } } } } } } }"""
    e = login(before=before).eval
    assert e("#layoutInfo.layouts") == 1 and e("layoutInfo.layouts[1].layoutName") == "Mine"
    assert e("layoutInfo.layouts[1].systems[1].settings[1].value") == 1


def test_edit_mode_failure_tells_the_player_and_breaks_nothing():
    lua = login(before="breakEditMode = true")
    assert any("Edit Mode" in m for m in lua.globals().messages.values())
    assert lua.eval("ForeverKitChar.version") == 4


def test_combat_defers_party_frames():
    lua = login(before="inCombat = true")
    assert lua.eval("saves") == 0 and lua.eval("ForeverKitChar.partyPending") is True


def test_layout_upgrade_reapplies_but_same_version_does_not():
    e = login(before='ForeverKitChar = { version = 1 }').eval
    assert e("saves") == 1
    settings = e("ForeverKitChar.settings")
    e = login(before=f"ForeverKitChar = {{ version = 4, settings = [==[{settings}]==], defaultsRestored = true }}").eval
    assert e("saves") == 0 and e("saved") == 0


def test_seeding_keeps_other_settings():
    before = "QuestieConfig = { profiles = { Default = { keep = true } } }"
    e = login(before=before, surname=None, name="Raba Canoosh").eval
    assert e('QuestieConfig.profiles.Default.keep') is True


def test_personal_overrides_apply_without_touching_layout():
    personal = 'ForeverKitConfig.binds.BUTTON4 = "TOGGLEAUTORUN"; ForeverKitConfig.binds["ALT-1"] = false; ForeverKitConfig.cvars.cameraFov = 75'
    e = login(before='ForeverKitChar = { version = 4, settings = "old", defaultsRestored = true }', personal=personal).eval
    assert e("saved") == 1 and e("binds.BUTTON4") == "TOGGLEAUTORUN"
    assert e('binds["ALT-1"]') is None and e("cvars.cameraFov") == 75 and e("saves") == 0


def test_old_kit_binds_reset_once_and_friends_never():
    e = login(before='ForeverKitChar = { version = 1, settings = "old" }').eval
    assert e("resets") == 1 and e("ForeverKitChar.defaultsRestored") is True
    assert login(name="Bob", surname=None).eval("resets") == 0


def test_party_waits_for_a_late_combat_to_end():
    lua = login(before="inCombat = true")
    lua.execute("inCombat = false")
    lua.globals().handler(None, "EDIT_MODE_LAYOUTS_UPDATED", None)
    assert lua.eval("saves") == 1


MACROS = """ForeverKitConfig.macros = {
  { name = "Heal", key = "SHIFT-2", body = "/cast Holy Light" },
  { name = "Skull", bind = "BUTTON3", body = "/tm !8" },
}
ForeverKitConfig.spells = { ["4"] = "Exorcism", ["CTRL-SHIFT-3"] = "Devotion Aura" }"""


def test_macros_land_on_the_button_each_key_presses():
    e = login(personal=MACROS).eval
    assert e("#macroList") == 2 and e("slots[62]") == "Heal"
    assert e("binds.BUTTON3") == "MACRO Skull" and e("slots[4]") == "Exorcism"


def test_unknown_spell_leaves_the_button_alone():
    e = login(personal=MACROS, before='slots[51] = "keep"').eval
    assert e("slots[51]") == "keep"


def test_friends_with_no_macros_touch_no_buttons():
    e = login().eval
    assert e("#macroList") == 0 and e("next(slots)") is None and e("ForeverKitChar.actions") is None


def test_macros_apply_once_and_update_in_place():
    lua = login(personal=MACROS)
    done = lua.eval("ForeverKitChar.actions")
    before = f'ForeverKitChar = {{ version = 4, settings = "old", actions = [==[{done}]==] }}'
    assert login(before=before, personal=MACROS).eval("#macroList") == 0
    edited = MACROS.replace("Holy Light", "Flash of Light")
    e = login(before='macroList = { { name = "Heal", body = "old" } }', personal=edited).eval
    assert e("#macroList") == 2 and e("macroList[1].body") == "/cast Flash of Light"


def test_macros_wait_for_combat_to_end():
    lua = login(before="inCombat = true", personal=MACROS)
    assert lua.eval("#macroList") == 0
    lua.execute("inCombat = false")
    lua.globals().handler(None, "PLAYER_REGEN_ENABLED", None)
    assert lua.eval("#macroList") == 2


def test_cards_line_up_with_the_bar_block_on_any_screen():
    unit = 'EllesmereUIDB.profiles.Default.addons.EllesmereUIUnitFrames'
    seen = []
    for width, height in ((1920, 1080), (2133, 1200), (4267, 1200)):
        e = login(before=f"screenWidth, screenHeight = {width}, {height}").eval
        player, target = f"{unit}.positions.player", f"{unit}.positions.target"
        assert e(f"{player}.x") == e(f"{AB}.barPositions.MainBar.x") and e(f"{target}.x") == -e(f"{player}.x")
        assert e(f"{player}.relPoint") == e(f"{target}.relPoint") == "BOTTOM"
        assert e(f"{unit}.player.frameWidth") + e(f"{unit}.player.healthHeight") + e(f"{unit}.player.powerHeight") == 186, "a card spans four of the twelve columns"
        seen.append(e(f"{player}.y"))
    assert len(set(seen)) == 1


def test_edge_frames_stay_inside_a_centered_16_by_9_area():
    wide = login(before="screenWidth, screenHeight = 4267, 1200").eval
    normal = login().eval
    inset = (4267 - 1200 * 16 / 9) / 2
    questie = "QuestieConfig.profiles.Default.TrackerLocation[4]"
    assert abs(normal(questie) - wide(questie) - inset) < 1e-6


def test_minimap_icons_hide_and_stay_hidden_but_pins_and_zone_text_stay():
    lua = login()
    e = lua.eval
    assert [e(f"mapChildren[{i}].shown") for i in range(1, 7)] == [False, False, False, True, True, True]
    lua.execute("mapChildren[1]:Show()")
    assert e("mapChildren[1].shown") is False and e("#mapChildren[1].hooks") == 1


def test_layout_version_bump_leaves_frames_alone():
    version = re.search(r"version = (\d+),\n\t\tplayer", (ADDON / "Layout.lua").read_text())[1]
    before = f"ForeverKitChar = {{ version = 4, seeded = {{ EllesmereUIUnitFrames = {version}, EllesmereUIRaidFrames = {version}, EllesmereUIMinimap = 3, EllesmereUIActionBars = 2, EllesmereUIBags = 1 }} }}"
    assert login(before=before).eval("EllesmereUIDB.profiles") is None


MENU = """
GameMenuFrame = { CreateFontString = function()
  return { SetPoint = function() end, SetText = function(_, t) menuText = t end }
end }
"""


def test_escape_menu_names_the_install_and_how_to_update():
    e = login(before=MENU, installed='ForeverKitInstall = { commit = "abc", date = "2026-11-17" }').eval
    assert e("menuText") == "Superb WoW Kit, installed 2026-11-17. To update, close WoW and run SuperbWoWKit.exe."
    assert login(before=MENU).eval("menuText") == "Superb WoW Kit. To update, close WoW and run SuperbWoWKit.exe."


def test_ellesmereui_never_asks_for_modules_or_a_look():
    e = login(before="EllesmereUIDB = { styleChoicePending = true }").eval
    assert e("EllesmereUIDB.firstInstallPopupShown") is True
    assert e("EllesmereUIDB.styleChoicePending") is None


def test_minimap_is_seven_modules_wide_in_the_top_right_with_the_tracker_below():
    e = login().eval
    m = 'EllesmereUIDB.profiles.Default.addons.EllesmereUIMinimap.minimap'
    assert e(f"{m}.mapSize") == 327 and e(f"{m}._capturedOnce") is True
    assert e(f"{m}.position.x") == e(f"{m}.position.y") == -24
    assert e("QuestieConfig.profiles.Default.trackerWidthRatio") == 0.2
    assert e(f"{m}.position.point") == "TOPRIGHT" and e(f"{m}.position.relPoint") == "TOPRIGHT"
    tracker = "QuestieConfig.profiles.Default.TrackerLocation"
    assert e(f"{tracker}[5]") < e(f"{m}.position.y") - e(f"{m}.mapSize"), "tracker starts below the map"
    wide = login(before="screenWidth, screenHeight = 4267, 1200").eval
    assert abs(e(f"{m}.position.x") - wide(f"{m}.position.x") - (4267 - 1200 * 16 / 9) / 2) < 1e-6


def test_minimap_and_tracker_move_once_for_characters_already_set_up():
    before = """ForeverKitChar = { version = 4, seeded = {} }
      QuestieConfig = { profiles = { Default = { TrackerLocation = { "TOPRIGHT", "UIParent", "TOPRIGHT", -14, -310 } } } }"""
    e = login(before=before).eval
    assert e("QuestieConfig.profiles.Default.TrackerLocation[5]") < -351
    assert e("ForeverKitChar.seeded.EllesmereUIMinimap") == 3 and e("ForeverKitChar.seeded.Questie") == 3


def test_cpu_report_ranks_loaded_addons_and_saves_them():
    before = """
    Enum = Enum or {}
    C_AddOns = {
      GetNumAddOns = function() return 3 end,
      GetAddOnInfo = function(i) return ({ "Light", "Heavy", "Unloaded" })[i] end,
      IsAddOnLoaded = function(i) return i < 3 end,
    }
    C_AddOnProfiler = { GetAddOnMetric = function(name, metric)
      return ({ Light = { 0.01, 1 }, Heavy = { 2.5, 40 } })[name][metric] end }
    """
    lua = login(before=before)
    lua.execute("Enum.AddOnProfilerMetric = { SessionAverageTime = 1, PeakTime = 2 }")
    lua.execute('SlashCmdList.FOREVERKIT("cpu")')
    e = lua.eval
    assert e("#ForeverKitChar.cpu") == 2
    assert e("ForeverKitChar.cpu[1].name") == "Heavy" and e("ForeverKitChar.cpu[1].peak") == 40
    assert "Heavy" in e("messages[#messages]") or "Light" in e("messages[#messages]")
    assert e("ForeverKitChar.version") is not None, "the report leaves the layout alone"


def test_rails_chat_guide_and_bags_sit_on_the_grid():
    e = login().eval
    chat = "layoutInfo.layouts[1].systems[2]"
    assert e(f"{chat}.anchorInfo.offsetX") == 52 and e(f"{chat}.anchorInfo.offsetY") == 56
    assert [e(f"{chat}.settings[{i}].value") for i in range(1, 5)] == [5, 15, 2, 12]
    assert e(f"{chat}.anchorInfo.offsetY") + 212 == 268, "chat rises to the top of the cards"
    buffs, debuffs = "layoutInfo.layouts[1].systems[3].anchorInfo", "layoutInfo.layouts[1].systems[4].anchorInfo"
    assert e(f"{buffs}.offsetX") == -(24 + 327 + 24) and e(f"{buffs}.offsetY") == -24
    assert e(f"{debuffs}.offsetY") < e(f"{buffs}.offsetY") and e("saves") == 1
    assert e("FTADB.profile.ui.main.w") == 374 and e("FTADB.profile.ui.main.x") == 24
    bags = "EllesmereUIDB.profiles.Default.addons.EllesmereUIBags"
    assert e(f"{bags}.bagsPosition.x") == -24 and e(f"{bags}.bagAnchorCorner") is True
    party = "EllesmereUIDB.profiles.Default.addons.EllesmereUIRaidFrames"
    assert e(f"{party}.partyFrameWidth") + e(f"{party}.partyFrameHeight") == 186
    assert e(f"{party}.partyUnlockPos.x") == e(f"{AB}.barPositions.MainBar.x")


def test_reseeding_clears_values_that_outrank_the_bar_settings():
    before = """EllesmereUIDB = { profiles = { Default = { addons = { EllesmereUIActionBars = { bars = {
      Bar5 = { _savedBarAlpha = 0.3, overrideNumRows = 6, keep = 1 } } } } } } }"""
    e = login(before=before).eval
    assert e(f"{AB}.bars.Bar5._savedBarAlpha") is None and e(f"{AB}.bars.Bar5.overrideNumRows") is None
    assert e(f"{AB}.bars.Bar5.keep") == 1


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_")]
    for name, test in tests:
        test()
        print("ok", name)
    print(len(tests), "passed")
