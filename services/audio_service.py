import sounddevice as sd
import numpy as np
import threading
import queue
import time
import soundfile as sf
import tempfile
import os

class AudioRecorder:
    def __init__(self, chunk_duration=30):
        self.chunk_duration = chunk_duration
        self.sample_rate = 48000
        self.channels = 2
        self.running = False  # Stream is active
        self.capturing = False # Actually saving audio to file
        self.audio_queue = queue.Queue()
        self._thread = None
        self._stop_event = threading.Event()
        self.device_map = {}
        self.device_id = None
        self.current_chunk_data = [] # Buffer for numpy arrays
        self.chunk_start_time = 0
        self.current_level = 0

    def get_input_devices(self):
        """Returns a list of input device names."""
        devices = []
        try:
            device_list = sd.query_devices()
            wasapi_index = -1
            
            # Find WASAPI Host API
            for i, api in enumerate(sd.query_hostapis()):
                if "WASAPI" in api['name']:
                    wasapi_index = i
                    break

            for i, d in enumerate(device_list):
                hostapi = d['hostapi']
                max_in = d['max_input_channels']
                max_out = d['max_output_channels']
                name = d['name']
                
                # For WASAPI loopback: We want OUTPUT devices (Speakers) that ALSO have input channels (or 0 inputs if we force loopback)
                # This is Windows' way of exposing loopback
                is_wasapi_loopback = (hostapi == wasapi_index and 
                                     max_out > 0 and 
                                     ("Speakers" in name or "Headphones" in name))
                
                # Regular input devices
                is_regular_input = max_in > 0
                
                if not (is_wasapi_loopback or is_regular_input):
                    continue
                
                display_name = name
                priority = 2  # 0=High, 1=Med, 2=Low
                
                if is_wasapi_loopback:
                    display_name = f"[SYSTEM AUDIO] {name}"
                    priority = 0
                elif hostapi == wasapi_index and "Stereo Mix" in name:
                    display_name = f"[Stereo Mix] {name}"
                    priority = 1
                elif hostapi == wasapi_index and max_in > 0:
                    display_name = f"[WASAPI] {name}"
                    priority = 2
                elif "Microphone" in name:
                    display_name = f"[Mic] {name}"
                    priority = 3
                
                display_name = display_name.replace("(Realtek(R) Audio)", "").strip()
                key_name = f"{i}: {display_name}"
                devices.append((priority, key_name, i)) # priority tuple
                self.device_map[key_name] = i

            # Sort by priority
            devices.sort(key=lambda x: x[0])
            return [d[1] for d in devices]

        except Exception as e:
            print(f"Error querying devices: {e}")
            return []

    def parse_device_id(self, selection):
        if not selection: 
            return None
        if selection == "Default":
            return None
        return self.device_map.get(selection)

    def start_stream(self, device_selection=None):
        """Starts the audio stream for monitoring (levels only)."""
        if self.running:
            self.stop_stream()
            
        self.device_id = self.parse_device_id(device_selection)
        self.running = True
        self.capturing = False
        self._stop_event.clear()
        
        # Reset buffer
        self.current_chunk_data = []
        self.chunk_start_time = time.time()
        
        self._thread = threading.Thread(target=self._record_loop)
        self._thread.start()

    def start_recording(self):
        """Enables saving audio to files."""
        # Reset buffer on start
        self.current_chunk_data = []
        self.chunk_start_time = time.time()
        self.capturing = True

    def stop_recording(self):
        """Disables saving audio (stream continues for monitoring)."""
        self.capturing = False
        # Flush last chunk if any
        self._flush_chunk()

    def stop_stream(self):
        """Stops the audio stream entirely."""
        self.running = False
        self.capturing = False
        self._stop_event.set()
        if self._thread:
            self._thread.join()
            self._thread = None

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice InputStream."""
        if status:
            print(status)
            
        if not self.running:
            raise sd.CallbackStop
            
        # 1. ALWAYS Calculate audio level (RMS) for monitoring
        rms = np.sqrt(np.mean(indata**2))
        self.current_level = min(100, int(rms * 1000))  # Scale to 0-100%
        
        # 2. Only save data if CAPTURING
        if self.capturing:
            # Append copy of data to current chunk
            self.current_chunk_data.append(indata.copy())
            
            # Check if chunk duration has passed
            if time.time() - self.chunk_start_time >= self.chunk_duration:
                 self._flush_chunk()

    def _flush_chunk(self):
        """Saves current buffer to file and resets."""
        if not self.current_chunk_data:
            return

        try:
            # Concatenate all numpy blocks
            chunk_audio = np.concatenate(self.current_chunk_data, axis=0)
            
            # Create temp file
            fd, filename = tempfile.mkstemp(suffix=".wav")
            os.close(fd)
            
            # Save using soundfile (efficiently handles float32)
            sf.write(filename, chunk_audio, self.sample_rate)
            
            print(f"Chunk created: {filename}")
            self.audio_queue.put(filename)
            
        except Exception as e:
            print(f"Error saving chunk: {e}")
            import traceback
            traceback.print_exec()
            
        # Reset
        self.current_chunk_data = []
        self.chunk_start_time = time.time()

    def get_next_chunk(self):
        """Returns path to the next audio chunk file."""
        try:
            return self.audio_queue.get(timeout=1) # Blocking with timeout
        except queue.Empty:
            return None

    def _record_loop(self):
        """Internal thread for sounddevice InputStream."""
        candidates = []
        if self.device_id is not None:
            try:
                dev_info = sd.query_devices(self.device_id)
                native_rate = int(dev_info.get('default_samplerate', 48000))
                native_ch = max(1, dev_info.get('max_input_channels', 2))
                
                # PRIORITY 1: Native settings
                candidates.append((self.device_id, native_rate, native_ch, 'float32', None))
                
                # PRIORITY 2: Standard 48k/44.1k
                candidates.append((self.device_id, 48000, 2, 'float32', None))
                candidates.append((self.device_id, 44100, 2, 'float32', None))
                
                # PRIORITY 3: FORCE WASAPI LOOPBACK (for Speakers/Output devices)
                try:
                    loopback_settings = sd.WasapiSettings(loopback=True)
                    # Loopback usually requires matching the output channels (usually 2)
                    candidates.insert(0, (self.device_id, native_rate, 2, 'float32', loopback_settings))
                except:
                    pass

            except Exception as e:
                print(f"Could not query device {self.device_id}: {e}")

        # Fallbacks
        candidates.append((None, 44100, 2, 'float32', None))

        stream = None
        success_config = None

        for item in candidates:
            if len(item) == 5:
                dev, rate, ch, dtype, settings = item
            else:
                dev, rate, ch, dtype = item
                settings = None

            if self._stop_event.is_set(): break
            
            try:
                print(f"Attempting Stream: Dev={dev}, Rate={rate}, Ch={ch}, Dtype={dtype}, Settings={settings is not None}")
                stream = sd.InputStream(samplerate=rate,
                                      device=dev,
                                      channels=ch,
                                      dtype=dtype,
                                      extra_settings=settings,
                                      callback=self._audio_callback)
                stream.start()
                success_config = (dev, rate, ch, dtype, settings is not None)
                self.sample_rate = rate 
                print(f"SUCCESS! Recording with: {success_config}")
                break
            except Exception as e:
                print(f"Failed config {dev}/{rate}/{ch}: {e}")
                if stream: 
                    try: stream.close()
                    except: pass
                stream = None

        if not stream:
            err_msg = "Could not initialize audio. Please check microphone settings."
            self.audio_queue.put({"error": err_msg})
            self.running = False
            return

        try:
             # Wait until stopped
            while not self._stop_event.wait(0.1):
                if not stream.active:
                    raise Exception("Stream stopped unexpectedly")
        except Exception as e:
            print(f"Recording Error: {e}")
            self.audio_queue.put({"error": str(e)})
        finally:
            self.running = False
            self.capturing = False
            if stream:
                stream.close()

    def get_audio_level(self):
        """Get the current audio level (0-100)."""
        return self.current_level

    def is_stream_active(self):
        """Check if audio stream is running."""
        return self.running
