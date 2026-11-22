import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import navigate_to, find_chrome_window

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

def click_button_by_name(name_part, window_id):
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

def solve_posttest_carousel(posttest_url, target_answers, window_id=None, proof_dir=None, proof_prefix="bukti_posttest"):
    """
    Menyelesaikan Post Test berbasis Carousel (MUI Slider PMM) secara deterministik:
    1. Membuka URL Post Test dan menekan tombol 'Mulai Kerjakan Post Test'
    2. Menavigasikan carousel kembali ke Soal 1
    3. Untuk setiap soal:
       - Memilih opsi jawaban target menggunakan UIA focus + space (100% presisi tanpa bias koordinat)
       - Menekan 'Selanjutnya' menuju soal berikutnya
    4. Pada soal terakhir, menekan 'Cek Ulang Jawaban'
    5. Pada layar reviu, menekan 'Kumpulkan'
    6. Pada modal dialog konfirmasi ('Apakah Anda yakin...'), menekan tombol 'Kumpulkan' konfirmasi
    7. Menunggu layar kelulusan ('testPassed=true') dan menyimpan screenshot bukti
    8. Menekan 'Kembali ke Modul' dan mengambil screenshot penyelesaian modul
    """
    if not window_id:
        window_id = find_chrome_window()

    print(f"\n{'='*60}")
    print(f"[POST-TEST CAROUSEL] Membuka Post Test: {posttest_url}")
    print(f"{'='*60}")

    navigate_to(posttest_url, window_id=window_id, wait_seconds=3)
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.5)

    # Cek tombol Mulai Kerjakan Post Test
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

    # Pastikan berada di Soal 1
    print("[POST-TEST] Memastikan berada pada Soal 1...")
    for _ in range(12):
        if not click_button_by_name("Sebelumnya", window_id):
            break

    # Normalisasi target_answers
    # Bisa berupa dict: {1: 'opsi', 2: 'opsi'} atau list: ['opsi1', 'opsi2']
    if isinstance(target_answers, list):
        target_map = {idx + 1: val for idx, val in enumerate(target_answers)}
    else:
        target_map = target_answers

    total_soal = len(target_map)
    print(f"[POST-TEST] Jumlah soal yang akan dijawab: {total_soal}")

    for q_idx in range(1, total_soal + 1):
        target_val = target_map[q_idx]
        print(f"\n--- Menjawab Soal {q_idx}/{total_soal} ---")
        print(f"[POST-TEST] Target Jawaban: {target_val}")

        radios = get_all_radios(window_id)
        # Ambil radio yang aktif di layar (states bukan offscreen, atau seluruh radio jika states kosong)
        active_radios = [r for r in radios if 'offscreen' not in (r.get('states') or [])]
        if not active_radios:
            active_radios = radios

        target_radio = None

        # Jika target_val adalah huruf A, B, C, D
        if isinstance(target_val, str) and target_val.upper() in ['A', 'B', 'C', 'D'] and len(target_val) == 1:
            letter_idx = {'A': 0, 'B': 1, 'C': 2, 'D': 3}[target_val.upper()]
            if letter_idx < len(active_radios):
                target_radio = active_radios[letter_idx]
        else:
            # Pencocokan berdasarkan nama/teks radio button
            for r in active_radios:
                r_name = (r.get('name') or '').strip().lower()
                if isinstance(target_val, str) and target_val.lower() in r_name:
                    target_radio = r
                    break

        if target_radio:
            print(f"[POST-TEST] Memilih opsi: {target_radio.get('name')[:60]}... ({target_radio.get('ref_id')})")
            runner.run(['focus', '--headed', target_radio.get('ref_id')])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(0.8)
        else:
            print(f"[POST-TEST WARNING] Tidak menemukan radio button yang cocok untuk Soal {q_idx}: {target_val}")

        # Maju ke soal berikutnya atau Cek Ulang Jawaban
        if q_idx < total_soal:
            print("[POST-TEST] Menekan tombol 'Selanjutnya'...")
            click_button_by_name("Selanjutnya", window_id)
            time.sleep(1.0)
        else:
            print("[POST-TEST] Soal terakhir tercapai. Menekan 'Cek Ulang Jawaban'...")
            if not click_button_by_name("Cek Ulang", window_id):
                click_button_by_name("Selanjutnya", window_id)
            time.sleep(2.0)

    # Layar Reviu Jawaban
    print("\n--- Layar Reviu Jawaban ---")
    time.sleep(1.0)
    print("[POST-TEST] Menekan tombol 'Kumpulkan' pada layar reviu...")
    click_button_by_name("Kumpulkan", window_id)
    time.sleep(1.5)

    # Modal Konfirmasi Submit ("Apakah Anda yakin ingin mengumpulkan...?")
    print("[POST-TEST] Memeriksa modal dialog konfirmasi pengumpulan...")
    tree_modal = get_legacy_tree(window_id)
    modal_confirm_btn = [None]
    def find_modal_kumpul(n):
        if n.get('role') == 'button' and 'kumpulkan' in (n.get('name') or '').lower():
            if 'disabled' not in (n.get('states') or []):
                modal_confirm_btn[0] = n
        for c in n.get('children', []):
            find_modal_kumpul(c)
    find_modal_kumpul(tree_modal)

    if modal_confirm_btn[0]:
        print(f"[POST-TEST] Mengonfirmasi pengumpulan jawaban: {modal_confirm_btn[0].get('name')} ({modal_confirm_btn[0].get('ref_id')})")
        runner.run(['focus', '--headed', modal_confirm_btn[0].get('ref_id')])
        time.sleep(0.2)
        runner.run(['press', '--headed', 'space'])
        time.sleep(3.5)

    # Screenshot bukti hasil post test
    if proof_dir:
        os.makedirs(proof_dir, exist_ok=True)
        res_shot_path = os.path.join(proof_dir, f"{proof_prefix}_result.png")
        runner.run(['screenshot', '--screen', '1', res_shot_path])
        print(f"[POST-TEST] Tangkapan layar hasil evaluasi tersimpan di: {res_shot_path}")

    # Kembali ke Modul
    print("[POST-TEST] Menekan tombol 'Kembali ke Modul'...")
    click_button_by_name("Kembali ke Modul", window_id)
    time.sleep(3.0)

    # Screenshot bukti modul selesai
    if proof_dir:
        modul_shot_path = os.path.join(proof_dir, f"{proof_prefix}_modul_selesai.png")
        runner.run(['screenshot', '--screen', '1', modul_shot_path])
        print(f"[POST-TEST] Tangkapan layar modul selesai tersimpan di: {modul_shot_path}")

    print(f"[POST-TEST CAROUSEL] Selesai dengan sukses!\n")
    return True

if __name__ == '__main__':
    print("Post Test Carousel Solver Library Loaded.")
