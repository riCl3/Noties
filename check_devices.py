import sounddevice as sd

print("=== All Audio Devices ===")
devices = sd.query_devices()
host_apis = sd.query_hostapis()

# Find WASAPI
wasapi_idx = next((i for i, api in enumerate(host_apis) if 'WASAPI' in api['name']), -1)

for i, d in enumerate(devices):
    hostapi_name = host_apis[d['hostapi']]['name']
    is_wasapi = d['hostapi'] == wasapi_idx
    
    print(f"\n[{i}] {d['name']}")
    print(f"    Host API: {hostapi_name}")
    print(f"    Input Channels: {d['max_input_channels']}")
    print(f"    Output Channels: {d['max_output_channels']}")
    print(f"    Default Sample Rate: {d['default_samplerate']}")
    
    # Check if it's a potential loopback device
    if is_wasapi and d['max_input_channels'] > 0:
        if "Speakers" in d['name'] or "Stereo Mix" in d['name']:
            print(f"    >>> POTENTIAL LOOPBACK DEVICE <<<")
