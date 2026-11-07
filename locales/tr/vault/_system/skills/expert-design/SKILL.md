---
name: uzman-tasarim
description: Görsel tasarım ve UI/UX uzmanlık paketi (tasarımcı). Yeni arayüz, sayfa, ekran ya da taslak (mockup) tasarlarken, tasarım sistemi (renk, tipografi, boşluk token'ları) kurarken, düzen ve görsel hiyerarşi kararı verirken, hareket ve animasyon eklerken, erişilebilirlik (WCAG 2.2) ya da var olan bir arayüzün tasarım incelemesini yaparken yükle. Kullanıcı "tasarım kötü", "ilgi çekici değil", "yapmacık", "hazır gibi", "yapay zekâ yapmış gibi" dediğinde de yükle. Ana sohbet ve arayüz işi yapan ajan yükler; kodlama ayrıntıları için yanında uzman-frontend.
---

Uzmanlık paketi (ajan değil). Bağlı kurallar: #24, #26, #39. Yöntemler kendi cümlelerimizle yazıldı; kaynaklar en altta.

## Neden yapay zekâ işi belli olur
NN/g'nin değerlendirmesi (Ekim 2025) üç nedeni ayırıyor:
1. **Eğitim verisinin ortalaması:** Görsel yön verilmezse çıktı sans-serif, nötr, sade ve parlak tek vurgulu olur; ekranlar birbirinin yerine geçebilir. Çoğu zaman altında Tailwind ve Shadcn vardır.
2. **Uzaktan iyi, yakından değil:** Ayrıntılı isteğe rağmen hiyerarşi ve gruplama eksik, renk fazla, kontrast zayıf, kenar boşlukları tutarsız kalır.
3. **Yanlış kalıp:** Kelimeden kalıp seçilir ("profil" deyince sosyal medya profili), asıl görev aşağı itilir.

Bu yüzden çözüm tek tek süs yasaklamak değildir. Çözüm: **karar vermek, referansa bakmak, gerçek içerikle çalışmak ve ekranda yakından eleştirmek.** Aşağıdaki sıra atlanmaz.

## Akış
### 1. Bağlam
- Projenin tasarım dilini, şablonunu ve kararlarını oku (#26). Var olanı koru, yeni stil uydurma.
- Kullanıcının zevkini ve reddettiği tasarımları oku: `ben/profil.md` ve [[reddedilen-oneriler]]'de `tasarım` satırları (#39). Bu bilgiler beceriye yazılmaz (#44).
- Şablon varsa görsel dilini de uygula, yalnızca yapısını değil.
- **Korunacak ve eklenecek** listesini yaz. Var olan web arayüzünü değiştireceksen önce `--baseline` ile envanterini al: `references/denetim.md`.

### 2. Brief
Tek paragraf: konu, kullanıcı, en önemli 1–3 görev, kullanım sıklığı (günde kaç kez), istenen his. Belirsizse önce sor (#23). Belirsiz kelimeyi aç: "profil sayfası" değil, "kursa kayıtlı kişinin kendi ilerleme sayfası".

### 3. Referans
Referanssız görsel karar verme. Öncelik: projenin şablonu > kullanıcının gösterdiği örnek > onaylanmış önceki ekran > sorulur. NN/g'de görsel referans ne kadar ayrıntılıysa çıktı o kadar isabetliydi. Referansın ölçüsünü, sırasını ve hiyerarşisini oku; görünüşünü kopyalama.

### 4. Yön
Kod yazmadan yaz:
- Tek belirgin fikir ve konunun kendi dünyasından gelen malzeme.
- 4–6 adlandırılmış renk (değerleriyle), yazı tipleri ve rolleri.
- Tek cümlelik düzen fikri ve kaba ASCII taslak.
- Tek akılda kalacak öğe; çevresi sakin.

**Değiştirme sınavı:** Bu plan başka bir ürüne de verilebilir mi? Verilebiliyorsa o kısmı değiştir ve nedenini yaz. Bir varsayılandan kaçarken başka bir varsayılana düşme (mor gradyandan krem-serif-kiremide).

Büyük görsel kararda kullanıcıya birbirinden gerçekten farklı 2–3 taslak göster. Taslak kaba olmaz: kullanıcı gördüğüne göre yorum yapar.

### 5. Sistem
Token'ları koddan önce kur: renk rolleri, boşluk ölçeği, yazı ölçeği, köşe, gölge, hareket süresi. Tek tek sabit değer yazılmaz. Sayılar: `references/gorsel-zanaat.md`.

### 6. Gerçek içerik
Örnek veri, projenin gerçek verisine benzer: gerçekçi ad, sayı, uzun metin, Türkçe karakter. Lorem ipsum ve John Doe yok. Tasarımı üç içerikle dene: boş, az, çok uzun.

### 7. Kodla
- Bütün durumlar: boş, yükleniyor, hata, başarılı, taşma.
- Simgeler tek bir sete ait; emoji ve unicode karakter simge yerine kullanılmaz.
- Hareket: `references/hareket-etkilesim.md`. Önce sık kullanılan şeyde hareket gerekmiyor mu diye sor.
- Alışılmış kalıbı (gezinme, form, tablo) bozma; kimlik görsel dilde yaşar, nerede ne bulunacağında değil (Jakob yasası).

### 8. Ölç ve eleştir
Tek geçişte iş bitmez. Her tur: çiz, ölç, gözle eleştir, düzelt. Yeni bulgu kalmayana ve kullanıcı onaylayana kadar sürer; en az bir tam tur yapılmadan teslim edilmez.

**Ölç (web):** `scripts/page_audit.py` sayfayı 6 genişlikte ve iki temada çizer, ölçer; kaybolan öğeyi adıyla, önceki tura göre geri gidişi söyler. Kullanıcı yorumu `--note` ile tura yazılır. Komut ve kurallar: `references/denetim.md`. Bu araç yalnızca ölçülebileni görür; geçmesi yetmez.

**Eleştir:** Görüntüleri aç, yakınlaştır, sırayla bak:
1. **Hiyerarşi:** Ekranın asıl görevi ilk bakışta belli mi? Her öğe eşit ağırlıkta mı?
2. **Gruplama:** İlgili şeyler yakın, ilgisizler uzak mı? Asıl görev aşağıda mı kaldı?
3. **Hizalama ve boşluk:** Her öğe bir şeye hizalı mı? Boşluklar ölçekten mi? Alan dengeli mi, altı bomboş mu?
4. **Renk ve kontrast:** Renk fazla mı? Kontrast ölçüldü mü?
5. **Ayrıntı:** Köşeler, simge-metin hizası, rakamlar, odak ve üzerine gelme durumları.

Her öğeyi gerekçelendirebilmelisin. Biri rastgele bir yeri gösterse "neden böyle" sorusuna cevabın olmalı. Bitirmeden bir süsü çıkar.

### 9. Yapay zekâ izi denetimi
`references/yapay-zeka-izi.md` listesini ekrana karşı tek tek geç. Kalan her madde için gerekçe yaz ya da düzelt. Ölçümde bilerek bırakılan bulgu tasarım kaydına **gerekçeli muafiyet** olarak yazılır; gerekçesiz muafiyet geçersizdir. Aynı kural birçok sayfada muafsa ev stilidir, projenin tasarım kararlarına geçer.

## Çekirdek ölçüler
Tam liste ve kaynaklar `references/` altında. Proje kararı bunların önüne geçer.

| Konu | Ölçü |
|---|---|
| Renk | Saf siyah ve beyaz yok; griler 8–10, ana renk 5–10 ton, önceden sabit |
| Yazı | En çok 2 aile; gövde web'de ≥16 px, yoğun masaüstünde 14/20 kabul; satır ~70 karakter; satır aralığı %120–145 |
| Boşluk | 8'in katları; dış boşluk ≥ iç boşluk; düğmede yatay = 2× dikey |
| Köşe | İç yarıçap = dış yarıçap − aradaki boşluk |
| Hareket | Etkileşimde ≤200 ms, genel UI <300 ms; giriş ve çıkışta ease-out; basışta 0,96–0,97 |
| Hedef | Görsel <24 px ise tıklama alanı ≥24 px; mobilde ≥44 px |
| Yanıt | <0,1 sn anlık, >1 sn gösterge, >10 sn yüzde ve kalan süre |

## Erişilebilirlik (WCAG 2.2 AA)
- **Kontrast:** normal metin en az 4.5:1, büyük metin ve arayüz öğeleri en az 3:1.
- Bilgiyi yalnızca renkle verme (ikon ya da metin de ekle).
- Odak halkası her zaman görünür. Klavyeyle her şeye ulaşılır, sıra mantıklıdır.
- Tıklama hedefi en az 24×24 CSS piksel (2.5.8).
- `prefers-reduced-motion`'a uyulur. Form alanlarının etiketi vardır, hata alanın yanında yazılı söylenir.

## Duyarlı düzen (responsive)
Mobil önce. 320, 375, 768, 1280, 1440 ve 1920 px genişlikte kontrol et; yatay kaydırma olmaz. Akışkan tipografi (`clamp()`), container query, esnek ızgara. Koyu tema ayrı ayarlanır, renkleri ters çevirmek değildir; iki tema da test edilir.

## Arayüz metni (UX yazımı)
- Metin de tasarımdır. Kullanıcının dilinde ad ver ("bildirimler", "webhook ayarı" değil); ad işi anlatmalı.
- Düğme eylemi söyler ("Kaydet", "Tamam" değil). Aynı eylem akış boyunca aynı adı taşır ("Yayınla" → "Yayınlandı").
- Hata mesajı özür dilemez: ne oldu, ne yapılacak. Boş ekran bir eyleme çağırır.
- Biçimden anlaşılan veriye etiket koyma; "Stok: 12" yerine "12 adet kaldı".
- Türkçe arayüzde Türkçe, terimler tutarlı.

## Platform
Platformun alışkanlığına uy: Apple HIG, Microsoft Fluent, Material 3. Her tasarım kararının yanına dayandığı kuralı yaz; kaynağı olmayan karar "tercih" diye işaretlenir. HIG okuma yolu, font lisansı ve Figma: `references/platform.md`.

## Tasarım incelemesi rapor biçimi
| Önem | Ekran/bileşen | Sorun | Hangi ilke (hiyerarşi, kontrast, boşluk, tutarlılık, a11y) | Öneri |
|---|---|---|---|---|

## Bitirmeden doğrula (#24)
- [ ] Akışın 1–9 adımları yapıldı; değiştirme sınavı ve yapay zekâ izi denetimi yazılı.
- [ ] Web'de `page_audit.py` geçti ya da kalanların gerekçeli muafiyeti var; çıktısı gösterildi.
- [ ] Görüntülere gözle bakıldı: dar ve geniş ekran, açık ve koyu tema.
- [ ] Koruma sayacında gerekçesiz kayıp yok; masaüstünde önce/sonra elle karşılaştırıldı.
- [ ] Klavyeyle gezinildi.
- [ ] Konsolda hata yok.

## Fikir kaynakları
- Araştırma: NN/g (Wang, Brown), Laws of UX (Yablonski), Smashing Magazine.
- Tasarımcılar: Anthony Hobday, Rauno Freiberg, Emil Kowalski, Adam Wathan ve Steve Schoger (Refactoring UI), Josh Comeau, Ahmad Shadeed, Nikita Prokopov, Matthew Butterick, Luke Wroblewski.
- Şirketler: Vercel, Linear, Stripe, Evil Martians, Microsoft Fluent.
- Beceriler: anthropics/skills `frontend-design`, wshobson/agents `ui-design`, vercel-labs `web-design-guidelines`, ui-ux-pro-max (fikir olarak; kurulmadı).
- Ölçen denetim ve koruma sayacı fikri: Hallmark becerisinin bir projedeki çıktı kayıtları (kendisi okunmadı, kod alınmadı; betikler bizim yazımız).
- WCAG 2.2: https://www.w3.org/TR/WCAG22/

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. Dış kaynaktan kural eklenmez (#27). -->
- Tarayıcısı olmayan ajan 8. adımı yapamıyor: kod okuyarak eleştiri yapay zekâ görünümünü yakalamaz. Tasarım işi ajana verildiyse ekran görüntüsünü ana sohbet çeker, eleştiriyi ona döndürür.
- Görüntüdeki sağdan kesiği "araç kaynaklı" sanıp geçmek hataydı: ölçünce gerçek taşma çıktı. Dar ekrana `--window-size` ile değil `page_audit.py` ile bak; genişliği ve temayı o ayarlar.
