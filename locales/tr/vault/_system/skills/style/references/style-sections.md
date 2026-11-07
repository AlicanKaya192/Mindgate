# Stil bölümleri: ne yazılır, ölçüt ne

`stil` becerisinin 3. adımı. Her bölüm referans görselden çıkarılır, ama hiçbir bölüm referansın yerleşimini, metnini ya da logosunu tarif etmez. Toplam 2.000–4.000 kelime. Her bölümde "nasıl görünür" ile birlikte "nasıl yapılır" yazılır; somut sayı (hex, px, ms, oran) verilmeyen cümle zayıf cümledir.

## 1. Görsel dil ve palet
- Betikle örneklenmiş hex değerleri; her rengin yaklaşık alan oranı (ör. zemin %70, ana mürekkep %20, vurgu %5).
- **Hangi renk nerede kullanılabilir:** zemin, metin, vurgu, uyarı. Vurgu rengi neye ayrılmış (yalnızca anahtar sayı mı, yalnızca hareket eden öğe mi)?
- Yasak eşleşmeler ve kontrast sınırı (metin zeminde en az 4,5:1).

## 2. Malzeme ve yüzey
- Görüntü fiziksel olarak neden yapılmış: kâğıt, mürekkep, serigrafi, cam, ışık, piksel, kumaş…
- Malzemenin davranışı: kenar (keskin, yırtık, taşmış mürekkep), tane (grain), gölge (düşen, iç, yok), üst üste baskı (overprint), aşınma, kayık baskı (misregistration).
- Her doku **deterministik** üretilir: tohumlu gürültü (value/Perlin/simplex), sabit tohum, önceden üretilip önbelleğe alınan katmanlar. Ekran üstüne konmuş hazır doku resmi yok.

## 3. Tipografi
- Yazı türleri ve onlara uyan ücretsiz web fontları (adıyla); başlık, gövde, etiket ve sayı için ayrı ayrı.
- Boyutlar (biçime göre px), büyük-küçük harf, harf aralığı, satır aralığı.
- Yazının sayfaya oturuşu: zemine basılmış mı, üstüne yapıştırılmış mı, kesilmiş mi?
- Giriş ve çıkış: harf harf mi, satır satır mı, damga gibi mi; hangi yumuşatma ve süre.

## 4. Kompozisyon alışkanlıkları
- Izgara ritmi, kenar boşlukları, ölçek karşıtlığı (en büyük ile en küçük öğe oranı), boş alan kullanımı, kırpma alışkanlığı.
- Referansın kendi yerleşimi değil, **alışkanlıkları** yazılır: "tek dev sayı ve yanında küçük etiket" alışkanlıktır; "sol üstte kırmızı daire" yerleşimdir.

## 5. İmza unsurları
- Bu görünümü tanınır kılan 3–5 şey. Her biri için: nasıl görünür, neden bu stile ait, videoda kaç kez ve nerede kullanılır (aşırı kullanım imzayı süse çevirir).

## 6. Teknik uygulama (en önemli bölüm)
- Çizici seçimi ve gerekçesi: Canvas 2D, SVG ya da WebGL. Doku ve ışık ağırsa WebGL; vektör ve metin ağırsa SVG ya da Canvas.
- Katman yapısı (alttan üste): zemin, doku, şekiller, metin, üst baskı, son işlem (vignette, tane).
- Ekran dışı tamponlar (offscreen canvas), maskeler, karıştırma kipleri (`multiply`, `screen`), gölgelendiriciler (shader) ya da gürültü fonksiyonları, adım adım.
- Dokuların nasıl üretilip önbelleğe alındığı; `seek(t)` çağrısında yeniden üretilmemesi.
- Performans sınırı: kare başına çizim süresi ölçülür; çok yavaşsa önce önbellek, sonra çözünürlük düşürülmüş ara tampon.

## 7. İmza hareketi
- Bu malzeme gerçek olsaydı nasıl hareket ederdi: mürekkep damgası (ani iniş, hafif yayılma), kâğıt kayması (sürtünmeli, hafif gecikmeli), ışık süpürmesi.
- Zamanlama (ms) ve yumuşatma eğrileri (ör. `cubic-bezier` değerleri); hareket hiyerarşisi: önce ana öğe, sonra destekleyenler, en son ayrıntı.
- Durgunluk payı: okunacak metin en az ne kadar sabit kalır.

## 8. Geçişler
- Sahne değişimlerinin çoğu düz kesme ya da kamera hareketidir, kurgulanmış bir film gibi.
- Büyük anlar için stilin kendi malzemesinden 1–2 imza geçiş (ör. kâğıdın yırtılıp alttakini göstermesi, mürekkebin yayılıp ekranı kaplaması); ne zaman kullanılacakları.

## 9. Bilgi tasarımı
- Bu stile uyan diyagram türleri (akış, karşılaştırma, zaman çizelgesi, oran).
- Sayılar, etiketler, oklar ve grafikler bu stilde nasıl görünür; sayı sayma (count-up) hareketi.
- Telefonda okunurluk: en küçük yazı boyutu, ekranda en çok kaç kelime.

## 10. Ses
- Malzemeye uyan efekt türleri, arama terimi olarak (ör. "paper slide", "rubber stamp", "pen scratch"). Seyrek kullanım kuralı.

## 11. Kaçınılacak ucuz kısa yollar
Modelin bu görünümü genelde taklit ettiği 4–6 yol ve her birinin yerine ne yapılacağı. Biçim: **kısa yol → neden sahte durur → yerine**. Örnek türler: gerçek üst baskı yerine düz renk, kırılma yerine bulanıklık, hazır gradyan, sabit doku resmi, her şeyin aynı anda kayması, her öğede aynı yumuşatma.
