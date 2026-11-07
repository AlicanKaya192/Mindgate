---
name: degerlendirme-yontemi
description: Bir LLM ya da ajan çıktısını, bir prompt veya beceri değişikliğini, iki seçeneği (A/B) ya da bir ML modelinin sonucunu puanlarken ve karşılaştırırken kullan. Ajan takımı kararları, beceri testi ve ML projelerindeki değerlendirme dahil. Değerlendirici ajanına önceden yüklenir; ana sohbet yükler, inceleyici yükleyebilir.
---

Yöntem becerisi (ajan değil). ML metrikleri için `uzman-ml` ile birlikte kullanılır.

## 1. Önce makine kontrolü
Bir komutla karar verilebilen her şeyi önce komutla kontrol et: testler geçiyor mu, şema geçerli mi, dosya var mı, sayı tutuyor mu. Yargıca (insan ya da model) yalnızca komutun karar veremediği kısım kalsın.

## 2. Yöntem seç
- **Doğru cevap varsa** (olgusal doğruluk, talimata uyma, biçim): **doğrudan puan.** Ölçütler, her ölçütün ağırlığı ve her puan düzeyinin tanımı (1–5 en dengelisi) yazılır.
- **Zevk ya da tercih işiyse** (üslup, okunabilirlik, tasarım): **ikili karşılaştırma (A/B).**

## 3. Önyargıları azalt
| Önyargı | Ne olur | Önlem |
|---|---|---|
| Sıra | İlk sıradaki seçenek kayırılır | Karşılaştırmayı iki kez yap, sırayı değiştir. Sonuçlar çelişirse "berabere", güven düşük |
| Uzunluk ve ayrıntı | Uzun cevap daha iyi sanılır | "Uzunluğu ödüllendirme" de; gereksiz ayrıntı ölçütte cezalandırılsın |
| Kendini kayırma | Model kendi çıktısını beğenir | Üreten ve değerlendiren farklı olsun (ör. inceleyici taze bağlamla) |
| Otorite | Kendinden emin ton doğru sanılır | Her puandan **önce** kanıt (alıntı, dosya:satır, komut çıktısı) iste |
| Uzlaşma | Ajanların hemfikir olması kanıt sanılır | Aynı model aynı yanılgıyı paylaşabilir; en az bir kontrol döngü dışında olsun |

## 4. Rubrik (puanlama cetveli)
- Her puan düzeyinin sınırı ve gözlenebilir özellikleri yazılır, belirsiz durumlar için not düşülür.
- Katılık bilinçli seçilir: deneme için hoşgörülü, sürüm ve güvenlik için katı.
- Puan dağılımı tek tip bir rubrik değil, konuya özgü terimlerle yazılır (kod için isimler ve fonksiyonlar, ML için metrik ve veri bölmesi).

## 5. Metrik seçimi
| Görev | Ana metrik |
|---|---|
| Geçti/kaldı | Kesinlik (precision), duyarlılık (recall), F1 |
| Sıralı puan (1–5) | Spearman ya da Kendall sıra korelasyonu |
| A/B tercihi | Uyuşma oranı, sıra tutarlılığı |
| İki değerlendirici uyumu | Cohen's kappa |

Rastgele hata yerine **sistematik** anlaşmazlığa bak: belli bir ölçütte hep ters düşen yargıç daha tehlikelidir.

## 6. Beceri ya da prompt değişikliğini ölçme
1. Gerçekçi 2–3 görev seç (kullanıcının gerçekten verdiği türden).
2. Her görevi **beceriyle** ve **becerisiz** (ya da eski sürümle) çalıştır.
3. Sonuçları kaynağı gizleyerek karşılaştır (kör A/B; sıra değiştir).
4. Beklentileri kanıtla geç/kal diye işaretle. Zayıf beklentiyi de eleştir: hep geçen beklenti hiçbir şey ölçmez.
5. Tek çalıştırmaya güvenme; aynı prompt farklı sonuç verebilir.

Bu bir ölçüm işidir: kullanım hakkı götürür. Büyük denemeden önce kullanıcıya sor.

## Rapor
| Ölçüt | Puan ya da kazanan | Kanıt | Güven |
|---|---|---|---|

Sonuna "makine kontrolleri" ve "değerlendirilemeyenler ve nedeni" bölümleri eklenir.

## Fikir kaynakları
- muratcankoylan/Agent-Skills-for-Context-Engineering `advanced-evaluation` ve `evaluation` (MIT).
- anthropics/skills `skill-creator` (Apache-2.0): beceriyle ve becerisiz karşılaştırma, kör karşılaştırıcı ve not veren ajan fikri.

Hepsi indirilen kopyalardan okundu; resmî depolarla eşleşmeleri doğrulanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
