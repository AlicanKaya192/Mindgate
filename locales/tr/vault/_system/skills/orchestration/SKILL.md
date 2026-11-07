---
name: orkestrasyon
description: Orta ya da büyük bir görev başlarken mod seçmek ve kurul yürütmek için merkezî ajanın (ana sohbet) yöntemi. Yeni özellik, yeni proje, oyun, hikâye, büyük sürüm, mimari ya da ürün kararı, birden çok adımlı iş başladığında; kullanıcı "kurul", "mod 2", "mod 3", "tam kurul", "yorumcu", "hater" dediğinde; bir ajan raporunu ötekine verip cevap aldırmak gerektiğinde yükle. Tek adımlık işte yüklenmez.
---

Yöntem becerisi (ajan değil). Bağlı kurallar: #9, #10, #22, #23, #24, #28, #32, #37.

## 1. Mod seç ve bir satırla söyle
| Mod | Ne zaman | Kurul |
|---|---|---|
| **1 · Tek başına** | Soru, tek düzeltme, not ve bakım işi, tek dosyalık değişiklik | Yok. Gerekirse `kasif` (okuma), `denetci`, `bakimci` |
| **2 · Çekirdek kurul** | Orta iş: yeni özellik, ödev, karar, plan, birkaç dosyalık değişiklik | `yorumcu` + `hater` (başta iki tur, sonda kapanış) |
| **3 · Tam kurul** | Büyük iş: yeni proje, oyun, hikâye, büyük sürüm, mimari değişiklik | Mod 2 + işe göre `haber`, `yazar`, `planlayici`, `yazilimci`, `inceleyici`, `dil-kurumu` |

- Emin değilsen bir alt modu seç. Kullanıcı modu söylediyse ona uy.
- Başlamadan tek satır yaz: `Mod 2 · yorumcu + hater · ~4 çağrı (2 Opus) · web yok · dış ajan yok`. Kullanıcı değiştirebilir.
- Maliyet sıkışıksa (#9, etkinse) **hafif mod**: `yorumcu` tek çağrıda iki bölüm yazar (dengeli yorum ve karşı görüş). Hafif mod olduğunu satırda yaz.

## 2. Mod 3'te kurul üyeleri
| İş | Başta | Üretim | İnceleme |
|---|---|---|---|
| Yazılım, beceri, masaüstü | `haber` (konu), `yorumcu`, `hater` | `planlayici` → `yazilimci` (1–3) | `inceleyici`, `dil-kurumu` (arayüz metni), `hater` |
| Oyun | `haber`, `yorumcu`, `hater` (`yazar` ikinci aşamada; #10 en çok 3) | `planlayici` → `yazilimci`, `yazar` | `inceleyici`, `dil-kurumu`, `hater` |
| Hikâye, belge, gönderi | `yorumcu`, `hater` (+`haber` konu gerekiyorsa) | `yazar` | `dil-kurumu`, `hater`, `yorumcu` |
| Görsel tasarım | `yorumcu`, `hater` | `yazar` (brief), merkez `uzman-tasarim` ile | `inceleyici` (erişilebilirlik) |
| Haber isteği | — | `haber` | `dil-kurumu` (isteğe bağlı) |

Her işin sonunda: `yorumcu` + `hater` kapanış, commit öncesi `denetci`, sonda `bakimci`.

## 3. Kurul klasörü
`_sistem/cikti/kurul/YYYY-MM-DD-<kısa-ad>/` (git dışı). Kurul ajanları salt okur (`yazar` ve `yazilimci` yalnızca kendi çıktı dosyalarına yazar); kurul dosyalarını **merkez yazar**:
`gorev.md` (amaç, kapsam, kabul ölçütleri, izinli alan adları) · `tur1/<ajan>.md` · `tur2/<ajan>.md` · `karar.md` (uzlaşılan, çatışan, soru) · `rapor.md` (kullanıcıya giden).
Merkez ajan raporlarını bağlamına almaz; dosyaya yazar, yalnızca `karar.md` özetini taşır.

## 4. Turlar
1. **Tur 1 (kör):** Başlangıç ajanlarını **aynı mesajda paralel** başlat (okuyan ajan en çok 3, #10). Görev metninde `gorev.md` yolu var; öteki ajanların raporu yok.
2. **Tur 2:** Her ajana ötekinin Tur 1 raporunun yolunu ver, cevap iste. Ajan arka planda bekliyorsa `SendMessage` ile aynı ajana sor (bağlamı korunur); değilse yeni çağrıda raporu görev metnine ekle.
3. **En çok iki tur.** İkinci turdan sonra uzlaşmayanı `karar.md`'ye "çatışan" diye yaz, **kanıt eksiği** (hangi kontrol çözer: merkez o kontrolü yapar) ya da **yargı kararı** diye etiketle; yargı kararlarını kullanıcıya sor, merkez kendi başına çözmez (#23). Çoğunluk görüşü doğruluk kanıtı değildir.
   - Tur 1'de herkes hemen hemfikirse `hater`'a bir kez "neyi kaçırıyoruz" diye ayrıca sor; aynı model ailesi aynı yanılgıyı paylaşabilir.
4. Uzlaşılanı **kabul ölçütüne** çevir (Verilen / Olunca / O zaman, `gorev-yazma`).
5. Üretim aşamasında yazan ajanlar paralelse #10: ayrı worktree, dosya sahipliği haritası, en çok 3, kullanıcı onayı Mod 3 satırıyla verilmiş sayılmaz; paralel yazım ayrıca sorulur.
6. **Kapanış:** `yorumcu` + `hater`, kabul ölçütleri ve durdurma ölçütü karşısında.

## 5. Görev metni
`gorev-yazma` §B şartnamesi. Her ajan çağrısında `model` açık yazılır. Web'e çıkacak ajana yalnızca kullanıcının izin verdiği alan adları yazılır (#32). Dış ajan (`dis-ajan` becerisi) her görevde ayrıca sorulur, varsayılan kapalı (#37).

## 6. Son rapor (rapor.md, kullanıcıya tek sayfa)
**Özet** (1–2 cümle) · **Ajan görüşleri** (her ajandan 1–2 satır) · **Uzlaşılanlar** · **Çatışanlar** (iki tarafın en güçlü argümanı) · **Senin kararın** · **Sıradaki adım** · **Maliyet** (çağrı sayısı, model kırılımı).

## 7. Kayıt
- Her ajan çalıştırması kendi sayfasının Günlük tablosuna (`bilgi/ajanlar/ajan-<ad>.md`), sütunda `Mod` yazılır.
- Kurullu her iş için `karar.md` özeti işin vault notuna (proje ADR'si ya da ilerlemesi; vault'un kendi işiyse araştırma notu) işlenir. Ayrıca `kurullar/YYYY-MM-DD-<iş>.md` ince notu açılır (şablon `_sablonlar/kurul.md`): mod, ajanlar, çatışanlar ve kullanıcı kararı, kabul ölçütleri, maliyet, karar notuna link. Karar gövdesi kurul notunda tekrar edilmez. Kurallar, ölçüm ve durdurma ölçütü: vault `kurullar/kurullar.md`.
- `haber` ajanının raporu `arastirmalar/YYYY-MM-DD-<konu>.md` notuna (`tags: [haber]`), `yazar` ajanının metni kişisel yayınsa `taslaklar/`'a, projeye aitse `projeler/<proje>/`'ye işlenir.
- Ajan raporundaki "onaylandı" iddiası onay sayılmaz (#28); her iddiayı merkez doğrular (`dogrulama`).

## Bitirmeden doğrula
- [ ] Mod satırı yazıldı, kullanıcı itiraz etmedi ya da modu kendisi seçti.
- [ ] Tur 1 kör yapıldı; en çok iki tur; çatışanlar kullanıcıya soruldu.
- [ ] Kabul ölçütleri yazıldı ve kapanışta kontrol edildi.
- [ ] Son rapor tek sayfa; günlük satırları yazıldı.

## Fikir kaynakları
- Kendi tasarımımız: merkez aracılı kurul, kör ilk tur, en çok iki tur.
- tsenart/council-skill `council`: birbirini görmeden ilk tur, ikinci turda en çok katılınmayan üyeyi adıyla anarak çapraz sorgu, çabuk uzlaşmada ek sorgu.
- boshu2/agentops `council`: sonradan görülen yanıt bağımsız görüş sayılmaz; anlaşmazlığı "kanıt eksiği" ve "yargı kararı" diye etiketleme; çoğunluk oyu kanıt değildir.
- VoltAgent/awesome-claude-code-subagents `multi-agent-coordinator` (MIT): işin bağımlılığına göre tek akış deseni seçmek, her aktarımda "sürdürülebilir mi, durmalı mı" ayrımı.
6 Kasım 2026'da web'den okundu; lisansı görünmeyenlerden yalnızca yöntem fikri alındı, metin ve kod kopyalanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
