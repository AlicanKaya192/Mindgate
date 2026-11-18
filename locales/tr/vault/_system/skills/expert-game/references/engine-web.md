# Web: Phaser, PixiJS, three.js

Kaynak paket Phaser 4.2, PixiJS 8.22 ve three.js r187'yi hedefliyor; sürüm ve davranış bilgileri sahibin 11 Kasım 2026 beyanıdır, bağımsız doğrulanmadı. Sürümü `package.json` ve kilit dosyasından oku.

## Ortak
**Yöntem**
- Oyun kurallarını motoru içe aktarmayan düz modüllerde tut, `node --test` ile sına.
- Tarayıcıda duman testi (kaynakta Playwright): renderer oluştu mu, sahne ya da çizim sayısı 0'dan büyük mü, konsol hata listesi boş mu. Sonra ekran görüntüsünü aç ve bak.
- Playwright ya da başka bir test aracı kurulu değilse neyin neden gerektiğini söyle ve izin iste. Yerel sunucu açmadan önce adresi ve nedeni söyle, izin bekle (#32).

**Tuzaklar**
- Yalnızca DOM'u denetleyen test, hiçbir şey çizmeyen tuvali kaçırır.
- Test için `window.game`, `window.app` ya da `window.renderer` açıldıysa yayından önce kaldır.

## Phaser
- Sahne örnekleri yeniden kullanılır. Sahne durumunu `init`'te sıfırla; kurucuda kurulan durum ikinci girişte eski kalır.
- HUD'u oyun sahnesinin üstünde ayrı bir sahne olarak `launch` ile çalıştır.
- Piksel sanatında v4'te `pixelArt: true`.
- 3'ten 4'e: efektler filtre sistemine geçti; `setTintFill` kaldırıldı; `Math.TAU` 2π'dir, 3'ten taşınan açı kodunu denetle.
- Arcade fizik:
  - Dinamik gövdeyi `x`/`y` atayarak taşıma; çarpışma atlanır. Hız ya da gövde yöntemlerini kullan.
  - Collider'ı `create`'te bir kez kur, `update`'te değil.
  - Hızlı mermi ince duvarın içinden geçer (`ses-golgelendirici-fizik-performans.md` → Fizik ayarı).

## PixiJS
- Uygulamayı `await app.init()` ile başlat.
- Ticker geri çağrısının argümanı bir sayı değil, Ticker nesnesidir; zamanı nesneden oku.
- `removeChild` GPU kaynağını boşaltmaz; işi biten nesneyi ayrıca yok et.

## three.js
- Piksel oranını `Math.min(devicePixelRatio, 1.5)` ile sınırla.
- `Clock` yerine `Timer` (r183'ten beri).
- Bağımlılıkları import map ile yükle.
- Oyun durumunu sahne grafiğinde değil düz bir nesnede tut; sahne bu durumdan çizilir.
- Gölge üç yerde açılır: renderer, ışık ve nesne (atan ve alan).
- Renk dokusu sRGB'dir; veri haritaları (normal, pürüzlülük) doğrusaldır.
- Son işleme zincirinin sonuna `OutputPass` koy.
- glTF santimetreyle gelirse model 100 kat büyük görünür; ölçeği düzelt.
- İskeletli modeli çoğaltırken `SkeletonUtils.clone` kullan.
