# Görsel zanaat ölçüleri

Kural değil, güvenli başlangıçtır: gerekçen varsa çiğne (Hobday). **(K)** kâşif raporundan, ham metinle karşılaştırılmadı; diğerleri 30 Ekim 2026'da sayfadan okundu.

## Renk
- Saf siyah ve beyaz yerine neredeyse siyah ve neredeyse beyaz. (Hobday, Refactoring UI)
- Grileri ana renge doğru hafif doygunlaştır: HSB'de <%5. Sıcak ve soğuğu karıştırma. (Hobday)
- Arayüzün çoğu gridir. Gri 8–10 ton, ana renk 1–2 tane ve 5–10 ton, vurgular seyrek; karmaşık arayüzde 10 renge kadar çıkabilir. (Refactoring UI)
- Tonları önceden sabit tanımla; `lighten`/`darken` ile anlık üretme. 9 basamak: önce 500 (düğme zemini olacak ton), sonra 900 ve 100, sonra 700 ve 300, sonra aralar. Matematik başlangıçtır; gözle düzelt. (Refactoring UI)
- Palet üreticisinden çıkan 5 renk yetmez, gerçek arayüz kurulmaz. (Refactoring UI)
- Paletteki renklerin parlaklığı birbirinden farklı olsun. (Hobday)
- HSL'de aynı açıklık farklı tonlarda farklı görünür. Algısal uzay kullan: OKLCH (K, Evil Martians), LCH (Linear), CIELAB (Stripe).
- Tema için az girdi: Linear 98 değişkeni 3'e indirdi (taban, vurgu, kontrast). Kontrast değişkeni yüksek kontrast temasını da verir.
- Ton basamakları kontrasta göre kurulursa: küçük metin için ≥5, ikon ve büyük metin için ≥4 basamak fark yeter. (Stripe)
- Erişilebilir olmak canlı olmak demek değildir; WCAG yalnızca kontrasta bakar. (Stripe)
- Koyulaştırırken siyah bindirme rengi soldurur; tonu koru, açıklığı düşür. (Comeau)

## Koyu tema
- Yakın öğeler daha açık; açık ve koyu temada aynı. (Hobday)
- Kap ile zemin parlaklık farkı HSB'de koyu temada ≤%12, açık temada ≤%7. (Hobday, yaklaşık 100 sitenin incelemesi)
- Koyu arayüzde gölge işe yaramaz; derinliği yüzey parlaklığıyla ver. (Hobday)
- Tema geçişi öğelerde geçiş animasyonu tetiklememeli. (Freiberg)
- `color-scheme: dark` ve `theme-color` ayarla. (Vercel)

## Tipografi
- En çok 2 yazı tipi; ikincisi fikri güçlendirmek için. (Hobday)
- Yazı tipi bilinçli seçilir: Butterick monospace, çoğu ücretsiz yazı tipi ve sistem fontlarından kaçınmayı önerir. Windows uygulamasında platform fontu makul olabilir; gerekçe yaz.
- Gövde web'de ≥16 px (Hobday); Butterick 15–25 px. Yoğun masaüstü: Fluent Body 14/20, Caption 12/16, Title 32/40 (K).
- Satır 60–80 karakter (Hobday), 45–90 (Butterick). Satır aralığı %120–145 (Butterick).
- Büyük yazıda harf ve satır aralığını azalt, küçükte artır. (Hobday) Dar içerikte ~1,5, geniş içerikte ~2, büyük başlıkta 1'e yakın. (K, Refactoring UI)
- Büyük harfli metne %5–12 harf aralığı; tek satırdan uzun olmasın. (Butterick) Tümü büyük harf okumayı zorlaştırır. (K, Fluent)
- 400'ün altında kalınlık kullanma; orta başlık 500–600. (Freiberg)
- Kalınlık üzerine gelince ya da seçilince değişmesin, düzen kayar. (Freiberg)
- Tablo ve sayaçta `font-variant-numeric: tabular-nums`. (Freiberg, Vercel)
- Kıvrık tırnak ve üç nokta karakteri (…). Kalın ve italik birlikte yok. Altı çizgi yalnızca bağlantıda. Ortalanmış metin seyrek. (Butterick, Vercel)
- Akışkan başlık: `clamp(48px, 5vw, 72px)` gibi. (Freiberg)
- Yazı tipi alt kümesi ve ön yükleme. (Freiberg, Vercel)

## Boşluk ve hizalama
- Ölçüler matematiksel olarak bağlı olsun; 8'in katları iyi başlangıç. (Hobday)
- Her şey bir şeye hizalı. Optik hizalama çoğu zaman matematikten iyidir; ±1 px oynat. (Hobday, Vercel)
- Dış boşluk ≥ iç boşluk: içeriği birbirine yakın, kenara uzak. (Hobday)
- Boşluk kontrast noktaları arasında ölçülür. (Hobday)
- Düğmede yatay dolgu dikeyin 2 katı. (Hobday)
- 12 sütunlu yatay ızgara. (Hobday)
- Yan yana iki sert ayrım koyma (zemin geçişi + kenarlık + çizgi). (Hobday)
- Listede tıklanabilir öğeler arasında ölü alan bırakma; dolguyu artır. (Freiberg)
- Görsel ağırlık sırası: en ağırdan en hafife, en ağır dış kenarda. (Hobday)
- Satır yüksekliğine bağlı hizalama: `calc((1lh - var(--size)) / 2)`; paragraf aralığı `1lh`. (K, Shadeed)
- Simgeyi büyük harf yüksekliğine göre ortala. (K, Prokopov)

## Köşe, kenarlık, derinlik
- İç köşe = dış köşe − aradaki boşluk (30 − 20 = 10). (Hobday) Çocuk köşe ≤ ebeveyn. (Vercel)
- Kenarlık hem kaptan hem zeminden kontrastlı olsun, ikisinin arası bir renk olmasın. (Hobday)
- Kenarlık yerine boşluk, zıt zemin ya da gölgeyle ayırmayı dene. (K, Refactoring UI)
- Tek derinlik tekniği kullan; karıştırma. (Hobday)
- Bütün gölgeler tek ışıktan, aynı yatay-dikey oranla. Yükseldikçe ofset ve bulanıklık artar, opaklık düşer. (Comeau)
- Tek gölge yerine katmanlı gölge: `0 1px 1px`, `0 2px 2px`, `0 4px 4px`, `0 8px 8px`, `0 16px 16px`, alfa 0,075. Vercel en az iki katman der. Çok öğede ve animasyonda performansa dikkat. (Comeau)
- Gölge rengi zeminin tonunu alır, gri olmaz. (Comeau, Vercel)
- Basit üstüne karmaşık ya da karmaşık üstüne basit; karmaşık üstüne karmaşık yok. (Hobday)

**Çelişki:** Hobday bulanıklık = 2 × uzaklık der (`0 4px 8px`). Comeau'nun katmanlı örneğinde bulanıklık = uzaklık; onun oranı dikey = 2 × yataydır. Tek gölgede Hobday'i, katmanlıda Comeau'yu kullan; projede birini seç.

## Hiyerarşi
- Yüksek kontrast önemli öğeye; yapısal öğeler olabildiğince düşük kontrast. (Hobday)
- `etiket: değer` kalıbı her şeye eşit ağırlık verir. Biçimden anlaşılıyorsa etiketi kaldır, değerle birleştir ("3 yatak odası"), gerekiyorsa küçült ve soldur. (Refactoring UI)
- Kullanıcı etiketi arıyorsa (teknik özellik sayfası) etiketi vurgula, değeri biraz aç. (Refactoring UI)
- Metin yanındaki simgenin kontrastını düşür, simge ağır görünür. İnce simge orta kalınlıkta metnin yanında kalınlaştırılabilir. (Hobday, Vercel)
- Üzerine gelme, basılma, odak dinlenme hâlinden yüksek kontrastlı. (Vercel)

## Süreç (Linear)
- Saarinen birkaç hafta her gün tam ekran seti ve akış tasarlayarak yüzlerce ekran üretti, sonra birkaç yöne indirdi. (Linear) Tek taslakla yetinme.
- Görünüm türlerine göre sına: liste, pano, zaman çizelgesi, bölünmüş, tam ekran. Yön, her ana ekranda stres testinden geçer.
- Sidebar ve sekmelerde etiket, simge, düğme hizası: "hemen görmezsin, birkaç dakika sonra hissedersin".
- Yenileme ürünü parçalamaz, evrim gibi hissettirir.
