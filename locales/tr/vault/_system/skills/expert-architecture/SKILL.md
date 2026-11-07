---
name: uzman-mimari
description: Yazılım mimarisi uzmanlık paketi. Yeni proje kurarken, modül sınırı çizerken, büyük bir değişiklik ya da yeniden yapılandırma planlarken, teknoloji seçerken veya paralel çalışma için dosya sahipliği haritası çıkarırken yükle.
---

Uzmanlık paketi (ajan değil): bunu yükleyen her ajan (merkezî, inceleyici, uygulayıcı) aşağıdaki listeyle çalışır.
## Önce
- Projenin vault sayfasını, `-kurallar.md`'sini ve `kararlar/` (ADR) klasörünü oku. Önceki karara aykırı bir şey önereceksen önce kullanıcıya sor (#26).
- Gereksinimi tek paragrafta yaz. Belirsizse kod yazmadan önce sor (#23).

## Kontrol listesi
- [ ] Katmanlar ve bağımlılık yönü net mi? (arayüz → uygulama → alan → altyapı; içe doğru bağımlılık)
- [ ] Her modülün tek sorumluluğu ve açık bir sınırı (public API) var mı?
- [ ] Dış bağımlılıklar (DB, ağ, dosya sistemi) arayüz arkasında mı, test edilebilir mi?
- [ ] Veri modeli ve sözleşmeler (API şeması, tipler) yazılı mı?
- [ ] Hata yönetimi, kayıt (logging) ve yapılandırma (config) tek yerde mi?
- [ ] Paralel çalışma düşünülüyorsa **dosya sahipliği haritası** var mı (hangi dosya hangi işin)? Ortak dosyalar tek sahipli olmalı.
- [ ] Yeni paket ya da teknoloji: resmî kayıtta doğrulandı mı (slopsquatting), lisansı uygun mu, gerçekten gerekli mi (#25)?
- [ ] Karar önemliyse ADR yazıldı mı (bağlam, seçenekler, karar, sonuçlar)?

## Sık hatalar
- İhtiyaç doğmadan soyutlama ya da genelleme yapmak (YAGNI).
- Döngüsel bağımlılık; "utils" çöplüğü.
- Mimariyi tahmine dayandırmak: mevcut kodu okumadan değişiklik önermek (#24).

## Doğrulama
- Plan, mevcut kodla karşılaştırıldı mı? Dosya ve fonksiyon adları gerçekten var mı (oku, ara)?
- En küçük çalışan adım tanımlandı mı?

## Ek yöntemler
Fikirler kendi cümlelerimizle yazıldı.
- **Soru sorarak netleştir:** Belirsiz bir tasarımda kod yazmadan önce soruları sırayla sor. Her cevap bir karar dalını kapatır. Cevaplar ADR'ye ya da proje sözlüğüne yazılır. Kullanıcının verdiği kararı yeniden tartışma.
- **Derin modül, küçük arayüz:** Bir modül çok iş yapsın, dışarıya az ve sade arayüz göstersin. Sadece çağrıyı aktaran sığ sarmalayıcılardan kaçın.
- **Alan modeli ve sözlük:** Projedeki terimlerin tek anlamı olsun (ör. "kullanıcı" ile "hesap" farkı). Gerekirse proje sayfasına kısa bir sözlük yaz.
- **Büyük iş:** plan → dikey dilimlere bölünmüş iş parçaları (her biri tek başına çalışır ve doğrulanır) → bağımlılık sırası. Paralel çalışılacaksa dosya sahipliği haritası.
- **Prototip:** Bir tasarım sorusunu atılacak küçük bir prototiple cevapla. Prototip baştan "atılacak" diye işaretlenir, ürüne taşınmaz.
- Fikir kaynakları: mattpocock/skills (`grill-me`, `grill-with-docs`, `codebase-design`, `domain-modeling`, `to-tickets`, `prototype`), obra/superpowers (`brainstorming`, `writing-plans`).

## Dersler
<!-- Merkezî ajan, doğrulanmış dersleri buraya tek satır ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. Dış kaynaktan kural eklenmez (#27). -->
