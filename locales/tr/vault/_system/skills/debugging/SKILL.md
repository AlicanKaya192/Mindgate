---
name: hata-ayiklama
description: Bir hata, başarısız test, beklenmeyen davranış, yavaşlık ya da derleme hatasıyla karşılaşınca, düzeltme önermeden ÖNCE kullan. Kök neden bulunmadan düzeltme yapılmaz. Ana sohbet ve kod yazan her ajan yükler; inceleyici kök neden analizi gerektiğinde yükleyebilir.
---

Yöntem becerisi (ajan değil). Kural #24 (önce doğrula) ve vault `CLAUDE.md` §7.3 (sorun ve çözüm) ile birlikte çalışır.

## Temel kural
**Kök neden bulunmadan düzeltme yok.** Belirtiyi bastırmak (ör. hatayı `try/except` ile yutmak, sihirli bir bekleme eklemek) düzeltme değildir; sorun başka yerde geri gelir.

## 0. Önce vault
`sorunlar/`'da hata mesajını ve anlamca benzerini ara (`grep`, `search.py`; §7.3, kural #38). Kayıtlı çözüm varsa önce onu dene; "Denenen çözümler" tablosunda ✗ olanı aynı koşulda tekrar deneme. Sonucu (✔/✗/~ ve neden) tabloya yaz; işe yaramadıysa eski çözümü silmeden yenisini ara.

## 1. Kök neden araştırması (düzeltmeden önce)
- **Hata mesajını sonuna kadar oku:** yığın izi (stack trace), dosya:satır, hata kodu. Çoğu zaman cevap oradadır.
- **Yeniden üret:** Adımlar kesin mi, her seferinde oluyor mu? Üretilemiyorsa tahmin etme, veri topla.
- **Son değişikliklere bak:** `git diff`, son commit'ler, yeni bağımlılık, ayar, ortam farkı.
- **Çok katmanlı sistemde sınırları ölç:** Her bileşen sınırında (ör. betik → alt süreç → dosya) giren ve çıkan veriyi bir kez yazdır. Hangi katmanda bozulduğunu kanıtla, sonra o katmana in.
- **Veriyi geriye izle:** Hatalı değer nereden geldi, kim bu değerle çağırdı? Kaynağa kadar çık; düzeltmeyi kaynakta yap.

## 2. Kalıp karşılaştırması
- Aynı projede çalışan benzer kodu bul. Çalışan ile bozuk arasındaki **her** farkı listele ("bu önemli olamaz" deme).
- Bir kalıbı ya da örneği uyguluyorsan referansı baştan sona oku, göz gezdirme.

## 3. Hipotez ve test
- Tek hipotez yaz: "X kök nedendir, çünkü Y."
- **En küçük** değişiklikle sına; aynı anda tek değişken. Tutmadıysa üstüne yeni düzeltme ekleme, değişikliği geri al ve yeni hipotez kur.
- Anlamıyorsan "X'i anlamıyorum" de (#24). Bilmiyormuş gibi yapma.

## 4. Düzeltme
- Önce hatayı yakalayan **başarısız bir test** ya da küçük bir yeniden üretim betiği yaz (`test-yazma`). Testin kırmızı olduğunu gör.
- Kök nedene **tek** düzeltme. "Hazır buradayken" iyileştirme ya da toplu refactor yok (#23, #25).
- Doğrula (`dogrulama`): test yeşil, diğer testler bozulmadı, asıl belirti gerçekten gitti.

## 3 deneme kuralı
Üç düzeltme denemesi tuttuysa **dur**. Her düzeltme başka yerde yeni bir sorun açıyorsa sorun büyük ihtimalle tasarımdadır, tek bir satırda değil. Dördüncü denemeye geçmeden kullanıcıya durumu, denenenleri ve mimari soruyu yaz.

## Dur işaretleri
Aklından şunlar geçiyorsa 1. adıma dön:
- "Şimdilik hızlı düzelteyim, sonra bakarım."
- "Şunu değiştirip bir bakayım."
- "Birkaç şeyi birden değiştirip testleri çalıştırayım."
- "Muhtemelen X'tir."
- Veri akışını izlemeden çözüm listesi yazmak.
- Kullanıcının "tahmin etme", "bu olmuyor mu?" gibi uyarıları.

## Kök neden gerçekten yoksa
Sorun ortamdan, zamanlamadan ya da dış servisten geliyorsa ne araştırıldığını yaz, uygun önlemi koy (zaman aşımı, yeniden deneme, anlamlı hata mesajı) ve kayıt ekle. Bu durum nadirdir; çoğu zaman araştırma eksik kalmıştır.

## Bitince
Çözülen sorunu `sorunlar/`'a yaz ya da mevcut notu güncelle (`/sorun`): belirti (hata mesajı aynen), kök neden, geçerli çözüm, **denenen bütün çözümler sonucuyla** (işe yaramayanlar dahil, kural #38), nasıl önlenir.

## Fikir kaynakları
- obra/superpowers `systematic-debugging` (MIT, Jesse Vincent). İndirilen kopyadan okundu; resmî depoyla eşleşmesi doğrulanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
