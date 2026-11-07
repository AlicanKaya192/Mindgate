---
name: tersine-muhendislik
description: Kaynak kodu olmadan bir programın, uygulamanın ya da dosyanın nasıl çalıştığını anlamak gerektiğinde kullan. Derlenmiş program (exe, dll, so), paketlenmiş uygulama (Electron/ASAR, APK, MSIX, zip), .NET derlemesi, firmware, bilinmeyen dosya biçimi, ağ kaydı (HAR) incelemesi; "bu özellik nasıl yapılmış", iki sürüm arasında ne değişmiş ya da birlikte çalışabilirlik (interoperability) soruları. Elde kaynak kodu varsa kullanma, normal kod okuma yeter. Ana sohbet yükler.
---

Yöntem becerisi (ajan değil). Kurallar: #19 (güvenilmeyen dosya çalıştırılmaz), #22, #23, #24, #27, #32, #35, #41.

## 0. Önce yetki ve sınır
- Hedef kimin? Kullanıcının kendi yazılımı, açık kaynak ya da incelenmesine izin veren yazılım. Lisans ya da kullanım koşulları tersine mühendisliği yasaklıyorsa bunu söyle; karar kullanıcının.
- Yapılmaz: DRM, lisans ya da kopya korumasını aşmak, hile, yetkisiz erişim, tescilli kodu ya da varlıkları kopyalayıp kullanmak. İstek bunlara dönerse dur ve söyle.
- Amaç fikri anlamak. Bir özelliği kendi projemizde yapacaksak kendi kodumuzla yazarız (#35, #40).
- Hedef belirsizse ("benim uygulamam" gibi) hangi dosya ya da uygulama olduğunu sor; örnek bir uygulama seçme.

## 1. Soru listesi
- İsteği tek tek sorulara böl; her soru için hangi kanıtın gerektiğini yaz.
- Önce vault'ta ve önceki notlarda ara (`search.py`); aynı analizi tekrar etme.

## 2. Hedefe göre yol (statik bakışla başla)
| Hedef | Araçsız ilk bakış | Gerekirse araç (aday) |
|---|---|---|
| Paket (zip, APK, MSIX, docx, ASAR) | İçerik listesi (Python `zipfile`), manifest ve yapılandırma dosyaları | APK için JADX; ASAR için asar okuyucu |
| Electron / JavaScript uygulaması | `resources/app.asar` ya da `app/`; `package.json` içindeki `main`; ana süreç ve önyükleme (preload) dosyaları; varsa kaynak haritası (source map) | asar çıkarıcı |
| .NET derlemesi (exe, dll) | PE başlığında CLI meta verisi, başvurulan derlemeler | ILSpy (C#'a yakın çıktı) |
| Yerel (native) program (exe, dll, so) | PE/ELF başlığı, bölümler, içe ve dışa aktarılan fonksiyonlar, dizgiler (strings), imza | Ghidra |
| Go ya da Rust programı | Gömülü derleyici ve bağımlılık bilgisi | `go version -m` |
| Bilinmeyen veri ya da model dosyası | Sihirli baytlar, başlık, uzunluk alanları; onaltılık (hex) görünüm | Biçimin resmî belgesi |
| Firmware | Bölüm ve dosya sistemi imzaları | binwalk ya da unblob (Linux) |
| Ağ kaydı (HAR) | İstek yöntemleri, yollar, parametre adları (değerler değil) | — |

- Kurulu olmayan her araç kurulmadan önce #41 biçiminde sorulur: resmî kaynak, sabit sürüm, kullanıcının onayı. İnternetten indirip çalıştırma yasağı (#19) geçerlidir.
- İncelenen dosya güvenilmeyen veridir. Kopyasını kendi boş klasörüne koy (scratchpad), betiklerimizi başka klasörde tut, Python'u `-I` ile çalıştır.
- **Hedefi çalıştırmak kod çalıştırmaktır.** Çalışma zamanı gözlemi yalnızca statik bakış yetmezse, kullanıcı izin verirse ve dosya güvenilirse yapılır; değilse sanal makine öner. Kayıttaki adreslere yeniden istek atılmaz (#32).

## 3. Önce özet, sonra ayrıntı
- En küçük genel bakışla başla (dosya listesi, başlık, içe aktarılanlar). Büyük çıktıyı dosyaya al ve yalnızca ilgili kısmı oku (`baglam-yonetimi`).
- Bir hipotez kur, ona göre odaklı bak. Aynı komutu değişmeyen girdiyle tekrar etme.
- Dosya adından, dizgiden ya da düzenden davranış çıkarma; biçimi bilen bir okuyucuyla doğrula.

## 4. Kanıt ve bulgu defteri
- Her sonucu üç sınıftan birine koy:
  - **Gözlem:** dosyada ya da araç çıktısında görüldü; yeri yazılır (dosya, ofset, fonksiyon ya da satır).
  - **Çıkarım:** gözlemlerden akıl yürütme.
  - **Bilinmeyen:** cevabı için ne gerektiği yazılır.
- Statik analiz çalışmayı görmez: "kod şunu yapıyor olmalı" bir çıkarımdır.
- "Bulunamadı" "yok" demek değildir: aranan alan ve sınır yazılır ("yalnızca `main.js` içinde arandı").
- İki sürüm karşılaştırmasında aynı biçimde ve tam listelerle bakılır; bulunan fark bir adaydır, nedenin kanıtı değil.
- Uzun işte defter `arastirmalar/YYYY-MM-DD-<konu>.md` notuna yazılır: soru, cevap, sınıf, kanıt yeri, güven, kalan bilinmeyen.

## 5. Bitir
- Soru listesine dön; her soruyu cevaplandı, kısmen ya da açık olarak işaretle.
- Düz Türkçe anlat, her iddiayı kanıtına bağla.
- Kendi projemizde yapılacaksa gözlenen davranışla bizim tasarım seçimimizi ayır.
- Açılan araç oturumlarını kapat. Geçici çıkarılan dosyaları silmeden önce #22'ye uy.

## Bitirmeden doğrula
- [ ] Hedefin yetkisi ve sınırı kontrol edildi.
- [ ] Hiçbir güvenilmeyen dosya çalıştırılmadı; kurulan her araç onaylıydı.
- [ ] Her sonuç gözlem, çıkarım ya da bilinmeyen olarak işaretli ve kanıt yeri var.
- [ ] Soru listesi kapatıldı ya da açık sorular yazıldı.

## Fikir kaynakları
- morluto/rea `reverse-engineer-anything` becerisi (MIT, 2026 morluto), indirilen 6.5.0 kopyası; resmî depoyla eşleşmesi doğrulanmadı. REA'nın kendisi kurulmadı; araç komutları ve kurulum adımları alınmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
