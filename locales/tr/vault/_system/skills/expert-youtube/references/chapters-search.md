# Bölümler ve arama metni

## Bölümler (chapters)
YouTube kuralları (`esikler.md`, resmî): ilk zaman damgası 00:00, en az 3 zaman damgası artan sırada, her bölüm en az 10 saniye. Biri bozulursa liste açıklamada durur ama bölüm olarak görünmez.

```bash
py -3 -I scripts/chapters.py kayit.srt --target 6          # öneri
py -3 -I scripts/chapters.py --check liste.txt --duration 612
```

- Araç bölüm sınırlarını, dökümdeki duraklamalara ve iki yandaki kelimelerin ne kadar değiştiğine bakarak bulur.
- Önerdiği başlıklar konu kelimeleridir, yani taslaktır. Her birini o bölümün vaadi olarak, kullanıcının sesiyle, 3–5 kelimeyle yeniden yaz.
- `--check`, kullanıcının yazdığı listeyi denetler. Zaman damgası olmayan satırlar (açıklamanın geri kalanı) atlanır ve listelenir; listeyi geçersiz yapmaz. `--duration` verilirse son bölümün uzunluğu da kontrol edilir.
- Bölümler izlenme tutma için de bir denetimdir: beş kelimeyle adlandırılamayan bir bölüm ya iki bölümdür ya da gereksizdir.

## Arama: açıklama ve etiketler
Arama, abone akışına giden bir video için küçük bir etkendir. Uzun süre aranan konularda daha önemlidir. Video abone akışı içinse bunu söyle ve emeği başlık ile küçük resme ver (`paket.md`).

**Açıklama** (en çok 5.000 karakter, resmî):
1. İlk iki satır: "Daha fazla" bağlantısının üstünde görünen tek kısım; arama sonuçlarında da çoğu zaman bu kısım görünür (gözlem). Videonun ne verdiğini, kişinin arayacağı kelimelerle söyle.
2. Bağlantı ya da kaynak varsa hemen ardından, katlanmadan önce.
3. Bölümler.
4. Uzun hâli: ne anlatılıyor, kimin için, neyi bildiği varsayılıyor.

**Etiketler:** YouTube'a göre keşifte çok küçük bir rol oynar ve asıl olarak sık yanlış yazılan kelimelerde işe yarar (resmî). Yazım varyantları, araç adları ve kısaltmalar için kullan; konuyla ilgisiz etiket ekleme.

**Sorgu testi:** Teslimden önce bu videonun kazanması gereken üç arama sorgusunu yaz. Başlıkta ve açıklamanın ilk iki satırında bu sorguların kelimeleri geçiyor mu, bak. Geçmiyorsa sorun açıklamada değil başlıktadır.
