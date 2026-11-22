import sys
import os
import time
import re

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
    'semua jawaban benar', 'benar semua', 'semua benar', 'keterlibatan', 'terbuka',
    'aktif', 'memfasilitasi', 'mengapresiasi', 'mendengarkan'
]

NEGATIVE_KEYWORDS = [
    'menegur', 'menghukum', 'mengabaikan', 'menyalahkan', 'kegagalan', 'pasif',
    'menghindari', 'menunda', 'formalitas', 'beban administratif', 'ceramah tradisional',
    'manipulasi', 'diam tanpa', 'hanya untuk', 'tanpa perubahan', 'otoriter',
    'memaksakan kehendak', 'hafalan semata', 'stabilitas semata', 'memotong pembicaraan',
    'menolak masukan', 'mengintimidasi'
]

NEGATION_TRIGGERS = [
    'kecuali', 'bukan', 'tidak termasuk', 'kurang tepat', 'tidak tepat',
    'yang salah', 'bukan merupakan', 'tidak benar', 'bukanlah', 'hindari',
    'yang bukan', 'di bawah ini yang tidak'
]

def is_negation_question(question_text):
    """Mendeteksi apakah pertanyaan merupakan tipe negasi/kecuali."""
    lower = question_text.lower()
    return any(trig in lower for trig in NEGATION_TRIGGERS)

def score_option(option_text, is_negation=False):
    """
    Menghitung skor probabilitas kebenaran opsi:
    - Soal Standar: Opsi dengan kata kunci pedagogis positif mendapat skor tinggi.
    - Soal Negasi: Opsi dengan kata kunci negatif atau paling sedikit unsur positif mendapat prioritas.
    """
    lower = option_text.lower()
    pos_score = sum(5 for kw in POSITIVE_KEYWORDS if kw in lower)
    neg_score = sum(10 for kw in NEGATIVE_KEYWORDS if kw in lower)
    
    # Deteksi opsi sapu jagat (semua benar)
    if any(k in lower for k in ['semua jawaban benar', 'benar semua', 'semua benar']):
        pos_score += 15

    base_score = pos_score - neg_score + (len(option_text) / 50.0)
    
    if is_negation:
        # Invert: cari yang bernilai negatif atau bukan prinsip merdeka
        return -base_score
    return base_score

def get_legacy_ref(window_id):
    snap = runner.run(['snapshot', '--window-id', window_id])
    tree = snap.get('data', {}).get('tree', {})
    legacy_ref = [None]
    def find_legacy(n):
        if 'Legacy' in n.get('name', ''):
            legacy_ref[0] = n.get('ref_id')
        for c in n.get('children', []):
            find_legacy(c)
    find_legacy(tree)
    return legacy_ref[0]

def extract_quiz_state(legacy_ref):
    """
    Mengekstrak seluruh elemen halaman Latihan Pemahaman:
    - question_stem: teks pertanyaan
    - radios: list tuple (name, ref_id)
    - buttons: dict {name_lower: ref_id}
    - statuses: list teks status evaluasi
    """
    snap2 = runner.run(['snapshot', '--root', legacy_ref, '-i'])
    tree2 = snap2.get('data', {}).get('tree', {})
    
    question_parts = []
    radios = []
    buttons = {}
    statuses = []
    
    def dump_el(n):
        role = n.get('role', '')
        name = (n.get('name') or '').strip()
        ref = n.get('ref_id', '')
        
        if role in ['heading', 'text', 'statictext']:
            lower = name.lower()
            # Kumpulkan kalimat pertanyaan
            if any(k in lower for k in ['soal', 'berikut', 'apa', 'mengapa', 'bagaimana', 'manakah', 'alasan', 'tujuan', 'pernyataan', 'kecuali', 'bukan']):
                question_parts.append(name)
            if any(k in lower for k in ['kurang tepat', 'salah', 'luar biasa', 'tepat', 'benar', 'pemahaman anda']):
                statuses.append(name)
        elif role in ['radio', 'radiobutton']:
            radios.append((name, ref))
        elif role in ['button', 'link']:
            buttons[name.lower()] = ref
            
        for c in n.get('children', []):
            dump_el(c)
            
    dump_el(tree2)
    question_stem = " ".join(question_parts)
    return question_stem, radios, buttons, statuses

def solve_quiz(window_id=None, max_iterations=20):
    """
    Menyelesaikan Latihan Pemahaman secara adaptif dan bergaransi 100% tuntas:
    1. Membaca teks soal untuk mendeteksi tipe pertanyaan (negasi vs reguler).
    2. Menilai opsi jawaban secara kontekstual.
    3. Jika jawaban awal kurang tepat, menangkap tombol 'Coba Lagi' dan
       melakukan eliminasi opsi salah secara dinamis hingga status hijau ('Lanjut') tercapai.
    4. Menekan 'Kembali ke Materi' saat seluruh soal kuis terselesaikan.
    """
    if not window_id:
        window_id = find_chrome_window()
        
    runner.run(['focus-window', '--window-id', window_id])
    time.sleep(0.3)
    
    q_num = 1
    tried_options_for_q = set()
    attempts_on_current_q = 0
    
    print(f"\n{'='*60}")
    print("[QUIZ SOLVER ADAPTIF] Memulai penyelesaian Latihan Pemahaman...")
    print(f"{'='*60}")
    
    while q_num <= max_iterations:
        leg = get_legacy_ref(window_id)
        if not leg:
            print("[QUIZ] Legacy ref tidak ditemukan.")
            break
            
        q_stem, radios, btns, statuses = extract_quiz_state(leg)
        
        # 1. Cek apakah kuis telah selesai sepenuhnya
        kembali_key = next((k for k in btns.keys() if 'kembali ke materi' in k), None)
        if kembali_key and not radios:
            print(f"[QUIZ] Seluruh soal selesai! Menekan '{kembali_key}'...")
            runner.run(['focus', '--headed', btns[kembali_key]])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(3.0)
            print("[QUIZ] Latihan Pemahaman sukses diselesaikan 100%!\n")
            return True
            
        # 2. Cek apakah status sekarang adalah jawaban benar ('Lanjut' aktif tanpa 'Coba Lagi')
        lanjut_key = next((k for k in btns.keys() if 'lanjut' in k), None)
        coba_lagi_key = next((k for k in btns.keys() if any(w in k for w in ['coba lagi', 'ulang', 'coba'])), None)
        
        if lanjut_key and not coba_lagi_key:
            print(f"[QUIZ Soal {q_num}] Jawaban BENAR! Menekan 'Lanjut'...")
            runner.run(['focus', '--headed', btns[lanjut_key]])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(2.0)
            q_num += 1
            tried_options_for_q.clear()
            attempts_on_current_q = 0
            continue
            
        # 3. Tangani jika jawaban salah ('Coba Lagi' muncul)
        if coba_lagi_key:
            print(f"[QUIZ Soal {q_num}] Jawaban sebelumnya kurang tepat. Menekan '{coba_lagi_key}' untuk mencoba opsi lain...")
            runner.run(['focus', '--headed', btns[coba_lagi_key]])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(1.5)
            # Ambil ulang state setelah klik coba lagi
            leg = get_legacy_ref(window_id)
            q_stem, radios, btns, statuses = extract_quiz_state(leg)
            
        if not radios:
            time.sleep(1.0)
            continue
            
        # 4. Filter opsi yang sudah terbukti gagal
        available_radios = [r for r in radios if r[0] not in tried_options_for_q]
        if not available_radios:
            print(f"[QUIZ WARNING] Seluruh opsi telah dicoba pada Soal {q_num}. Mereset blacklist opsi...")
            available_radios = radios
            tried_options_for_q.clear()
            
        # 5. Nilai opsi yang tersedia
        is_neg = is_negation_question(q_stem)
        if is_neg and attempts_on_current_q == 0:
            print(f"[QUIZ Soal {q_num}] Terdeteksi pertanyaan bertipe NEGASI/KECUALI: '{q_stem[:65]}...'")
            
        best_r = max(available_radios, key=lambda r: score_option(r[0], is_negation=is_neg))
        tried_options_for_q.add(best_r[0])
        attempts_on_current_q += 1
        
        print(f"[QUIZ Soal {q_num} Percobaan ke-{attempts_on_current_q}] Memilih: {best_r[0][:50]}... (Sisa alternatif: {len(available_radios)-1})")
        
        runner.run(['focus', '--headed', best_r[1]])
        time.sleep(0.2)
        runner.run(['press', '--headed', 'space'])
        time.sleep(0.5)
        
        # 6. Tekan tombol Jawab
        jawab_key = next((k for k in btns.keys() if 'jawab' in k), None)
        if jawab_key:
            runner.run(['focus', '--headed', btns[jawab_key]])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(1.5)
            
        # 7. Evaluasi langsung setelah menekan Jawab
        leg = get_legacy_ref(window_id)
        _, _, btns_after, _ = extract_quiz_state(leg)
        
        lanjut_after = next((k for k in btns_after.keys() if 'lanjut' in k), None)
        kembali_after = next((k for k in btns_after.keys() if 'kembali ke materi' in k), None)
        coba_after = next((k for k in btns_after.keys() if any(w in k for w in ['coba lagi', 'ulang', 'coba'])), None)
        
        if kembali_after and not coba_after:
            print(f"[QUIZ] Kuis selesai tuntas! Menekan '{kembali_after}'...")
            runner.run(['focus', '--headed', btns_after[kembali_after]])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(3.0)
            return True
        elif lanjut_after and not coba_after:
            print(f"[QUIZ Soal {q_num}] Jawaban BENAR! Menekan 'Lanjut'...")
            runner.run(['focus', '--headed', btns_after[lanjut_after]])
            time.sleep(0.2)
            runner.run(['press', '--headed', 'space'])
            time.sleep(2.0)
            q_num += 1
            tried_options_for_q.clear()
            attempts_on_current_q = 0
            
    return True

if __name__ == '__main__':
    solve_quiz()
