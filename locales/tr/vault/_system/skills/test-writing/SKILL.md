---
name: test-yazma
description: Yeni özellik, hata düzeltmesi ya da davranış değişikliği için kod yazmadan önce ve bir web arayüzünü test ederken kullan. Ana sohbet yükler; inceleyici test kapsamı geçişinde yükleyebilir.
---

Yöntem becerisi (ajan değil). `temiz-kod` §8 (F.I.R.S.T.) ile birlikte çalışır. Projenin kendi test çerçevesi ve kuralları önce gelir.

## Kırmızı → yeşil → düzenle
1. **Kırmızı:** Tek bir davranışı anlatan, açık isimli bir test yaz.
2. **Kırmızıyı gör (atlanmaz):** Testi çalıştır.
   - Test hata vermeden **başarısız** olmalı.
   - Başarısızlık mesajı beklenen mesaj olmalı.
   - Neden de doğru olmalı: özellik eksik, yazım hatası değil.
   - Test hemen geçiyorsa var olan davranışı test ediyorsun; testi düzelt.
3. **Yeşil:** Testi geçirecek en az kodu yaz. İstenmeyen özellik ekleme (#25).
4. **Yeşili gör:** Bu testi ve bütün testleri çalıştır.
5. **Düzenle:** Testler yeşil kalarak kodu temizle (`temiz-kod`).

Testten önce kod yazdıysan: o kodu **silme** (#22). Kenara al ve testi ona bakmadan yaz. Test kırmızıyı gösterdikten sonra kodu ölçüt olarak kullan. (Kaynaktaki "sil ve baştan yaz" kuralı bizde geçerli değil.)

## İyi test
- Tek davranış; isim davranışı anlatır (`test_bos_listede_sifir_doner`).
- Sahte nesne (mock) yerine gerçek kod. Mock yalnızca dış servis, saat, ağ gibi kaçınılmaz yerlerde kullanılır. Mock'u test edip kodu test etmiş sanma.
- Hazırla → çalıştır → doğrula. Test başına tek kavram.
- Sınır durumları ayrı testlerde: boş, tek eleman, çok büyük, geçersiz girdi, hata yolu.
- **Test kazara geçemesin:** Önemli bir test için kodu bilerek boz ve testin kaldığını gör. Hep geçen test, hiç test olmamasından kötüdür.

## Hata düzeltmede regresyon testi
Önce hatayı yeniden üreten test (kırmızı) gelir, sonra düzeltme (yeşil) yapılır. Doğrulama sırası: düzeltmeyi geri al, test kalmalı; düzeltmeyi geri koy, test geçmeli (`dogrulama`).

## Web arayüzü testi (keşif önce, eylem sonra)
1. Statik HTML ise önce dosyayı oku, seçicileri oradan bul.
2. Dinamik uygulamada sayfa yüklensin ve ağ sakinleşsin. Playwright'ta bunun karşılığı `wait_for_load_state("networkidle")`.
3. Sonra ekran görüntüsü al ya da DOM'u incele (uygulama içi tarayıcı: `read_page`).
4. Seçicileri **görülen** duruma göre seç: rol, metin, id. Sonra eylemi yap.

Ek kurallar:
- Sayfa yüklenmeden DOM'a bakma.
- Yerel sunucu da bir sayfadır: açmadan önce kullanıcının izni gerekir (#32). Port doluysa süreci öldürme, boş port seç (#20).
- Playwright bu bilgisayarda kurulu değilse kurmadan önce sor (#23).

## Ne zaman test yazılmaz
Atılacak deneme kodu, üretilmiş kod ve yapılandırma dosyaları. Emin değilsen kullanıcıya sor.

## Fikir kaynakları
- obra/superpowers `test-driven-development` (MIT, Jesse Vincent).
- anthropics/skills `webapp-testing` (Apache-2.0).

İkisi de indirilen kopyalardan okundu; resmî depolarla eşleşmeleri doğrulanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
- Koda yeni bir dosya yolu sabiti (ör. arşiv dizini) eklenince onu kullanan bütün test sınıflarında geçici dizine yönlendir ve yeni testi yolları yönlendiren sınıfa koy. Testten sonra `git status` ile gerçek veri klasörüne dosya yazılmadığını kontrol et (iki kez gerçek arşive sahte satır yazıldı).
- Ağa dokunmaması gereken bir kapının testleri soket açmayı yasaklayarak ağsız çalışır; böylece "onaydan önce ağ yok" iddiası da test edilir.
