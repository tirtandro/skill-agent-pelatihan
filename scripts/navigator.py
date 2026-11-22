import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner

runner = AgentDesktopRunner()

def find_chrome_window():
    """
    Menemukan window ID Google Chrome yang sedang membuka Pelatihan Mandiri PMM.
    Mendukung deteksi judul 'Pelatihan Mandiri', 'Topik', 'Modul', atau URL guru.kemendikdasmen.go.id.
    """
    res = runner.run(['list-windows'])
    windows = res.get('data', [])
    if isinstance(windows, list):
        # Prioritas 1: Chrome dengan judul Pelatihan Mandiri / Guru Kemendikdasmen
        for w in windows:
            app = w.get('app_name', '').lower()
            title = w.get('title', '').lower()
            if 'chrome' in app:
                if any(k in title for k in ['pelatihan mandiri', 'guru.kemendikdasmen', 'topik', 'modul']):
                    return w.get('id')
        # Prioritas 2: Jendela Chrome apa pun yang aktif/terlihat
        for w in windows:
            if 'chrome' in w.get('app_name', '').lower() and w.get('visible', True):
                return w.get('id')
    return 'w-132020'

def navigate_to(url, window_id=None, wait_seconds=3, neutral_xy="-540,500"):
    """
    Menavigasikan Chrome ke URL target secara aman dan membebaskan omnibox trap:
    1. Fokuskan jendela Chrome
    2. Set URL ke clipboard
    3. Buka address bar via ctrl+l, tempel via ctrl+v, dan tekan enter
    4. Tunggu halaman termuat (wait_seconds)
    5. Lepaskan kursor dari omnibox via escape dan klik fisik netral
    """
    if not window_id:
        window_id = find_chrome_window()
        
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.1)
    runner.run(['clipboard-set', url])
    time.sleep(0.1)
    runner.run(['press', '--headed', 'ctrl+l'])
    time.sleep(0.15)
    runner.run(['press', '--headed', 'ctrl+v'])
    time.sleep(0.15)
    runner.run(['press', '--headed', 'return'])
    if wait_seconds > 0:
        time.sleep(wait_seconds)
        
    # Lepaskan omnibox focus trap
    runner.run(['press', '--headed', 'escape'])
    time.sleep(0.2)
    runner.run(['mouse-click', '--headed', f'--xy={neutral_xy}'])
    time.sleep(0.3)

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/topik/1'
    win = sys.argv[2] if len(sys.argv) > 2 else None
    navigate_to(url, window_id=win)
    print("Navigated safely to:", url)
