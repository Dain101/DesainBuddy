"""Pengujian otomatis untuk bagian logika (tanpa Streamlit dan tanpa internet).
Jalankan dengan:  python uji_logika.py
"""
import json
import os
import tempfile
import unittest

import logika as lg


class UjiMateri(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.indeks = lg.IndeksMateri()

    def test_semua_bab_terbaca(self):
        self.assertEqual(len(self.indeks.judul_bab), 6)
        self.assertEqual(len(self.indeks.daftar_bab_belajar()), 5)
        self.assertIn(lg.BAB_PRAKTIK, self.indeks.judul_bab)

    def test_pencarian_relevan(self):
        kasus = {
            "apa bedanya RGB dan CMYK": "03_warna",
            "apa itu kerning dan leading": "04_tipografi",
            "kenapa ruang kosong penting di tata letak": "05_tata_letak",
            "apa bedanya gambar raster dan vektor": "01_pengantar_desain_grafis",
            "apa itu keseimbangan simetris": "02_elemen_prinsip_desain",
            "bagaimana rubrik penilaian poster canva": "06_praktik_poster_canva",
        }
        for pertanyaan, bab_diharapkan in kasus.items():
            hasil = self.indeks.cari(pertanyaan, k=3)
            self.assertTrue(hasil, f"Tidak ada hasil untuk: {pertanyaan}")
            self.assertEqual(hasil[0][0]["kunci"], bab_diharapkan, f"Salah bab untuk: {pertanyaan}")

    def test_pertanyaan_di_luar_topik(self):
        hasil = self.indeks.cari("resep nasi goreng spesial", k=3)
        self.assertEqual(hasil, [])

    def test_bonus_bab_terpilih(self):
        hasil = self.indeks.cari("jelaskan dasarnya", kunci_bab="04_tipografi", k=3)
        self.assertTrue(hasil)
        self.assertEqual(hasil[0][0]["kunci"], "04_tipografi")

    def test_format_konteks(self):
        hasil = self.indeks.cari("apa itu serif", k=2)
        teks = lg.format_konteks(hasil)
        self.assertTrue(teks.startswith("KONTEKS MATERI"))
        self.assertIn("[1]", teks)
        self.assertIn("tidak ada potongan", lg.format_konteks([]))


class UjiKuis(unittest.TestCase):
    def test_integritas_soal(self):
        soal = lg.muat_kuis()
        kunci_bab = set(lg.IndeksMateri().judul_bab)
        id_terlihat = set()
        self.assertEqual(len(soal), 20)
        for s in soal:
            self.assertNotIn(s["id"], id_terlihat)
            id_terlihat.add(s["id"])
            self.assertIn(s["bab"], kunci_bab)
            self.assertEqual(len(s["pilihan"]), 4)
            self.assertEqual(len(set(s["pilihan"])), 4)
            self.assertIn(s["jawaban"], range(4))
            self.assertTrue(s["penjelasan"].strip())

    def test_kode_siswa(self):
        self.assertTrue(lg.kode_valid("S01"))
        self.assertTrue(lg.kode_valid(" s_12 "))
        self.assertFalse(lg.kode_valid("A"))
        self.assertFalse(lg.kode_valid("nama lengkap saya"))
        self.assertFalse(lg.kode_valid(""))
        self.assertFalse(lg.kode_valid(None))


class UjiPrivasi(unittest.TestCase):
    def test_penyamaran(self):
        teks, ada = lg.samarkan_data_pribadi("Hubungi aku di budi.santoso@mail.com atau 081234567890 ya")
        self.assertTrue(ada)
        self.assertNotIn("@", teks)
        self.assertNotIn("0812", teks)
        teks, ada = lg.samarkan_data_pribadi("NISN-ku 0012345678901234")
        self.assertTrue(ada)
        self.assertNotIn("0012345678901234", teks)

    def test_pesan_biasa_tidak_diubah(self):
        asli = "Apa bedanya serif dan sans-serif? Aku pakai 2 font dan 3 warna."
        teks, ada = lg.samarkan_data_pribadi(asli)
        self.assertFalse(ada)
        self.assertEqual(teks, asli)


class UjiDatabase(unittest.TestCase):
    def setUp(self):
        self.berkas = os.path.join(tempfile.mkdtemp(), "uji.db")
        lg.siapkan_db(self.berkas)

    def test_pesan_rating_dan_kuis(self):
        id1 = lg.simpan_pesan("S01", "Belajar", "Warna", "siswa", "halo", jalur=self.berkas)
        id2 = lg.simpan_pesan("S01", "Belajar", "Warna", "asisten", "hai", "Warna > Skema", jalur=self.berkas)
        self.assertNotEqual(id1, id2)
        lg.beri_rating(id2, 1, jalur=self.berkas)
        lg.simpan_kuis("S01", "03_warna", "03q1", "CMYK", True, 1, jalur=self.berkas)
        lg.simpan_kuis("S02", "03_warna", "03q2", "RGB", False, 3, jalur=self.berkas)

        ring = lg.ringkasan(self.berkas)
        self.assertEqual(ring["siswa_aktif"], 1)
        self.assertEqual(ring["pesan_siswa"], 1)
        self.assertEqual(ring["rating_naik"], 1)
        self.assertEqual(ring["rating_turun"], 0)
        self.assertEqual(ring["kuis_per_bab"][0][:3], ("03_warna", 2, 1))

        kolom, baris = lg.baca_tabel("pesan", self.berkas)
        self.assertIn("rating", kolom)
        self.assertEqual(len(baris), 2)
        with self.assertRaises(ValueError):
            lg.baca_tabel("pesan; DROP TABLE pesan", self.berkas)

    def test_isi_dengan_tanda_kutip_aman(self):
        lg.simpan_pesan("S01", "Tanya Bebas", "x", "siswa", "kata 'aneh' \"ini\"; DROP TABLE pesan;--", jalur=self.berkas)
        kolom, baris = lg.baca_tabel("pesan", self.berkas)
        self.assertEqual(len(baris), 1)


class UjiInstruksi(unittest.TestCase):
    def test_semua_mode_tersusun(self):
        konteks = lg.format_konteks([])
        for mode in (lg.MODE_BELAJAR, lg.MODE_TANYA, lg.MODE_PRAKTIK):
            teks = lg.susun_instruksi(mode, "Warna dalam Desain", konteks)
            self.assertIn("DesainBuddy", teks)
            self.assertIn("KONTEKS MATERI", teks)
        self.assertIn("Warna dalam Desain", lg.susun_instruksi(lg.MODE_BELAJAR, "Warna dalam Desain", konteks))

    def test_instruksi_petunjuk(self):
        soal = lg.muat_kuis()[0]
        teks = lg.susun_instruksi(lg.MODE_PETUNJUK, "Pengantar", lg.format_konteks([]), level=2, soal=soal)
        self.assertIn("level 2", teks)
        self.assertIn("RAHASIA", teks)
        self.assertIn(soal["pilihan"][soal["jawaban"]], teks)


if __name__ == "__main__":
    unittest.main(verbosity=2)
