# Instagram GC Bot

Ye ek simple Instagram Group Chat bot hai jo Render pe host hota hai.

## Features
- 6 Ghante baad Welcome Back message.
- "Ignore" word pe reply.
- Promotion link (ig.me) pe reply.
- Raat 12 baje Good Night aur subah 6 baje Good Morning.
- Admin `/start` command aur DM se `/message_send` command.

## Setup Instructions
1. GitHub pe is repo ko push karein.
2. Render pe new Web Service banayein.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python main.py`

## Configuration
- `session.txt` mein Instagram Session ID daalein.
- `group.txt` mein Group Thread ID daalein.
- `admins.txt` mein Admin Usernames (line by line) daalein.