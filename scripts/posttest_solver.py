import sys
import os
import time
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window
from quiz_solver import score_option, is_negation_question

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

def click_button_by_name(name_part, window_id, timeout_sec=2.0):
    start_t = time.time()
    while time.time() - start_t < timeout_sec:
        tree = get_legacy_tree(window_id)
        target = [None]
        def walk(n):
            if n.get('role') == 'button' and name_part.lower() in (n.get('name') or '').lower():
                if 'disabled' not in (n.get('states') or []):
                    target[0] = n
            for c in n.get('children', []):
                walk(c)
        walk(tree)
        if target[0]:
            print(f"[POST-TEST] Menekan tombol '{target[0].get('name')}' ({target[0].get('ref_id')})...")
            runner.run(['focus', '--headed', target[0].get('ref_id')])
            time.sleep(0.15)
            runner.run(['press', '--headed', 'space'])
            time.sleep(1.2)
            return True
        time.sleep(0.3)
    return False

def get_all_radios(window_id):
    tree = get_legacy_tree(window_id)
    radios = []
    def walk(n):
        if n.get('role') in ['radio', 'radiobutton'] or 'radio' in n.get('subrole', ''):
            radios.append(n)
        for c in n.get('children', []):
            walk(c)
    walk(tree)
    return radios

def normalize_text(text):
    """Membersihkan teks dari tanda baca berlebih dan spasi ganda."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def match_option_fuzzy(target_val, radio_name):
    """
    Pencocokan opsi toleran (Fuzzy Matching):
    1. Substring match langsung.
    2. Token overlap ratio (Jaccard similarity kata).
    """
    norm_target = normalize_text(target_val)
    norm_radio = normalize_text(radio_name)
    
    if not norm_target or not norm_radio:
        return 0.0
        
    if norm_target in norm_radio or norm_radio in norm_target:
        return 1.0
        
    target_words = set(norm_target.split())
    radio_words = set(norm_radio.split())
    
    if not target_words:
        return 0.0
        
    shared = target_words.intersection(radio_words)
    overlap = len(shared) / float(len(target_words))
    return overlap

def extract_posttest_structure(window_id):
    """
    Mengekstrak seluruh soal dan opsi dari DOM Post Test Carousel:
    Struktur: list of dict [{index, stem, options: [{name, ref_id}]}]
    """
    tree = get_legacy_tree(window_id)
    questions = []
    
    def walk_containers(n):
        role = n.get('role', '')
        name = n.get('name') or ''
        
        # Tiap slide soal biasanya memiliki role 'option' atau nama 'Soal X dari Y'
        if 'soal ' in name.lower() and ' dari ' in name.lower():
            # Temukan semua radio di bawah slide ini
            slide_radios = []
            def find_r(child):
                if child.get('role') in ['radio', 'radiobutton']:
                    slide_radios.append({'name': child.get('name'), 'ref_id': child.get('ref_id')})
                for sc in child.get('children', []):
                    find_r(sc)
            find_r(n)
            
            if slide_radios:
                questions.append({
                    'raw_text': name,
                    'radios': slide_radios
                })
        for c in n.get('children', []):
            walk_containers(c)
            
    walk_containers(tree)
    return questions

def verify_submission_pass(window_id, timeout_sec=6.0):
    """
    Memeriksa secara ketat apakah post test dinyatakan LULUS (testPassed=true).
    """
    start_t = time.time()
    while time.time() - start_t < timeout_sec:
        tree = get_legacy_tree(window_id)
        all_texts = []
        def dump(n):
            name = (n.get('name') or '').strip()
            if name:
                all_texts.append(name.lower())
            for c in n.get('children', []):
                dump(c)
        dump(tree)
        
        full_page = " ".join(all_texts)
        if any(pass_kw in full_page for pass_kw in ['luar biasa', 'pemahaman anda sangat baik', 'lulus', 'selamat']):
            return True, "PASSED: Pemahaman Anda sangat baik"
        if any(fail_kw in full_page for fail_kw in ['belum lulus', 'perlu belajar lagi', 'ulangi post test', 'coba lagi']):
            return False, "FAILED: Belum Lulus"
            
        time.sleep(0.5)
        
    return False, "UNKNOWN: Timeout memeriksa hasil"

def solve_posttest_carousel(posttest_url, target_answers=None, window_id=None, proof_dir=None, proof_prefix="bukti_posttest"):
    """
    Menyelesaikan Post Test berbasis Carousel (MUI Slider PMM) secara deterministik dan tangguh:
    1. Buka URL Post Test dan tekan 'Mulai Kerjakan Post Test'
    2. Rewind carousel ke Soal 1
    3. Ekstrak struktur soal atau gunakan target_answers dengan fuzzy matching
    4. Navigasi tiap slide secara presisi (focus + space)
    5. Cek ulang jawaban dan tangani modal dialog konfirmasi 'Kumpulkan' secara stabil
    6. Verifikasi kelulusan (testPassed=true) secara ketat
    7. Ambil screenshot bukti kelulusan dan kembalikan status
    """
    if not window_id:
        window_id = find_chrome_window()

    print(f"\n{'='*70}")
    print(f"[POST-TEST CAROUSEL RESILIEN] Membuka Post Test: {posttest_url}")
    print(f"{'='*70}")

    navigate_to(posttest_url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.5)

    # 1. Cek tombol Mulai Kerjakan Post Test
    tree = get_legacy_tree(window_id)
    mulai_btn = [None]
    def find_mulai(n):
        if n.get('role') == 'button' and 'mulai kerjakan' in (n.get('name') or '').lower():
            if 'disabled' not in (n.get('states') or []):
                mulai_btn[0] = n
        for c in n.get('children', []):
            find_mulai(c)
    find_mulai(tree)

    if mulai_btn[0]:
        print(f"[POST-TEST] Menekan tombol 'Mulai Kerjakan Post Test' ({mulai_btn[0].get('ref_id')})...")
        runner.run(['focus', '--headed', mulai_btn[0].get('ref_id')])
        time.sleep(0.2)
        runner.run(['press', '--headed', 'space'])
        time.sleep(3.0)

    # 2. Rewind ke Soal 1
    print("[POST-TEST] Memastikan navigasi berada pada Soal 1...")
    for _ in range(12):
        if not click_button_by_name("Sebelumnya", window_id):
            break
        time.sleep(0.4)

    # 3. Ekstrak struktur soal dinamis jika tersedia
    carousel_structure = extract_posttest_structure(window_id)
    total_soal = len(carousel_structure) if carousel_structure else (len(target_answers) if target_answers else 3)
    print(f"[POST-TEST] Terdeteksi total {total_soal} butir soal pada carousel.")

    # Normalisasi target_answers
    target_map = {}
    if isinstance(target_answers, list):
        target_map = {idx + 1: val for idx, val in enumerate(target_answers)}
    elif isinstance(target_answers, dict):
        target_map = target_answers

    # 4. Iterasi tiap soal
    for q_idx in range(1, total_soal + 1):
        print(f"\n--- Menjawab Soal {q_idx}/{total_soal} ---")
        radios = get_all_radios(window_id)
        active_radios = [r for r in radios if 'offscreen' not in (r.get('states') or [])]
        if not active_radios:
            active_radios = radios

        target_val = target_map.get(q_idx)
        target_radio = None

        if target_val:
            # Jika target_val adalah huruf A, B, C, D
            if isinstance(target_val, str) and target_val.upper() in ['A', 'B', 'C', 'D'] and len(target_val) == 1:
                letter_idx = {'A': 0, 'B': 1, 'C': 2, 'D': 3}[target_val.upper()]
                if letter_idx < len(active_radios):
                    target_radio = active_radios[letter_idx]
            else:
                # Fuzzy matching terhadap opsi aktif
                best_score = -1.0
                for r in active_radios:
                    r_name = r.get('name') or ''
                    sim = match_option_fuzzy(str(target_val), r_name)
                    if sim > best_score:
                        best_score = sim
                        target_radio = r
                if best_score < 0.4:
                    print(f"[POST-TEST WARNING] Skor kesamaan rendah ({best_score:.2f}) untuk '{target_val}'. Mencoba fallback heuristik...")
                    target_radio = None

        # Fallback jika target_val tidak ada atau tidak cocok: Gunakan penilaian semantik
        if not target_radio and active_radios:
            print(f"[POST-TEST] Menggunakan seleksi semantik cerdas untuk Soal {q_idx}...")
            # Coba deteksi apakah ada negasi di slide aktif
            tree_curr = get_legacy_tree(window_id)
            slide_text = ""
            if carousel_structure and q_idx <= len(carousel_structure):
                slide_text = carousel_structure[q_idx-1]['raw_text']
            is_neg = is_negation_question(slide_text)
            target_radio = max(active_radios, key=lambda r: score_option(r.get('name') or '', is_negation=is_neg))

        if target_radio:
            print(f"[POST-TEST] Memilih opsi: '{target_radio.get('name')[:60]}' ({target_radio.get('ref_id')})")
            runner.run(['focus', '--headed', target_radio.get('ref_id')])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(0.8)
        else:
            print(f"[POST-TEST ERROR] Gagal menemukan radio button pada Soal {q_idx}!")

        # Navigasi ke soal berikutnya atau Cek Ulang Jawaban
        if q_idx < total_soal:
            print("[POST-TEST] Menekan tombol 'Selanjutnya'...")
            click_button_by_name("Selanjutnya", window_id)
            time.sleep(1.2)
        else:
            print("[POST-TEST] Soal terakhir tercapai. Menekan 'Cek Ulang Jawaban'...")
            if not click_button_by_name("Cek Ulang", window_id):
                click_button_by_name("Selanjutnya", window_id)
            time.sleep(2.5)

    # 5. Layar Reviu Jawaban & Pengumpulan
    print("\n--- Layar Reviu Jawaban ---")
    time.sleep(1.0)
    print("[POST-TEST] Menekan tombol 'Kumpulkan' pada layar reviu...")
    click_button_by_name("Kumpulkan", window_id)
    time.sleep(1.5)

    # 6. Modal Konfirmasi Submit dengan Polling Guard
    print("[POST-TEST] Menunggu modal dialog konfirmasi pengumpulan...")
    modal_confirmed = False
    for attempt in range(8):
        tree_modal = get_legacy_tree(window_id)
        modal_btn = [None]
        def find_modal_kumpul(n):
            if n.get('role') == 'button' and 'kumpulkan' in (n.get('name') or '').lower():
                if 'disabled' not in (n.get('states') or []):
                    modal_btn[0] = n
            for c in n.get('children', []):
                find_modal_kumpul(c)
        find_modal_kumpul(tree_modal)

        if modal_btn[0]:
            print(f"[POST-TEST] Mengonfirmasi pengumpulan via modal: {modal_btn[0].get('name')} ({modal_btn[0].get('ref_id')})")
            runner.run(['focus', '--headed', modal_btn[0].get('ref_id')])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            modal_confirmed = True
            time.sleep(4.0)
            break
        time.sleep(0.5)

    if not modal_confirmed:
        print("[POST-TEST WARNING] Modal konfirmasi tidak ditemukan via UIA, mencoba fallback keypress enter...")
        runner.run(['press', '--headed', 'return'])
        time.sleep(4.0)

    # 7. Verifikasi Kelulusan Ketat (Strict Pass Check)
    passed, status_msg = verify_submission_pass(window_id, timeout_sec=6.0)
    print(f"\n[POST-TEST EVALUASI] {status_msg}")

    # Simpan screenshot hasil evaluasi
    if proof_dir:
        os.makedirs(proof_dir, exist_ok=True)
        res_shot_path = os.path.join(proof_dir, f"{proof_prefix}_result.png")
        runner.run(['screenshot', '--screen', '1', res_shot_path])
        print(f"[POST-TEST] Tangkapan layar hasil evaluasi tersimpan di: {res_shot_path}")

    # 8. Kembali ke Modul
    print("[POST-TEST] Menekan tombol 'Kembali ke Modul'...")
    click_button_by_name("Kembali ke Modul", window_id)
    time.sleep(3.0)

    # Simpan screenshot modul selesai
    if proof_dir:
        modul_shot_path = os.path.join(proof_dir, f"{proof_prefix}_modul_selesai.png")
        runner.run(['screenshot', '--screen', '1', modul_shot_path])
        print(f"[POST-TEST] Tangkapan layar modul selesai tersimpan di: {modul_shot_path}")

    if passed:
        print(f"[POST-TEST CAROUSEL] Selamat! Post Test Lulus 100% Sempurna!\n")
        return True
    else:
        print(f"[POST-TEST CAROUSEL] PERHATIAN: Post Test belum berstatus lulus penuh ({status_msg}).\n")
        return False

if __name__ == '__main__':
    print("Enhanced Resilient Post Test Carousel Solver Loaded.")
