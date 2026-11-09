# Bike Sharing | Pola Permintaan 2011–2012

Analisis Capital Bikeshare untuk memilih jam redistribusi, menilai perubahan volume saat cuaca memburuk, dan memilih blok jam untuk uji promosi pengguna kasual. Notebook mengisi 40 sel yang sudah tersedia pada template proyek dan menyimpan hasil eksekusi, grafik, dan rekomendasi. Sel pemuatan membaca CSV dari folder proyek agar dapat dijalankan tanpa memasang Google Drive.

| Berkas | Isi |
| --- | --- |
| `notebook.ipynb` | Tiga pertanyaan SMART, wrangling, EDA, uji sensitivitas, segmentasi, dan action item |
| `dashboard/dashboard.py` | Dashboard dengan filter tanggal dan tipe hari |
| `dashboard/main_data.csv` | Data hasil cleaning untuk dashboard. Kolom `tingkat` memisahkan 731 baris harian dan 17.379 baris per jam. |
| `data/day.csv` |  dataset per harian |
| `data/hour.csv` | dataset per jam |
| `requirements.txt` | Dependensi dashboard dan notebook |
| `url.txt` | Isi dengan URL dashboard yang sudah aktif setelah deploy. |

## Jalankan secara lokal

Ekstrak ZIP, buka terminal di folder `submission` yang berisi README, lalu jalankan perintah ini. Proyek diuji dengan Python 3.10.

```sh
python -m venv .venv
```

Aktifkan lingkungan dengan `.venv\Scripts\Activate.ps1` di PowerShell atau `source .venv/bin/activate` di macOS/Linux.

```sh
python -m pip install -r requirements.txt
python -m streamlit run dashboard/dashboard.py
```

Buka alamat lokal yang ditampilkan Streamlit. Pilih rentang tanggal inklusif dan tipe hari di panel kiri. Seluruh ringkasan dan grafik mengikuti filter. Tab **Jam puncak** dapat dibatasi pada hari dengan 24 slot. Tab **Cuaca harian** menampilkan perbandingan mentah dan sebanding serta pilihan minimum hari per kategori. Tab **Segmentasi jam** menyediakan grafik seluruh sewa atau sewa kasual.

Untuk mengeksekusi ulang notebook, buka `notebook.ipynb` dari folder `submission` dan pilih **Run All**. Sel **Cleaning Data** membuat ulang `dashboard/main_data.csv`. Notebook juga dapat dijalankan dengan:

```sh
python -m nbconvert --to notebook --execute --inplace notebook.ipynb
```

## Deploy ke Streamlit Community Cloud

1. Ekstrak ZIP dan unggah isi folder `submission` ke root repositori GitHub. Sertakan `requirements.txt` dan `dashboard/main_data.csv`.
2. Di [Streamlit Community Cloud](https://share.streamlit.io/), pilih **Create app** lalu pilih repositori dan branch.
3. Isi **Main file path** dengan `dashboard/dashboard.py` dan pilih Python 3.12 di **Advanced settings**. Aplikasi membaca CSV yang ikut diunggah dan tidak memerlukan secret.
4. Klik **Deploy**, lalu periksa grafik dan filter pada URL aplikasi. Tempel URL aplikasi yang sudah aktif ke `url.txt` sebagai satu baris. [Panduan resmi](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Cara membaca metrik

- **Jam prioritas.** Notebook membandingkan tiga jam tersibuk per tipe hari pada periode gabungan, masing-masing tahun, dan hari dengan 24 slot. Slot tak tercatat dikeluarkan dari penyebut. Hari nonkerja mencakup akhir pekan dan hari libur.
- **Cuaca sebanding.** Perbandingan dengan kategori cerah dilakukan dalam kelompok tahun, musim, dan tipe hari. Hasil ditimbang menurut jumlah hari kategori pembanding dan dilaporkan bersama cakupannya. Hubungan ini bersifat deskriptif.
- **Promosi kasual.** Lima blok tetap dibandingkan berdasarkan sewa kasual per slot tercatat dan porsi kasual dari seluruh transaksi dalam blok. Ambang keputusan pada notebook merupakan asumsi untuk uji coba.

Total dan tren menggunakan tabel harian. Profil jam dan segmentasi menggunakan tabel per jam. Data historis ini merekam transaksi yang terjadi, tanpa ukuran ketersediaan sepeda atau permintaan yang gagal terpenuhi.

Sumber data: Hadi Fanaee-T (2013), [Bike Sharing, UCI Machine Learning Repository](https://doi.org/10.24432/C5W894), CC BY 4.0.
