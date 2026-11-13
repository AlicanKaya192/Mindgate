# Başlık ve küçük resim

Başlık ile küçük resim tek birimdir. Ayrı yazılınca küçük resim çoğu zaman başlığı tekrar eder ve tıklama alanının yarısı aynı şeyi iki kez söyler.

## Akış
1. On başlık yaz. Hepsini bir dosyaya koyup `title_check.py dosya.txt` ile denetle; araç sorunu en az olandan başlayarak sıralar.
2. En iyi üçünü araç çıktısıyla göster. Her birinin tek sorununu da söyle.
3. Kazanan başlık için küçük resim özeti yaz:
   - en çok 3 kelimelik metin (başlıktaki kelimeleri tekrar etmez)
   - yüz ifadesi ve kadraj
   - arka planın akış boyutunda karşıtlığı nasıl koruyacağı
4. Başlık ve küçük resim metnini birlikte denetle: `title_check.py --title "..." --thumb "..."`.

## Kurallar ve nedenleri
| Kural | Neden | Kaynak |
|---|---|---|
| En çok 100 karakter | YouTube daha uzun başlığı kabul etmez | Resmî (`esikler.md`) |
| 60'tan sonrası aramada, 40'tan sonrası mobil akışta kesilebilir | Masaüstünde kuyruk, mobilde konu kaybolabilir | Gözlem, resmî değil |
| Küçük resim başlığı tekrar etmez | Aynı vaat, farklı kelimeler | Yöntem |
| Küçük resimde en çok 3 kelime | Akış boyutunda dördüncü kelime okunmaz | Yöntem |
| Sayı, ad ya da tarih | Her sıfattan daha çok şey söyler | Yöntem |
| En çok 2 tamamen büyük harfli kelime | Fazlası spam gibi okunur; 3 harfli kısaltmalar (SQL, API) sayılmaz | Yöntem |

**Türkçe notu:** Araç iki kelimeyi şu durumlarda aynı sayar: biri ötekiyle başlıyorsa ("kanal" ve "kanalı") ya da yalnızca son ünsüz yumuşamışsa ("kitap" ve "kitabı"; p/b, ç/c, t/d, k/ğ). "Model" ile "modern" ya da "kanal" ile "kanat" aynı sayılmaz. Sonuç bir uyarıdır, karar kullanıcınındır.
