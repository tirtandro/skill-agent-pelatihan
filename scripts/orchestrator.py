import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window
from video_runner import complete_video
from text_runner import complete_text_material
from quiz_solver import solve_quiz
from refleksi_submitter import submit_refleksi
from posttest_solver import solve_posttest_carousel

runner = AgentDesktopRunner()

def get_legacy_tree(window_id):
    snap = runner.run(['snapshot', '--window-id', window_id])
    legacy_ref = [None]
    def find_legacy(n):
        if 'Legacy' in n.get('name', ''):
            legacy_ref[0] = n.get('ref_id')
        for c in n.get('children', []):
            find_legacy(c)
    find_legacy(snap.get('data', {}).get('tree', {}))
    if not legacy_ref[0]:
        return snap.get('data', {}).get('tree', {})
    snap2 = runner.run(['snapshot', '--root', legacy_ref[0], '-i'])
    return snap2.get('data', {}).get('tree', {})

def discover_module_items(modul_url, window_id=None):
    """
    Menginspeksi halaman modul PMM dan mengelompokkan seluruh aktivitas yang ada:
    - Video pembelajaran
    - Materi teks / PDF
    - Kuis Latihan Pemahaman
    - Cerita Reflektif
    - Link Post Test
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n[ORCHESTRATOR] Menginspeksi struktur modul: {modul_url}")
    navigate_to(modul_url, window_id=window_id, wait_seconds=3)
    
    tree = get_legacy_tree(window_id)
    items = {
        'videos': [],
        'texts': [],
        'quizzes': [],
        'refleksi': [],
        'posttest': None
    }
    
    def walk(n):
        role = n.get('role', '')
        name = n.get('name') or ''
        val = n.get('value') or ''
        ref = n.get('ref_id') or ''
        
        if role in ['link', 'button']:
            lower_val = val.lower()
            lower_name = name.lower()
            if '/video/' in lower_val:
                items['videos'].append({'name': name, 'url': val, 'ref_id': ref})
            elif '/text/' in lower_val:
                items['texts'].append({'name': name, 'url': val, 'ref_id': ref})
            elif '/quiz/' in lower_val:
                items['quizzes'].append({'name': name, 'url': val, 'ref_id': ref})
            elif '/refleksi/' in lower_val:
                items['refleksi'].append({'name': name, 'url': val, 'ref_id': ref})
            elif 'post-test' in lower_val or 'post test' in lower_name:
                items['posttest'] = {'name': name, 'url': val, 'ref_id': ref}
                
        for c in n.get('children', []):
            walk(c)
            
    walk(tree)
    print(f"[ORCHESTRATOR] Ditemukan: {len(items['videos'])} Video, {len(items['texts'])} Teks, {len(items['quizzes'])} Kuis, {len(items['refleksi'])} Refleksi, Post Test: {'Ada' if items['posttest'] else 'Belum Aktif'}")
    return items

def run_module_pipeline(modul_url, materials_sequence, posttest_answers=None, window_id=None, proof_dir=None, modul_label="modul", max_posttest_retries=2):
    """
    Menjalankan seluruh rangkaian modul secara otomatis dari awal hingga post test:
    - materials_sequence: list of tuples:
        ('video', url)
        ('text', url)
        ('quiz', url)
        ('refleksi', url, default_text)
    - posttest_answers: dict or list jawaban post test (opsional, jika None menggunakan penalaran dinamis)
    """
    if not window_id:
        window_id = find_chrome_window()
        
    print(f"\n{'='*70}")
    print(f"[ORCHESTRATOR] MEMULAI PIPELINE MODUL: {modul_label}")
    print(f"URL Modul: {modul_url}")
    print(f"{'='*70}")
    
    # 1. Eksekusi seluruh materi
    for item in materials_sequence:
        act_type = item[0]
        url = item[1]
        
        if act_type == 'video':
            complete_video(url, window_id=window_id)
            time.sleep(2)
        elif act_type == 'text':
            complete_text_material(url, window_id=window_id)
            time.sleep(2)
        elif act_type == 'quiz':
            navigate_to(url, window_id=window_id, wait_seconds=3)
            solve_quiz(window_id=window_id)
            time.sleep(2)
        elif act_type == 'refleksi':
            ref_text = item[2] if len(item) > 2 else "Saya akan menerapkan pemahaman baru ini secara konsisten dalam proses pembelajaran di kelas."
            submit_refleksi(url, ref_text, window_id=window_id)
            time.sleep(2)
            
    # 2. Navigasi kembali ke modul untuk memicu aktivasi post test
    navigate_to(modul_url, window_id=window_id, wait_seconds=3)
    time.sleep(2)
    
    # 3. Eksekusi Post Test dengan Verifikasi Kelulusan & Auto-Retry Loop
    posttest_url = f"{modul_url}/post-test" if not '/post-test' in modul_url else modul_url
    items = discover_module_items(modul_url, window_id=window_id)
    if items['posttest'] and items['posttest']['url']:
        posttest_url = items['posttest']['url']
        
    proof_prefix = f"bukti_{modul_label}"
    
    passed = False
    for pt_attempt in range(1, max_posttest_retries + 1):
        print(f"\n[ORCHESTRATOR] Menjalankan Post Test Percobaan {pt_attempt}/{max_posttest_retries}...")
        passed = solve_posttest_carousel(
            posttest_url,
            posttest_answers,
            window_id=window_id,
            proof_dir=proof_dir,
            proof_prefix=proof_prefix
        )
        if passed:
            break
        print(f"[ORCHESTRATOR WARNING] Percobaan post test ke-{pt_attempt} belum lulus. Mencoba kembali...")
        time.sleep(3.0)
        
    if passed:
        print(f"[ORCHESTRATOR] Pipeline {modul_label} selesai dengan SUKSES (LULUS 100%)!\n")
    else:
        print(f"[ORCHESTRATOR ERROR] Pipeline {modul_label} selesai tetapi Post Test belum lulus penuh.\n")
        
    return passed

if __name__ == '__main__':
    print("Enhanced Orchestrator Library Loaded.")
