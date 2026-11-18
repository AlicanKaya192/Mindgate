# Türler

Sayılar kaynak paketin sahibinin beyanıdır, bağımsız doğrulanmadı. Her eşik başlangıç noktasıdır: ölç, oynat, ayarla. Bir istek genelde bir türe bağlanır; melez oyunda ikinci türün yalnızca ilgili bölümü okunur. Roguelike bölümü klasik, sıra tabanlı ızgara roguelike içindir; gerçek zamanlı roguelite'ta yalnızca tohum, koşu/profil ve kabul denetimi kuralları geçerlidir; disiplin kuralları (kamera, kayıt, yapay zekâ) kendi dosyalarındadır.

## Platform
**Kapsam:** Zıplama, yerçekimi, hava kontrolü ve bağışlayıcı zamanlamalar.

**Eşikler** (tile = bir ızgara karesi)
| Ayar | Başlangıç | Aralık |
|---|---|---|
| Tam zıplama yüksekliği | 3,5 tile | 2–5 |
| Tepeye varış süresi | 0,35 s | 0,25–0,45 |
| Kısa zıplama | %30 | kaynakta neye uygulandığı (hız ya da yükseklik) okunmadı; ölçerek seç |
| Düşüşte yerçekimi | 1,8x | 1,3–2,5 |
| Tepede asılı kalma | 0,5x yerçekimi | |
| Coyote süresi | 0,1 s | 0,06–0,15 |
| Zıplama tamponu | 0,1–0,15 s | |
| Hava kontrolü | yerdekinin 0,65x'i | |
| Köşe düzeltme | yarım tile'a kadar | |
| Son hız | tik başına yarım tile'ın altında | |

**Yöntem**
- Yerçekimini ve ilk hızı yükseklikten (h) ve tepe süresinden (t) hesapla, deneme yanılmayla seçme: `g = 2 * h / t^2`, `v0 = 2 * h / t` (bizim türetmemiz; kaynakta yalnızca hesaplayıcı betiğin adı geçer).
- Bölümde boşluk hesaplanan erişimden en az 1 tile kısa olsun (`his-kamera-seviye.md` → Seviye tasarımı).

**Tuzaklar**
- Değişken `dt` tepe yüksekliğini yaklaşık %5 kısaltır; sabit tik kullan.
- Ondalıklı (float) zamanlayıcı tik kaybeder; coyote ve tamponu tik sayacıyla tut.
- Coyote süresi zıplayınca sıfırlanmazsa havada ikinci zıplama açılır.

**Doğrulama**
- Tik başına konumu CSV'ye yaz, hesaplanan eğriyle karşılaştır; %5'ten fazla sapan satır başarısız.
- 4 uç durum testi yaz (kaynağın listesi okunmadı; ör. coyote sınırı, tampon sınırı, tavana çarpma, köşe düzeltme).

## Roguelike
**Kapsam:** Koşu yapısı, tohum, sıra sistemi, görüş alanı.

**Yöntem**
- Koşu (run) ve profil (kalıcı ilerleme) ayrı dosyalara kaydedilir.
- Tek tohumdan amaç başına alt tohum (`yapay-zeka-uretim.md` → Prosedürel üretim).
- Enerji zamanlayıcısı: her aktör tik başına hızı kadar enerji kazanır, eylem 100 enerji harcar. Hız 50 yavaş, 100 normal, 200 hızlı.
- Görüş alanı (FOV) yarıçapı 6–9 ve simetrik: A, B'yi görüyorsa B de A'yı görür.
- Güvenli başlangıç: başlangıç noktasının 6–8 tile çevresinde düşman olmasın.

**Tuzaklar**
- Üretim ve savaş aynı rastgele akışı kullanırsa aynı tohum farklı harita verir. Python `hash()` süreç başına rastgeledir.

**Doğrulama**
- Aynı tohum aynı harita hash'ini verir.
- 500+ tohumda kabul denetimi (bağlılık, güvenli başlangıç, anahtar sırası).

## RPG
**Kapsam:** Stat, değiştirici, hasar formülü ve denge.

**Yöntem**
- Stat = taban değer + değiştirici yığını. Her değiştirici kaynağının kimliğini taşır (eşya, büyü); çıkarılınca doğru olanı silinir.
- Yuvarlama yalnızca en sonda yapılır.
- Savunma formülü `hasar * K / (K + savunma)`: savunma arttıkça etkisi azalır, hasar sıfıra inmez.
- Direnç en çok %75.

**Eşikler**
| Kim ölür | Vuruş sayısı |
|---|---|
| Sıradan düşman | 2–4 |
| Oyuncu | 5–8 |
| Patron | 25–60 |

**Doğrulama**
- Seviye başına denge tablosu çıkar; vuruş sayıları bandın dışındaysa satır başarısız.
- Tak ve çıkar özdeşliği: eşyayı tak, çıkar; statlar birebir başa dönmeli.

## FPS
**Kapsam:** Silah zamanlaması, öldürme süresi (TTK), nişan duyarlılığı.

**Yöntem**
- TTK tablosu: atış sayısı `ceil(can / hasar)`, süre `(atış - 1) / saniyede atış`.
- Ateş zamanlayıcısı saate bağlıdır, kare hızından bağımsızdır. Fare hareketi (delta) `dt` ile çarpılmaz; zaten kare başına birikmiş yoldur.
- Nişan alırken (ADS) duyarlılık oranı `tan(ads_fov / 2) / tan(hip_fov / 2)`.

**Doğrulama**
- 30, 60 ve 144 FPS'te 10 s ateş et: atış sayısı `saniyede atış * 10` ±1 olmalı.

## Kule savunması
**Kapsam:** Dalga büyümesi, hedefleme, yol.

**Yöntem**
- Dalga başına düşman canı 1,12–1,18x büyür.
- Baskı 0,6–0,95 aralığında tutulur (kaynakta baskının tanımı okunmadı; tanımı projede yazılı olsun).
- Varsayılan hedefleme "ilk": yolda en önde olan düşman.
- Oyuncu labirent kurabiliyorsa yerleştirme yolu tamamen kesemez; yerleştirmeden önce yol hâlâ var mı bak.
- Dalga zamanlayıcısı oyun saatiyle çalışır.

**Doğrulama**
- Her dalganın baskısını hesaplayan tablo çıkar; bandı aşan dalga başarısız.

## Kart
**Kapsam:** Bölgeler, karıştırma, tetikleyici zinciri.

**Yöntem**
- Her kart her an tam olarak bir bölgededir (deste, el, mezarlık, oyun alanı).
- Oynanmakta olan kart çözülene kadar ayrı bir bekleme bölgesinde (limbo) durur.
- Karıştırma Fisher-Yates ile ve tohumlu. Tetikleyici zinciri 100 adımda kesilir; sonsuz döngü oyunu kilitlemez.

**Doğrulama**
- 10.000 bot turu oynat, her adımda değişmezleri denetle (kart sayısı korunur, kart iki bölgede değil).
- 4 kartı 24.000 kez karıştır, sıraların dağılımına ki-kare testi uygula.

## Görsel roman
**Kapsam:** Dallanma, okuma süresi, okunmuş metin.

**Yöntem**
- Metinden önce rota haritasını çiz: dallar, birleşmeler, sonlar.
- Süre tahmini için okuma hızı 200–250 kelime/dk.
- Satır kimlikleri kararlı olsun; metin düzeltilince okunmuş işareti kaybolmasın. Okunmuş metin kaydı oyun kaydından ayrı, kalıcı veridir.

**Doğrulama**
- Erişilemez son denetimi: Ink'te genişlik öncelikli gezinti, Ren'Py'da lint.

## Hayatta kalma
**Kapsam:** Üretim (crafting), ihtiyaçlar, bozulma.

**Yöntem**
- Üretim önce ürünün envantere sığdığını doğrular, sonra malzemeyi düşmeyi ve ürünü eklemeyi tek adımda yapar.
- Açlık, susuzluk gibi ihtiyaçlar oyun saatiyle azalır. Birleşen yığında bozulma (çürüme, aşınma) ağırlıklı ortalamayla hesaplanır.
- Her eşya başlangıçtan bir tarif zinciriyle erişilebilir olmalı.

**Doğrulama**
- Tarif grafiğinde erişim denetimi: başlangıç eşyalarından her eşyaya yol var mı.

## Bulmaca
**Kapsam:** Durum, hamle, çözücü, geri alma.

**Yöntem**
- Kural saf bir işlevdir: `apply(durum, hamle)` yeni durumu döndürür, eskisini değiştirmez.
- Çözücüyü erken yaz; bölüm zorluğunu çözücüyle ölç.
- Geri alma tam anlık görüntü saklar, rastgele üreticinin durumu dahil.

**Doğrulama**
- Çözücü her bölümü çözer. 1.000 geri alma sonrası durumun hash'i başlangıçla aynı.
- Eşleştirme bulmacasında 10.000 rastgele tahtada başlangıçta hazır eşleşme yok.
