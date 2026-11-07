# Hareket, etkileşim ve UX ölçüleri

**(K)** kâşif raporundan, ham metinle karşılaştırılmadı; diğerleri 30 Ekim 2026'da sayfadan okundu.

## Hareket: önce gerekli mi?
- Amaç sor: nedeni ya da sonucu açıklıyor mu, mekânsal tutarlılık veriyor mu, nadir bir sevinç mi? Cevap yoksa ekleme. (Kowalski, Vercel)
- Sıklığa bak: günde onlarca-yüzlerce kez görülen şeyde hareket yok. Raycast açılışı hiç animasyonsuz. (Kowalski)
- **Klavyeyle tetiklenen eylem asla animasyonlu olmaz.** (Kowalski)
- Sık ve yeniliksiz eylemde gereksiz hareket yok: sağ tık menüsü, listeye ekleme ve silme, önemsiz düğmede üzerine gelme. (Freiberg)
- İşlevsel veri ekranında çoğu zaman hiç hareket en iyisidir. (K, Kowalski)
- Tanıtım sayfası ayrı: orada hareket anlatabilir ve daha uzun olabilir. (Kowalski)
- Temalı sahnede hareket kimliğin parçası olabilir. Bu kurallar sık eylemler içindir, sahne için değil.

## Hareket: nasıl
- Süre: etkileşimde ≤200 ms (Freiberg), genel UI <300 ms; 180 ms'lik seçim 400 ms'den duyarlı hissettirir. (Kowalski)
- Giriş ve çıkışta ease-out. Ease-in UI'a uygun değil: sonda hızlanır, 300 ms'lik aynı açılır menü yavaş hissettirir. (Kowalski)
- Yerleşik CSS eğrileri çoğu zaman zayıftır; özel eğri kullan. Sürekli dönmede linear. (Kowalski; K, Fluent)
- `scale(0)`'dan başlama: ~0,9+ ve opaklıkla (Kowalski örneği 0,93); iletişim kutusu ~0,8'den (Freiberg).
- Basışta `:active` ile `scale(0.97)` (Kowalski), ~0,96 ya da ~0,9 (Freiberg); 0,8 çok fazla.
- Popover tetikleyiciden açılır; `transform-origin: center` çoğu zaman yanlış. (Kowalski, Vercel)
- Tooltip: ilkinde gecikme, grupta sonrakilerde gecikme ve animasyon yok. Etkileşimli içerik koyma. (Kowalski, Vercel, Freiberg)
- Yalnızca `transform` ve `opacity`; `width`, `height`, `top`, `left` kaçınılır. `transition: all` yasak; özellikleri tek tek yaz. (Vercel)
- Hareket kesilebilir olsun. Önce CSS, sonra Web Animations API, sonra JS kütüphanesi. (Vercel)
- Otomatik oynayan ve >5 sn süren harekette durdur ya da gizle düğmesi. Görünmeyen döngüyü duraklat. (Vercel, Freiberg)
- `prefers-reduced-motion` karşılığı zorunlu. (Vercel)
- Bir geçiş hâlâ kötüyse iki durum arasına ~2 px `blur` denenebilir; büyük blur yavaştır. (Kowalski, Freiberg)
- Bulanık ya da ölçeklenen dolu dikdörtgen bantlanma yapar; radyal gradyan kullan. (Freiberg)

## Bekleme ve geri bildirim
- <0,1 sn anlık hisseder; 1 sn düşünce akışını korur; >10 sn yüzde, kalan süre ve iptal ister. (K, NN/g) Doherty: <400 ms verimli. (K, Laws of UX)
- >10 sn işte kalan süreyi söyle. (NN/g) 1 sn üstü gösterge, 2–10 sn döngüsel, 10 sn üstü yüzde. (K, NN/g)
- Gösterge ~150–300 ms gecikmeyle başlar, ~300–500 ms görünür; titreme olmaz. (Vercel)
- İskelet son içerikle birebir aynı ölçüde, düzen kaymaz. (Vercel) 10 sn altı yüklemede. (K, NN/g)
- Yükleyen düğme göstergeyi gösterir, etiketini korur. (Vercel)
- İyimser güncelleme: başarı olasıysa hemen değiştir, hatada geri al ya da Geri Al sun. (Vercel, Freiberg; K, Wroblewski)
- Geri bildirim tetikleyicinin yanında: kopyalamada bildirim değil yerinde onay işareti. (Freiberg)
- Yıkıcı işlemde onay ya da süreli Geri Al. (Vercel) Değiştirici (toggle) anında etkili, onay istemez. (Freiberg)
- Yazma işlemi <500 ms bütçe. (Vercel)

## Durumlar
- Boş, az, yoğun ve hata ayrı tasarlanır. Kısa, ortalama, çok uzun içerik düzeni bozmaz. (Vercel)
- Boş ekran ne olduğunu ve nasıl dolacağını söyler, yeni öğeye ya da şablona götürür. (Freiberg; K, NN/g)
- Çıkmaz sokak yok: her ekranda bir sonraki adım ya da kurtarma yolu. (Vercel)
- Hata ne olduğunu ve nasıl düzeltileceğini sade dille söyler. (Vercel; K, NN/g)

## Formlar
- Etiket her alanda, tıklayınca odaklar; yer tutucu etiket değildir, örnek gösterir. (Vercel, Freiberg; K, Smashing)
- Gönder düğmesini önceden devre dışı bırakma; gönderim başlayınca kilitle, gösterge koy. (Vercel)
- Hata alanın yanında; gönderimde ilk hataya odaklan. (Vercel) Doğrulamayı yazma durduktan sonra göster. (K, Smashing)
- Tuşa basışı engelleme, yapıştırmayı engelleme; uyarıyı göster. Kaydedilmemiş değişiklikte çıkarken uyar. (Vercel)
- Doğru `type`, `inputmode`, `autocomplete`. Enter gönderir. Mobilde girdi ≥16 px, iOS yakınlaştırmasını önler. (Vercel, Freiberg)
- Alan sayısını azalt; tek sütun; altıdan fazla soruda grupla. (K, Smashing)
- Açılır menü son çare: az seçenekte adımlayıcı ya da radyo, altı menü yerine tek tarih seçici. (K, Wroblewski)

## Veri yoğun ekran ve tablo
- Rakamlar `tabular-nums`; ondalık sayısı ihtiyaca göre, sunucudaki tam değer korunur. (Vercel; K, Smashing)
- Anahtar sütunlar (ad, durum) kaydırılmaz. Küçük tablo mobilde kart dizisine döner. (K, Smashing)
- Tıklanabilir öğe ≥40×40 px, %200 büyütmede düzen bozulmaz. (K, Smashing)
- Büyük listeyi sanallaştır. (Vercel)
- Sidebar ve başlıkları yoğun tut, içeriğe yer aç. (Linear)

## Etkileşim ayrıntıları
- Klavye her yerde; `:focus-visible`; odak halkası yapışkan başlık altında kalmaz. (Vercel) Yarıçapa uyan halka için `box-shadow`. (Freiberg)
- Görsel hedef <24 px ise hedefi 24 px'e büyüt; mobilde ≥44 px. Yakınlaştırmayı kapatma. (Vercel)
- Bağlantı `<a>`dır, `<button>` ya da `<div>` değil. (Vercel)
- Sıralı listede ↑ ↓ ile gezinme; açılır menü `mousedown` ile anında. (Freiberg)
- Üzerine gelme durumu `@media (hover: hover)` içinde; dokunmatikte yanıp sönmez. (Freiberg)
- Süzgeç, sekme, sayfalama URL'de durur; Geri tuşu kaydırma yerini korur. (Vercel)
- Yalnızca simgeli düğmede `aria-label`; devre dışı düğmeye tooltip konmaz. (Freiberg)
- Süs öğesi (ışıma, gradyan) `pointer-events: none`. (Freiberg)

## Yasalar (K, Laws of UX)
- Jakob: kullanıcı başka yerde öğrendiğini bekler. Hick: seçenek arttıkça karar uzar. Fitts: hedef küçük ve uzaksa ulaşmak uzar. Miller: 7 ± 2 öğe. Doruk-son: deneyim en yoğun an ve sonla hatırlanır. Estetik-kullanılabilirlik: güzel olan daha kullanışlı sanılır, sorunları gizleyebilir.

## Çelişkiler
- **Dokunma hedefi:** Vercel 44 px, Smashing 48 dp ve 40 px (2018, 2019). Mobilde ≥44 px kullan.
- **Kontrast:** Vercel APCA'yı tercih eder; bu beceri WCAG 2.2 AA'yı asgari tutar.
- **İlk odak:** Vercel masaüstünde tek ana girdide otomatik odak der, mobilde nadiren; Freiberg dokunmatikte yok der. Uyumlu.
- **Yazım işaretleri:** Vercel'in Title Case ve `&` tercihleri kendi markasınındır, evrensel değil.
