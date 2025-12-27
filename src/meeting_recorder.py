# meeting_recorder.py
import subprocess, os, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import whisper
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

OUTPUT_AUDIO = "last_meeting_recording.wav"
OUTPUT_SUMMARY = "last_meeting_summary.txt"


# === Minimal Transcriber Class ===
class AudioTranscriber:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("Loading Whisper model...")
        self.whisper_model = whisper.load_model("base")
        print("Whisper loaded.")

    def process_audio(self, audio_path):
        print("Transcribing...")
        transcript = self.whisper_model.transcribe(audio_path)["text"]
        print("Summarizing...")
        prompt = f"""Summarize the following meeting transcript:\n\n{transcript}"""
        summary = self.model.generate_content(prompt).text
        return {"transcript": transcript, "summary": summary}


# === Global instance ===
transcriber = None


def initialize_transcriber():
    global transcriber
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Gemini API key not found in environment or .env file.")
    transcriber = AudioTranscriber(api_key.strip())


def check_exists_by_xpath(driver, xpath, timeout=5):
    """Check if element exists by xpath"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except (NoSuchElementException, TimeoutException):
        return False


def check_exists_by_id(driver, element_id, timeout=5):
    """Check if element exists by ID"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, element_id))
        )
        return True
    except (NoSuchElementException, TimeoutException):
        return False


# === Browser + Meeting Logic ===
def setup_driver():
    options = Options()
    options.add_argument("--use-fake-ui-for-media-stream")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")

    # Allow microphone and camera access
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.media_stream_mic": 1,
        "profile.default_content_setting_values.media_stream_camera": 1,
        "profile.default_content_setting_values.geolocation": 1,
        "profile.default_content_setting_values.notifications": 1
    })

    return webdriver.Chrome(service=Service(), options=options)


def manual_login_to_google(driver):
    """Guide user through manual Google login"""
    print("🔐 Starting manual Google login process...")

    try:
        # Go to Google login page
        driver.get("https://accounts.google.com/signin")
        time.sleep(3)

        print("=" * 60)
        print("🔐 MANUAL LOGIN REQUIRED")
        print("=" * 60)
        print("Google has opened in your browser.")
        print("Please complete the following steps:")
        print("1. Enter your email address")
        print("2. Click 'Next'")
        print("3. Enter your password")
        print("4. Click 'Next'")
        print("5. Complete any 2FA if required")
        print("6. Wait for login to complete")
        print("=" * 60)
        print("⏳ Waiting for you to complete login...")
        print("The bot will automatically continue once you're logged in.")
        print("=" * 60)

        # Wait for login completion (check for various post-login URLs)
        login_complete = False
        max_wait_time = 300  # 5 minutes
        start_time = time.time()

        while not login_complete and (time.time() - start_time) < max_wait_time:
            current_url = driver.current_url.lower()

            # Check if we're on a post-login page
            if any(indicator in current_url for indicator in [
                "myaccount.google.com",
                "accounts.google.com/signin/oauth",
                "accounts.google.com/b/0/ManageAccount",
                "gmail.com",
                "drive.google.com"
            ]) and "signin" not in current_url:
                login_complete = True
                break

            # Also check if we can access Google services
            try:
                # Try to find elements that indicate successful login
                if driver.find_elements(By.XPATH, "//a[contains(@href,'myaccount.google.com')]") or \
                        driver.find_elements(By.XPATH, "//div[@data-ogsr-up='']") or \
                        driver.find_elements(By.XPATH, "//*[contains(@aria-label,'Google Account')]"):
                    login_complete = True
                    break
            except:
                pass

            time.sleep(2)
            print(f"⏳ Still waiting... ({int(time.time() - start_time)}s elapsed)")

        if login_complete:
            print("✅ Login detected! Proceeding to meeting...")
            return True
        else:
            print("⏰ Login wait timeout. Proceeding anyway...")
            print("If you're not logged in, you may need to join the meeting manually.")
            return False

    except Exception as e:
        print(f"❌ Login process error: {str(e)}")
        return False


def join_meeting_with_manual_login(driver, meeting_url, use_login=False):
    """Join Google Meet with optional manual login"""
    print(f"🚀 Starting meeting join process...")

    # If login requested, do manual login first
    if use_login:
        login_success = manual_login_to_google(driver)
        if login_success:
            print("✅ Login completed successfully!")
        else:
            print("⚠️ Login may not be complete, but proceeding to meeting...")
        time.sleep(2)

    # Navigate to meeting
    print(f"🎯 Navigating to meeting: {meeting_url}")
    driver.get(meeting_url)
    time.sleep(10)

    print("=" * 60)
    print("🎥 MEETING JOIN PROCESS")
    print("=" * 60)
    print("The meeting page has loaded.")
    print("Please complete the following if needed:")
    print("1. Review camera/microphone permissions")
    print("2. Click 'Join now' or 'Ask to join' if not automatic")
    print("3. Wait for host approval if required")
    print("=" * 60)
    print("⏳ Bot will automatically continue in 20 seconds...")
    print("Or click join manually if needed.")
    print("=" * 60)

    # Wait a bit for manual intervention if needed
    time.sleep(20)

    try:
        # Try to find join button and click if available
        join_selectors = [
            "//span[contains(text(),'Join now')]",
            "//button[contains(@aria-label,'Join')]",
            "//div[contains(text(),'Join now')]",
            "//span[contains(text(),'Ask to join')]",
            "//button[contains(text(),'Join now')]"
        ]

        joined = False
        for selector in join_selectors:
            if check_exists_by_xpath(driver, selector, timeout=3):
                try:
                    join_button = driver.find_element(By.XPATH, selector)
                    join_button.click()
                    print("✅ Automatically clicked join button")
                    joined = True
                    break
                except:
                    continue

        if not joined:
            print("ℹ️ No join button found - assuming already joined or waiting for approval")

        time.sleep(5)

        # Try to control camera and microphone
        print("🎛️ Attempting to control camera and microphone...")

        try:
            # Turn off camera
            camera_selectors = [
                "//button[@aria-label='Turn off camera (ctrl + e)']",
                "//button[contains(@aria-label,'Turn off camera')]",
                "//button[contains(@aria-label,'camera')][@data-is-muted='false']",
                "//div[@aria-label='Turn off camera']"
            ]

            for selector in camera_selectors:
                if check_exists_by_xpath(driver, selector, timeout=2):
                    try:
                        camera_button = driver.find_element(By.XPATH, selector)
                        driver.execute_script("arguments[0].click();", camera_button)
                        print("✅ Camera turned off")
                        break
                    except:
                        continue

            time.sleep(1)

            # Turn off microphone
            mic_selectors = [
                "//button[@aria-label='Turn off microphone (ctrl + d)']",
                "//button[contains(@aria-label,'Turn off microphone')]",
                "//button[contains(@aria-label,'microphone')][@data-is-muted='false']",
                "//div[@aria-label='Turn off microphone']"
            ]

            for selector in mic_selectors:
                if check_exists_by_xpath(driver, selector, timeout=2):
                    try:
                        mic_button = driver.find_element(By.XPATH, selector)
                        driver.execute_script("arguments[0].click();", mic_button)
                        print("✅ Microphone turned off")
                        break
                    except:
                        continue

        except Exception as e:
            print(f"⚠️ Could not control camera/mic automatically: {str(e)}")
            print("Please manually turn off camera/microphone if needed.")

        print("✅ Meeting join process completed!")
        return True

    except Exception as e:
        print(f"❌ Error in meeting join process: {str(e)}")
        return False


# === Audio Recording ===
def record_audio(duration_seconds):
    devices = [
        "Stereo Mix (Realtek(R) Audio)",
        "Microphone Array (Realtek(R) Audio)",
        "Microphone (Realtek(R) Audio)",
        "Default"
    ]
    print("🎙️ Available devices to try:", devices)

    for device in devices:
        print(f"🔄 Trying device: {device}")
        if device == "Default":
            cmd = [
                "ffmpeg", "-y",
                "-f", "dshow",
                "-i", "audio=",
                "-t", str(duration_seconds),
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                OUTPUT_AUDIO
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "dshow",
                "-i", f"audio={device}",
                "-t", str(duration_seconds),
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                OUTPUT_AUDIO
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(OUTPUT_AUDIO) and os.path.getsize(OUTPUT_AUDIO) > 10000:
            print(f"✅ Recording succeeded with: {device}")
            return OUTPUT_AUDIO
        else:
            print(f"❌ Failed with: {device}")
            if result.stderr:
                print("Error:", result.stderr[:200])

    print("❌ All audio devices failed. Please check device settings or permissions.")
    return None


# === Entry Point from GUI ===
def record_and_process_meeting(meeting_url: str, duration_minutes: int, use_login: bool = False):
    """
    Record and process meeting with optional manual login

    Args:
        meeting_url: Google Meet URL
        duration_minutes: Recording duration in minutes
        use_login: Whether to go through login process first
    """
    driver = None
    try:
        print("🚀 Starting meeting recording process...")

        # Initialize transcriber
        initialize_transcriber()

        # Setup browser
        driver = setup_driver()

        # Join meeting (with optional manual login)
        success = join_meeting_with_manual_login(driver, meeting_url, use_login)
        if not success:
            return "❌ Failed to join meeting.", "", ""

        # Give user time to ensure they're properly in the meeting
        print("=" * 60)
        print("🎙️ RECORDING PREPARATION")
        print("=" * 60)
        print(f"Recording will start in 10 seconds for {duration_minutes} minutes.")
        print("Please ensure:")
        print("- You are successfully in the meeting")
        print("- Audio is working properly")
        print("- Meeting has started")
        print("=" * 60)

        # Countdown
        for i in range(10, 0, -1):
            print(f"Recording starts in {i} seconds...")
            time.sleep(1)

        # Record audio
        duration_seconds = duration_minutes * 60
        print(f"🎙️ 🔴 RECORDING STARTED - Duration: {duration_minutes} minutes")
        print("=" * 60)

        audio_file = record_audio(duration_seconds)

        print("=" * 60)
        print("🎙️ ⏹️ RECORDING COMPLETED")
        print("=" * 60)

        if not audio_file:
            return "❌ Recording failed - no audio captured.", "", ""

        print("✅ Recording completed, processing transcript and summary...")

        # Process audio
        results = transcriber.process_audio(audio_file)

        # Save summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
            f.write(f"Meeting Summary - {timestamp}\n")
            f.write("=" * 50 + "\n\n")
            f.write("TRANSCRIPT:\n")
            f.write("-" * 20 + "\n")
            f.write(results["transcript"])
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("SUMMARY:\n")
            f.write("-" * 20 + "\n")
            f.write(results["summary"])

        print(f"📄 Summary saved to: {OUTPUT_SUMMARY}")
        print("✅ Meeting processing completed successfully!")

        return "✅ Meeting processed successfully!", results["transcript"], results["summary"]

    except Exception as e:
        print(f"❌ Error in meeting process: {str(e)}")
        return f"❌ Error: {e}", "", ""

    finally:
        if driver:
            try:
                print("Closing browser in 5 seconds...")
                time.sleep(5)
                driver.quit()
                print("🔄 Browser closed")
            except:
                pass