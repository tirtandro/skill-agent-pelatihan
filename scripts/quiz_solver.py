import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from runner import AgentDesktopRunner
from navigator import find_chrome_window

runner = AgentDesktopRunner()

POSITIVE_KEYWORDS = [
    'refleksi', 'data nyata', 'kolaborat', 'inkuiri', 'mendalam', 'bermakna',
    'kontekstual', 'peserta didik', 'kebutuhan murid', 'karakteristik', 'berbagi praktik',
    'umpan balik', 'evaluasi', 'peningkatan nyata', 'daya nalar', 'solusi nyata',
    'kesepakatan', 'laboratorium pembelajaran', 'pola masalah', 'coaching',
    'perbaikan', 'unplugged', 'mengevaluasi', 'menganalisis', 'menyesuaikan',
    'kodrat', 'menuntun', 'selamat dan bahagia', 'sistem among', 'tri sentra',
    'kemerdekaan', 'tut wuri handayani', 'budi pekerti', 'berkesadaran', 'profil lulusan',
    'semua jawaban benar', 'benar semua'
]

NEGATIVE_KEYWORDS = [
    'menegur', 'menghukum', 'mengabaikan', 'menyalahkan', 'kegagalan', 'pasif',
    'menghindari', 'menunda', 'formalitas', 'beban administratif', 'ceramah tradisional',
    'manipulasi', 'diam tanpa', 'hanya untuk', 'tanpa perubahan', 'otoriter',
    'memaksakan kehendak', 'hafalan semata'
]

def score_option(text):
    score = 0
    lower = text.lower()
    for kw in POSITIVE_KEYWORDS:
        if kw in lower:
            score += 5
    for kw in NEGATIVE_KEYWORDS:
        if kw in lower:
            score -= 10
    score += len(text) / 50.0
    return score

def get_legacy_ref(window_id):
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

def get_elements(legacy_ref):
    snap2 = runner.run(['snapshot', '--root', legacy_ref, '-i'])
    tree2 = snap2.get('data', {}).get('tree', {})
    radios = []
    buttons = {}
    def dump_el(n):
        role = n.get('role', '')
        name = n.get('name', '').strip()
        ref = n.get('ref_id', '')
        if role == 'radiobutton':
            radios.append((name, ref))
        elif role in ['button', 'link']:
            buttons[name.lower()] = ref
        for c in n.get('children', []):
            dump_el(c)
    dump_el(tree2)
    return radios, buttons

def solve_quiz(window_id=None, max_iterations=15):
    if not window_id:
        window_id = find_chrome_window()
        
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.3)
    
    for q_idx in range(1, max_iterations + 1):
        leg = get_legacy_ref(window_id)
        if not leg:
            print("[QUIZ] Legacy ref tidak ditemukan.")
            break
            
        radios, btns = get_elements(leg)
        
        # Cek jika kuis sudah selesai
        kembali_key = next((k for k in btns.keys() if 'kembali ke materi' in k), None)
        if kembali_key and not radios:
            print(f"[QUIZ] Kuis selesai! Menekan {kembali_key}...")
            runner.run(['focus', '--headed', btns[kembali_key]])
            time.sleep(0.3)
            runner.run(['press', '--headed', 'space'])
            time.sleep(3)
            return True
            
        if not radios:
            lanjut_key = next((k for k in btns.keys() if 'lanjut' in k), None)
            if lanjut_key:
                runner.run(['focus', '--headed', btns[lanjut_key]])
                time.sleep(0.3)
                runner.run(['press', '--headed', 'space'])
                time.sleep(2)
                continue
            break
            
        # Pilih opsi terbaik
        best_r = max(radios, key=lambda r: score_option(r[0]))
        print(f"[QUIZ Soal {q_idx}] Memilih: {best_r[0][:50]}... (Skor: {score_option(best_r[0]):.1f})")
        
        runner.run(['focus', '--headed', best_r[1]])
        time.sleep(0.3)
        runner.run(['press', '--headed', 'space'])
        time.sleep(0.4)
        
        # Tekan Jawab
        jawab_key = next((k for k in btns.keys() if 'jawab' in k), None)
        if jawab_key:
            runner.run(['focus', '--headed', btns[jawab_key]])
            time.sleep(0.3)
            runner.run(['press', '--headed', 'space'])
            time.sleep(1.5)
            
        # Cek Lanjut atau Kembali
        leg = get_legacy_ref(window_id)
        radios, btns = get_elements(leg)
        
        lanjut_key = next((k for k in btns.keys() if 'lanjut' in k), None)
        kembali_key = next((k for k in btns.keys() if 'kembali ke materi' in k), None)
        
        if lanjut_key:
            runner.run(['focus', '--headed', btns[lanjut_key]])
            time.sleep(0.3)
            runner.run(['press', '--headed', 'space'])
            time.sleep(2)
        elif kembali_key:
            runner.run(['focus', '--headed', btns[kembali_key]])
            time.sleep(0.3)
            runner.run(['press', '--headed', 'space'])
            time.sleep(3)
            return True
            
    return True

if __name__ == '__main__':
    solve_quiz()
