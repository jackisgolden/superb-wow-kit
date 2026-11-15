-- The Forever Kit layout, as data. ForeverKit.lua applies it. Everything is built
-- from the action bar block, the way a page is built from one grid unit: frames
-- in the middle hang off the bottom of the screen with the bars, so they keep
-- their spacing at any resolution, and frames on the screen edges stay inside a
-- centered 16:9 area, so an ultrawide keeps them in view. Bartender4 positions
-- are a bar's top-left corner, measured from the named screen point.
--
-- Raise VERSION to re-apply this for every character. Raise frames.version,
-- minimap.version, or questie.version to re-apply only that part. /forever re-applies it all,
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

	bartender = {
		-- Bar ids are Bartender4's. Bar 1 is the bottom row.
		bars = {
			[1] = { rows = 1, x = BAR_LEFT, y = BOTTOM_ROW_TOP },
			[6] = { rows = 1, x = BAR_LEFT, y = BOTTOM_ROW_TOP + ROW },
			[5] = { rows = 1, x = BAR_LEFT, y = BOTTOM_ROW_TOP + 2 * ROW },
			[4] = {
				rows = 6, x = -104 - edgeInset, y = 320, point = "BOTTOMRIGHT",
				fadeout = true, fadeoutalpha = 0.3,
			},
		},
		disabledBars = { 2, 3 },
		hidden = { "BlizzardArt", "BagBar", "MicroMenu" },
		placed = {
			StatusTrackingBar = { x = -285, y = 20 },
			StanceBar = { x = BAR_LEFT, y = BOTTOM_ROW_TOP + 2 * ROW + 40 },
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
