import sys
import os
import time
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

runner = AgentDesktopRunner()

def submit_refleksi(url, text, window_id=None, textarea_xy="-540,600"):
    """
    Mengisi dan menyimpan cerita reflektif:
    1. Navigasi ke URL refleksi materi
    2. Fokuskan textarea refleksi melalui klik mouse
    3. Bersihkan tanda petik tunggal dan set ke clipboard
    4. Tempel via ctrl+v dan tambahkan spasi agar tombol Simpan aktif
    5. Cari dan tekan tombol Simpan pada accessibility tree
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[REFLEKSI] Membuka refleksi: {url}")
    navigate_to(url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.3)
    
    # Fokus textarea
    runner.run(['mouse-click', '--headed', f'--xy={textarea_xy}'])
    time.sleep(0.5)
    
    # Sanitasi teks (hindari kutip tunggal yang merusak parser PowerShell)
    clean_text = text.replace("'", "")
    subprocess.run(["powershell", "-command", f"Set-Clipboard -Value '{clean_text}'"])
    time.sleep(0.3)
    
    runner.run(['press', '--headed', 'ctrl+a'])
    time.sleep(0.2)
    runner.run(['press', '--headed', 'backspace'])
    time.sleep(0.2)
    runner.run(['press', '--headed', 'ctrl+v'])
    time.sleep(0.5)
    runner.run(['press', '--headed', 'space'])
    time.sleep(0.5)
    
    # Cari tombol Simpan
    snap = runner.run(['snapshot', '--window-id', window_id])
    tree = snap.get('data', {}).get('tree', {})
    legacy_ref = None
    def find_legacy(n):
        nonlocal legacy_ref
        if 'Legacy' in n.get('name', ''):
            legacy_ref = n.get('ref_id')
        for c in n.get('children', []):
            find_legacy(c)
    find_legacy(tree)
    
    if not legacy_ref:
        print("[REFLEKSI] Gagal menemukan container Legacy Window.")
        return False
        
    snap2 = runner.run(['snapshot', '--root', legacy_ref, '-i'])
    tree2 = snap2.get('data', {}).get('tree', {})
    simpan_ref = None
    def find_simpan(n):
        nonlocal simpan_ref
        if 'simpan' in n.get('name', '').lower() and n.get('role') == 'button':
            simpan_ref = n.get('ref_id')
        for c in n.get('children', []):
            find_simpan(c)
    find_simpan(tree2)
    
    if simpan_ref:
        runner.run(['focus', '--headed', simpan_ref])
        time.sleep(0.3)
        runner.run(['press', '--headed', 'space'])
        time.sleep(3)
        print("[REFLEKSI] Cerita reflektif berhasil disimpan.")
        return True
    else:
        print("[REFLEKSI] Tombol Simpan tidak ditemukan.")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 2:
        submit_refleksi(sys.argv[1], sys.argv[2])
    else:
        print("Penggunaan: python refleksi_submitter.py <URL_REFLEKSI> <TEKS_REFLEKSI>")
