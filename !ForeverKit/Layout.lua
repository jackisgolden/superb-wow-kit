-- The Superb WoW Kit layout, as data. ForeverKit.lua applies it.
--
-- One module builds the page: an action button plus its gap. The screen is a
-- three by three grid. The middle column holds the action bars, twelve modules
-- wide, and each side column holds a rail eight modules wide, with the
-- minimap at seven and chat at eleven. Nothing sits
-- closer to a screen edge than one margin, and the middle of the screen stays
-- empty.
--
--   guide          arrow            minimap
--                                   quest tracker
--
--   chat      player . target       damage meter
--             three rows of twelve  utility buttons
--
-- The twelve columns split into three groups of four: the player card, a gap
-- and the target card. The utility buttons are one more group of four on the
-- same three row lines. Chat rises to the top line of the cards.
--
-- Frames in the middle hang off the bottom of the screen with the bars, so
-- they keep their spacing at any resolution, and the rails stay inside a
-- centered 16:9 area, so an ultrawide keeps them in view. A bar's position is
-- its bottom-left corner, measured from the named screen point.
--
-- Each part has a version. Raise one to re-apply that part for every
-- character. /superb re-applies them all, which also fits the rails to a
-- new monitor.

local BUTTON = 45
local GAP = 2
local ROW = BUTTON + GAP
local MARGIN = 24            -- the least distance from any screen edge
local SPACE = 8              -- the gap between neighbouring frames

local function span(buttons) return buttons * ROW - GAP end

-- How far an ultrawide's edges sit outside the centered 16:9 area.
local edgeInset = math.max(0, (GetScreenWidth() - GetScreenHeight() * 16 / 9) / 2)
local EDGE = MARGIN + edgeInset

local RAIL = span(8)
local MAP = span(7)
local THIRD = span(4)
local BLOCK_HEIGHT = span(3)

local XP_HEIGHT = 10
local BAR_LEFT = -span(12) / 2
local BLOCK_RIGHT = -BAR_LEFT
local BLOCK_BOTTOM = MARGIN + XP_HEIGHT + SPACE / 2
local BLOCK_TOP = BLOCK_BOTTOM + BLOCK_HEIGHT

local CARD_HEALTH = 28
local CARD_POWER = 8
local CARD_HEIGHT = CARD_HEALTH + CARD_POWER

-- The swing timers hang under the player card's health bar, as wide as it:
-- main hand first, then off hand or ranged. The game's bar is at least 213
-- wide and 15 tall, so it draws at 60% scale.
local SWING_SCALE = 0.6
local SWING_HEIGHT = 15 * SWING_SCALE
local SWING_WIDTH = THIRD - CARD_HEIGHT
local SWING_BOTTOM = BLOCK_TOP + ROW + SPACE    -- clears the stance bar and the cast bar
local CARD_BOTTOM = SWING_BOTTOM + 2 * (SWING_HEIGHT + GAP)
local CARD_TOP = CARD_BOTTOM + CARD_HEIGHT
local CARD_OPACITY = 60

local PARTY_HEIGHT = 30

-- The right rail, from the bottom: utility buttons, damage meter, then the
-- tooltip and the bags.
local METER_BOTTOM = BLOCK_TOP + SPACE
local RAIL_STACK_TOP = METER_BOTTOM + BLOCK_HEIGHT + SPACE

local TRACKER_TOP = MARGIN + MAP + 2 * SPACE
local TRACKER_PAD = 13       -- Questie's own padding right of its text

local CHAT_BUTTONS = 28      -- the column of chat buttons left of the chat frame
local CHAT_INPUT = 32        -- the typing box under the chat frame
local CHAT_WIDTH = span(11)
local CHAT_BOTTOM = MARGIN + CHAT_INPUT
local CHAT_HEIGHT = CARD_TOP - CHAT_BOTTOM

local RESTING_ALPHA = 0.3

local HIDDEN = { barVisibility = "never", alwaysHidden = true }

local function row()
	return { numIcons = 12, numRows = 1, buttonWidth = BUTTON, buttonHeight = BUTTON, buttonPadding = GAP }
end

local function corner(x, y)
	return { point = "BOTTOMLEFT", relPoint = "BOTTOM", x = x, y = y }
end

local function swing(index, y)
	return {
		system = "SwingTimer", indexNames = "EditModeSwingTimerSystemIndices", index = index,
		point = "BOTTOMLEFT", relPoint = "BOTTOM", x = BAR_LEFT + CARD_HEIGHT, y = y,
		settingNames = "EditModeSwingTimerSetting",
		settings = {
			Scale = (SWING_SCALE * 100 - 50) / 10, Visibility = 1,     -- in combat
			Width = math.floor(SWING_WIDTH / SWING_SCALE + 0.5) - 213, Height = 0,
			ShowBarTitle = 0, ShowTime = 0,
		},
	}
end

local HEALTH_GREEN = { r = 37 / 255, g = 193 / 255, b = 29 / 255 }

-- A card's portrait is a square as tall as the card, attached outside its width.
local function card(side)
	return {
		frameWidth = THIRD - CARD_HEIGHT, healthHeight = CARD_HEALTH, powerHeight = CARD_POWER,
		healthBarOpacity = CARD_OPACITY, powerBarOpacity = CARD_OPACITY,
		showPortrait = true, portraitStyle = "attached", portraitSide = side,
	}
end

ForeverKitLayout = {
	version = 5,
	profile = "Forever Kit",

	-- EllesmereUI action bars. Bar2, Bar3 and Bar5 are the game's bottom left,
	-- bottom right and left bars, which the Alt, Ctrl + Shift and utility keys press.
	-- Bar5 rests faded and lights up under the mouse: its opacity is the resting
	-- value, and the fade condition lifts it to full.
	actionBars = {
		version = 2,
		bars = {
			MainBar = row(), Bar2 = row(), Bar3 = row(),
			Bar5 = {
				numIcons = 12, numRows = 3, buttonWidth = BUTTON, buttonHeight = BUTTON, buttonPadding = GAP,
				barVisibility = "always", alwaysHidden = false, mouseoverEnabled = false,
				mouseoverAlpha = RESTING_ALPHA, fadeMaxAlpha = 1, advancedFadeConditions = { mouseover = true },
			},
			Bar4 = HIDDEN, Bar6 = HIDDEN, Bar7 = HIDDEN, Bar8 = HIDDEN, MicroBar = HIDDEN, BagBar = HIDDEN,
			XPBar = { width = span(12), height = XP_HEIGHT },
		},
		positions = {
			XPBar = { point = "BOTTOM", relPoint = "BOTTOM", x = 0, y = MARGIN },
			MainBar = corner(BAR_LEFT, BLOCK_BOTTOM),
			Bar2 = corner(BAR_LEFT, BLOCK_BOTTOM + ROW),
			Bar3 = corner(BAR_LEFT, BLOCK_BOTTOM + 2 * ROW),
			StanceBar = corner(BAR_LEFT, BLOCK_TOP + SPACE),
			Bar5 = { point = "BOTTOMLEFT", relPoint = "BOTTOMRIGHT", x = -EDGE - THIRD, y = BLOCK_BOTTOM },
		},
	},

	-- The kit hides addon icons on the minimap on every login. Each addon's menu
	-- stays on its chat command.
	minimapIcons = { "^LibDBIcon10_", "MinimapButton$", "MinimapBadge$" },

	-- The EllesmereUI minimap, by its top right corner, seven modules wide.
	-- Its size slider runs from 100 to 600, and 198 is the stock size.
	minimap = { version = 3, size = MAP, x = -EDGE, y = -MARGIN },

	-- The quest tracker hangs below the minimap at Questie's own size limits.
	questie = {
		version = 3,
		location = { "TOPRIGHT", "UIParent", "TOPRIGHT", TRACKER_PAD - EDGE, -TRACKER_TOP },
		settings = {
			trackerWidthRatio = 0.2,
			trackerHeightRatio = 0.5,
		},
	},

	-- Follow The Arrow: the guide window in the top left, one rail wide, with
	-- the arrow on the screen's centre line.
	guide = {
		version = 1,
		ui = {
			main = { point = "TOPLEFT", x = EDGE, y = -MARGIN, w = RAIL },
			arrow = { point = "TOP", relPoint = "TOP", x = 0, y = -MARGIN },
			mainBgAlpha = 0.35,
		},
	},

	-- EllesmereUI bags open above the damage meter and grow up and left.
	bags = {
		version = 1,
		bagAnchorCorner = true,
		bagsPosition = { point = "BOTTOMRIGHT", relativePoint = "BOTTOMRIGHT", x = -EDGE, y = RAIL_STACK_TOP, corner = true },
	},

	-- Frames the game places through Edit Mode, each by the named corner.
	-- Chat sits beside its buttons and above its typing box, which lands on
	-- the bottom margin. Buffs run left from the minimap along the top margin.
	editMode = {
		{
			system = "ChatFrame", point = "BOTTOMLEFT", x = EDGE + CHAT_BUTTONS, y = CHAT_BOTTOM,
			settingNames = "EditModeChatFrameSetting",
			settings = {
				WidthHundreds = math.floor(CHAT_WIDTH / 100), WidthTensAndOnes = CHAT_WIDTH % 100,
				HeightHundreds = math.floor(CHAT_HEIGHT / 100), HeightTensAndOnes = CHAT_HEIGHT % 100,
			},
		},
		{
			system = "AuraFrame", indexNames = "EditModeAuraFrameSystemIndices", index = "BuffFrame",
			point = "TOPRIGHT", x = -EDGE - MAP - MARGIN, y = -MARGIN,
		},
		{
			system = "AuraFrame", indexNames = "EditModeAuraFrameSystemIndices", index = "DebuffFrame",
			point = "TOPRIGHT", x = -EDGE - MAP - MARGIN, y = -MARGIN - 3 * ROW,
		},
		{ system = "DamageMeter", point = "BOTTOMRIGHT", x = -EDGE, y = METER_BOTTOM },
		swing("MainHand", SWING_BOTTOM + SWING_HEIGHT + GAP),
		swing("OffHand", SWING_BOTTOM),
		swing("Ranged", SWING_BOTTOM),
		{ system = "HudTooltip", point = "BOTTOMRIGHT", x = -EDGE, y = RAIL_STACK_TOP },
	},

	-- Raid-style party frames, just left of the player frame.
	party = { point = "TOPRIGHT", relativePoint = "CENTER", x = -480, y = -240 },

	-- EllesmereUI cards take the outer thirds of the bar block, and the party
	-- stacks up from the player card at the same width. Target of target sits
	-- just right of the target card, level with its health bar.
	frames = {
		version = 7,
		player = card("left"),
		playerHealth = { healthClassColored = false, customFillColor = HEALTH_GREEN },
		target = card("right"),
		targettarget = { frameWidth = span(2), healthHeight = CARD_HEALTH, healthBarOpacity = CARD_OPACITY },
		positions = {
			player = { point = "BOTTOMLEFT", relPoint = "BOTTOM", x = BAR_LEFT, y = CARD_BOTTOM },
			target = { point = "BOTTOMRIGHT", relPoint = "BOTTOM", x = BLOCK_RIGHT, y = CARD_BOTTOM },
			targettarget = { point = "BOTTOMLEFT", relPoint = "BOTTOM", x = BLOCK_RIGHT + SPACE, y = CARD_BOTTOM + CARD_POWER },
		},
		party = {
			partyFrameWidth = THIRD - PARTY_HEIGHT, partyFrameHeight = PARTY_HEIGHT, partyHideSelf = true,
			partyFlipGrowth = true, healthBarOpacity = CARD_OPACITY,
			healthColorMode = "custom", customFillColor = HEALTH_GREEN, healthBarTexture = "none",
			showPowerBar = true, powerHeight = 4,
			powerShowForTank = true, powerShowForHealer = true, powerShowForDPS = true,
			healthTextMode = "percent", healthTextPosition = "right",
			partyPortraitStyle = "attached", partyPortraitSide = "left",
			partyUnlockPos = { point = "BOTTOMLEFT", relPoint = "BOTTOM", x = BAR_LEFT, y = CARD_TOP + SPACE },
		},
	},
}
