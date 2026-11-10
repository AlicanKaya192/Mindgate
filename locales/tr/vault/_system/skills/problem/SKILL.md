---
name: sorun
description: Bir hata/sorun ve çözümünü ikinci beynin merkezi sorun kütüphanesine (sorunlar) kaydeder; önce aynı sorun var mı diye arar. Bir hata çözüldüğünde ya da kullanıcı "bunu sorunlara yaz" dediğinde kullan.
---

Vault: `{{VAULT}}`. Şema: vault `CLAUDE.md` §7.3, şablon `_sablonlar/sorun.md`. Türkçe yaz; İngilizce terimlerin yanına parantez içinde Türkçesi.

1. **Önce ara (kural #38):** `sorunlar/` içinde hata mesajının ayırt edici kısmını ve anahtar kelimeleri ara (`grep -ril`), sonra anlamca ara (`{{PY}} -I _sistem/search.py "<belirti>"`); benzer sorunlar da sayılır. `index.md` "Sorunlar" bölümüne de bak.
2. **Varsa — önce eski çözümü dene.** Notun "Denenen çözümler" tablosunda ✗ (işe yaramadı) yazan çözümü aynı koşulda tekrar deneme. Sonucu tabloya yeni satır olarak yaz: `| tarih | [[proje]] | ne denendi | ✔ işe yaradı / ✗ işe yaramadı / ~ kısmen | neden |`.
   - **İşe yaradıysa:** satır ✔; "Tekrar görüldüğü yerler"e tarih + proje ekle.
   - **İşe yaramadıysa:** eski çözümün **üzerine yazma, silme**; satırı ✗ ve nedeniyle kalır. Yeni çözümü bul (`hata-ayiklama`), onu da yeni satır olarak ekle ve "Çözüm" bölümünü yeni geçerli çözümle değiştir. Kök neden değiştiyse "Kök neden"e tarihli ek yaz.
   - **Çözülemediyse:** `status: open`, denenenler tabloda.
   - `updated` alanını bugüne çek. Sorun benzer ama farklıysa yeni not aç, eskisine link ver.
3. **Yoksa:** `sorunlar/<kisa-ad>.md` oluştur (küçük harf, ASCII, tire). Zorunlu bölümler: Belirti (hata mesajı **aynen**, kod bloğunda), Ortam, Kök neden, Çözüm (geçerli çözüm, adım adım, komutlarla), Denenen çözümler (işe yaramayan denemeler dahil), Nasıl önlenir, Tekrar görüldüğü yerler, Kaynaklar. Frontmatter: `type: problem`, `status: solved|open`, `project: "[[<proje>]]"`, `tags`, `aliases` (hata mesajının aranabilir biçimi).
   - **Regresyon işaretçisi:** Çözüm koda ayırt edici bir dize bıraktıysa (yeni bir parametre, koruma satırı, sabit) "Regresyon işaretçisi" bölümüne yaz: ``- `<dosya yolu>` → `<dize>` ``. Dize yalnızca o çözümde geçmeli (`grep` ile tek eşleşme). `health.py` dize kaybolursa ya da dosya taşınırsa uyarır; böylece çözüm sessizce geri alınırsa fark edilir. Yol `~` ile başlayabilir; sır, IP ya da bilgisayar adı içeren dize yazılmaz (#18).
4. Çözüm bir kavramı gerektiriyorsa ve `bilgi/`'de sayfası yoksa kısa bir kavram notu aç, link ver (sadece not; öğretme yok, #15).
5. Projenin ana sayfasındaki içerik haritasının (MOC) "Sorunlar" satırına link ekle. `index.md` "Sorunlar" bölümüne tek satır ekle.
6. Log: `{{PY}} -I _sistem/records.py log --operation sorun --title "<başlık>" --evidence "<commit/test>" --learned "…"`; gövdede hangi çözümün denendiği ve sonucu.
7. Vault'ta commit (uzak depo tanımlıysa push), sonra panoyu güncelle (`/pano`).
8. `_sistem/beceriler/beceriler.md` tablosunda kullanım sayısını 1 artır.

Yazılmayacaklar: şifre, anahtar, token, IP/MAC, bilgisayar adı, kişisel veri (#18). Komutun kaynağı belirsizse yazma (§9).
