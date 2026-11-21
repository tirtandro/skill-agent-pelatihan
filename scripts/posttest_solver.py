import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

runner = AgentDesktopRunner()

def get_legacy_node(window_id):
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
    return legacy_ref

def solve_posttest(posttest_url, target_answers, window_id=None, proof_dir=None):
    """
    Menyelesaikan Post Test modul secara otomatis:
    1. Navigasi ke URL post test
    2. Klik Mulai Kerjakan Post Test jika ada
    3. Pilih jawaban yang sesuai dengan target_answers
    4. Klik Cek Ulang Jawaban / Selanjutnya
    5. Klik Kumpulkan pada halaman konfirmasi
    6. Ambil screenshot hasil evaluasi
    7. Klik Kembali ke Modul
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[POST-TEST] Membuka Post Test: {posttest_url}")
    navigate_to(posttest_url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.5)
    
    # Cek tombol Mulai
    snap = runner.run(['snapshot', '--window-id', window_id, '-i'])
    tree = snap.get('data', {}).get('tree', {})
    mulai_ref = None
    def find_mulai(n):
        nonlocal mulai_ref
        if 'mulai' in n.get('name', '').lower() and n.get('role') == 'button':
            mulai_ref = n.get('ref_id')
        for c in n.get('children', []):
            find_mulai(c)
    find_mulai(tree)
    
    if mulai_ref:
        print("[POST-TEST] Menekan Mulai Kerjakan...")
        runner.run(['focus', '--headed', mulai_ref])
        time.sleep(0.3)
        runner.run(['press', '--headed', 'space'])
        time.sleep(3)
        
    # Ambil Legacy container
    leg = get_legacy_node(window_id)
    if not leg:
        print("[POST-TEST] Gagal menemukan Legacy Window.")
        return False
        
    snap2 = runner.run(['snapshot', '--root', leg, '-i'])
    tree2 = snap2.get('data', {}).get('tree', {})
    
    radios = []
    def find_radios(n):
        if n.get('role') == 'radiobutton':
            radios.append((n.get('name', '').strip(), n.get('ref_id')))
        for c in n.get('children', []):
            find_radios(c)
    find_radios(tree2)
    print(f"[POST-TEST] Ditemukan {len(radios)} opsi pilihan ganda.")
    
    for ans in target_answers:
        matched = False
        for r_name, r_ref in radios:
            if ans.startswith("EXACT:"):
                target = ans[6:].strip()
                if r_name == target:
                    print(f"[POST-TEST] Memilih (EXACT): {r_name} ({r_ref})")
                    runner.run(['focus', '--headed', r_ref])
                    time.sleep(0.3)
                    runner.run(['press', '--headed', 'space'])
                    time.sleep(0.3)
                    matched = True
                    break
            else:
                if ans.lower() in r_name.lower():
                    print(f"[POST-TEST] Memilih: {r_name[:50]}... ({r_ref})")
                    runner.run(['focus', '--headed', r_ref])
                    time.sleep(0.3)
                    runner.run(['press', '--headed', 'space'])
                    time.sleep(0.3)
                    matched = True
                    break
        if not matched:
            print(f"[POST-TEST WARNING] Tidak menemukan kecocokan untuk: {ans}")
            
    time.sleep(1)
    
    # Cek Ulang Jawaban / Selanjutnya
    leg = get_legacy_node(window_id)
    snap3 = runner.run(['snapshot', '--root', leg, '-i'])
    tree3 = snap3.get('data', {}).get('tree', {})
    cek_ref = None
    def find_cek(n):
        nonlocal cek_ref
        name = n.get('name', '').lower()
        role = n.get('role', '')
        if ('cek ulang' in name or 'selanjutnya' in name) and role == 'button':
            cek_ref = n.get('ref_id')
        for c in n.get('children', []):
            find_cek(c)
    find_cek(tree3)
    
    if cek_ref:
        print("[POST-TEST] Menekan Cek Ulang Jawaban...")
        runner.run(['focus', '--headed', cek_ref])
        time.sleep(0.3)
        runner.run(['press', '--headed', 'space'])
        time.sleep(2)
        
    # Kumpulkan Jawaban
    leg = get_legacy_node(window_id)
    snap4 = runner.run(['snapshot', '--root', leg, '-i'])
    tree4 = snap4.get('data', {}).get('tree', {})
    kumpul_ref = None
    def find_kumpul(n):
        nonlocal kumpul_ref
        if 'kumpulkan' in n.get('name', '').lower() and n.get('role') == 'button':
            kumpul_ref = n.get('ref_id')
        for c in n.get('children', []):
            find_kumpul(c)
    find_kumpul(tree4)
    
    if kumpul_ref:
        print("[POST-TEST] Menekan Kumpulkan...")
        runner.run(['focus', '--headed', kumpul_ref])
        time.sleep(0.3)
        runner.run(['press', '--headed', 'space'])
        time.sleep(4)
        
    # Screenshot hasil
    if proof_dir:
        os.makedirs(proof_dir, exist_ok=True)
        shot_path = os.path.join(proof_dir, "bukti_posttest_result.png")
        runner.run(['screenshot', shot_path, '--window-id', window_id])
        print(f"[POST-TEST] Bukti hasil evaluasi disimpan di: {shot_path}")
        
    # Kembali ke Modul
    leg = get_legacy_node(window_id)
    snap5 = runner.run(['snapshot', '--root', leg, '-i'])
    tree5 = snap5.get('data', {}).get('tree', {})
    kembali_ref = None
    def find_kembali(n):
        nonlocal kembali_ref
        if 'kembali ke modul' in n.get('name', '').lower() and n.get('role') == 'button':
            kembali_ref = n.get('ref_id')
        for c in n.get('children', []):
            find_kembali(c)
    find_kembali(tree5)
    
    if kembali_ref:
        runner.run(['focus', '--headed', kembali_ref])
        time.sleep(0.3)
        runner.run(['press', '--headed', 'space'])
        time.sleep(3)
        print("[POST-TEST] Berhasil kembali ke modul pelatihan.")
        
    return True

if __name__ == '__main__':
    print("Post Test Solver Library Loaded.")
