# Ölçen denetim

Çalışan sayfayı gerçek tarayıcıda çizer ve ölçer. Standart kütüphane ve kurulu Edge ya da Chrome yeter; paket kurulmaz. Yalnızca web arayüzleri içindir. Masaüstü arayüzünde (WinUI, Slint, Qt) elle liste ve ekran görüntüsü kullanılır.

## Kullanım
Yerel sayfa ya da sunucu da bir sayfadır: açmadan önce #32 izni alınır.

```bash
{{PY}} -I scripts/page_audit.py http://localhost:3000/ http://localhost:3000/ayarlar --output audit --record design-record.json --baseline
```

| Seçenek | Ne yapar |
|---|---|
| `--output` | Tam sayfa görüntüleri ve `summary.json` |
| `--record` | Projenin tasarım kaydı; projede saklanır |
| `--baseline` | Bu ölçümü yeniden tasarımdan önceki envanter olarak yazar. Değişiklikten **önce** bir kez çalıştır |
| `--note "..."` | Kullanıcının bu turdaki yorumunu tura yazar |
| `--widths` | Varsayılan 320, 375, 768, 1280, 1440, 1920; koyu tema 375 ve 1440'ta da ölçülür |
| `--external-url` | Yerel olmayan adresi ve dış ağı açar. Yalnızca site izni varken |

Çıkış kodu: 0 geçti, 1 kaldı, 2 kullanım hatası. **Geçti, güzel demek değildir:** ölçüm yalnızca ölçülebileni yakalar; görüntülere yine gözle bakılır.

**Güvenli varsayılan:** Yerel olmayan adres reddedilir, sayfanın dış ağa çıkması engellenir. Dış font ya da CDN kullanan sayfa bu yüzden yedek yazıyla görünebilir; `summary.json`'daki `external_resources` ve görüntüye bak.

## Tasarım kaydı (`design-record.json`)
```json
{
  "keep": ["arama", "yer imleri"],
  "add": ["sıkı tablo"],
  "exemptions": [{"rule": "T04", "scope": ".chip", "reason": "yoğun süzgeç, masaüstü", "date": "YYYY-AA-GG"}],
  "removed": [{"type": "buttons", "name": "Gönder", "reason": "üst menüde tek düğmeye indi"}],
  "baseline_inventory": {},
  "rounds": []
}
```
- **Korunacak ve eklenecek (`keep`, `add`):** 1. adımda yazılır; değişiklik bunlara göre yapılır.
- **Muafiyet (`exemptions`):** `reason` zorunludur; gerekçesiz muafiyet geçersizdir ve sınavı düşürür. `scope` seçicide aranır, boşsa kural bütün sayfada muaf olur. Artık kullanılmayan muafiyet bildirilir, silinir.
- **Ev stili:** Aynı kural 3 sayfada muafsa bu istisna değil kuraldır; projenin tasarım kararlarına yazılır.
- **Koruma sayacı:** Bağlantı, düğme, alan, başlık, görsel ve tablo adıyla kıyaslanır. Kaybolan her öğe `LOST` olarak adıyla yazılır ve sınavı düşürür; bilerek çıkarıldıysa `removed`'a gerekçesiyle yazılır. Olay dinleyicileri sayılmaz, düğme ve bağlantı listesi ona yakın bir işarettir.
- **Turlar (`rounds`):** Her çalıştırma tur olarak yazılır. Yeni hata ya da uyarı çıkarsa `REGRESSED` denir: bir yeri düzeltirken başka yer bozulmuştur.

## Kurallar
**Hata** sınavı düşürür, **uyarı** düzeltilir ya da gerekçelendirilir, **not** bakılıp karar verilir. Notlar suçlama değildir, seçimin bilinçli olduğunu sorar.

| Kural | Önem | Ölçülen | Dayanak |
|---|---|---|---|
| T01 | hata | Yatay kaydırma | Duyarlı düzen |
| T02 | hata | Ekran dışına taşan öğe | Duyarlı düzen |
| T03 | hata | Metin kontrastı: <4.5:1, büyükte <3:1 | WCAG 1.4.3 |
| T04 | hata, uyarı | Hedef <24 px; mobilde <44 px | WCAG 2.5.8, Vercel |
| T05 | uyarı | Mobilde girdi yazısı <16 px | Vercel, Freiberg |
| T06 | uyarı | Baskın yazı mobilde <16, masaüstünde <14 px | Hobday, Fluent |
| T07 | uyarı | Satırda ortalama >90 karakter | Butterick |
| T08 | uyarı | Satır aralığı <%120 | Butterick |
| T09 | uyarı | 2'den çok yazı ailesi | Hobday |
| T10 | not | Boşlukların %25'inden çoğu 4'lü ölçek dışında | Hobday |
| T11 | not | 4'ten çok renk ailesi | NN/g: fazla renk |
| T12 | not | Saf siyah ya da beyaz | Hobday, Refactoring UI |
| T13 | not | 3'ten çok gölge; koyu arayüzde gölge | Hobday |
| T14 | uyarı | İç köşe yarıçapı uyumsuz | Hobday |
| T15 | uyarı | `transition: all` | Vercel |
| T16 | uyarı | Kontrolde >300 ms geçiş | Kowalski |
| T17 | hata | Alt metni, etiketi ya da adı olmayan öğe | WCAG 1.1.1, 4.1.2 |
| T18 | uyarı | Lorem ipsum, John Doe | Yapay zekâ izi |
| T19–T24 | not | Gradyanlı metin, kenar şeritli kart, küçük büyük harfli etiket, küçük mono etiket, emoji simge, metin sonu ok | `yapay-zeka-izi.md` |
| T25 | uyarı | Düğme ya da menü etiketi kırılıyor | Üretilmiş arayüz denetimi |
| T26 | not | Tablo rakamında `tabular-nums` yok | Freiberg, Vercel |
| T27 | uyarı | Hareket var, `prefers-reduced-motion` yok | WCAG 2.3.3, Vercel |
| T28 | uyarı | Odakta görünür değişiklik yok | WCAG 2.4.7 |
| T29 | not | İçerik kısa, ekranın altı boş | Üretilmiş arayüz denetimi |
| T30 | uyarı | h1 sayısı 1 değil | Vercel |

**Ölçümler** (`summary.json`, kural değil, gözle yorumlanır): kontrol yükseklikleri, bölüm aralıkları, ilk ekrandaki kelime, h1 ilk ekranda mı, baskın yazı, yazı aileleri, renk ailesi, gölge ve köşe çeşidi, ölçülemeyen kontrast, dış kaynaklar. Kontrol yüksekliğinde çok farklı değer ya da düzensiz bölüm aralığı tutarsızlık işaretidir. Sayısal eşik konmadı, çünkü kaynaklı bir eşik bulunmadı.

## Sınırlar
- Görsel ya da gradyan zeminli metnin kontrastı ölçülmez (`unmeasurable_contrast`); üst üste binen öğeler hesaba katılmaz.
- Kod okuyamaz; yalnızca ilk çizim durumunu görür. Açılır menü, iletişim kutusu ve hata durumu için o duruma götüren adresi ölçmek gerekir.
- Tema yalnızca `prefers-color-scheme` ile değişir; sınıfla tema değiştiren sayfanın koyu hâli ölçülmez.
- Zevk, özgünlük ve doğru kalıp seçimi ölçülmez: akışın 4. ve 8. adımları onun içindir.
