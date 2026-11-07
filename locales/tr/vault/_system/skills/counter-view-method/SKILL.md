---
name: karsi-gorus-yontemi
description: Bir planı, kararı ya da teslim edilmiş işi bilerek karşı taraftan okumanın yöntemi: ön ölüm analizi (pre-mortem), en güçlü karşı argüman, durdurma ölçütü (kill criteria). Hater ajanına önceden yüklenir; ana sohbet "bunun neden batabileceğine bak", "şeytanın avukatlığını yap", "karşı görüş" istendiğinde de yükleyebilir.
---

Yöntem becerisi (ajan değil). Bağlı kurallar: #23, #24, #27.

## Tur 1 (kör)
1. **Tezi tek cümleyle yaz:** Bu iş neyi, kimin için, hangi ölçütle başaracak?
2. **Ön ölüm:** "Altı ay sonra bu iş başarısız oldu" diye varsay ve geriye doğru çalış. En olası 3–5 başarısızlık hikâyesi çıkar.
3. Her hikâyede **gizli varsayımı** (doğru sanıp kontrol etmediğimiz şey) ve 1–2 **gözlenebilir erken uyarı işaretini** yaz.
4. En güçlü uyarı işaretini **durdurma ölçütüne** çevir: ölçülebilir, tarihli ya da aşamaya bağlı ("200 MB dosya 3 saniyede açılmıyorsa mimari yeniden düşünülür").
5. **İtirazlar:** En çok 5. Her biri: kanıt, önem (yüksek / orta / düşük), önerilen cevap ya da önlem, "ne olursa vazgeçerim".
6. Kanıtsız şüpheyi itiraz diye yazma; "açık soru" diye ayrı listele.

## Tur 2
- Sana verilen raporları oku. En çok katılmadığın görüşü adıyla an ve neden katılmadığını kanıtla yaz.
- İkna olduğun itirazı geri çek ve bunu açıkça söyle. Amaç kazanmak değil, doğru kararı bulmak.
- Kalan her anlaşmazlığı etiketle: **kanıt eksiği** (hangi kontrol çözer) ya da **yargı kararı** (kullanıcı seçer).

## Kapanış
- Durdurma ölçütü karşılandı mı? Kanıtla evet ya da hayır.
- **Cevapsız kalan en güçlü itiraz:** tek cümle. Yoksa "yok" yaz.
- Karar önerisi: geçti / koşullu geçti (hangi koşul) / kaldı.

## Sınırlar
- Kapsam karar ve yön; satır satır kod incelemesi, güvenlik taraması ve vault savunma testi başka ajanların işi.
- Kullanıcının önceden verdiği kararı yeniden tartışma; çelişki görürsen bir satırla not düş.
- Sonsuz itiraz yok: en çok iki tur ve kapanış.

## Bitirmeden doğrula
- [ ] Her itirazın kanıtı ve vazgeçme koşulu var.
- [ ] Durdurma ölçütü ölçülebilir.
- [ ] Tur 2'de geri çekilen itirazlar açıkça yazıldı.

## Fikir kaynakları
- vishalsachdev/claude-skills `premortem` (depo MIT): geriye doğru başarısızlık hikâyesi, gizli varsayım, erken uyarı işareti. Erken uyarıyı durdurma ölçütüne çevirmek bizim eklememiz.
- AmrAnwar/objection (MIT): kapanışta cevapsız en güçlü itiraz, geçti/kaldı kararı. Sınırsız itiraz döngüsü alınmadı.
- mattpocock/skills `grilling` (MIT): soruları kararın açık uçlarından sormak, her soruya önerilen cevap eklemek. Sınırsız sorgu alınmadı.
- boshu2/agentops `council`: anlaşmazlığı "kanıt eksiği" ve "yargı kararı" diye ayırmak.
6 Kasım 2026'da web'den okundu; metin ve kod kopyalanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
