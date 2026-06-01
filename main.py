import requests
import time
import itertools
import string
import os
import sys
from concurrent.futures import ThreadPoolExecutor

MAX_THREADS = 60  

def get_api_keys():
    if os.path.exists("config.txt"):
        with open("config.txt", "r") as f:
            keys = [line.strip() for line in f if line.strip()]
            if keys: return keys
    print("error: not found api keys in config.txt")
    return []

def load_checked_ids(log_file):
    """extract already checked usernames from log file to avoid rechecking"""
    if not os.path.exists(log_file):
        return set()
    with open(log_file, "r") as f:
        return {line.split("|")[0].strip() for line in f if "|" in line}

def save_log(username, status, id_type):
    """edit file"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{username} | {status} | {timestamp}\n"
    
    with open("log.txt", "a") as f: f.write(f"[{id_type}] " + log_entry)
    with open(f"{id_type}_log.txt", "a") as f: f.write(log_entry)
    
    if status == "Available":
        with open(f"{id_type}_available.txt", "a") as f: f.write(f"{username}\n")
    elif status == "Taken":
        with open(f"{id_type}_unavailable.txt", "a") as f: f.write(f"{username}\n")

def check_username(username, api_key, id_type):
    url = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
    scraperapi_url = f"http://api.scraperapi.com?api_key={api_key}&url={requests.utils.quote(url, safe='')}&residential=true"
    
    try:
        start_time = time.perf_counter()
        response = requests.post(scraperapi_url, json={"username": username}, timeout=15)
        ms = int((time.perf_counter() - start_time) * 1000)
        
        if response.status_code == 200:
            is_taken = response.json().get("taken")
            
            save_status = "Taken" if is_taken else "Available"
            display_status = "unvalid" if is_taken else "valid"
            
            save_log(username, save_status, id_type)
            
            print(f"{username} | {display_status} | {ms}ms")
            
        elif response.status_code == 403:
            print(f"[!] API Key Limit: {api_key[:5]}...")
        elif response.status_code == 429:
            time.sleep(5)
    except:
        pass

def main():
    api_keys = get_api_keys()
    if not api_keys: return
    key_cycle = itertools.cycle(api_keys)

    print("username checker:")
    print("4l | 5n")
    choice = input("select option 4l or 5n: ").strip()

    if choice == "4l":
        id_type = "4l"
        chars = string.ascii_lowercase
        length = 4
    elif choice == "5n":
        id_type = "5n"
        chars = string.digits
        length = 5
    else:
        print("Invalid selection.")
        return

    log_file = f"{id_type}_log.txt"
    checked_ids = load_checked_ids(log_file)
    print(f"[*] {len(checked_ids)} is already checked.")

    all_combinations = ("".join(i) for i in itertools.product(chars, repeat=length))
    
    targets = [item for item in all_combinations if item not in checked_ids]
    print(f"[*] Remaining {len(targets)} items to check. (Ctrl+C to stop)")

    try:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for username in targets:
                executor.submit(check_username, username, next(key_cycle), id_type)
    except KeyboardInterrupt:
        print("\n[!] Interrupt request received. Exiting...")
        os._exit(0)

if __name__ == "__main__":
    main()