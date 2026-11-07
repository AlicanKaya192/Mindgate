# Platform rehberleri ve lisans

## Apple HIG
- Sayfalar JavaScript ile çizildiği için HTML boş döner. JSON'dan oku (web izni #32 ile):
  - İçindekiler: `https://developer.apple.com/tutorials/data/design/human-interface-guidelines.json`
  - Sayfa: `https://developer.apple.com/tutorials/data/design/human-interface-guidelines/<sayfa>.json` (layout, typography, color, materials, accessibility…)
- HIG'in platformdan bağımsız ilkeleri her projede geçerlidir: hiyerarşi, gruplama, amaca göre adlandırılmış renk rolleri, minimum yazı boyutu, kontrast, hedef boyutu ve aralığı, hareketi azaltma, sekme gezinme içindir ve eylem araç çubuğundadır. Liquid Glass ve sistem API'leri gibi Apple'a özel görünüm Windows'a kopyalanmaz.
- **Lisans:** SF fontları yalnızca Apple platformları için taslak (mockup) yapmakta kullanılabilir. Uygulamaya gömmek ve web sitesinde kullanmak yasaktır (Apple font lisansı). SF Symbols lisansı doğrulanmadı; Apple dışı projede kullanma. Uygulama ikonunda ve logoda hiçbir koşulda kullanılmaz.

## Microsoft Fluent
- `fluent2.microsoft.design/typography` ve `/motion` açılıyor. Kâşif raporu (30 Ekim 2026, ham metinle karşılaştırılmadı): Body 1 14/20 px, Caption 1 12/16 px, Title 1 32/40 px; sürekli dönme dışında linear eğri yok; hareket yok ayarı sunulur.
- Temalı uygulamada Fluent'i yapı ve erişilebilirlik için al, görsel kimliği proje verir.

## Material 3
`m3.material.io` sayfaları JavaScript ile çiziliyor, kâşif başlıktan fazlasını okuyamadı. Sayı gerekirse başka yol aranır, hafızadan yazılmaz.

## Figma
Figma'dan koda için resmî Figma MCP vardır. Hesap ister ve tasarım verisi dış servise gider. Kurmadan önce kullanıcıya sor (#23, #27).

## CSS tuzağı
Bölüm sınıfı ile öğe sınıfının birbirini ezmemesine dikkat et. Bu en çok bölümler arası boşlukta (padding, margin) olur.
