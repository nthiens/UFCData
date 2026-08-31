import time
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

## For windows, use task scheduler
## 1. In the VS Code terminal, run >>where python
##  C:\Users\Juno\AppData\Local\Microsoft\WindowsApps\python3.10.exe
## 2. Open task scheduler and create a basic task
## 3. Choose any name and trigger weekly on Monday
## 4. Start a program
##      For program, paste in 1.
##      For add arguments, enter this python file:
##      "C:\Users\Juno\Desktop\UFCData\scraper\scheduler.py"
##      For start in, enter C:\Users\Juno\Desktop\UFCData

TIME_FILE = Path(r"C:\Users\Juno\Desktop\UFCData\scraper\scraper_data\next_event_time.txt")
PYTHON = r"C:\Users\Juno\AppData\Local\Microsoft\WindowsApps\python3.10.exe"

pre_fight_script = r"C:\Users\Juno\Desktop\UFCData\scraper\updater.py"
post_fight_script = [
    r"C:\Users\Juno\Desktop\UFCData\scraper\updater.py",
    r"C:\Users\Juno\Desktop\UFCData\scraper\next_event.py",
]

pre_fight_time = 5 ## In minutes
post_fight_time = 8 ## In hours

def read_scheduled_time():
    with open(TIME_FILE, "r") as file:
        time_string = file.read().strip()
    return datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")


def pre_fight():
    print("Running pre-fight script...")
    subprocess.Popen([PYTHON, pre_fight_script])

def post_fight():
    print("Running post-fight script...")
    for script in post_fight_script:
        subprocess.Popen([PYTHON, script])

scheduled_time = read_scheduled_time()
pre_fight_time = scheduled_time - timedelta(minutes=pre_fight_time)
post_fight_time = scheduled_time + timedelta(hours=post_fight_time)

print(f"Scheduled time: {scheduled_time}")
print(f"Pre-fight scripts will run: {pre_fight_time}")
print(f"Post-fight script will run: {post_fight_time}")

pre_fight_ran = False
post_fight_ran = False

while True:
    now = datetime.now()
    # 5 minutes before
    if now >= pre_fight_time and not pre_fight_ran:
        pre_fight()
        pre_fight_ran = True
    # 8 hours after
    if now >= post_fight_time and not post_fight_ran:
        post_fight()
        post_fight_ran = True
    # Stop once both jobs have run
    if pre_fight_ran and post_fight_ran:
        break
    time.sleep(1)
print("All scheduled scripts have run.")