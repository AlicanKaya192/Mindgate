# Oyun yapay zekâsı, davranış ağacı ve utility, prosedürel üretim

Sayılar kaynak paketin sahibinin beyanıdır, bağımsız doğrulanmadı. Her eşik başlangıç noktasıdır: ölç, oynat, ayarla.

## Oyun yapay zekâsı
**Kapsam:** Düşman ve NPC'nin algısı, kararı, yol bulması ve hareketi.

**Yöntem**
- Beş katmanı ayrı tut: algıla, karar ver, yol bul, yönlen (steering), canlandır. Animasyon karar vermez, karar katmanı çizim yapmaz.
- Karar yapısını sadeden karmaşığa seç:
  - Sonlu durum makinesi (FSM): 2–6 durum yetiyorsa bu.
  - Davranış ağacı (BT): durumlar çoğalıp geçişler karışınca.
  - Utility: birkaç seçenek arasında puanla seçmek gerekince.
  - GOAP (hedefe yönelik eylem planlama): son çare.
- Algıyı her karede değil 5–10 Hz'de çalıştır. Ajanların tiklerini kaydır; hepsi aynı karede düşünmesin.
- Histerezis: kovalamaya 10 birim mesafede başla, 14'te bırak. Bir durumda en az 0,3–0,5 s kal. Tepki gecikmesi 0,2–0,5 s olsun; anında tepki insan dışı görünür.
- 2 s boyunca hedefe yaklaşma yoksa yolu yeniden iste.
- Sekiz yönlü ızgarada oktil sezgiselini (octile heuristic) kullan.
- Görünür niyet: saldırıdan önce uyarı (telegraph) ver; oyuncu tepki verebilsin.

**Tuzaklar**
- Histerezis yoksa düşman sınırda girip çıkar, titrer.
- Yanlış yazılmış durum ya da anahtar adı çoğu motorda hata vermez, sessizce çalışmaz.

**Doğrulama**
- Sezgisel 0 iken A*, Dijkstra ile aynı yol maliyetini vermeli. 50 farklı ızgarada karşılaştır.
- Durum geçişlerini say: saniyede 2'den fazla geçiş histerezisin eksik olduğunu gösterir.

## Davranış ağacı ve utility
**Kapsam:** BT ve utility ile karar yapısı kurma.

**Yöntem**
- Dışta BT yapıyı kurar (devriye, savaş, kaçış), içte utility seçimi yapar (hangi saldırı, hangi hedef).
- Önce Blackboard'u tanımla: anahtar adları ve tipleri. Düğümler birbirine değil Blackboard'a yazar ve oradan okur.
- Tepkisel (reactive) Sequence kullan: koşul her tikte yeniden denetlenir.
- Utility:
  - Her ölçüt 0..1 aralığına bir eğriyle çevrilir.
  - Ölçütler çarpılır; biri 0 ise eylem elenir (veto).
  - Seçili eyleme 0,05 atalet payı ekle; puanlar yakınken seçim her tikte değişmesin.
- Karar tiki 5–15 Hz yeterlidir.

**Tuzaklar**
- Hafızalı (memory) Sequence koşul bozulsa da ortadaki düğümden sürer: düşman görüşten çıkan oyuncuyu sonsuza dek kovalar.
- Zamanlı düğüm (bekleme, bekleme süresi) kesildiğinde sıfırlanmazsa (Reset) sonraki girişte eski sayaçla devam eder.
- Tick içinde bellek ayırmak (yeni liste, yeni nesne) çok ajanla kare hızını düşürür.

**Doğrulama**
- Her dal için koşulu bilerek değiştir ve ağacın doğru dala geçtiğini testle gör.
- Motor özelinde: Unreal'da `Observer Aborts` ayarı (`motor-unreal.md`).

## Prosedürel üretim
**Kapsam:** Tohumdan harita, oda, ganimet ve düşman yerleşimi üretme.

**Yöntem**
- Tek ana tohum; her amaç için ondan türetilen alt tohum (harita, düşman, ganimet ayrı).
- Kendi sözde rastgele üreticini (PRNG) taşı (ör. SplitMix64); aynı tohum her ortamda aynı sonucu versin.
- Önce düz veri üret (ızgara, oda listesi), sahneyi sonra bu veriden kur.
- Her sonucu doğrula, geçmeyeni reddet:
  - Taşkın dolgusuyla (flood fill) her oda bağlı mı.
  - Doğuş noktası güvenli mi.
  - Anahtar, kapısından önce ulaşılabilir mi.

**Eşikler**
- En az 200 tohumda 0 hata. Roguelike için 500+ tohum (`turler.md`).

**Tuzaklar**
- Perlin gürültüsü tamsayı koordinatlarda 0 verir; girdiyi ölçekle ya da kaydır.
- Dalga fonksiyonu çöküşü (WFC) kuralları simetrik değilse (A, B'nin yanına girebiliyor ama B, A'nın yanına giremiyorsa) çelişki çıkar.
- Üretim ve savaş aynı rastgele akışı paylaşırsa oyuncunun hamlesi sonraki haritayı değiştirir.
- Python'da `hash()` süreç başına rastgeledir; tohum türetmede kullanma.

**Doğrulama**
- Aynı tohum iki kez üretilir, çıktının hash'i aynı olmalı.
- 200+ tohum ekransız üretilir, her biri doğrulayıcılardan geçer; tek hata bile başarısızlıktır.
