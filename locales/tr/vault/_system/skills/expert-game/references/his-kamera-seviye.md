# Oyun hissi, kamera ve seviye tasarımı

Sayılar kaynak paketin sahibinin beyanıdır, bağımsız doğrulanmadı. Her eşik başlangıç noktasıdır: ölç, oynat, ayarla.

## Oyun hissi
**Kapsam:** Vuruşun, çarpmanın ve toplamanın oyuncuya tepki olarak hissettirilmesi.

Sayılar bir oyun geliştirme beceri paketinin sahibinin beyanıdır, bağımsız doğrulanmadı; başlangıç noktasıdır, ölçerek ayarla. Azami ofset (12×8 px) piksel sanatında büyük kalabilir; ofseti oyunun piksel ölçeğine göre seç. Unity'ye özgü `Lerp` notu `motor-unity.md`'de.

**Kademeler.** Olay yalnızca kademesini söyler; değerler tek tabloda durur.

| Kademe | Travma | Donma | Parçacık |
|---|---|---|---|
| Küçük | 0,10–0,20 | yok | 0–4 |
| Orta | 0,30–0,50 | 0,04–0,06 s | 6–12 |
| Büyük | 0,70–1,00 | 0,10–0,15 s | 20–40 |

**Travma modeli**
- Travma 0..1 arasında birikir. Sarsıntı gücü travmanın karesidir: küçük olay daha da küçülür, büyük olay öne çıkar.
- Travma gerçek zamanla söner, saniyede 1,2. Donma sönümü durdurmaz.
- Azami ofset 12×8 px, azami dönme (roll) 0,1 rad. Kendi örneğimiz:
  `sarsinti = travma * travma`
  `ofset = azami_ofset * sarsinti * gurultu(t)`
- Sarsıntıyı kameranın ofsetine uygula; karakterin gövdesini ya da kameranın asıl konumunu oynatma. Kamera zincirinde en son eklenir.
- Gürültü yumuşak olsun (zamanla akan gürültü). Her karede yeni rastgele ofset titreme gibi durur.

**Donma ve zaman**
- Donma ~0,15 s'nin altında kalsın.
- Üst üste donmada zamanı yalnızca son çağrı geri açar. Her çağrı bitiş anını ileri atar; ilk donmanın bitişi ikincisini erken kesmez.
- Arayüz geçişleri ve sarsıntı sönümü gerçek zamanla akar, donmadan etkilenmez.
- Zaman ölçeği (time scale) sesi yavaşlatmaz. Donmada ve ağır çekimde sesin ne yapacağını ayrıca kararlaştır.
- Donma sırasında basılan tuş tamponlanır, donma bitince işlenir.

**Easing ve squash-stretch**
- Beliriş ve büyüme (pop) aşımlı (overshoot) easing ile; yerine oturma ease-out ile. Ease-in yalnızca hazırlıkta kullanılır.
- Ezilme (squash): yatay 1,3, dikey 0,7; 0,18 s içinde normale döner.

**Görsel varlık seti**
- Birden çok görsel (sprite, tileset, arayüz öğesi) üretilecekse önce varlık manifesti yaz; her satırda ad, boyut, durum, kaynak, lisans, onay.
- Tüm seti üretmeden önce tek bir hedef görseli oyun ölçeğinde (oyunun gerçek çözünürlüğünde, oyun ekranında) kullanıcıya onaylat.
- Arayüz öğesi tek görsel değildir: kaynak paket her öğe için 6 durum ister (listesi okunmadı); her durumu manifestte ayrı satır yaz.
- Kırpma, alfa ve boyut denetimi model gözüyle değil araçla yapılır (görüntü kütüphanesi kullanan küçük bir betik).

**Doğrulama**
- 30 ms arayla iki donma tetikle: sonunda zaman ölçeği 1,0'a döner.
- Travmayı 1'e çıkar: 1/sönüm saniye sonra 0 olur, donma sırasında da azalır.
- Bu testler ekransız yazılır. Hissin kendisini kullanıcı oynayarak onaylar.

## Kamera
**Kapsam:** Oyuncuyu izleyen kameranın takibi, ölü bölgesi, ileri bakışı ve sınırları.

**Yöntem**
- Takipte `1 - exp(-hız * dt)` katsayılı yumuşatma ya da kritik sönümlü yay kullan.
- Ölü bölge (dead zone) içinde kamera kıpırdamaz; hedef bölgeden çıkınca izlemeye başlar.
- İleri bakış (look-ahead): kamera hareket yönüne doğru kayar, kayma kısa bir sürede kurulur.
- Görünümü bölüm sınırına kırp; oyuncu haritanın dışını görmesin.
- Sarsıntı her şeyden sonra, en son eklenir.

**Eşikler**
| Ayar | Başlangıç |
|---|---|
| Yumuşatma hızı | 5–12 |
| Ölü bölge | 32–64 px |
| İleri bakış mesafesi | 40–120 px |
| İleri bakışın kurulma süresi | 0,2–0,4 s |

**Tuzaklar**
- Kare başına sabit katsayılı lerp: yüksek FPS'te kamera daha sıkı izler, düşük FPS'te geri kalır.
- Işınlanmada (oda geçişi, yeniden doğma, sahne yükleme) yumuşatma durumu sıfırlanmazsa kamera haritayı süpürerek gelir.

**Doğrulama**
- Aynı hareketi iki farklı FPS'te oynat, kameranın hedefe gecikmesini karşılaştır. Gecikme aynı kalmalı.

## Seviye tasarımı
**Kapsam:** Bölüm geometrisi, öğretim sırası, tempo ve kilitlenme denetimi.

**Yöntem**
- Önce erişimi ölç: karakterin gerçek kontrolcüsüyle en yüksek ve en uzak zıplamayı kaydet. Bölüm, tahmin edilen değerle değil ölçülen değerle kurulur.
- Zıplama ayarı değişirse ölçümü yenile ve bölümleri yeniden denetle.
- Yeni mekaniği dört adımda öğret: tanıt (güvenli ortamda), geliştir, bük (beklenmedik bir kullanım), baskı altında sına.
- Tempo: yoğunluğu 0..1 ile işaretle. Yoğun bölümleri (0,7 ve üstü) en çok 2 art arda koy, arkasından nefes aldır.
- Anahtar kendi kapısının arkasında kalmasın. Her kilidin anahtarı, o kilit açılmadan ulaşılabilen bir yerde olsun.

**Eşikler**
| Ölçü | Başlangıç |
|---|---|
| Zorunlu boşluk | ölçülen erişimin 0,7'si |
| İsteğe bağlı zor geçiş | ölçülen erişimin 0,95'i |
| Art arda yoğun bölüm (≥0,7) | en çok 2 |

Platform oyununda tür dosyasındaki "boşluk hesaplanan erişimden en az 1 tile kısa" kuralı da geçerlidir; iki sınırdan hangisi daha kısa boşluk veriyorsa onu al.

**Tuzaklar**
- Erişimi tahminle ya da editördeki ızgaraya bakarak varsaymak.
- Anahtar ve kapı sırası yalnızca elle oynayarak denetlenirse kilitlenme kaçar.

**Doğrulama**
- Hedefe ulaşılabilirlik denetimi yaz (kaynakta `goal_reachable`): başlangıçtan hedefe, anahtar sırasına uyarak yol var mı. Yoksa bölüm kilitlenmiştir.
- Tempo denetimi (kaynakta `pacing_problems`) boş dönmeli: art arda yoğun bölüm sınırı aşılmamış.
- Akışın iyi olup olmadığına kullanıcı oynayarak karar verir.
