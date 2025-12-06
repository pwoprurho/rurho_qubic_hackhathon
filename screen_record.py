import cv2
import numpy as np
import pyautogui
import time
import keyboard  # Used for global key detection

def record_screen(output_filename="hd_recording.mp4", fps=20.0):
    # 1. Get native screen resolution
    screen_width, screen_height = pyautogui.size()
    screen_size = (screen_width, screen_height)
    
    print(f"🖥️  Resolution: {screen_width}x{screen_height}")
    print("-" * 50)
    print("⏳ WAITING: Switch to your browser/app now.")
    print("🟢 READY: Press the 'Alt' key (Left or Right) to START recording...")
    print("-" * 50)

    # --- WAIT FOR TRIGGER ---
    keyboard.wait('alt')
    print("🚀 STARTED! Recording in progress...")
    print("⏹️  Press 'Esc' to STOP recording.")

    # 2. Define codec
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, fps, screen_size)
    
    start_time = time.time()

    try:
        while True:
            # 3. Check for 'Esc' key globally to STOP
            if keyboard.is_pressed('esc'):
                print("\n⏹️ 'Esc' pressed. Stopping recording...")
                break

            # 4. Capture screen
            img = pyautogui.screenshot()
            
            # 5. Convert to numpy array
            frame = np.array(img)
            
            # 6. Convert colors BGR -> RGB (OpenCV expects BGR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 7. Write frame
            out.write(frame)

    except KeyboardInterrupt:
        print("\n⚠️ Ctrl+C detected. Saving video...")

    finally:
        out.release()
        cv2.destroyAllWindows()
        duration = time.time() - start_time
        print(f"✅ Video saved: {output_filename} (Duration: {duration:.1f}s)")

if __name__ == "__main__":
    record_screen()