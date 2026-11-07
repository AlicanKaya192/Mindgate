---
name: obsidian-yazimi
description: İkinci beyin vault'una yazarken Obsidian sözdizimi ve vault kuralları; bitirmeden doğrulama listesi. Bakımcı ajanına önceden yüklenir; ana sohbet de vault'a not yazarken kullanabilir.
---

Yöntem becerisi (ajan değil). Asıl kural kaynağı vault `CLAUDE.md` (§3 adlandırma, §5 frontmatter, §6 bağlantı, §10 index/log/git). Bu beceri onun kısa uygulama özetidir; çelişirse `CLAUDE.md` geçerlidir.

## Sözdizimi
- **Bağlantı:**
  - `[[dosya-adi]]`, görünen adla `[[dosya-adi|Görünen Ad]]`
  - başlığa `[[dosya-adi#Başlık]]`
  - Uzantı yazılmaz. Dosya adı vault genelinde benzersizdir.
- **Gömme (embed):** `![[dosya-adi]]`, görsel için `![[resim.png]]`.
- **Callout:**
  - `> [!note]`, `> [!warning] Başlık`, `> [!tip]`
  - katlanır hâli `> [!info]-`
  - Vault'ta kullanılanlar: `[!warning] Çelişki`, `[!warning] Yerini aldı`.
- **Properties (frontmatter):**
  - Düz YAML; iç içe alan yok. Aynı alan her notta aynı tipte.
  - Tarih `YYYY-MM-DD`. Liste `[a, b]`.
  - Property içindeki bağlantı **tırnakla** yazılır: `project: "[[proje-adi]]"`.
  - `tags` içinde `#` ve boşluk yok.
  - İsteğe bağlı alanlar:
    - `source_type: stated|inferred|verified`
    - `privacy: private`: otomatik bağlama ve ajan görevine girmez
    - reddedilen çıkarım için `invalid` + `invalid_reason` (silinmez)
  - Paylaşılan dosyalara (bekleyenler, log, devir) `_sistem/records.py` ile yaz (kilitli, #36).
- **Diğer Obsidian sözdizimi:**
  - Bloğa bağlantı: paragraf sonuna `^blok-id` yazılır, `[[dosya#^blok-id]]` ile bağlanır. Liste ve alıntıda `^blok-id` ayrı satıra konur.
  - Gömmede genişlik `![[resim.png|300]]`, PDF sayfası `![[belge.pdf#page=3]]`.
  - Gizli yorum `%%…%%`, vurgu `==…==`, dipnot `[^1]`.
  - Callout türleri: `note`, `tip`, `info`, `warning`, `danger`, `bug`, `example`, `question`, `success`, `failure`, `todo`. `-` kapalı, `+` açık katlanır.
  - Satır içi etikette ilk karakter rakam olmaz; iç içe etiket `#ust/alt`.
- **Bases (`.base`)** dosyaları giriş sayfalarının tablolarını üretir. İş gerektirmedikçe dokunma. Dokunursan:
  - İki tarihin farkı sayı değil süredir (Duration). Gün için `.days` al, sonra yuvarla: `(now() - file.ctime).days`. Doğrudan `.round()` hata verir.
  - Boş olabilen alanı `if(alan, …, "")` ile koru.
  - Özel karakter içeren YAML değerini tırnakla. Formülü tek tırnağa, içindeki metni çift tırnağa al.
  - `formula.X` kullanıyorsan `formulas:` altında `X` tanımlı olmalı.
- **Canvas (`.canvas`, JSON Canvas 1.0):** Düğüm kimlikleri benzersiz olmalı (16 haneli onaltılık). Her kenarın `fromNode` ve `toNode` alanı var olan bir düğümü göstermeli. Kaydetmeden önce JSON'un geçerli olduğunu kontrol et.
- **Görünmez karakter ve dış görsel** (`![](https://…)`) vault'a girmez (#27).

## Vault kuralları (özet)
- Dosya adı küçük harf, ASCII, tire (ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u). Tarihli notlar `YYYY-MM-DD-` önekli.
- Her not şablondan (`_sablonlar/`) başlar ve en az bir yere bağlanır; yetim not olmaz.
- Değişen notta `updated` alanı güncellenir.
- `log.md` yalnızca sona eklenir: `## [YYYY-MM-DD] <işlem> | <başlık>`.
- `index.md` satırı: `- [[dosya]] — tek satır özet`.
- Hassas bilgi, sır ve bilgisayar kodu yazılmaz (#17, #18). Silme yok, arşive taşınır (#22).

## Bitirmeden doğrula (#24)
- [ ] Yazdığın her `[[bağlantı]]`'nın hedef dosyası var (Glob ile bak). Yoksa düz metin ya da kod biçimi kullan.
- [ ] Frontmatter geçerli YAML; `type`, `status`, `updated` doğru.
- [ ] `index.md` ve `log.md` güncellendi.
- [ ] Dış kaynaklı içerik `{{PY}} -I _sistem/security_scan.py <dosya>` ile tarandı.
- [ ] `git diff --cached` ile sır kontrolü yapıldı, commit atıldı (uzak depo tanımlıysa push edildi).
- [ ] Raporda kanıt var: commit kimliği. "Yaptım" demek yetmez.

## Fikir kaynakları
- kepano/obsidian-skills (`obsidian-markdown`, `obsidian-bases`, `json-canvas`; MIT, Steph Ango): https://github.com/kepano/obsidian-skills. 13 Ekim 2026'da indirilen kopyadan eksikler eklendi.
- obra/superpowers `verification-before-completion`: https://github.com/obra/superpowers

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
- Yeni `index.md` satırını **`records.py index --section … --line …`** ile ekle; elle eklemede bir satır kayboldu (#36 ihlali). Proje alt notu (ADR, ilerleme) için satırın başına iki boşluk koy: `--line "  - [[proje-adi-adr-009-…]] — …"` (girintili satır destekleniyor).
- Paralel sohbetler aynı anda `bekleyenler.md`'ye yazabiliyor (aynı numara iki kez alındı). B-NNN numarasını yazmadan hemen önce dosyayı yeniden oku, yazdıktan sonra numaranın tek olduğunu kontrol et.
