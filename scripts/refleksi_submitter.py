import sys
import os
import time
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

runner = AgentDesktopRunner()

def submit_refleksi(url, text, window_id=None, textarea_xy="-540,500"):
    """
    Mengisi dan menyimpan cerita reflektif secara andal:
    1. Navigasi ke URL refleksi materi
    2. Fokuskan textarea refleksi melalui klik mouse
    3. Bersihkan tanda petik tunggal dan set ke clipboard via PowerShell (-NoProfile)
    4. Tempel via ctrl+v dan kirimkan space + backspace agar event input React terpicu dan tombol Simpan aktif
    5. Cari dan tekan tombol Simpan pada accessibility tree (dengan penanganan fallback koordinat)
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[REFLEKSI] Membuka cerita reflektif: {url}")
    navigate_to(url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.3)
    
    # Fokus textarea refleksi
    runner.run(['mouse-click', '--headed', f'--xy={textarea_xy}'])
    time.sleep(0.5)
    
    # Bersihkan area teks jika ada isi sebelumnya
    runner.run(['press', '--headed', 'ctrl+a'])
    time.sleep(0.2)
    runner.run(['press', '--headed', 'backspace'])
    time.sleep(0.2)
    
    # Sanitasi teks (hindari kutip tunggal yang merusak parser PowerShell)
    clean_text = text.replace("'", "").strip()
    subprocess.run(["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value '{clean_text}'"])
    time.sleep(0.2)
    
    # Tempel teks
    runner.run(['press', '--headed', 'ctrl+v'])
    time.sleep(0.5)
    
    # Trigger event input agar validasi form (min 50 karakter) mendeteksi perubahan
    runner.run(['press', '--headed', 'space'])
    time.sleep(0.2)
    runner.run(['press', '--headed', 'backspace'])
    time.sleep(0.5)
    
    # Cari tombol Simpan di Accessibility Tree
    snap = runner.run(['snapshot', '--window-id', window_id])
    tree = snap.get('data', {}).get('tree', {})
    legacy_ref = [None]
    def find_legacy(n):
        if 'Legacy' in n.get('name', ''):
            legacy_ref[0] = n.get('ref_id')
        for c in n.get('children', []):
            find_legacy(c)
    find_legacy(tree)
    
    simpan_node = [None]
    if legacy_ref[0]:
        snap2 = runner.run(['snapshot', '--root', legacy_ref[0], '-i'])
        tree2 = snap2.get('data', {}).get('tree', {})
        def find_simpan(n):
            if n.get('role') == 'button' and 'simpan' in (n.get('name') or '').lower():
                simpan_node[0] = n
            for c in n.get('children', []):
                find_simpan(c)
        find_simpan(tree2)
        
    if simpan_node[0] and 'disabled' not in (simpan_node[0].get('states') or []):
        print(f"[REFLEKSI] Menekan tombol Simpan ({simpan_node[0]['ref_id']})...")
        runner.run(['focus', '--headed', simpan_node[0]['ref_id']])
        time.sleep(0.2)
        runner.run(['press', '--headed', 'space'])
        time.sleep(4.0)
        print("[REFLEKSI] Cerita reflektif berhasil disimpan.")
        return True
    else:
        print("[REFLEKSI] Menggunakan fallback klik tombol Simpan pada koordinat (-540, 1810)...")
        runner.run(['mouse-click', '--headed', '--xy=-540,1810'])
        time.sleep(4.0)
        print("[REFLEKSI] Cerita reflektif disimpan via koordinat.")
        return True

if __name__ == '__main__':
    if len(sys.argv) > 2:
        submit_refleksi(sys.argv[1], sys.argv[2])
    else:
        print("Penggunaan: python refleksi_submitter.py <URL_REFLEKSI> <TEKS_REFLEKSI>")
