---
name: uzman-dil
description: Türkçe ve İngilizce yazım, noktalama ve bağlam denetimi ile metinden yapay zekâ izini ayıklama uzmanlık paketi. Arayüz metni, hata mesajı, README, belge, rapor, hikâye, gönderi ya da e-posta taslağı yazılırken veya incelenirken; kullanıcı "imla", "yazım", "dil bilgisi", "TDK", "proofread", "AI gibi duruyor" dediğinde yükle. Dil Kurumu ajanına önceden yüklenir; ana sohbet ve yazar da yükleyebilir.
---

Uzmanlık paketi (ajan değil). Bağlı kurallar: #1, #8, #24. Ayrıntılı kural listesi: `references/tdk.md` (Türkçe), `references/yapay-zeka-izi.md` (iz kalıpları).

## Sıra
1. **Yazım ve noktalama** (kesin kurallar). Türkçe için `references/tdk.md`, İngilizce için genel dil bilgisi.
2. **Bağlam:** Cümle bir insanın kuracağı gibi mi? Özne ve yüklem uyumu, gereksiz tekrar, eksik bağ, yanlış terim.
3. **Yapay zekâ izi:** `references/yapay-zeka-izi.md` listesine karşı tek tek bak.
4. **Ses:** Metin bir kişinin ağzındansa onun sesini koru; daha "güzel" ama başka birinin cümlesini önerme.

## En sık Türkçe hatalar (ayrıntı `references/tdk.md`)
- Bağlaç "de/da" ve "ki" ayrı, ek "-de/-da" bitişik yazılır; soru eki "mi" ayrı yazılır, sonraki ekler ona bitişir.
- Özel ada gelen ek kesmeyle ayrılır; bağlaç "de" kesmeyle bitişmez.
- Binlik ayırıcı nokta, ondalık virgül; yüzde işaretinden sonra boşluk yok ("%25").
- Birleşik kelimeler: anlam kayması ya da ses düşmesi varsa bitişik, yoksa ayrı.

## İngilizce
- Özne-yüklem uyumu, zaman tutarlılığı, artikel (a/an/the), virgülle birleştirilmiş cümle (comma splice).
- Türkçe metinde İngilizce terim ilk geçtiğinde parantez içinde Türkçesi (#1, #8); kod, komut ve hata mesajı çevrilmez.

## Çıktı
Düzeltme tablosu: yer, yanlış, doğru, kural, kesin ya da öneri. Emin olmadığın düzeltme "öneri"dir. Anlamı değiştirme.

## Bitirmeden doğrula
- [ ] Her kesin düzeltmenin dayandığı kural yazılı.
- [ ] Kişinin sesi korundu; anlam değişmedi.
- [ ] Kod, komut ve dosya adına dokunulmadı.

## Fikir kaynakları
- Türk Dil Kurumu yazım kuralları sayfaları (tdk.gov.tr, 6 Kasım 2026'da okundu; adresler `references/tdk.md` içinde).
- Vault içi: `uzman-icerik` becerisinin yapay zekâ izi listesi.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
