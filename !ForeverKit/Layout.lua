-- The Forever Kit layout, as data. ForeverKit.lua applies it. Everything is built
-- from the action bar block, the way a page is built from one grid unit: frames
-- in the middle hang off the bottom of the screen with the bars, so they keep
-- their spacing at any resolution, and frames on the screen edges stay inside a
-- centered 16:9 area, so an ultrawide keeps them in view. A bar's position is
-- its bottom-left corner, measured from the named screen point.
--
-- Each part has a version. Raise one to re-apply that part for every
-- character. /forever re-applies them all. /forever re-applies it all,
-- which also fits the edges to a new monitor.

local BUTTON = 45
local GAP = 2
local ROW = BUTTON + GAP
local BAR_LEFT = -(12 * BUTTON + 11 * GAP) / 2
local BOTTOM_ROW_TOP = 67

-- How far an ultrawide's edges sit outside the centered 16:9 area.
local edgeInset = math.max(0, (GetScreenWidth() - GetScreenHeight() * 16 / 9) / 2)

local function span(buttons) return buttons * ROW - GAP end

local BLOCK_RIGHT = -BAR_LEFT
local BLOCK_TOP = BOTTOM_ROW_TOP + 2 * ROW
local BLOCK_BOTTOM = BOTTOM_ROW_TOP - BUTTON
local SPACE = 8              -- the gap between neighbouring frames

local CARD_HEALTH = 28
local CARD_POWER = 8
local CARD_HEIGHT = CARD_HEALTH + CARD_POWER
local CARD_SPAN = span(5)    -- two cards leave two buttons free in the middle
local CARD_BOTTOM = BLOCK_TOP + ROW + SPACE      -- clears the stance bar
local CARD_OPACITY = 60

local PARTY_SHIFT = 2 * ROW  -- how far left of the player card the party sits

local MAP_SIZE = 396
local MAP_TOP = 58           -- leaves room for the buff row above the map
local MAP_RIGHT = 27

local XP_HEIGHT = 10

local HIDDEN = { barVisibility = "never", alwaysHidden = true }

local function row()
	return { numIcons = 12, numRows = 1, buttonWidth = BUTTON, buttonHeight = BUTTON, buttonPadding = GAP }
end

local function corner(x, y)
	return { point = "BOTTOMLEFT", relPoint = "BOTTOM", x = x, y = y }
end

local HEALTH_GREEN = { r = 37 / 255, g = 193 / 255, b = 29 / 255 }

local function card(side)
	return {
		frameWidth = CARD_SPAN - CARD_HEIGHT, healthHeight = CARD_HEALTH, powerHeight = CARD_POWER,
		healthBarOpacity = CARD_OPACITY, powerBarOpacity = CARD_OPACITY,
		showPortrait = true, portraitStyle = "attached", portraitSide = side,
	}
end

ForeverKitLayout = {
	version = 2,
	profile = "Forever Kit",

	-- EllesmereUI action bars. Bar2, Bar3 and Bar5 are the game's bottom left,
	-- bottom right and left bars, which the Alt, Ctrl + Shift and utility keys press.
	actionBars = {
		version = 1,
		bars = {
			MainBar = row(), Bar2 = row(), Bar3 = row(),
			Bar5 = {
				numIcons = 12, numRows = 6, buttonWidth = BUTTON, buttonHeight = BUTTON, buttonPadding = GAP,
				barVisibility = "mouseover", mouseoverEnabled = true, mouseoverAlpha = 0.3,
			},
			Bar4 = HIDDEN, Bar6 = HIDDEN, Bar7 = HIDDEN, Bar8 = HIDDEN, MicroBar = HIDDEN, BagBar = HIDDEN,
			XPBar = { width = span(12), height = XP_HEIGHT },
		},
		positions = {
			XPBar = { point = "BOTTOM", relPoint = "BOTTOM", x = 0, y = BLOCK_BOTTOM - SPACE / 2 - XP_HEIGHT },
			MainBar = corner(BAR_LEFT, BLOCK_BOTTOM),
			Bar2 = corner(BAR_LEFT, BLOCK_BOTTOM + ROW),
			Bar3 = corner(BAR_LEFT, BLOCK_BOTTOM + 2 * ROW),
			StanceBar = corner(BAR_LEFT, BLOCK_TOP + SPACE),
			Bar5 = { point = "BOTTOMLEFT", relPoint = "BOTTOMRIGHT", x = -104 - edgeInset, y = 40 },
		},
	},

	-- The kit hides addon icons on the minimap on every login. Each addon's menu
	-- stays on its chat command.
	minimapIcons = { "^LibDBIcon10_", "MinimapButton$", "MinimapBadge$" },

	-- The EllesmereUI minimap, by its top right corner. Its size slider runs
	-- from 100 to 600, and 198 is the stock size.
	minimap = { version = 1, size = MAP_SIZE, x = -MAP_RIGHT - edgeInset, y = -MAP_TOP },

	-- The quest tracker hangs below the minimap.
	questie = {
		version = 1,
		location = { "TOPRIGHT", "UIParent", "TOPRIGHT", -14 - edgeInset, -(MAP_TOP + MAP_SIZE + 2 * SPACE) },
	},

	-- Raid-style party frames, just left of the player frame.
	party = { point = "TOPRIGHT", relativePoint = "CENTER", x = -480, y = -240 },

	-- EllesmereUI cards sit flush with the left and right of the bar block, and
	-- the party stacks up from above the player card.
	frames = {
		version = 4,
		player = card("left"),
		playerHealth = { healthClassColored = false, customFillColor = HEALTH_GREEN },
		target = card("right"),
		positions = {
			player = { point = "BOTTOMLEFT", relPoint = "BOTTOM", x = BAR_LEFT, y = CARD_BOTTOM },
			target = { point = "BOTTOMRIGHT", relPoint = "BOTTOM", x = BLOCK_RIGHT, y = CARD_BOTTOM },
		},
		party = {
			partyFrameWidth = span(3), partyFrameHeight = 30, partyHideSelf = true,
			partyFlipGrowth = true, healthBarOpacity = CARD_OPACITY,
			healthColorMode = "custom", customFillColor = HEALTH_GREEN, healthBarTexture = "none",
			showPowerBar = true, powerHeight = 4,
			powerShowForTank = true, powerShowForHealer = true, powerShowForDPS = true,
			healthTextMode = "percent", healthTextPosition = "right",
			partyPortraitStyle = "attached", partyPortraitSide = "left",
			partyUnlockPos = {
				point = "BOTTOMLEFT", relPoint = "BOTTOM",
				x = BAR_LEFT - PARTY_SHIFT, y = CARD_BOTTOM + CARD_HEIGHT + SPACE,
			},
		},
	},
}
