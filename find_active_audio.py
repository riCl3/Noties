import sounddevice as sd
import numpy as np
import time

def get_audio_level(device_id):
    """Records 0.5s of audio and returns max amplitude."""
    max_level = 0
    
    def callback(indata, frames, time, status):
        nonlocal max_level
        current = np.max(np.abs(indata))
        if current > max_level:
            max_level = current
            
    try:
        # Try to open stream
        with sd.InputStream(device=device_id, channels=2, callback=callback, blocksize=4000):
            sd.sleep(500) # Listen for 0.5 seconds
            
    except Exception as e:
        return -1 # Device unavailable/error
        
    return max_level

print("Scanning for ACTIVE audio devices (playing sound)...")
print("-" * 60)
print(f"{'ID':<4} {'Level':<10} {'Device Name'}")
print("-" * 60)

devices = sd.query_devices()
host_apis = sd.query_hostapis()
wasapi_index = next((i for i, api in enumerate(host_apis) if 'WASAPI' in api['name']), -1)

found_active = False

for i, d in enumerate(devices):
    # Only check input devices or WASAPI loopback candidates
    is_input = d['max_input_channels'] > 0
    is_wasapi = d['hostapi'] == wasapi_index
    
    if is_input:
        # Check level
        level = get_audio_level(i)
        
        # Format visual bar
        if level < 0:
            bar = "[ERROR]"
        else:
            bar_len = int(level * 20)
            bar = "|" + "=" * bar_len + "-" * (20 - bar_len) + "|"
            
        if level > 0.01 or (is_wasapi and ("Speakers" in d['name'] or "Stereo" in d['name'])):
             marker = ""
             if level > 0.01: 
                 marker = ">> ACTIVE! <<"
                 found_active = True
             if is_wasapi and ("Speakers" in d['name'] or "Stereo" in d['name']):
                 marker += " [Loopback Candidate]"
             
             print(f"{i:<4} {bar:<10} {d['name'][:40]} {marker}")

print("-" * 60)
if not found_active:
    print("\n[WARN] NO ACTIVE AUDIO FOUND!")
    print("Please ensure:")
    print("1. Music/Video is currently PAYLING on your system")
    print("2. Volume is turned up")
else:
    print("\n[OK] Found active audio! Use the ID marked '>> ACTIVE! <<' in the app.")
