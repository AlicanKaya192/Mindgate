# Kurgu karar listesi ve Shorts

## Kurgu karar listesi (edit decision list)
`dead_air.py`, zaman damgalı bir döküm (transkript) dosyasını okur ve kesilecek yerleri yazar: ölü boşluk (dead air), dolgu ve tekrar. Videoya dokunmaz; kesimleri kullanıcı kendi kurgu programında yapar.

```bash
py -3 -I scripts/dead_air.py kayit.srt --floor 0.6
```

Döküm yoksa kullanıcıdan iste. YouTube'a liste dışı (unlisted) yüklenen videonun otomatik altyazısı Studio'dan indirilebilir; Studio'daki Türkçe etiketin adı doğrulanmadı. Zamanları tahmin etme.

| Tür | Ne | Not |
|---|---|---|
| BOŞLUK | `--floor` saniyeden uzun sessizlik | Ortasından kesilir, iki yanda 0,15 sn nefes kalır; tam konuşma kenarından kesmek nefessiz bir ses verir |
| DOLGU | Yalnızca dolgu kelimesinden oluşan satır ("eee", "yani", "ııı") | "Yani bu yöntem işe yarıyor" gibi cümle kesilmez |
| TEKRAR | Yeniden başlanan cümle | Önceki konuşma satırı sonrakinin başıyla aynıysa ve aralarında duraklama varsa ilk deneme kesilir; aradaki "eee" sayılmaz. Uç uca eklenen kayan altyazı satırları tekrar sayılmaz |

**İki aşamada kes, her kesimi kayda geçir:**
1. Önce yalnızca BOŞLUK satırları. Bunlar ölçüme dayanır; toplu onaylanabilir.
2. Sonra DOLGU ve TEKRAR adayları. Betiğin önerisi adaydır, karar değil: her birini önceki ve sonraki cümleyle birlikte oku, anlamı bozuyorsa kesme.
3. Kullanıcıya verdiğin listede her kesim başlangıç, bitiş ve neden taşır ("12:04–12:09, tekrar: cümle yeniden başlıyor"). Kesmemeye karar verdiğin adayları da nedeniyle yaz; liste, kurgunun neden böyle olduğunu sonradan açıklayan kayıttır.
4. Ham kayıt değişmez; kullanıcıya kesilmiş dosyayı yeni adla kaydetmesini söyle.
5. **Ucuz kesim denetimi:** Seslendirme satırlara bölündüyse her satırın saniyedeki harf sayısını hesapla. Ortancadan %35'ten fazla sapan satır büyük olasılıkla yanlış yerden kesilmiş ya da bir kelimesi yutulmuştur; yalnızca bu satırları kullanıcıya dinlet.

**Dikkat:** Kısalma yüzdesi yalnızca konuşma süresinden hesaplanır. Videoda uzun bir sessiz gösterim varsa gerçek süre farklıdır. Sonucu görüntüyle karşılaştırmadan süreye güvenme.

**Bilinen sınırlar:** Otomatik altyazıların "eee" ve "ııı" seslerini yazıp yazmadığı doğrulanmadı; yazmıyorsa dolgu yalnızca boşluk olarak görünür. YouTube'un kendi VTT dosyalarının gerçek biçimi de doğrulanmadı. UTF-16 kaydedilmiş dosya (Not Defteri'nde "Unicode") okunmaz; araç bunu söyler, UTF-8 olarak kaydet.

## Shorts
Uzun videodan çıkan bir Short, en iyi anın kesiti değildir. **Videonun geri kalanı olmadan da anlaşılan** bir andır; bu çok daha küçük bir kümedir.

Dökümde 20–55 saniyelik kesitler ara. Üç koşul birlikte sağlanmalı:
1. Tam bir düşünceyle açılır; ilk cümle önceki dakikaya muhtaç değildir.
2. İçinde bir dönüm noktası vardır: bir iddia ve onu zorlayan ya da kanıtlayan şey.
3. Yarım kalmadan, bir cümleyle biter.

Adayları sırala; ilk beşini zaman damgası ve ilk cümlesiyle göster ki kullanıcı dökümü okumadan eleyebilsin. Her biri için şunları yaz:
- **Yeni bir ilk satır:** Uzun videodaki cümle bağlam ister. Yenisini yaz ve `hook_check.py`'den geçir.
- **İlk 2 saniyenin ekran metni:** Söylenen cümleden farklı kelimelerle.
- **Döngü noktası:** Son cümleyi, video başa sarınca ilk cümleye bağlanacak biçimde kur.
- **Dikey kadraj notu:** 16:9 görüntüden ne kesilir ve önemli mi?
