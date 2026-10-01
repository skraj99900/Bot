# SK HOST

Telegram bot jo tumhari Python scripts NONSTOP host karta hai (Railway par deploy).

## Railway Variables (zaroori)
- `BOT_TOKEN` : BotFather wala token
- `OWNER_ID`  : tumhari Telegram numeric ID (`/myid` se milegi)

## Volume (zaroori, tabhi redeploy ke baad bhi scripts bachengi)
1. Railway -> apni service -> Volumes -> New Volume, mount path `/data`
2. Variables me add karo: `DATA_DIR` = `/data`

## Script host karna
1. Bot ko `.py` ya `.zip` bhejo (zip ho to `/unzip file.zip`, phir `cd folder`)
2. `pip install -r requirements.txt`
3. `python main.py`  -> 20s se zyada chale to NONSTOP mode on
   (ya seedha `/run python main.py`)

## Nonstop kaise kaam karta hai
- Script crash ho ya band ho jaye -> khud dobara start (3s se shuru, crash-loop me max 120s gap)
- Bot redeploy/restart ho -> saari nonstop scripts khud wapas chalu
- Crash hone par chat me last logs aate hain

## Commands
`/ps` list | `/logs <id>` logs | `/restart <id>` | `/stop <id>` (isse auto-restart bhi band)
