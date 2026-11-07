---
name: uzman-backend
description: Backend ve veritabanı uzmanlık paketi. API, sunucu tarafı iş mantığı, veritabanı şeması, sorgu, migration, kimlik doğrulama, kuyruk ya da dış servis entegrasyonu üzerinde çalışırken veya bunları incelerken yükle.
---

Uzmanlık paketi (ajan değil). Önce projenin kurallarını, ADR'lerini ve `sorunlar/`'da ilgili hataları ara (#26).

## Kontrol listesi
- [ ] Girdi doğrulama sınırda yapılıyor mu (tip, uzunluk, aralık, biçim)? İstemciye güvenme.
- [ ] SQL parametreli mi (string birleştirme yok)? ORM kullanılıyorsa ham sorgular ayrıca kontrol edildi mi?
- [ ] Transaction sınırları doğru mu? Kısmi yazma kalmıyor mu? Eşzamanlılıkta yarış durumu (race condition) var mı?
- [ ] Migration geri alınabilir mi? Veri kaybı riski var mı? Büyük tabloda kilitlenme (lock) olur mu? Önce yedek ya da deneme ortamı.
- [ ] Sorgu verimliliği: N+1, eksik indeks, sınırsız `SELECT *`, sayfalama.
- [ ] Hata yönetimi: anlamlı hata kodu, iç ayrıntı (stack trace, sorgu) istemciye sızmıyor; kayıtta sır yok.
- [ ] Kimlik doğrulama ve yetki: her uç noktada yetki kontrolü, en az yetki ilkesi.
- [ ] Sırlar `.env` ya da gizli depoda; koda ve vault'a yazılmaz (#18).
- [ ] Dış servis çağrıları: zaman aşımı, yeniden deneme sınırı, idempotency.
- [ ] Testler: mutlu yol + sınır durumları + hata yolu.

## Doğrulama
- Değişikliği gerçekten çalıştır (test, örnek istek). Çıktıyı göster. Sayı uydurma (#24).
- Veritabanı işlemleri **asla** gerçek veride denenmez; silme ya da toplu güncelleme kullanıcının onayıyla (#22).

## Sık hatalar
- Migration'ı geri dönüşsüz yazmak.
- Zaman dilimi ve tarih karışıklıkları (UTC sakla, gösterirken çevir).
- Kayıp hatayı yutmak (`except: pass`).

## Ek yöntemler
Fikirler kendi cümlelerimizle yazıldı.
- **API tasarımı:**
  - [ ] Kaynak adları ve URL yapısı tutarlı; HTTP durum kodları doğru (400 doğrulama, 401/403 yetki, 404, 409 çakışma).
  - [ ] Hata gövdesi her uç noktada aynı biçimde.
  - [ ] Liste uç noktalarında sayfalama ve üst sınır var.
  - [ ] Tekrar denenebilecek yazma isteklerinde idempotency anahtarı var.
  - [ ] Kırıcı değişiklikte sürümleme var.
- **Migration:**
  - Genişlet → taşı → daralt sırasını izle: önce yeni sütunu ekle, veriyi taşı, en son eskiyi kaldır.
  - Büyük tabloda işlemi parça parça yap.
  - Her migration'ın geri alma adımı yazılıdır.
- **TDD döngüsü:** kırmızı (başarısız test) → yeşil (en küçük kod) → düzenle. Tek seferde bir dikey dilim. Hata düzeltirken önce hatayı yakalayan testi yaz.
- **Sistematik hata ayıklama:**
  1. Hatayı tekrar üret.
  2. Kanıtı topla (log, girdi).
  3. Tek hipotez kur, tek değişkeni değiştirerek dene.
  4. Kök nedeni bul. Belirtiyi değil nedeni düzelt.
  5. Düzeltmeden sonra aynı adımla doğrula.

  Önce `sorunlar/`'da ara.
- **Sessiz hata avı:** yutulan exception, boş `catch`, hatayı varsayılan değerle gizleme, kontrol edilmeyen dönüş değeri.
- **Devre kesici (circuit breaker):** Sürekli hata veren dış servise istek atmayı keser.
  - Üç durumu var. **Kapalı:** istekler geçer, art arda hatalar sayılır. **Açık:** eşik aşılınca istek gönderilmez, hemen hata ya da yedek cevap döner. **Yarı açık:** bekleme süresi dolunca tek bir deneme isteği geçer; başarılıysa kapanır, değilse yeniden açılır.
  - Yeniden denemeyle birlikte kullanılır: önce sınırlı ve artan beklemeli yeniden deneme (exponential backoff + jitter), onun dışında devre kesici. Yalnızca geçici hatalar (zaman aşımı, 503) sayılır; 400 gibi istemci hataları sayılmaz.
  - Kontrol: eşik, bekleme süresi ve yedek davranış yazılı mı? Devre açıldığında kayda geçiyor mu? Testte sahte servisle açık → yarı açık → kapalı geçişi deneniyor mu?
  - Ne zaman gerekmez: tek kullanıcılı yerel araç, dış servis yok. Gereksiz katman eklenmez (#25).
  - Fikir kaynağı: ruvnet/claude-flow (ruflo) 3.58.1 `sparc/refinement.md` (MIT). Kod örneği alınmadı.
- Fikir kaynakları: obra/superpowers (`systematic-debugging`, `test-driven-development`), mattpocock/skills (`tdd`, `diagnosing-bugs`), everything-claude-code (`api-design`, `database-migrations`), anthropics `pr-review-toolkit` (silent-failure-hunter).

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
