# Agent Pelatihan: Otomatisasi Pelatihan Mandiri PMM

> **Skill Agent Pintar untuk Otomatisasi End-to-End Pelatihan Mandiri Guru pada Platform Merdeka Mengajar (PMM - Kemendikdasmen).**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-informational.svg)](https://microsoft.com)
[![Automation](https://img.shields.io/badge/Engine-UIA%20%2B%20Headed%20Desktop-success.svg)]()
[![PMM Compatible](https://img.shields.io/badge/Target-PMM%20Kemendikdasmen-orange.svg)](https://guru.kemendikdasmen.go.id/)

---

## Tentang Skill Ini

`agent-pelatihan` adalah kumpulan pustaka dan panduan otomasi yang dirancang khusus untuk mempermudah dan mempercepat penyelesaian topik-topik pelatihan pada **Platform Merdeka Mengajar (PMM)**.

Skill ini secara otomatis mengendalikan browser Google Chrome untuk:
1. **Menonton Video Pembelajaran:** Memutar dan menyelesaikan video YouTube tersemat menggunakan pintasan scrubbing cerdas (`9` + panah kanan).
2. **Membaca Dokumen & PDF:** Membalik seluruh halaman dokumen dan melakukan scroll hingga status terbaca 100%.
3. **Mengerjakan Latihan Pemahaman Cerdas (Kuis):** Menjawab pertanyaan kuis secara otomatis dengan analisis konteks pertanyaan (deteksi negasi/pengecualian) dan **Adaptive Elimination Loop** (otomatis mencoba opsi lain bila muncul *"Coba Lagi"* hingga 100% tuntas).
4. **Mengisi Cerita Reflektif:** Mengunggah esai refleksi yang mendalam, bermutu tinggi, dan kontekstual dengan event sintetis agar form terdeteksi aktif.
5. **Menyelesaikan Post Test Resilien (MUI Carousel Slider):** Menavigasi carousel soal, ekstraksi soal dinamis dari DOM, pemilihan jawaban via Fuzzy Option Matcher dan UIA Focus + Space, penanganan modal dialog submit dengan polling guard, serta verifikasi ketat kelulusan (`testPassed=true`).
6. **Verifikasi & Surat Keterangan:** Memverifikasi centang hijau seluruh modul dan memastikan tautan **"Unduh Surat Keterangan Selesai Topik"** telah aktif.

---

## Fitur Unggulan

- **Headed & Accessibility Tree Driven:** Menggunakan Windows UI Automation (UIA) dan input fisik untuk interaksi yang 100% andal dan tidak mudah terblokir.
- **Adaptive Elimination & Retry Loop (Kuis):** Bebas macet dan bergaransi 100% benar; otomatis membaca pertanyaan bertipe negasi (*kecuali*, *bukan*), mengeliminasi opsi salah saat muncul tombol *"Coba Lagi"*, dan memilih opsi sisa hingga tombol *"Lanjut"* aktif.
- **Carousel-Aware Post Test Engine dengan Strict Pass Check:** Mendukung slider soal 1-by-1, ekstraksi butir soal dinamis dari DOM, Fuzzy Option Matcher, polling modal konfirmasi submit, dan validasi kelulusan hasil post test.
- **Deterministic Radio Selection:** Seleksi pilihan ganda langsung pada node `radiobutton` via `focus` + `space`, menghilangkan resiko salah klik akibat pembungkusan teks pilihan yang panjang.
- **Scrubbing Video Cepat:** Tidak perlu menunggu video 10-20 menit; diselesaikan dalam hitungan detik dengan validasi playback backend.
- **Pedagogical Keyword Engine:** Algoritma skoring cerdas untuk kuis yang mengutamakan nilai-nilai Kurikulum Merdeka, Pemikiran Ki Hadjar Dewantara, dan Taksonomi SOLO.
- **Kebal Focus Trap:** Dilengkapi mekanisme pelepasan fokus Omnibox Chrome otomatis (`escape` + neutral click).
- **Regulasi PMM Terkini:** Mengikuti aturan baru di mana **Aksi Nyata tidak lagi diwajibkan**, melainkan langsung berhak mendapatkan **Surat Keterangan Selesai Topik**.

---

## Struktur Direktori

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
│   ├── refleksi_submitter.py         # Form filler Cerita Reflektif dengan paste & synthetic event
│   ├── posttest_solver.py            # Engine pengerjaan Post Test Carousel & Modal Konfirmasi
│   ├── orchestrator.py               # Pipeline otomasi modul end-to-end
│   └── verifier.py                   # Pemeriksa status topik dan pengambil screenshot bukti
│
└── references/                       # Basis data pengetahuan & panduan teknis
    ├── pmm_pedagogy_guide.md         # Rangkuman konsep pedagogi KHD, SOLO, Asesmen & PM
    └── troubleshooting_guide.md      # Solusi kendala teknis nyata (Carousel, Radio wrapping, Modal)
```

---

## Persyaratan Sistem

- **Sistem Operasi:** Windows 10 atau Windows 11 (64-bit).
- **Python:** Versi 3.10 atau lebih tinggi.
- **Browser:** Google Chrome (telah login ke akun Belajar.id / Platform Merdeka Mengajar).
- **Desktop Automation Engine:** `agent-desktop-win32-x64.exe` (tersedia via package `agent-desktop`).

---

## Panduan Cepat (Quick Start)

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

### 5. Menyelesaikan Post Test Carousel
```python
from scripts.posttest_solver import solve_posttest_carousel

kunci_jawaban = {
    1: "rehat, refleksi, rencana",
    2: "Pengetahuan yang komprehensif",
    3: "Salah"
}
solve_posttest_carousel(
    "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/modul/96/post-test",
    kunci_jawaban,
    proof_dir="./bukti",
    proof_prefix="bukti_posttest3"
)
```

### 6. Memverifikasi Topik & Mengambil Bukti Screenshot
```bash
python scripts/verifier.py "https://guru.kemendikdasmen.go.id/pelatihan-mandiri/topik/<TOPIK_ID>"
```

---

## Contoh Alur Penuh (End-to-End Orchestration)

Berikut adalah contoh skrip menggunakan `orchestrator.py` untuk menyelesaikan satu modul pelatihan secara otomatis:

```python
from scripts.orchestrator import run_module_pipeline

# 1. Definisikan urutan materi modul
materi_modul = [
    ('video', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/video/266?...recordProgress=true'),
    ('video', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/video/267?...recordProgress=true'),
    ('text', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/text/118?...recordProgress=true'),
    ('quiz', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/quiz/463?...'),
    ('refleksi', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/refleksi/463?...', 'Refleksi saya...'),
    ('video', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/video/268?...recordProgress=true'),
    ('video', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/video/269?...recordProgress=true'),
    ('text', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/text/128?...recordProgress=true'),
    ('text', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/text/119?...recordProgress=true'),
    ('quiz', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/quiz/464?...'),
    ('refleksi', 'https://guru.kemendikdasmen.go.id/pelatihan-mandiri/refleksi/464?...', 'Refleksi saya...')
]

# 2. Definisikan kunci jawaban Post Test
kunci_posttest = {
    1: "Melakukan refleksi dengan memetakan situasi, mencari tahu apa yang perlu dilakukan, lalu melakukan aksi.",
    2: "Carilah teman",
    3: "Memeriksa finalisasi kesiapan perangkat pembelajaran",
    4: "bisa lebih tenang dan jujur saat berdialog dengan diri"
}

# 3. Jalankan pipeline modul hingga selesai
run_module_pipeline(
    modul_url="https://guru.kemendikdasmen.go.id/pelatihan-mandiri/modul/97",
    materials_sequence=materi_modul,
    posttest_answers=kunci_posttest,
    proof_dir="./bukti",
    modul_label="modul4"
)
```

---

## Best Practices & Tips

1. **Jaga Visibilitas Jendela Chrome:** Pastikan jendela Chrome tidak di-minimize saat script dijalankan, agar UIA dapat merender accessibility tree secara akurat.
2. **Koordinat Multi-Monitor:** Jika Chrome dibuka di monitor sekunder (posisi x negatif), runner tetap bekerja proporsional berkat sistem koordinat desktop terpadu.
3. **Penyusunan Refleksi:** Hindari jawaban pendek satu kata ("sudah", "baik"). Tulis refleksi bermakna minimal 50 karakter agar validasi platform terpenuhi dan tombol Simpan aktif.

---

## Lisensi & Kontribusi

Dibuat untuk memfasilitasi peningkatan kompetensi guru di Indonesia melalui pemanfaatan AI Agent yang efisien dan bertanggung jawab.
