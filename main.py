import os
import time
import re
import threading
import random
from datetime import datetime
from fastapi import FastAPI
import uvicorn
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, RateLimitError
from database import update_user_welcome, get_user_last_welcome

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Bot is running!"}

class InstagramBot(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        self.cl = None
        self.group_id = ""
        self.admins = []
        self.session_id = ""
        self.cookies = {}
        self.processed_msgs = set()
        self.sent_good_night = False
        self.sent_good_morning = False
        self.current_date = datetime.now().date()

    def load_config(self):
        try:
            if os.path.exists("cookies.txt"):
                with open("cookies.txt", "r") as f:
                    for line in f:
                        if line.startswith("#") or not line.strip(): continue
                        parts = line.strip().split('\t')
                        if len(parts) >= 7:
                            self.cookies[parts[5]] = parts[6]
                self.session_id = self.cookies.get("sessionid", "")
                print("[+] Netscape Cookies loaded.")
            elif os.path.exists("session.txt"):
                with open("session.txt", "r") as f:
                    self.session_id = f.read().strip()
                print("[+] Session ID loaded from session.txt")
            else:
                print("[-] No cookies.txt or session.txt found.")
                self.running = False
                return

            with open("group.txt", "r") as f:
                self.group_id = f.read().strip()
            with open("admins.txt", "r") as f:
                self.admins = [line.strip().replace("@", "") for line in f if line.strip()]
            
        except Exception as e:
            print(f"[-] Config error: {e}")
            self.running = False

    def safe_send(self, text, thread_id=None, reply_to_id=None):
        try:
            target_thread = thread_id if thread_id else self.group_id
            time.sleep(random.uniform(1.5, 3.0))
            
            if reply_to_id:
                try:
                    self.cl.direct_send(text, thread_ids=[target_thread], reply_to_message=reply_to_id)
                except TypeError:
                    self.cl.direct_send(text, thread_ids=[target_thread], replied_to_message_id=reply_to_id)
            else:
                self.cl.direct_send(text, thread_ids=[target_thread])
        except Exception as e:
            print(f"[-] Send Failed: {e}")

    def keep_alive(self):
        while self.running:
            try:
                time.sleep(480) 
                if self.running and self.cl:
                    self.cl.get_timeline_feed()
                    print("[*] Keep-Alive Ping")
            except Exception:
                pass

    def login_and_retry(self):
        while self.running:
            try:
                print("[*] Initializing Instagram Client (No Spoofing)...")
                self.cl = Client()
                
                if self.cookies:
                    # Set cookies safely
                    self.cl.set_settings({"cookies": self.cookies})
                
                print("[*] Logging in...")
                self.cl.login_by_sessionid(self.session_id)
                print(f"[+] Login Successful! @{self.cl.username}")
                return True
            except Exception as e:
                print(f"[-] Login Failed: {e}")
                time.sleep(60)
        return False

    def check_time_events(self):
        now = datetime.now()
        
        if now.date() != self.current_date:
            self.sent_good_night = False
            self.sent_good_morning = False
            self.current_date = now.date()

        if now.hour == 0 and now.minute == 0 and not self.sent_good_night:
            self.safe_send("GOOD NIGHT @everyone TAKE CARE BAD DREAM'S... Susu karke soo jana 💋💦")
            self.sent_good_night = True
            print("[*] Sent Good Night")

        if now.hour == 6 and now.minute == 0 and not self.sent_good_morning:
            self.safe_send("GOOD MORNING @everyone JOO 6 baje ke pehle nhi utha wo G4Y")
            self.sent_good_morning = True
            print("[*] Sent Good Morning")

    def run(self):
        self.load_config()
        if not self.running: return
            
        if not self.login_and_retry(): return

        threading.Thread(target=self.keep_alive, daemon=True).start()
        print("[*] Bot Engine Started.")

        while self.running:
            try:
                self.check_time_events()
                messages = self.cl.direct_messages(amount=10)
                
                for msg in reversed(messages):
                    if msg.id in self.processed_msgs: continue
                    self.processed_msgs.add(msg.id)
                    if len(self.processed_msgs) > 100: self.processed_msgs.pop()

                    if msg.user_id == self.cl.user_id: continue 

                    try:
                        username = self.cl.user_info(msg.user_id).username
                    except Exception:
                        username = "Unknown"
                        
                    text = msg.text.strip() if msg.text else ""
                    user_id = str(msg.user_id)
                    thread_id = msg.thread_id
                    
                    # DM SYSTEM
                    if str(thread_id) != str(self.group_id):
                        if username in self.admins and text.startswith("/message_send "):
                            send_text = text.replace("/message_send ", "")
                            self.safe_send(send_text, thread_id=self.group_id)
                            self.safe_send("Message sent to GC!", thread_id=thread_id, reply_to_id=msg.id)
                        continue 

                    # GC COMMANDS
                    if f"@{self.cl.username}" in text:
                        text = text.replace(f"@{self.cl.username}", "").strip()

                    if text == "/start" and username in self.admins:
                        self.safe_send("BOT IS ACTIVE 🟢", reply_to_id=msg.id)
                        continue

                    if re.search(r'i\s*g\s*n\s*o\s*r\s*e', text, re.IGNORECASE):
                        self.safe_send("AWW BACCHA ISSOKIEE MEIN HU NA APKE LIYE 🥹💋", reply_to_id=msg.id)
                        continue

                    if re.search(r'https:\/\/ig\.me\/', text):
                        self.safe_send("AWWW TERE B44P KI BIWI KI PIC DE RHA KYA ISS GC PE", reply_to_id=msg.id)
                        continue

                    last_welcome = get_user_last_welcome(user_id)
                    now = datetime.now()
                    if not last_welcome or (now - last_welcome).total_seconds() > 6 * 3600:
                        self.safe_send(f"Welcome back to our gc @{username} how are you? 🎈", reply_to_id=msg.id)
                        update_user_welcome(user_id, username)

                time.sleep(random.uniform(3.0, 5.0)) 

            except LoginRequired:
                print("[!] Session expired. Relogging...")
                if not self.login_and_retry(): break
            except RateLimitError:
                time.sleep(120)
            except Exception as e:
                print(f"[!] Error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    bot = InstagramBot()
    bot.start()
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)