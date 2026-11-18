# Superb WoW Kit

WoW Forever, set up in one click: six addons, a clean layout, and keybinds that work for every class.

**[Download SuperbWoWKit.exe](https://github.com/jackisgolden/superb-wow-kit/releases/latest/download/SuperbWoWKit.exe)**

## Install

1. Close WoW.
2. Run the file. If Windows says it protected your PC, click More info, then Run anyway.
3. Click Install.
4. Start WoW. On the character screen, open AddOns and check they are all ticked.

Your first login sets everything up and says so in chat.

## Update

Open the same file. It says Up to date, or shows an Update button. The Escape menu in game shows when you last installed.

Your settings stay put.

## Other addons

Use CurseForge, WowUp, or a zip, same as always. The kit only touches the folders it installed.

To keep the six addons without the layout, untick Superb WoW Kit in the AddOns list.

## What you get

| Where | What |
|---|---|
| Bottom | Three rows of 12 buttons on 1 to =, Alt, and Ctrl + Shift |
| Bottom right | A faded block for Hearthstone and food, first six on Alt + Q E R F C V |
| Above the bars | Your health on the left, your target on the right, party above you |
| Top right | Minimap, with your quests below it |
| Top left | The levelling guide |
| Bottom left | Chat |

Your normal WoW keys still work. [GUIDE.md](GUIDE.md) shows which job goes on which key, for any class.

| Addon | Does |
|---|---|
| EllesmereUI | Bars, health cards, minimap, bags, world map, auto repair. `/eui` |
| Questie | Quests on your map |
| Follow The Arrow | A free levelling guide with an arrow |
| What's Training | Spells you can learn, in your spellbook. `/wt` |
| Auctionator | A usable Auction House |
| QuestieDB | Questie's data |

| Type | Does |
|---|---|
| `/superb` | Resets your layout, or fits it to a new monitor |
| `/superb cpu` | Lists the addons costing the most time per frame |

## If something breaks

| Problem | Fix |
|---|---|
| Can't find WoW Forever | Install it from Battle.net, or click Pick folder |
| Can't write to the folder | Right-click the file, Run as administrator |
| An addon FAILED | Click Update again |
| Red error in chat | Update, then fully quit and reopen WoW |
| Antivirus deleted the exe | Use [Install.bat](https://github.com/jackisgolden/superb-wow-kit/releases/latest/download/Install.bat), which does the same in a console |

## How it works

| Piece | Job |
|---|---|
| `launcher/SuperbWoWKit.cs` | The exe. Compares the installed commit with `main` and runs the installer. |
| `install.ps1` | Downloads each addon in `addons.tsv` from its author's newest Forever release, with a pinned fallback. Kit files come from one commit. |
| `!ForeverKit/Installed.lua` | Written by the installer: commit, date, and the folders it owns. The next install removes only those it no longer ships. |
| `!ForeverKit/` | The kit addon. `Layout.lua` is the layout as data, applied once per character. `Config.lua` holds binds and settings. `Personal.lua` is yours and survives updates. |
| `tests/` | The kit runs in real Lua against a stubbed WoW API on every push. A daily audit refreshes the pins. |

Nothing writes to WTF, where your settings live.

Every addon comes straight from its author's release. All credit goes to the people who make them.

Jack
