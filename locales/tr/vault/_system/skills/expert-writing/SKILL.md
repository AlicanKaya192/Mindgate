---
name: uzman-yazarlik
description: Metin üretimi uzmanlık paketi. Oyun anlatısı, dünya ve karakter, diyalog, hikâye, arayüz metni (düğme, hata mesajı, boş ekran, onay penceresi), teknik belge ve kılavuz, sunum metni ya da görsel tasarım brief'i yazarken yükle. Yazar ajanına önceden yüklenir; ana sohbet de yükleyebilir. Blog, LinkedIn ve README gibi kişisel gönderiler için önce `uzman-icerik`, yazım denetimi için `uzman-dil`.
---

Uzmanlık paketi (ajan değil). Bağlı kurallar: #14, #24, #44. Yapay zekâ izi listesi: `uzman-dil` → `references/yapay-zeka-izi.md`.

## Her metinden önce
1. **Okur kim, metni nerede görecek, ne yapmasını istiyoruz?** Tek cümleyle yaz.
2. **Ses profili:** Projenin ses ve ton notu varsa oku (hedef okur, ton, kullanılmayacak kelimeler, kendi örnekleri). Yoksa görev metnindeki tonu kullan; kişisel örnekleri vault dışına taşıma.
3. **Olgular:** İsim, sayı, tarih ve iddia yalnızca verilen kaynaklardan. Eksikse `[KANIT GEREK: …]`.

## Türe göre
**Arayüz metni (UX yazımı)**
- Düğme eylemi söyler ve fiille başlar ("Kaydet", "Dosyayı aç"); "Tamam" yerine eyleme özgü etiket.
- Hata mesajı ne olduğunu, nedenini ve ne yapılacağını söyler; özür dilemez, kullanıcıyı suçlamaz.
- Boş ekran ilk eyleme çağırır. Aynı eylem akış boyunca aynı adı taşır.
- Çıktı: öneri, bir iki alternatif, gerekçe, Türkçe ve İngilizce uzunluk farkı için not.

**Teknik belge, kılavuz, tasarım brief'i**
- Önce bağlamı topla (amaç, okur, kısıtlar), sonra bölüm bölüm yaz; düzeltmeyi bütün metni yeniden yazarak değil, hedefli yap.
- Bitince "bağlamı bilmeyen okur" testi: konuşmayı görmemiş biri yalnızca bu metinle işi yapabilir mi?
- Brief'te: amaç, okur, en önemli 1–3 görev, kısıtlar, referans, teslim biçimi.

**Oyun anlatısı, hikâye, karakter, diyalog**
- Önce dünyanın kuralı ve oyuncunun hedefi; anlatı mekaniğe hizmet eder, onu geciktirmez.
- Karakterin bir isteği ve onu engelleyen bir şey olsun; her karakterin konuşma biçimi ayırt edilebilir olsun.
- Diyalog kısa tutulur, bilgi göstererek verilir; oyuncunun seçimi varsa her seçeneğin sonucu farklı olur.
- Var olan bir oyunun, filmin ya da kitabın karakterini, dünyasını ve adlarını kopyalama; özgün yaz.

## Bitirmeden doğrula
- [ ] Okur ve amaç cümlesi metne uyuyor.
- [ ] Uydurma olgu yok; eksikler işaretli.
- [ ] Yapay zekâ izi listesine karşı bakıldı.
- [ ] Yalnızca verilen çıktı dosyasına yazıldı.

## Fikir kaynakları
- anthropics/knowledge-work-plugins `design/skills/ux-copy` (depo Apache-2.0): fiille başlayan düğme, üç parçalı hata mesajı, öneri ve gerekçe çıktısı.
- anthropics/skills `doc-coauthoring` (depo Apache-2.0): bağlam toplama, bölüm bölüm taslak, bağlamsız okur testi.
- alexconner-79/ill-communication (MIT, depo sayfasına göre): ses profili şablonu, ayrı mikro metin başvurusu.
- Oyun anlatısı bölümü: açık kaynak bir beceri bulunamadı (6 Kasım 2026 taraması); genel anlatı tasarımı bilgisiyle yazıldı, ölçülmedi.

Hepsi 6 Kasım 2026'da web'den okundu (özetler; tam metin ve LICENSE dosyaları açılmadı). Kod ve metin kopyalanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
