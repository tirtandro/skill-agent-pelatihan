import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

runner = AgentDesktopRunner()

def complete_video(url, window_id=None, play_xy="-654,401"):
    """
    Menuntaskan video pembelajaran PMM:
    1. Navigasi ke URL video dengan recordProgress=true
    2. Klik pemutar video YouTube
    3. Tekan '9' untuk melompat ke 90% durasi
    4. Tekan tombol panah kanan 15x untuk menggeser ke akhir video
    5. Menunggu event playback selesai disimpan backend PMM
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[VIDEO] Memulai penyelesaian video: {url}")
    navigate_to(url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.5)
    
    # Klik pemutar video
    runner.run(['mouse-click', '--headed', f'--xy={play_xy}'])
    time.sleep(2.0)
    
    # Lompat ke 90%
    runner.run(['press', '--headed', '9'])
    time.sleep(1.0)
    
    # Scrubbing cepat ke akhir video
    for _ in range(15):
        runner.run(['press', '--headed', 'right'])
        time.sleep(0.15)
        
    time.sleep(4.0)
    print("[VIDEO] Video tuntas diputar.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        complete_video(sys.argv[1])
    else:
        print("Penggunaan: python video_runner.py <URL_VIDEO_PMM>")
