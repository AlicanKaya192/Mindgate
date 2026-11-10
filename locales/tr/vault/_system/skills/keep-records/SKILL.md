---
name: kayitlari-tut
description: İkinci beyin — oturum kayıtlarını tara, bu konuşmayı gözden geçir, eksikleri vault'a işle, log, commit. Kullanıcı "kayıtları tut" dediğinde ya da büyük bir iş bitince kullan.
---

Vault: `{{VAULT}}`. Şema: vault `CLAUDE.md` (§7.8 oturum kayıtları, §10 git). Türkçe yaz; İngilizce terimlerin yanına parantez içinde Türkçesi.

1. Vault kökünde `{{PY}} -I _sistem/session_log.py scan` çalıştır.
2. `gelen/oturumlar/` altındaki her kaydı oku. **Bu konuşmanın kendisini de** gözden geçir. Vault'ta karşılığı olmayan şeyleri ilgili notlara işle:
   - fikir → `gelen/` (şablon `fikir`)
   - sorun/çözüm → `sorunlar/` (önce aynı sorun var mı ara; varsa "Tekrar görüldüğü yerler"e ekle)
   - teknik karar → projenin `kararlar/` ADR'si
   - ilerleme → `<proje>-ilerleme.md` tarihli girdi
   - yeni kural → `kurallar/genel-kurallar.md` ya da `<proje>-kurallar.md`
   - hassas olmayan profil bilgisi → `ben/`
   Zaten vault'ta olanı tekrar yazma. Emin olamadığını uydurma; gerekirse kayıttaki transkript yolundan ilgili kısmı oku.
   - Kullanıcıya sorulmuş ama cevaplanmamış soru, istenmiş onay/karar, ona bırakılmış iş ya da görmesi gereken bildirim → `gelen/bekleyenler.md`'ye `B-NNN` maddesi (sonunda `| sohbet: <sohbet başlığı> | proje: [[<proje>]]`) + log'a `bekleyen` girdisi (§7.10). Cevaplanmış/bitmiş olanları kapat (`[x]`, `✔ tarih`, log'a `tamam`).
3. Dokunulan notların `updated` alanını bugüne çek; yeni sayfaları `index.md`'ye ekle; yetim not bırakma.
4. İşlenen kayıtları **silme**, arşive taşı: `{{PY}} -I _sistem/session_log.py process <kayıt.md> ...` (kural #22: izinsiz silme yok). `log.md` sonuna `## [YYYY-MM-DD] ilerleme | Kayıtlar tutuldu` girdisi ekle (kısa: kaç kayıt, hangi notlar).
5. `git add -A`; `git diff --cached` ile sır sızmadığını kontrol et; commit (Türkçe mesaj); uzak depo tanımlıysa push. Başka bir oturum aynı anda vault'a yazıyorsa yarım dosyalarını bozma.
6. Panoyu güncelle (`/pano`).
7. `_sistem/beceriler/beceriler.md` tablosunda bu becerinin "kullanım" sayısını 1 artır, "son kullanım" tarihini yaz; hata olduysa "son hata" sütununa tek satır yaz.
8. Kullanıcıya 2–4 satır özet.

Kesin kurallar: sadece bu bilgisayar (#17, etkinse); bilgisayar kodları, şifre, anahtar, IP/MAC, bilgisayar adı hiçbir yere yazılmaz (#18); öğretme yok (#15).
