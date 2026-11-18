# Ebitengine, Bevy, pygame-ce, LÖVE, Defold

Sürüm ve davranış bilgileri kaynak paketin sahibinin 11 Kasım 2026 beyanıdır, bağımsız doğrulanmadı. Sürümü projenin kendi dosyasından oku.

## Ebitengine
- Saniyede 60 tik. `Update` girdiyi okur ve durumu değiştirir; `Draw` yalnızca çizer, durumu değiştirmez.
- Ses bağlamı (`audio.NewContext`) programda bir kez oluşturulur.
- Ekransız ortamda ekran görüntüsü: oyunu xvfb altında çalıştırıp görüntü al (kaynak bunun için `-shot` bayrağını kullanıyor; projede böyle bir bayrak yoksa eklemeden önce sor). xvfb yoksa da sor.
- Teslim raporunda gözlenen (ekran görüntüsü, günlük) ve gözlenmeyen (his, ses) ayrı yazılır.
- Kaynaktaki macOS paketleme betiği var olan klasörü zorla siliyor. Bu beceri bunu yapmaz; çıktı klasörü varsa yeni ad seç ya da sor (#22).

## Bevy
- Kaynak 0.20'yi hedefliyor. Sürümü `Cargo.lock`'tan oku; sürümler arası API çok değişir.
- Commands ertelenir: aynı sistemde eklenen bileşen hemen görünmez.
- İlk güncellemede delta 0'dır; hıza bölen kodu koru.
- Ekransız test: `MinimalPlugins` ile uygulama kur, zamanı elle ilerlet.

## pygame-ce
- Ekransız test için `SDL_VIDEODRIVER=dummy`.
- `dt`'yi 0,05 s'de kıstır.
- `Rect` tamsayıya keser; ondalıklı konum için `FRect`.
- pygame ve pygame-ce aynı ortamda kurulmaz; projede hangisi varsa onu kullan.

## LÖVE
- Kaynak 11.5'i hedefliyor.
- Sabit adım `1/60`; `dt`'yi 0,25'te kıstır.
- Piksel sanatında `love.graphics.setDefaultFilter("nearest")` görseller yüklenmeden önce çağrılır.
- `t.identity` (kayıt klasörünün adı) ilk yayından önce belirlenir.
- Ekransız koşu: `--frames 120` ve zaman aşımı. Zaman aşımı çıkış kodu 124 ise oyun takılmıştır.

## Defold
- Kaynak 1.14'ü hedefliyor.
- Statik denetim (kaynakta `check_defold_project.py`).
- Derleme Bob ile (kaynağa göre JDK 25 ister). JDK yoksa sor.
- Ekransız çalıştır, günlükte `ERROR:SCRIPT:` ara.
- Testin kendi bitiş satırını yazdırması zorunludur; satır yoksa koşu bitmemiştir.
