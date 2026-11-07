---
name: yorum-yontemi
description: Bir işi başta ve sonda dengeli bir gözle değerlendirmenin yöntemi: yön ve kapsam doğru mu, eksik, yanlış ya da olmaması gereken ne var, sonunda hedefe ulaşıldı mı. Yorumcu ajanına önceden yüklenir; ana sohbet "bunu yorumla", "doğru yolda mıyız", "bitti mi, eksik ne" sorulduğunda da yükleyebilir.
---

Yöntem becerisi (ajan değil). Bağlı kurallar: #23, #24, #26.

## Başta
1. **Asıl istek:** Kullanıcının sözünü tek cümleyle yeniden yaz. Görev kartı bununla örtüşüyor mu?
2. **Yön:** Bu yol isteği karşılıyor mu? Önce yapılması gereken bir şey var mı?
3. **Kapsam:** Fazlası (istenmeyen iş, #23) ya da eksiği var mı?
4. **Kurallar ve önceki kararlar:** Projenin kuralları ve ADR'leriyle çelişki var mı (#26)?
5. Gözlemlere dört bakış açısından bak: **şüpheci** (bu bulgu gerçekten doğru mu), **kurucu** (somut düzeltme ne), **bütünlük** (dosyalar ve adımlar arası uyumsuzluk), **son kullanıcı** (bunu kullanan kişi ne yaşar).

## Tur 2
- Hater'ın raporunu oku. Haklı olduğu yeri kabul et; abarttığı yeri gerekçeyle söyle.
- İki kaygıyı da karşılayan bir yol öner. Anlaşmazlık kalırsa iki tarafın en güçlü argümanını yaz, kararı merkeze bırak.

## Kapanışta
- Her kabul ölçütü için: karşılandı / karşılanmadı ve kanıt.
- Kalan bulguları önem sırasına koy: **bozar** (somut olarak ne, kimin için kırılır), **maliyet getirir** (zaman, para, kullanım hakkı), **zamanla çürütür** (bakım, tutarlılık).
- Karar önerisi: hazır / düzeltmeyle hazır (hangi düzeltme) / hazır değil.
- Sıradaki tek adım.

## İlkeler
- Az ama doğru bulgu: her madde kanıtlı; doldurmak için bulgu üretme. Bulgu yoksa "bulgu yok" de.
- İyi gideni de yaz; yalnızca eleştiri dengeli yorum değildir.
- Karar vermezsin, öneri yazarsın.

## Bitirmeden doğrula
- [ ] Asıl istek cümlesi yazıldı ve görevle karşılaştırıldı.
- [ ] Her bulgunun kanıtı ve önerisi var.
- [ ] Kapanışta kabul ölçütleri tek tek işaretlendi.

## Fikir kaynakları
- VoltAgent/awesome-claude-code-subagents `surgeon-reviewer` (MIT, depo sayfasına göre): üç önem derecesi, "somut ne bozulur" kapı sorusu, üç seçenekli karar, az ama doğru bulgu.
- VoltAgent/awesome-claude-code-subagents `ponder-auditor` (MIT): dört bakış açısı (şüpheci, kurucu, bütünlük, son kullanıcı). Tur sınırı olmaması alınmadı.
- Başta ve sonda iki uçlu değerlendirme yapısı: açık kaynakta bulunamadı, bizim tasarımımız.
6 Kasım 2026'da web'den okundu; metin ve kod kopyalanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
