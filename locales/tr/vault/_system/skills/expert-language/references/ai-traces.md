# Metinde yapay zekâ izi: kalıplar ve düzeltme

Kendi cümlelerimizle yazıldı. Ek olarak `uzman-icerik` becerisindeki "Yapay zekâ izi" listesi geçerlidir.

## Nasıl kullanılır
1. **Önce yalnızca işaretle**, sonra düzelt. Kullanıcı "sadece bak" dediyse yeniden yazma, yalnızca tablo ver.
2. Sorunlu ifadeyi alıntıla ve kalıbın adını yaz. "Yapay zekâ olasılığı %70" gibi genel puan verme; kanıtı yok.
3. Tek bir kalıp tek başına sorun değildir; aynı kalıp metin boyunca birikiyorsa işaretle.
4. Düzeltirken sıra: önce gereksizi at (kısalt), sonra üslubu düzelt, en son olguları kontrol et.
5. Olgu eksikse (isim, sayı, tarih) uydurarak doldurma; `[KANIT GEREK: …]` yaz ya da sor.
6. Kelimeyi eş anlamlısıyla değiştirmek yeni bir iz üretir. Cümleyi olgudan yola çıkarak yeniden kur.

## Kalıplar
| Grup | Kalıp | Yerine |
|---|---|---|
| Yapı | "X değil, Y" karşıtlığıyla açılış | Y'yi gerekçesiyle doğrudan söyle |
| Yapı | "X yok, Y yok, Z yok" olumsuzluk dizisi | Ne olduğunu söyle |
| Yapı | Her bölümde aynı kalıp (özet kutusu, kalın başlıklı madde, "Artıları / Eksileri") | Bölümün içeriğine göre değişen yapı; düzyazı |
| Yapı | Üçlü listeler ve her paragrafın üç cümle olması | İçerik ne gerektiriyorsa |
| Yapı | Her satırda tek cümle | Normal paragraf |
| Noktalama | Uzun tire (—) ile cümle bağlama | Nokta ya da virgül |
| Noktalama | İki noktayla sonuç açıklama ("Sonuç: …") | Cümlenin kendisi |
| Retorik | Kendi sorusunu cevaplama ("Peki neden? Çünkü…") | Doğrudan anlatım |
| Retorik | Okura kapanış sorusu, etkileşim tuzağı | Sonuç cümlesi |
| Retorik | Belgeyi ya da adı tanıtan duyuru cümlesi ("Adını X koydum", "ekte paylaşıyorum") | Doğrudan içerik |
| Kelime | İçi boş süs kelimeleri: "güçlü", "kusursuz", "devrim niteliğinde", "bir üst seviyeye" | Ölçü ya da olgu |
| Kelime | Hazır açılışlar: "Günümüzün hızla değişen dünyasında", "İşte mesele şu" | Okurun sorunuyla ya da sonuçla açılış |
| Kelime | Aşırı yumuşatma: "belki de", "bir nevi", "oldukça" yığılması | Emin olunan şeyi düz söyle, emin olunmayanı bir kez belirt |
| İçerik | Yaşanmamış deneyim ya da duygu ("açık konuşayım, çok korkmuştum") | Gerçek deneyim yoksa yazma |
| İçerik | Kaynaksız sayı ya da "araştırmalar gösteriyor ki" | Kaynaklı sayı ya da iddiayı çıkar |
| Biçim | Satır başında emoji, her başlıkta simge | Sade başlık |

## Fikir kaynakları
- blader/humanizer (MIT, depo sayfasına göre): kalıpları gruplama, önce işaretleme sonra yeniden yazma, eksik olguyu sorma.
- conorbronsdon/avoid-ai-writing ve jooray/humanizer (MIT, depo sayfalarına göre): yalnızca işaretleyen tespit modu, genel olasılık puanı vermeme.
- ghanemzadeh/claude-skills `line-and-copy-editor` (MIT, depo sayfasına göre): düzeltme sırası, kalıbı yalnızca birikince işaretleme.
- Kullanıcının reddettiği metin kalıpları vault'ta tutulur (`fikirler/reddedilen-oneriler.md`); bu dosyaya kişisel örnek yazılmaz (#44).

Hepsi 6 Kasım 2026'da web'den okundu; kod ve metin kopyalanmadı, LICENSE dosyaları açılmadı. Tespit atlatma amaçlı araçlar alınmadı.
