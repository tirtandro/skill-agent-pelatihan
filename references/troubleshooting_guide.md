# Panduan Troubleshooting & Solusi Teknis Otomasi PMM

Panduan ini mendokumentasikan kendala teknis nyata yang dihadapi saat mengotomasi browser PMM via UIA Windows dan solusi deterministik untuk mengatasinya.

---

## 1. Omnibox Focus Trap

### Gejala:
Setelah script menavigasikan URL via `ctrl+l` -> `ctrl+v` -> `return`, snapshot accessibility tree mengembalikan tree kosong atau hanya menampakkan address bar dan tab strip Chrome. Seluruh elemen web dokumen menghilang.

### Penyebab:
Kursor keyboard tetap terkunci di dalam address bar (Omnibox) Chrome. Saat omnibox aktif, elemen web di dalam viewport browser tidak diekspos sebagai active focus oleh browser renderer.

### Solusi:
Selalu lakukan pembebasan fokus segera setelah navigasi:
```python
runner.run(['press', '--headed', 'escape'])
time.sleep(0.2)
runner.run(['mouse-click', '--headed', '--xy=-540,500'])  # Koordinat tengah dokumen
```

---

## 2. PowerShell Positional Parameter Error pada `Set-Clipboard`

### Gejala:
Saat menjalankan script pengisian refleksi melalui perintah:
```powershell
powershell -command "Set-Clipboard -Value 'Guru tidak boleh 'memaksakan' kehendak'"
```
Muncul error PowerShell:
`A positional parameter cannot be found that accepts argument...`

### Penyebab:
Tanda petik tunggal (`'`) di dalam teks refleksi memutus kutipan string PowerShell sehingga parser mengira kata berikutnya adalah nama argumen/parameter baru.

### Solusi:
Selalu bersihkan tanda petik tunggal sebelum mengirim string ke PowerShell dan sertakan `-NoProfile`:
```python
clean_text = text.replace("'", "")
subprocess.run(["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value '{clean_text}'"])
```

---

## 3. Tombol "Simpan" Refleksi Tidak Aktif (Disabled)

### Gejala:
Teks refleksi berhasil ditempel ke textarea melalui `ctrl+v`, namun tombol "Simpan" tetap abu-abu (disabled) dan tidak dapat diklik.

### Penyebab:
Framework frontend PMM (React / Material UI) mendengarkan event keyboard fisik `input` / `change` dan memvalidasi batas minimal 50 karakter. Menempel via clipboard terkadang tidak memicu event state update pada DOM form.

### Solusi:
Kirimkan satu ketukan tombol spasi (`space`) diikuti tombol `backspace` setelah paste untuk memicu event input tanpa merusak format teks:
```python
runner.run(['press', '--headed', 'ctrl+v'])
time.sleep(0.3)
runner.run(['press', '--headed', 'space'])      # Memicu event form input
time.sleep(0.2)
runner.run(['press', '--headed', 'backspace'])  # Mengembalikan teks semula
```

---

## 4. `AMBIGUOUS_TARGET` pada Tombol Next Halaman PDF

### Gejala:
Saat mencoba mengeklik tombol next page pada viewer PDF via semantic ref atau nama elemen, runner mengembalikan error `AMBIGUOUS_TARGET`.

### Penyebab:
Tombol navigasi viewer PDF pada browser tidak memiliki nama aksesibilitas yang unik (nama kosong `""` atau hanya ikon SVG).

### Solusi:
Gunakan physical mouse-click pada koordinat layar absolut tombol pembalik halaman:
```python
runner.run(['mouse-click', '--headed', '--xy=-239,1811'])
```

---

## 5. Sinkronisasi Video YouTube Embed

### Gejala:
Video sudah ditonton, namun modul tetap meminta video diselesaikan (`recordProgress=true` tetap muncul).

### Penyebab:
Backend PMM memvalidasi event `onEnded` dari YouTube IFrame API. Jika tab langsung ditutup atau dinavigasikan sebelum event terkirim ke backend, progress tidak tercatat.

### Solusi:
1. Mulai video dengan klik fisik di tengah player.
2. Lompat ke 90% via tombol `9`.
3. Scrubbing cepat dengan panah kanan (`right` arrow 15x) ke titik 1-2 detik sebelum durasi usai.
4. Beri jeda tunggu minimal 4 detik agar video natural berakhir dan memicu callback `ended`.

---

## 6. Offset Drift pada Template Matching Pilihan Ganda Post Test (Text Wrapping)

### Gejala:
Template matching menemukan lingkaran radio button A, lalu menambahkan offset vertikal (+62, +122, +182) untuk option B, C, D. Pada soal dengan teks pilihan panjang yang membungkus (wrapped) menjadi 2-3 baris, tinggi kotak pilihan menjadi ~80-120px sehingga offset +122px meleset dan tidak mengeklik option C.

### Penyebab:
Variasi tinggi baris elemen HTML radio group dinamis berdasarkan panjang kalimat pilihan.

### Solusi:
Gunakan seleksi langsung berbasis Accessibility Tree UIA (`role='radiobutton'`). Cari elemen radio button berdasarkan nama teks target atau urutan indeks, kemudian kirimkan:
```python
runner.run(['focus', '--headed', target_radio['ref_id']])
time.sleep(0.2)
runner.run(['press', '--headed', 'space'])
```
Pendekatan ini deterministik 100%, tahan terhadap text wrapping, dan tidak bergantung pada resolusi layar maupun posisi scroll.

---

## 7. Modal Dialog Konfirmasi Submit Post Test

### Gejala:
Tombol "Kumpulkan" di halaman reviu jawaban sudah diklik, namun post test tidak tersubmit dan hasil evaluasi kelulusan tidak muncul.

### Penyebab:
Mengklik tombol "Kumpulkan" pada halaman reviu tidak langsung mengirim jawaban, melainkan memunculkan **Modal Dialog Konfirmasi** ("Apakah Anda yakin ingin mengumpulkan post test ini?").

### Solusi:
Cari tombol "Kumpulkan" konfirmasi yang muncul di dalam modal dialog UIA tree setelah jeda 1-1.5 detik, lalu fokuskan dan tekan spasi:
```python
tree_modal = get_legacy_tree(window_id)
# Cari tombol dengan nama 'Kumpulkan' di dalam modal tree
runner.run(['focus', '--headed', modal_confirm_btn['ref_id']])
time.sleep(0.2)
runner.run(['press', '--headed', 'space'])
time.sleep(3.5)
```

---

## 8. Verifikasi Kelulusan URL `testPassed=true`

### Gejala:
Setelah submit post test, browser terkadang membutuhkan waktu beberapa detik untuk merender kartu hasil kelulusan.

### Solusi:
Periksa atribut tautan post test pada halaman modul. Begitu lulus, URL otomatis berubah dari:
`.../modul/<ID>/post-test?...testPassed=false`
menjadi:
`.../modul/<ID>/post-test/passed?...testPassed=true`

Jika perlu mengambil tangkapan layar kartu hasil evaluasi secara langsung, navigasikan langsung ke endpoint `/passed` tersebut.

---

## 9. Scoping Variable pada Python Closures (`nonlocal` Syntax Error)

### Gejala:
`SyntaxError: no binding for nonlocal 'simpan' found` saat menjalankan fungsi traversal tree UIA.

### Penyebab:
Penggunaan kata kunci `nonlocal` di luar nested function scope yang memiliki binding lokal.

### Solusi:
Gunakan mutable list beranggotakan satu elemen untuk menangkap referensi node secara aman:
```python
target_node = [None]
def walk(n):
    if n.get('role') == 'button' and 'simpan' in (n.get('name') or '').lower():
        target_node[0] = n
    for c in n.get('children', []):
        walk(c)
walk(tree)
```


---

## 10. Penanganan Soal Negasi ("Kecuali" / "Bukan") & Adaptive Elimination Loop pada Kuis

### Gejala:
Script Latihan Pemahaman terus-menerus memilih jawaban salah pada soal yang memuat kata *"kecuali"*, *"bukan"*, atau *"pernyataan yang salah"*.

### Penyebab:
Scoring heuristik berbasis kata kunci secara default memprioritaskan opsi dengan nilai positif pedagogis tertinggi, padahal soal negasi mencari opsi pengecualian (yang bertentangan dengan prinsip positif).

### Solusi:
1. Periksa teks pertanyaan (`question_stem`) untuk keberadaan kata kunci negasi (`is_negation_question()`).
2. Jika terdeteksi negasi, balikkan arah skoring (`is_negation=True`).
3. Terapkan **Adaptive Elimination Loop**: bila muncul tombol *"Coba Lagi"* (jawaban salah), masukkan opsi tersebut ke dalam himpunan opsi tereliminasi (`tried_options`), tekan *"Coba Lagi"*, dan pilih opsi terbaik berikutnya hingga status hijau *"Lanjut"* tercapai.

---

## 11. Fuzzy Option Matching & Strict Pass Verification pada Post Test

### Gejala:
Post test gagal menjawab butir soal tertentu karena string target jawaban berbeda spasi atau format dengan nama radio button di PMM (`Tidak menemukan radio button yang cocok...`), atau modul dianggap selesai padahal hasil post test adalah `Belum Lulus`.

### Solusi:
1. Gunakan algoritma pencocokan toleran (*Fuzzy Matching*) dengan token overlap ratio / Jaccard similarity kata pada teks yang telah dinormalisasi.
2. Terapkan fallback semantik dinamis jika target teks tidak cocok dengan opsi mana pun.
3. Selalu jalankan `verify_submission_pass()` setelah submit modal konfirmasi untuk memeriksa keberadaan teks *"Luar biasa! Pemahaman Anda sangat baik"* atau indikator kelulusan sebelum menandai modul berhasil.
