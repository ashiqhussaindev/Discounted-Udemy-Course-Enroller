import threading
import time
import traceback

from tqdm import tqdm

from base import VERSION, LoginException, Scraper, Udemy, scraper_dict
from colors import bw, by, fb, fg, fr

# DUCE-CLI


def create_scraping_thread(site: str):

    code_name = scraper_dict[site]
    try:
        t = threading.Thread(target=getattr(scraper, code_name), daemon=True)
        t.start()

        while getattr(scraper, f"{code_name}_length") == 0:
            time.sleep(0.1)  # Avoid busy waiting
        if getattr(scraper, f"{code_name}_length") == -1:
            raise Exception(f"Error in: {site}")
        progress_bar = tqdm(
            total=getattr(scraper, f"{code_name}_length"), desc=site, leave=False
        )
        prev_progress = -1

        while not getattr(scraper, f"{code_name}_done"):
            time.sleep(0.1)
            current_progress = getattr(scraper, f"{code_name}_progress")
            progress_bar.update(current_progress - prev_progress)
            prev_progress = current_progress

        progress_bar.update(getattr(scraper, f"{code_name}_length") - prev_progress)

    except Exception:
        error = getattr(scraper, f"{code_name}_error", traceback.format_exc())
        print(error)
        print("\nError in: " + site + " " + str(VERSION))


##########################################

udemy = Udemy("cli")
udemy.load_settings()
login_title, main_title = udemy.check_for_update()
if login_title.__contains__("Update"):
    print(by + fr + login_title)

############## MAIN #############

# Updated login flow
login_successful = False
cookies_loaded = False

# First try loading cookies
if udemy.load_cookies():
    try:
        udemy.get_session_info()
        print(fg + f"Logged in via cookies as {udemy.display_name}")
        login_successful = True
        cookies_loaded = True
    except Exception as e:
        print(fr + "Saved cookies expired/invalid, reauthenticating...")

while not login_successful:
    try:
        if udemy.settings["use_browser_cookies"] and not cookies_loaded:
            udemy.fetch_cookies()
            login_method = "Browser Cookies"
        elif udemy.settings["email"] and udemy.settings["password"] and not cookies_loaded:
            email, password = udemy.settings["email"], udemy.settings["password"]
            login_method = "Saved Email/Password"
        else:
            email = input("Email: ")
            password = input("Password: ")
            login_method = "Manual Email/Password"
            
        print(fb + f"Trying to login using {login_method}")
        
        if "Email" in login_method:
            udemy.manual_login(email, password)
            udemy.save_cookies()  # Save cookies after successful login
            
        udemy.get_session_info()
        
        if "Email" in login_method:
            udemy.settings["email"], udemy.settings["password"] = email, password
            udemy.save_settings()
            
        login_successful = True

    except LoginException as e:
        print(fr + str(e))
        if "Browser" in login_method:
            print("Can't login using cookies")
            udemy.settings["use_browser_cookies"] = False
        elif "Email" in login_method:
            udemy.settings["email"], udemy.settings["password"] = "", ""
            udemy.save_settings()

print(fg + f"Logged in as {udemy.display_name}")
user_dumb = udemy.is_user_dumb()
if user_dumb:
    print(bw + fr + "What do you even expect to happen!")
    exit()
if not user_dumb:
    scraper = Scraper(udemy.sites)
try:
    udemy.scraped_data = scraper.get_scraped_courses(create_scraping_thread)
    time.sleep(0.5)
    print("\n")
    udemy.start_enrolling()

    udemy.print(
        f"\nSuccessfully Enrolled: {udemy.successfully_enrolled_c}", color="green"
    )
    udemy.print(
        f"Amount Saved: {round(udemy.amount_saved_c,2)} {udemy.currency.upper()}",
        color="light green",
    )
    udemy.print(f"Already Enrolled: {udemy.already_enrolled_c}", color="blue")
    udemy.print(f"Excluded Courses: {udemy.excluded_c}", color="yellow")
    udemy.print(f"Expired Courses: {udemy.expired_c}", color="red")

except:
    e = traceback.format_exc()
    print(
        (
            "Error",
            e + f"\n\n{udemy.link}\n{udemy.title}" + f"|:|Unknown Error {VERSION}",
        )
    )
input("Press Enter to exit...")
