# Panduan Troubleshooting & Solusi Teknis Otomasi PMM

Panduan ini mendokumentasikan kendala teknis nyata yang dihadapi saat mengotomasi browser PMM via UIA Windows dan cara mengatasinya secara elegan.

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
Selalu bersihkan tanda petik tunggal sebelum mengirim string ke PowerShell:
```python
clean_text = text.replace("'", "")
subprocess.run(["powershell", "-command", f"Set-Clipboard -Value '{clean_text}'"])
```

---

## 3. Tombol "Simpan" Refleksi Tidak Aktif (Disabled)

### Gejala:
Teks refleksi berhasil ditempel ke textarea melalui `ctrl+v`, namun tombol "Simpan" tetap abu-abu (disabled) dan tidak dapat diklik.

### Penyebab:
Framework frontend PMM (React / Vue) mendengarkan event keyboard fisik `input` / `change`. Menempel via clipboard terkadang tidak memicu event state update pada DOM form.

### Solusi:
Tambahkan satu ketukan tombol spasi (`space`) setelah paste untuk memicu event input:
```python
runner.run(['press', '--headed', 'ctrl+v'])
time.sleep(0.3)
runner.run(['press', '--headed', 'space'])  # Memicu event input
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
