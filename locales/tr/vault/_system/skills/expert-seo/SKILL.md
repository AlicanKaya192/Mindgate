---
name: uzman-seo
description: Arama motoru optimizasyonu (SEO) uzmanlık paketi. Bir web sitesinin (özellikle kişisel portfolio sitesinin) SEO denetimini yaparken, sayfa başlığı ve açıklaması yazarken, yapılandırılmış veri (schema, JSON-LD) eklerken, site ve URL yapısı kurarken veya yapay zekâ aramalarında görünürlüğü düşünürken yükle. Arayüz kodu için yanında uzman-frontend.
---

Uzmanlık paketi (ajan değil). Projenin kendi kuralları önce gelir. Ölçmeden puan verme (#24): ölçülemeyen madde "ölçülmedi" diye yazılır.

## Önce
- Sitenin nasıl üretildiğine bak: statik, sunucuda üretilen (SSR) ya da yalnızca tarayıcıda çalışan React (CSR). **Kritik içerik ham HTML'de yoksa** arama motorları ve yapay zekâ tarayıcıları onu göremeyebilir. Bu, portfolio sitesinde en önemli maddedir.
- Canlı siteye girmek bir site ziyaretidir: adres, neden ve link doğrulamasını yazıp izin al (#32, #33). Yerel derlemeyi açmak da izin ister.
- Dış SEO araçları (ücretli tarayıcılar, API anahtarı isteyen servisler) kullanılmaz; gerekirse kullanıcıya sorulur (#23).

## Teknik SEO kontrol listesi
- [ ] **robots.txt:** Önemli sayfaları yanlışlıkla engellemiyor; sitemap adresini gösteriyor.
- [ ] **XML sitemap:** Yalnızca kanonik ve indekslenebilir adresler var.
- [ ] **Taranabilirlik:** Önemli sayfalar ana sayfadan en fazla 3 tıkta. Hiçbir yerden bağlantı almayan (yetim) sayfa yok.
- [ ] **noindex:** Varsa bilerek mi konmuş?
- [ ] **Kanonik (canonical):** Her sayfada var; benzersiz sayfa kendini gösteriyor. Sonda eğik çizgi kullanımı tutarlı.
- [ ] **JavaScript:** Başlık, açıklama, kanonik, meta robots ve JSON-LD ilk HTML'de var. Statik içerik için önceden üretme (SSG), genel içerik için SSR, CSR yalnızca giriş gerektiren sayfalarda.
- [ ] **HTTPS:** Zorunlu, karışık içerik (mixed content) yok, HTTP'den HTTPS'e yönlendirme var. Güvenlik başlıkları (CSP, HSTS, X-Content-Type-Options, Referrer-Policy) güvenlik için iyidir ama sıralamaya etkisi küçüktür. Ayrıntı için `uzman-guvenlik`.
- [ ] **Yönlendirme:** Zincir en fazla 1 adım; kalıcı taşımada 301. Adres değişince eskisi yönlendirilir.
- [ ] **Mobil:**
  - viewport etiketi, yatay kaydırma yok
  - mobilde de masaüstündeki ana içerik var
  - sayfayı kaplayan açılır pencere (interstitial) yok
  - dokunma hedefi en az 24×24 CSS piksel (WCAG 2.2; `uzman-tasarim`)
- [ ] **Core Web Vitals:** Gerçek kullanıcı verisinin 75. yüzdelik diliminde ölçülür. INP, 2024'te FID'in yerini aldı.
  - LCP ≤ 2,5 sn
  - INP ≤ 200 ms
  - CLS ≤ 0,1

  Ölçemiyorsan sayı yazma.

## Sayfa içi (on-page)
- **Başlık (title):** Her sayfada benzersiz, asıl konu başta, yaklaşık 50–60 karakter, H1 ile uyumlu. Örnek: `Yapay Zekâ Mühendisliği Projeleri | Ad Soyad`.
- **Açıklama (meta description):** Benzersiz, yaklaşık 150–160 karakter. Sayfada ne bulunacağını söyler. Tıklama tuzağı yok.
- **Başlıklar:** Sayfada tek H1. H1 → H2 → H3 sırası atlanmaz.
- **İç bağlantı:** Bağlantı metni açıklayıcı ("buraya tıkla" değil). Kırık bağlantı yok. Önemli sayfalar (projeler) çok bağlantı alır.
- **Görseller:** Betimleyici dosya adı, her görselde anlamlı alt metin (süs görselinde `alt=""`). Sıkıştırılmış, modern biçimde (WebP/AVIF), boyutları belirtilmiş (CLS), ekran dışındakiler tembel yüklenir (lazy).
- **Adresler (URL):** Okunabilir, küçük harf, tire ile ayrılmış. Kimlik numarası ve tarih yok: `/projeler/proje-adi`.
- **Güven:** Yazar kim, ne zaman yayınlandı ve güncellendi, kaynaklara bağlantı. Adres ve telefon yazılmaz (#18); iletişim için e-posta ya da profil bağlantısı yeterli.

## Yapılandırılmış veri (JSON-LD)
- Portfolio sitesi için türler:
  - `Person` (ad, `url`, `jobTitle`, `sameAs`: GitHub, LinkedIn)
  - `WebSite`
  - `ProfilePage` (hakkında sayfası)
  - `BreadcrumbList`
  - `SoftwareSourceCode` (kod projeleri)
  - `BlogPosting` (blog yazıları: `headline`, `datePublished`, `dateModified`, `author`, `image`)
- Birden çok türü tek blokta `@graph` ile birleştir. `@context` ve `@type` her blokta olur. Adresler tam (mutlak) olur, tarih ISO biçiminde yazılır, yer tutucu metin bırakılmaz.
- Şema, sayfada **görünen** içerikle aynı şeyi söyler. Görünmeyen ya da uydurma bilgi (sahte değerlendirme ve puan) eklenmez.
- **Doğrulama:** Schema.org Validator ve Google Rich Results Test. Bu siteler de birer site ziyaretidir (#32).
- **Zengin sonucu kalkmış türler** (kaynağa göre, doğrulanmadı):
  - `HowTo`: Eylül 2023.
  - `FAQPage`: bütün siteler için Mayıs 2026.
  - `WebSite` arama kutusu (`SearchAction`): Kasım 2024. `WebSite` yine de site adı için kullanılır.

  Bu türleri zengin sonuç almak için önerme.

## Site yapısı (portfolio)
- Düz yapı, en fazla 2 seviye. Örnek: ana sayfa, `/projeler`, `/projeler/<ad>`, `/blog`, `/blog/<yazi>`, `/hakkinda`.
- Gezinme 4–7 öğe; logo ana sayfaya gider.
- Breadcrumb adres yapısını yansıtır; son öğe dışındakiler tıklanabilir.
- Öneri çıktısı: ASCII ağaç ya da adres tablosu (adres, sayfa, amaç, iç bağlantılar).

## Yapay zekâ aramalarında görünürlük
- Ayrı bir "yapay zekâ için yazım" gerekmez; iyi SEO ve açık içerik temeldir. Kaynaklar özel işaretlemenin zorunlu olmadığını söylüyor.
- Somut yöntemler:
  - Soruya verilen net cevap bölümün başında olsun.
  - Başlıklar açıklayıcı, paragraflar kısa, karşılaştırmalar tablo hâlinde.
  - Yazar ve tarih görünür; birincil kaynağa bağlantı var.
  - Kritik içerik JavaScript olmadan görünür.
- **Yapay zekâ tarayıcıları** (robots.txt): Arama için olanlar (OAI-SearchBot, Claude-SearchBot, PerplexityBot) ile eğitim için olanlar (GPTBot, ClaudeBot, CCBot, Google-Extended) ayrıdır. Eğitim tarayıcılarına izin vermek ya da vermemek kullanıcının tercihidir; sor. Google-Extended'ın sıralamaya etkisi yoktur (kaynağa göre).
- **`llms.txt`:** Google araması için etkisi yok (kaynağa göre). Diğer yapay zekâ sistemleri için isteğe bağlıdır. İki kaynak bu konuda çelişiyor; sıralama aracı olarak önerme.
- Kaynaklardaki yüzde ve oranlar (ör. "şema ile %30–40 daha görünür") doğrulanmadı; kullanılmaz.

## Denetim rapor biçimi
**Özet:** genel durum, en önemli 3–5 sorun, hızlı kazanımlar.

| Öncelik | Alan | Sorun | Kanıt (adres, dosya:satır, komut çıktısı) | Düzeltme |
|---|---|---|---|---|

Öncelik düzeyleri:
- **Kritik:** indekslemeyi engeller
- **Yüksek**
- **Orta**
- **Düşük**
- **Bilgi**

Ölçülmeyen alan "ölçülmedi" diye yazılır; puan uydurulmaz.

## Bitirmeden doğrula (#24)
- [ ] Ham HTML'e bakıldı (tarayıcıdaki görüntüye değil): başlık, açıklama, kanonik ve JSON-LD orada mı?
- [ ] JSON-LD geçerli JSON ve görünen içerikle uyumlu.
- [ ] Önerilen her değişikliğin kanıtı var. Doğrulanmayan Google politikası "kaynağa göre" diye işaretli.

## Fikir kaynakları
- coreyhaines31/marketingskills (MIT, Corey Haines): `seo-audit`, `schema`, `site-architecture`, `ai-seo`.
- agricidaniel/claude-seo (MIT): `seo-audit`, `seo-technical`, `seo-schema`, `seo-geo`.

İkisi de 13 Ekim 2026'da indirilen kopyalardan okundu; resmî depolarla eşleşmeleri doğrulanmadı. Ücretli araç önerileri, API anahtarı isteyen adımlar, kurulum betikleri ve doğrulanmamış istatistikler alınmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
