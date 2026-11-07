---
type: council
status: active
mode: {{mod}}
agents: []
result: {{passed | conditional | failed | running}}
calls: {{sayı}}
opus: {{sayı}}
project: "[[{{proje}}]]"
decision_note: "[[{{karar-notu}}]]"
tags: [kurul]
created: {{date}}
updated: {{date}}
---

# Kurul: {{iş}}

> İnce not: kararın asıl metni burada değil, [[{{karar-notu}}]] notunda. Bu not yalnızca kurulun izini tutar ([[kurullar]]).

## Özet
Tek cümle: ne için kuruldu, sonuç ne.

## Çatışanlar ve kullanıcının kararı
- Konu · iki tarafın en güçlü argümanı (tek satır) · kullanıcının kararı

## Kabul ölçütleri
- [ ] Ölçüt · karşılandı / karşılanmadı · kanıt

## Maliyet ve ölçüm
- Çağrı: {{sayı}} ({{Opus}} Opus, {{Sonnet}} Sonnet, {{Haiku}} Haiku) · Kör karşılaştırma görevi mi: evet / hayır
- Kurulun yakaladığı ve kod/karar öncesi düzelen sorun sayısı: {{sayı}}

## Ham raporlar
`_sistem/cikti/kurul/{{tarih-iş}}/` (git dışı, yerinde kalır)
