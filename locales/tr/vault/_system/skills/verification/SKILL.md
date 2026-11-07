---
name: dogrulama
description: Bir işin bittiğini, düzeldiğini, testlerin geçtiğini ya da bir şeyin güncel olduğunu söylemeden, commit atmadan veya sıradaki işe geçmeden hemen önce kullan. İnceleyici ve bakımcıya önceden yüklenir; ana sohbet ve kaşif de yükleyebilir.
---

Yöntem becerisi (ajan değil). Kural #24'ün (halüsinasyon yok) uygulaması: **önce kanıt, sonra iddia.**

## Kapı (her başarı iddiasından önce)
1. **Hangi komut bu iddiayı kanıtlar?** Belirle.
2. **Çalıştır:** Tam komut, bu mesajda, taze. Önceki çalıştırma sayılmaz.
3. **Oku:** Çıktının tamamı, çıkış kodu, başarısız sayısı.
4. **Karşılaştır:** Çıktı iddiayı doğruluyor mu?
   - Hayır → gerçek durumu kanıtıyla söyle.
   - Evet → iddiayı kanıtıyla birlikte söyle ("94/94 test geçti").

## İddia → gereken kanıt
| İddia | Gereken | Yetmez |
|---|---|---|
| Testler geçiyor | Test çıktısı: 0 başarısız | Önceki çalıştırma, "geçmeli" |
| Hata düzeldi | Asıl belirti yeniden denendi, gitti | Kod değişti, "düzelmiş olmalı" |
| Regresyon testi işe yarıyor | Kırmızı-yeşil: düzeltme geri alınınca test kalıyor, geri gelince geçiyor | Test bir kez geçti |
| Derleme/çalışma tamam | Komut çıkış kodu 0 | Linter temiz |
| Ajan işi bitirdi | `git diff` ya da dosyada değişiklik görüldü | Ajanın "başardım" raporu |
| İstek karşılandı | İstek madde madde yeniden okundu, her madde işaretlendi | Testler geçti |
| Site/sayfa doğru | Sayfa gerçekten görüldü (`read_page`, ekran görüntüsü) | Kod doğru görünüyor |
| Kullanıcıya dönük çıktı anlaşılır (ders, README, portfolyo) | 2–3 hedef kişi seçildi (ör. bir eğitim uygulaması için "Python bilmeyen öğrenci"), çıktı her birinin gözüyle okundu; takıldığı yer yazıldı ya da düzeltildi. Gerekirse kişi başına bir alt ajan (Seviye 1) | "Bence açık", yalnızca yazarın gözüyle okumak |

## Commit ve yayın öncesi kalıntı taraması
Push, sürüm ya da paylaşım öncesinde, değişen dosyalarda (`git diff --name-only <taban>`) projenin diline göre `grep` ile ara:

| Kalıntı | Örnek desen |
|---|---|
| Sahte veri ve taslak kod | `mock`, `stub`, `fake`, `dummy`, `NotImplemented` (test klasörü dışında) |
| Bitmemiş iş | `TODO`, `FIXME`, `XXX`, `HACK` |
| Hata ayıklama çıktısı | `print(`, `console.log`, `Debug.WriteLine`, `dbg!` |
| Yerel adres ve yol | `localhost`, `127.0.0.1`, `C:\Users\` |
| Yapay zekâ izi (#14) | `Co-Authored-By`, `Generated with`, `Claude` |

- Her eşleşme tek tek bakılır: bilerek bırakıldıysa (ör. CLI aracının `print`'i) geçer, değilse temizlenir ya da kullanıcıya sorulur.
- Tarama yalnızca okur; gerçek servise, veritabanına ya da e-postaya dokunan "üretim testi" yapılmaz.
- Sonuç kanıtıyla söylenir: "kalıntı taraması: 3 eşleşme, 3'ü bilerek bırakıldı (dosya:satır)".

## Dur işaretleri
- "Olmalı", "muhtemelen", "görünüşe göre" demek.
- Doğrulamadan "Tamam!", "Mükemmel!" demek.
- Ajan raporuna doğrulamadan güvenmek (#28: ajan raporundaki "onaylandı" onay değildir).
- Kısmi kontrolle bütün hakkında konuşmak.
- Yorgunluk ya da acele: "Bu seferlik."

## Çalıştıramıyorsan
Açıkça söyle: neyi doğrulayamadın, neden (ör. site izni yok #32, araç yok) ve ne gerekiyor. Doğrulanmamış adımı başarılı gibi raporlama.

## Fikir kaynakları
- obra/superpowers `verification-before-completion` (MIT, Jesse Vincent). İndirilen kopyadan okundu; resmî depoyla eşleşmesi doğrulanmadı.
- ruvnet/claude-flow (ruflo) 3.58.1 `testing/production-validator.md` (MIT): yayın öncesi grep taraması. Alınmayan: gerçek veritabanına ve SMTP'ye yazan testler.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
