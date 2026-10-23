"""DesainBuddy: chatbot pembelajaran desain grafis.

Jalankan di laptop dengan perintah:  streamlit run app.py
Atau pasang online lewat Streamlit Community Cloud (lihat PANDUAN.md).
"""
import hmac
import os
import time

import pandas as pd
import streamlit as st

import logika as lg

st.set_page_config(page_title="DesainBuddy", page_icon="🎨", layout="centered")


# ---------------------------------------------------------------
# Pengaturan dan sumber daya
# ---------------------------------------------------------------
def ambil_rahasia(nama, bawaan=""):
    """Baca nilai dari Secrets Streamlit. Kalau tidak ada, coba variabel lingkungan."""
    try:
        return str(st.secrets[nama])
    except Exception:
        return os.environ.get(nama, bawaan)


NAMA_MODEL = ambil_rahasia("GEMINI_MODEL", "gemini-3.8-flash")


@st.cache_resource
def indeks():
    return lg.IndeksMateri()


@st.cache_resource
def semua_soal():
    return lg.muat_kuis()


@st.cache_resource
def siapkan_penyimpanan():
    lg.siapkan_db()
    return True


@st.cache_resource
def klien_gemini():
    kunci = ambil_rahasia("GEMINI_API_KEY")
    if not kunci:
        return None
    from google import genai

    return genai.Client(api_key=kunci)


def siapkan_state():
    bawaan = {
        "kode": None,
        "riwayat": {m: [] for m in lg.SEMUA_MODE},
        "jumlah_pesan": 0,
        "petunjuk": {},
        "hasil_kuis": {},
        "gambar_terkirim": None,
        "admin": False,
    }
    for kunci, nilai in bawaan.items():
        if kunci not in st.session_state:
            st.session_state[kunci] = nilai


# ---------------------------------------------------------------
# Pemanggil AI
# ---------------------------------------------------------------
def tanya_gemini(riwayat, instruksi, gambar=None):
    """Kirim riwayat percakapan ke Gemini dan kembalikan teks jawabannya."""
    from google.genai import types

    klien = klien_gemini()
    if klien is None:
        raise RuntimeError("Kunci API belum diisi di Secrets (GEMINI_API_KEY).")

    potongan = list(riwayat[-8:])
    while potongan and potongan[0]["peran"] != "siswa":
        potongan = potongan[1:]

    isi = []
    for i, pesan in enumerate(potongan):
        bagian = [types.Part.from_text(text=pesan["isi"])]
        if gambar is not None and i == len(potongan) - 1:
            bagian.append(types.Part.from_bytes(data=gambar["byte"], mime_type=gambar["tipe"]))
        peran = "user" if pesan["peran"] == "siswa" else "model"
        isi.append(types.Content(role=peran, parts=bagian))

    konfigurasi = types.GenerateContentConfig(system_instruction=instruksi, temperature=0.4)
    for percobaan in range(2):
        try:
            respons = klien.models.generate_content(
                model=NAMA_MODEL, contents=isi, config=konfigurasi
            )
            teks = (respons.text or "").strip()
            if not teks:
                raise RuntimeError("Model tidak mengembalikan teks. Mungkin ditahan filter keamanan.")
            return teks
        except Exception:
            if percobaan == 1:
                raise
            time.sleep(2)


def tampilkan_galat(e):
    detail = str(e)
    if "Kunci API" in detail or "API key" in detail or "API_KEY" in detail:
        st.error("Kunci API belum benar. Minta peneliti memeriksa Secrets.")
    elif "429" in detail or "RESOURCE_EXHAUSTED" in detail:
        st.error("Kuota AI sedang penuh. Tunggu satu menit lalu coba lagi.")
    elif "404" in detail or "NOT_FOUND" in detail:
        st.error("Nama model AI tidak ditemukan. Minta peneliti memperbarui GEMINI_MODEL di Secrets.")
    else:
        st.error("AI belum bisa menjawab. Coba lagi sebentar lagi.")
    with st.expander("Detail teknis (untuk peneliti)"):
        st.code(detail[:1500])


# ---------------------------------------------------------------
# Halaman masuk
# ---------------------------------------------------------------
def halaman_masuk():
    st.title("🎨 DesainBuddy")
    st.write(
        "Teman belajar desain grafis. Tanya konsep, kerjakan latihan, "
        "lalu minta umpan balik untuk poster buatanmu."
    )
    with st.form("form_masuk"):
        kode = st.text_input("Kode siswa", placeholder="Contoh: S01", max_chars=12)
        setuju = st.checkbox(
            "Aku paham bahwa percakapanku direkam tanpa nama untuk keperluan penelitian. "
            "Aku tidak akan menulis data pribadi seperti nama lengkap, alamat, atau nomor HP."
        )
        kirim = st.form_submit_button("Mulai belajar")
    if kirim:
        if not lg.kode_valid(kode):
            st.error("Kode siswa hanya boleh huruf dan angka, 2 sampai 12 karakter.")
        elif not setuju:
            st.warning("Centang kotak persetujuan dulu ya.")
        else:
            st.session_state.kode = kode.strip().upper()
            st.rerun()
    st.caption("DesainBuddy adalah AI dan bisa keliru. Kalau ragu, tanyakan ke gurumu.")


# ---------------------------------------------------------------
# Komponen chat
# ---------------------------------------------------------------
def beri_nilai(mode, nomor, nilai):
    pesan = st.session_state.riwayat[mode][nomor]
    pesan["rating"] = nilai
    lg.beri_rating(pesan["id_db"], nilai)


def tampilkan_rating(mode, nomor, pesan):
    if pesan.get("rating") is not None:
        st.caption("Terima kasih atas penilaianmu.")
        return
    kolom1, kolom2, _ = st.columns([1, 1, 6])
    kolom1.button("👍", key=f"suka_{mode}_{nomor}", on_click=beri_nilai, args=(mode, nomor, 1))
    kolom2.button("👎", key=f"kurang_{mode}_{nomor}", on_click=beri_nilai, args=(mode, nomor, -1))


def tampilkan_riwayat(mode):
    for nomor, pesan in enumerate(st.session_state.riwayat[mode]):
        siswa = pesan["peran"] == "siswa"
        with st.chat_message("user" if siswa else "assistant", avatar="🙂" if siswa else "🎨"):
            st.markdown(pesan["isi"])
            if not siswa:
                if pesan.get("sumber"):
                    with st.expander("Sumber materi"):
                        for baris in pesan["sumber"]:
                            st.caption(baris)
                tampilkan_rating(mode, nomor, pesan)


def kirim_pesan(mode, kunci_bab, judul_bab, teks, gambar=None):
    """Proses satu pesan siswa: samarkan data pribadi, cari materi, tanya AI, catat log."""
    kode = st.session_state.kode
    bersih, ada_pribadi = lg.samarkan_data_pribadi(teks[: lg.MAKS_PANJANG_PESAN])
    if ada_pribadi:
        st.warning("Aku menyamarkan data pribadi di pesanmu. Jangan bagikan data pribadi ya.")

    st.session_state.jumlah_pesan += 1
    st.session_state.riwayat[mode].append({"peran": "siswa", "isi": bersih})
    lg.simpan_pesan(kode, mode, judul_bab, "siswa", bersih + (" [gambar diunggah]" if gambar else ""))

    with st.chat_message("user", avatar="🙂"):
        st.markdown(bersih)

    if mode == lg.MODE_PRAKTIK:
        konteks = lg.format_konteks([({"bab": judul_bab, "subjudul": "Rubrik dan brief", "isi": indeks().teks_bab(lg.BAB_PRAKTIK)}, 1.0)])
        sumber = ["Praktik Membuat Poster di Canva > Rubrik dan brief"]
    else:
        hasil = indeks().cari(bersih, kunci_bab)
        konteks = lg.format_konteks(hasil)
        sumber = lg.label_sumber(hasil)

    instruksi = lg.susun_instruksi(mode, judul_bab, konteks)
    with st.chat_message("assistant", avatar="🎨"):
        try:
            with st.spinner("DesainBuddy sedang berpikir..."):
                jawaban = tanya_gemini(st.session_state.riwayat[mode], instruksi, gambar)
        except Exception as e:
            st.session_state.riwayat[mode].pop()
            st.session_state.jumlah_pesan -= 1
            tampilkan_galat(e)
            return
    id_db = lg.simpan_pesan(kode, mode, judul_bab, "asisten", jawaban, " | ".join(sumber))
    st.session_state.riwayat[mode].append(
        {"peran": "asisten", "isi": jawaban, "sumber": sumber, "id_db": id_db, "rating": None}
    )
    st.rerun()


def batas_tercapai():
    if st.session_state.jumlah_pesan >= lg.MAKS_PESAN_PER_SESI:
        st.info(
            "Batas pesan untuk sesi ini sudah tercapai. "
            "Muat ulang halaman untuk memulai sesi baru."
        )
        return True
    return False


# ---------------------------------------------------------------
# Halaman per mode
# ---------------------------------------------------------------
def halaman_chat(mode, kunci_bab, judul_bab):
    mulai = False
    if mode == lg.MODE_BELAJAR and not st.session_state.riwayat[mode]:
        st.write(f"Bab yang dipilih: **{judul_bab}**")
        mulai = st.button("Mulai belajar bab ini")
    tampilkan_riwayat(mode)
    if batas_tercapai():
        return
    prompt = st.chat_input("Tulis pertanyaanmu di sini...")
    if mulai:
        prompt = f"Ajarkan aku bab {judul_bab} dari dasar, mulai dari langkah pertama."
    if prompt:
        kirim_pesan(mode, kunci_bab, judul_bab, prompt)


def halaman_praktik(judul_praktik):
    with st.expander("Lihat brief tugas dan rubrik", expanded=not st.session_state.riwayat[lg.MODE_PRAKTIK]):
        st.markdown(indeks().teks_bab(lg.BAB_PRAKTIK))
    berkas = st.file_uploader(
        "Unggah posterku (PNG atau JPG, maksimal 4 MB, tanpa foto wajah)",
        type=["png", "jpg", "jpeg"],
    )
    gambar = None
    if berkas is not None:
        if berkas.size > 4 * 1024 * 1024:
            st.error("Ukuran gambar lebih dari 4 MB. Perkecil dulu lalu unggah lagi.")
        else:
            st.image(berkas, caption="Poster yang akan dinilai", width=260)
            tanda = (berkas.name, berkas.size)
            if tanda != st.session_state.gambar_terkirim:
                gambar = {"byte": berkas.getvalue(), "tipe": berkas.type or "image/png"}
    tampilkan_riwayat(lg.MODE_PRAKTIK)
    if batas_tercapai():
        return
    prompt = st.chat_input("Tulis pesan, misalnya: tolong nilai posterku")
    if prompt:
        sebelumnya = st.session_state.gambar_terkirim
        if gambar is not None and berkas is not None:
            st.session_state.gambar_terkirim = (berkas.name, berkas.size)
        kirim_pesan(lg.MODE_PRAKTIK, lg.BAB_PRAKTIK, judul_praktik, prompt, gambar)
        # Baris di bawah hanya tercapai kalau pengiriman gagal (kalau berhasil, halaman dimuat ulang)
        st.session_state.gambar_terkirim = sebelumnya


def periksa_jawaban(soal, bab_kunci):
    sid = soal["id"]
    pilihan = st.session_state.get(f"jwb_{sid}")
    if pilihan is None:
        return
    benar = pilihan == soal["jawaban"]
    st.session_state.hasil_kuis[sid] = (pilihan, benar)
    jumlah_petunjuk = len(st.session_state.petunjuk.get(sid, []))
    lg.simpan_kuis(st.session_state.kode, bab_kunci, sid, soal["pilihan"][pilihan], benar, jumlah_petunjuk)


def halaman_latihan(bab_kunci, judul_bab):
    daftar = [s for s in semua_soal() if s["bab"] == bab_kunci]
    if not daftar:
        st.info("Belum ada soal untuk bab ini.")
        return
    st.subheader(f"Latihan: {judul_bab}")
    benar_total = sum(1 for s in daftar if st.session_state.hasil_kuis.get(s["id"], (None, False))[1])
    dijawab = sum(1 for s in daftar if s["id"] in st.session_state.hasil_kuis)
    st.progress(dijawab / len(daftar), text=f"Terjawab {dijawab} dari {len(daftar)}, benar {benar_total}")

    for soal in daftar:
        sid = soal["id"]
        terkunci = sid in st.session_state.hasil_kuis
        with st.container(border=True):
            st.markdown(f"**{soal['soal']}**")
            st.radio(
                "Pilih jawaban",
                options=list(range(len(soal["pilihan"]))),
                format_func=lambda x, s=soal: s["pilihan"][x],
                index=None,
                key=f"jwb_{sid}",
                disabled=terkunci,
                label_visibility="collapsed",
            )
            daftar_petunjuk = st.session_state.petunjuk.setdefault(sid, [])
            for nomor, teks in enumerate(daftar_petunjuk, start=1):
                st.info(f"Petunjuk {nomor}: {teks}")

            if terkunci:
                _, ok = st.session_state.hasil_kuis[sid]
                if ok:
                    st.success("Benar. " + soal["penjelasan"])
                else:
                    kunci = soal["pilihan"][soal["jawaban"]]
                    st.error(f"Belum tepat. Jawaban yang benar: {kunci}. {soal['penjelasan']}")
                continue

            kolom1, kolom2 = st.columns(2)
            cek = kolom1.button("Periksa jawaban", key=f"cek_{sid}")
            minta = False
            if len(daftar_petunjuk) < 3:
                minta = kolom2.button(f"Minta petunjuk ({len(daftar_petunjuk)}/3)", key=f"hint_{sid}")

            if cek:
                if st.session_state.get(f"jwb_{sid}") is None:
                    st.warning("Pilih satu jawaban dulu.")
                else:
                    periksa_jawaban(soal, bab_kunci)
                    st.rerun()

            if minta and not batas_tercapai():
                level = len(daftar_petunjuk) + 1
                konteks = lg.format_konteks(
                    [({"bab": judul_bab, "subjudul": "Materi bab", "isi": indeks().teks_bab(bab_kunci)}, 1.0)]
                )
                instruksi = lg.susun_instruksi(lg.MODE_PETUNJUK, judul_bab, konteks, level=level, soal=soal)
                berhasil = False
                try:
                    with st.spinner("Menyiapkan petunjuk..."):
                        teks = tanya_gemini(
                            [{"peran": "siswa", "isi": f"Aku butuh petunjuk level {level} untuk soal ini."}],
                            instruksi,
                        )
                    daftar_petunjuk.append(teks)
                    st.session_state.jumlah_pesan += 1
                    lg.simpan_pesan(st.session_state.kode, lg.MODE_PETUNJUK, judul_bab, "asisten", f"[{sid}] {teks}")
                    berhasil = True
                except Exception as e:
                    tampilkan_galat(e)
                if berhasil:
                    st.rerun()


# ---------------------------------------------------------------
# Panel peneliti
# ---------------------------------------------------------------
def cek_admin():
    sandi = ambil_rahasia("ADMIN_PASSWORD")
    with st.sidebar.expander("Panel peneliti"):
        if not sandi:
            st.caption("Isi ADMIN_PASSWORD di Secrets untuk membuka panel ini.")
            return
        if not st.session_state.admin:
            masukan = st.text_input("Kata sandi", type="password", key="sandi_admin")
            if masukan and hmac.compare_digest(masukan.encode(), sandi.encode()):
                st.session_state.admin = True
                st.rerun()
            return
        st.toggle("Tampilkan panel peneliti", key="tampil_admin")


def halaman_admin():
    st.title("Panel peneliti")
    st.warning(
        "Data di server gratis bisa hilang saat aplikasi dimulai ulang. "
        "Unduh kedua berkas CSV di bawah ini secara rutin, misalnya setiap selesai pertemuan."
    )
    ring = lg.ringkasan()
    kolom = st.columns(3)
    kolom[0].metric("Siswa aktif", ring["siswa_aktif"])
    kolom[1].metric("Pesan siswa", ring["pesan_siswa"])
    kolom[2].metric("Rating 👍 / 👎", f"{ring['rating_naik']} / {ring['rating_turun']}")

    st.subheader("Hasil kuis per bab")
    if ring["kuis_per_bab"]:
        tabel = pd.DataFrame(
            ring["kuis_per_bab"],
            columns=["Bab", "Jumlah jawaban", "Jumlah benar", "Rata-rata petunjuk"],
        )
        st.dataframe(tabel, hide_index=True)
    else:
        st.caption("Belum ada jawaban kuis.")

    st.subheader("Unduh data mentah")
    for nama, label in (("pesan", "Percakapan"), ("kuis", "Jawaban kuis")):
        kolom_tabel, baris = lg.baca_tabel(nama)
        df = pd.DataFrame(baris, columns=kolom_tabel)
        st.download_button(
            f"Unduh {label} (CSV)",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{nama}.csv",
            mime="text/csv",
            key=f"unduh_{nama}",
        )


# ---------------------------------------------------------------
# Program utama
# ---------------------------------------------------------------
def main():
    siapkan_state()
    siapkan_penyimpanan()

    if not st.session_state.kode:
        halaman_masuk()
        return

    cek_admin()
    if st.session_state.admin and st.session_state.get("tampil_admin"):
        halaman_admin()
        return

    materi = indeks()
    st.sidebar.markdown(f"**Kode siswa:** {st.session_state.kode}")
    mode = st.sidebar.radio(
        "Mode belajar",
        lg.SEMUA_MODE,
        captions=[
            "Dijelaskan dari dasar",
            "Kuis dengan petunjuk",
            "Poster di Canva dan umpan balik",
            "Tanya apa saja soal desain",
        ],
    )

    st.title("🎨 DesainBuddy")
    if mode == lg.MODE_PRAKTIK:
        halaman_praktik(materi.judul_bab[lg.BAB_PRAKTIK])
    else:
        daftar_bab = materi.daftar_bab_belajar()
        kunci_bab = st.sidebar.selectbox("Bab", daftar_bab, format_func=lambda k: materi.judul_bab[k])
        judul_bab = materi.judul_bab[kunci_bab]
        if mode == lg.MODE_LATIHAN:
            halaman_latihan(kunci_bab, judul_bab)
        else:
            halaman_chat(mode, kunci_bab, judul_bab)

    if mode in (lg.MODE_BELAJAR, lg.MODE_TANYA, lg.MODE_PRAKTIK) and st.session_state.riwayat[mode]:
        if st.sidebar.button("Hapus percakapan mode ini"):
            st.session_state.riwayat[mode] = []
            st.rerun()
    st.sidebar.caption("DesainBuddy adalah AI dan bisa keliru. Kalau ragu, tanyakan ke gurumu.")


main()
