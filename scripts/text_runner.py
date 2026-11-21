import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

runner = AgentDesktopRunner()

def complete_text_material(url, window_id=None, next_page_xy="-239,1811", pages=5):
    """
    Menuntaskan bahan bacaan atau dokumen PDF pada PMM:
    1. Navigasi ke URL teks dengan recordProgress=true
    2. Klik tombol next page pada toolbar viewer berulang kali
    3. Scroll ke bawah menggunakan pagedown untuk memastikan seluruh area termuat
    4. Menunggu sinkronisasi progres ke sistem PMM
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[TEXT] Memulai penyelesaian materi teks/PDF: {url}")
    navigate_to(url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.5)
    
    # Klik tombol pembalik halaman PDF
    for i in range(pages):
        runner.run(['mouse-click', '--headed', f'--xy={next_page_xy}'])
        time.sleep(0.8)
        
    # Scroll ke bawah
    for _ in range(5):
        runner.run(['press', '--headed', 'pagedown'])
        time.sleep(0.2)
        
    time.sleep(2.0)
    print("[TEXT] Materi teks/PDF tuntas dibaca.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        complete_text_material(sys.argv[1])
    else:
        print("Penggunaan: python text_runner.py <URL_TEXT_PMM>")
