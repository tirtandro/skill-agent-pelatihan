import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

runner = AgentDesktopRunner()

def verify_topic(topic_url, window_id=None, proof_dir=None):
    """
    Memverifikasi status kelulusan topik:
    1. Buka URL topik
    2. Cek apakah seluruh modul centang hijau / selesai
    3. Cek apakah tautan 'Unduh Surat' (/surat-selesai-belajar) telah tersedia
    4. Ambil screenshot bukti kelulusan penuh
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[VERIFIER] Memeriksa status kelulusan topik: {topic_url}")
    navigate_to(topic_url, window_id=window_id, wait_seconds=4)
    runner.run(['focus-window', '--window-id', window_id])
    
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
        print("[VERIFIER] Gagal membaca Accessibility Tree.")
        return False
        
    snap2 = runner.run(['snapshot', '--root', legacy_ref, '-i'])
    tree2 = snap2.get('data', {}).get('tree', {})
    
    links = []
    buttons = []
    def dump_nodes(n):
        role = n.get('role', '')
        name = n.get('name', '').strip()
        val = n.get('value', '')
        if role == 'link':
            links.append((name, val))
        elif role == 'button':
            buttons.append(name)
        for c in n.get('children', []):
            dump_nodes(c)
    dump_nodes(tree2)
    
    unduh_surat = any('unduh surat' in l[0].lower() or 'surat-selesai' in l[1].lower() for l in links)
    
    print("\n--- HASIL PEMERIKSAAN TOPIK ---")
    if unduh_surat:
        print("[STATUS] TOPIK LULUS 100%! Surat Keterangan Selesai Topik TERSEDIA.")
    else:
        print("[STATUS] Topik belum 100% tuntas (Tombol Unduh Surat belum aktif).")
        
    if proof_dir:
        os.makedirs(proof_dir, exist_ok=True)
        shot_path = os.path.join(proof_dir, "bukti_selesai_topik.png")
        runner.run(['screenshot', shot_path, '--window-id', window_id])
        print(f"[VERIFIER] Tangkapan layar bukti topik tersimpan di: {shot_path}")
        
    return unduh_surat

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/topik/1'
    verify_topic(url)
