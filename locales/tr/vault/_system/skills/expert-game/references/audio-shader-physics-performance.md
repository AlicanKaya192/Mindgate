# Ses, gölgelendirici, fizik ayarı ve performans

Sayılar kaynak paketin sahibinin beyanıdır, bağımsız doğrulanmadı. Her eşik başlangıç noktasıdır: ölç, oynat, ayarla.

## Ses
**Kapsam:** Ses veriyolları (bus), ses düzeyi, kısma (ducking), çeşitleme, müzik geçişleri.

**Yöntem**
- Veriyolları: Master altında Music, MusicDuck, SFX, Ambience, UI, Voice. Her ses kaynağı bir veriyoluna atanır.
- Ayar kaydırıcısı 0..1 arasıdır. Değerin karesini al, dB'ye çevir; 0'da veriyolunu sustur.
- Kısma: konuşma ya da önemli ses gelince müzik kısılır (MusicDuck veriyolu).
- Her SFX çalınışında perdeyi ±1 yarım ton, düzeyi ±2 dB rastgele oynat; aynı ses art arda makine gibi duyulmasın.
- Müzik katmanları yoğunluğa göre histerezisle değişir: 0,6'da yoğun katmana geç, 0,4'te geri dön.
- Müzik zamanlaması ses saatine bağlanır, oyun saatine değil.
- Donma ve ağır çekimde sesin davranışı: `his-kamera-seviye.md` → Oyun hissi, "Donma ve zaman".

**Eşikler**
| Ölçü | Başlangıç |
|---|---|
| Gerçek tepe | ≤ -1 dBTP |
| Ortalama ses düzeyi | PC ve konsol yaklaşık -24 LUFS, mobil yaklaşık -18 LUFS |
| Kısma oranı | 4:1–8:1 |
| Kısma atağı | ≤10 ms |
| Kısma bırakması | 300–500 ms |

**Tuzaklar**
- Motor özelinde (Godot veriyolu, `volume_db`, `max_polyphony`; Ebitengine ses bağlamı): ilgili motor dosyası.

**Doğrulama**
- Oyunun 2–5 dakikalık ses çıktısını kaydet ve `ebur128` ile ölç (ffmpeg filtresi). Araç yoksa neyin neden gerektiğini söyle, izin iste.
- Ajan dinleyemez. Ses dengesine kullanıcı dinleyerek karar verir.

## Gölgelendirici (shader)
**Kapsam:** Gölgelendirici yazma, derleme denetimi ve motorlar arası taşıma.

**Yöntem**
- Hesabın tamamını tek uzayda yap (dünya ya da görünüm); iki uzayı karıştırma.
- Normali parça (fragment) aşamasında yeniden normalleştir; enterpolasyon boyunu bozar.
- Derlemeyi motor dışında da denetle: GLSL için `glslangValidator`, WGSL için `naga`. Araç yoksa sor.
- Uç değer testi: girdileri 0, 1, negatif ve çok büyük değerlerle çiz.

**Tuzaklar**
- `smoothstep`'te kenarlar ters verilirse (ilk kenar ikinciden büyükse) sonuç tanımsızdır.
- Doku V ekseni motorlar arasında ters olabilir; taşırken denetle.
- Mobilde `mediump` hassasiyeti büyük değerlerde titreme yapar.
- İlk kullanımda gölgelendirici derlemesi takılma yapar (performans bölümü).
- Motor özelinde (Godot `TIME`, `ALPHA`): `motor-godot.md`.

**Doğrulama**
- Doğrulayıcı temiz geçer; uç değer görüntüleri açılıp bakılır.

## Fizik ayarı
**Kapsam:** Fizik adımı, tünelleme, kütle oranı, kararlılık.

**Yöntem**
- Fizik sabit adımla çalışır; çizim iki adım arasında enterpolasyon yapar.
- Tünellemeyi önle: tik başına yol en ince duvardan kısa olsun (`hız / tik < en ince duvar`). Değilse sürekli çarpışma ya da shapecast kullan.
- Çarpışan cisimlerin kütle oranı yaklaşık 1:10 içinde kalsın.
- Ölüm sarmalı: uzun bir kare çok sayıda fizik adımı ister, adımlar kareyi daha da uzatır. Kare başına adım sayısına üst sınır koy.

**Tuzaklar**
- Işınlanmada (yeniden doğma, kapı) enterpolasyon geçmişi sıfırlanmazsa cisim iki konum arasında kayarak çizilir.
- Gövdeyi konumunu doğrudan değiştirerek taşımak çarpışmayı atlar (Godot `position +=`, Phaser Arcade `x/y`).

**Doğrulama**
- Tünel testi: en hızlı cismi en ince duvara at; geçmemeli.
- 30 ve 144 FPS'te aynı hareketin hızını ölç (hız probu); sonuç aynı olmalı.

## Performans
**Kapsam:** Kare hızı sorununu ölçme ve en büyük maliyeti bulma.

**Yöntem**
- "Takılıyor" şikâyetini ms bütçesine çevir: hedef kare hızında bir kareye kaç ms düşüyor.
- Ölçüm koşulları: VSync kapalı, yayın (release) yapısı, hedef donanım. Editörde ölçülen sayı karar vermez.
- Önce CPU mu GPU mu sınırlı, ayır. Sonra en büyük tek maliyeti bul, önce onu düzelt.
- Ölçüm: aynı makinede 3 koşu; 60 kare ısınma, ardından 600 örnek; ortalamaya değil p95'e bak.
- Mobilde bütçeye %20–30 pay bırak.
- İlk kullanım shader takılması: gölgelendiricileri yükleme ekranında önceden ısıt.

**Tuzaklar**
- Hata ayıklama yapısında ya da VSync açıkken ölçmek.
- Motor özelinde bellek ve piksel oranı sorunları (PixiJS `removeChild`, three.js piksel oranı): `motor-web.md`.

**Doğrulama**
- Değişiklikten önce ve sonra aynı koşulda 3 ölçüm al, p95'leri karşılaştır.
- Hedef cihazda akıcılığa kullanıcı karar verir.
