# Agent Pelatihan: Otomatisasi Pelatihan Mandiri PMM

> **Skill Agent Pintar untuk Otomatisasi End-to-End Pelatihan Mandiri Guru pada Platform Merdeka Mengajar (PMM - Kemendikdasmen).**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-informational.svg)](https://microsoft.com)
[![Automation](https://img.shields.io/badge/Engine-UIA%20%2B%20Headed%20Desktop-success.svg)]()
[![PMM Compatible](https://img.shields.io/badge/Target-PMM%20Kemendikdasmen-orange.svg)](https://guru.kemendikdasmen.go.id/)

---

## 📖 Tentang Skill Ini

`agent-pelatihan` adalah kumpulan pustaka dan panduan otomasi yang dirancang khusus untuk mempermudah dan mempercepat penyelesaian topik-topik pelatihan pada **Platform Merdeka Mengajar (PMM)**.

Skill ini secara otomatis mengendalikan browser Google Chrome untuk:
1. **Menonton Video Pembelajaran:** Memutar dan menyelesaikan video YouTube tersemat menggunakan pintasan scrubbing cerdas (`9` + panah kanan).
2. **Membaca Dokumen & PDF:** Membalik seluruh halaman dokumen dan melakukan scroll hingga status terbaca 100%.
3. **Mengerjakan Latihan Pemahaman (Kuis):** Menjawab pertanyaan kuis secara otomatis berbasis skoring kata kunci pedagogis Kurikulum Merdeka.
4. **Mengisi Cerita Reflektif:** Mengunggah esai refleksi yang mendalam, bermutu tinggi, dan kontekstual.
5. **Menyelesaikan Post Test:** Menganalisis butir soal, mencocokkan kunci jawaban akurat (100% lulus), dan mengumpulkan hasil ujian.
6. **Verifikasi & Surat Keterangan:** Memverifikasi centang hijau seluruh modul dan memastikan tautan **"Unduh Surat Keterangan Selesai Topik"** telah aktif.

---

## 🚀 Fitur Unggulan

- **Headed & Accessibility Tree Driven:** Menggunakan Windows UI Automation (UIA) dan input fisik untuk interaksi yang 100% andal dan tidak mudah terblokir.
- **Scrubbing Video Cepat:** Tidak perlu menunggu video 10-20 menit; diselesaikan dalam hitungan detik dengan validasi playback backend.
- **Pedagogical Keyword Engine:** Algoritma skoring cerdas untuk kuis yang mengutamakan nilai-nilai Kurikulum Merdeka, Pemikiran Ki Hadjar Dewantara, dan Taksonomi SOLO.
- **Kebal Focus Trap:** Dilengkapi mekanisme pelepasan fokus Omnibox Chrome otomatis.
- **Regulasi PMM Terkini:** Mengikuti aturan baru di mana **Aksi Nyata tidak lagi diwajibkan**, melainkan langsung berhak mendapatkan **Surat Keterangan Selesai Topik**.

---

## 📂 Struktur Direktori

```
E:\Projects 2\skill-agent-pelatihan\
│
├── SKILL.md                          # Definisi resmi skill untuk Agent AI (Codex / Antigravity)
├── README.md                         # Dokumentasi panduan lengkap penggunaan
│
├── scripts/                          # Pustaka skrip Python otomasi
│   ├── runner.py                     # Wrapper eksekusi CLI desktop automation Win32
│   ├── navigator.py                  # Navigasi URL Chrome aman bebas focus trap
│   ├── video_runner.py               # Otomasi video pembelajaran YouTube embed
│   ├── text_runner.py                # Otomasi membaca dan membalik halaman materi bacaan/PDF
│   ├── quiz_solver.py                # Engine pengerjaan Latihan Pemahaman berbasis skor
│   ├── refleksi_submitter.py         # Form filler Cerita Reflektif dengan paste clipboard
│   ├── posttest_solver.py            # Engine pengerjaan Post Test modul akurasi 100%
│   └── verifier.py                   # Pemeriksa status topik dan pengambil screenshot bukti
│
└── references/                       # Basis data pengetahuan & panduan teknis
    ├── pmm_pedagogy_guide.md         # Rangkuman konsep pedagogi KHD, SOLO, Asesmen & PM
    └── troubleshooting_guide.md      # Solusi kendala teknis nyata (PowerShell, UIA, Coordinates)
```

---

## 🛠️ Persyaratan Sistem

- **Sistem Operasi:** Windows 10 atau Windows 11 (64-bit).
- **Python:** Versi 3.10 atau lebih tinggi.
- **Browser:** Google Chrome (telah login ke akun Belajar.id / Platform Merdeka Mengajar).
- **Desktop Automation Engine:** `agent-desktop-win32-x64.exe` (tersedia via package `agent-desktop`).

---

## ⚡ Panduan Cepat (Quick Start)

### 1. Menjalankan Otomasi Video
Untuk menuntaskan video pembelajaran pada materi yang sedang aktif:
```bash
python scripts/video_runner.py "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/video/<ID>?recordProgress=true"
```

### 2. Menjalankan Otomasi Bahan Bacaan / PDF
Untuk menyelesaikan dokumen bacaan berhalaman:
```bash
python scripts/text_runner.py "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/text/<ID>?recordProgress=true"
```

### 3. Menyelesaikan Latihan Pemahaman (Kuis)
Buka halaman kuis di Chrome, lalu jalankan:
```bash
python scripts/quiz_solver.py
```

### 4. Mengunggah Cerita Reflektif
```bash
python scripts/refleksi_submitter.py "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/refleksi/<ID>" "Teks refleksi Anda di sini..."
```

### 5. Memverifikasi Topik & Mengambil Bukti Screenshot
```bash
python scripts/verifier.py "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/topik/<TOPIK_ID>"
```

---

## 📊 Contoh Alur Penuh (End-to-End Orchestration)

Berikut adalah contoh skrip orkestrasi lengkap untuk menyelesaikan satu modul pelatihan secara otomatis:

```python
import time
from scripts.navigator import navigate_to
from scripts.video_runner import complete_video
from scripts.text_runner import complete_text_material
from scripts.quiz_solver import solve_quiz
from scripts.refleksi_submitter import submit_refleksi
from scripts.posttest_solver import solve_posttest
from scripts.verifier import verify_topic

# 1. Buka materi video & selesaikan
complete_video("https://guru.kemendikdasmen.go.id/pelatihan-mandiri/video/100?recordProgress=true")

# 2. Buka materi bacaan & balik halaman
complete_text_material("https://guru.kemendikdasmen.go.id/pelatihan-mandiri/text/200?recordProgress=true")

# 3. Kerjakan Latihan Pemahaman
navigate_to("https://guru.kemendikdasmen.go.id/pelatihan-mandiri/quiz/300")
solve_quiz()

# 4. Kirim Cerita Reflektif
submit_refleksi(
    "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/refleksi/300",
    "Melalui pembelajaran ini, saya memahami pentingnya pendekatan yang berkesadaran, bermakna, dan menyenangkan bagi murid."
)

# 5. Kerjakan Post Test Modul
kunci_jawaban = [
    "Kompetensi literasi",
    "di depan memberi teladan",
    "diri sendiri",
    "memiliki keyakinan untuk dapat terus berkembang"
]
solve_posttest("https://guru.kemendikdasmen.go.id/pelatihan-mandiri/modul/24/post-test", kunci_jawaban, proof_dir="./bukti")

# 6. Verifikasi Topik Selesai & Unduh Surat
verify_topic("https://guru.kemendikdasmen.go.id/pelatihan-mandiri/topik/1", proof_dir="./bukti")
```

---

## 💡 Best Practices & Tips

1. **Jaga Visibilitas Jendela Chrome:** Pastikan jendela Chrome tidak di-minimize saat script dijalankan, agar UIA dapat merender accessibility tree secara akurat.
2. **Koordinat Multi-Monitor:** Jika Chrome dibuka di monitor sekunder (posisi x negatif), koordinat klik tetap bekerja secara proporsional berkat sistem koordinat desktop terpadu.
3. **Penyusunan Refleksi:** Hindari jawaban pendek satu kata ("sudah", "baik"). Tulis refleksi bermakna 2-3 kalimat agar akun pendidik memiliki reputasi aktivitas yang unggul.

---

## 📜 Lisensi & Kontribusi

Dibuat untuk memfasilitasi peningkatan kompetensi guru di Indonesia melalui pemanfaatan AI Agent yang efisien dan bertanggung jawab.
