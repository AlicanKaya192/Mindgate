---
name: uzman-frontend
description: Arayüz (UI) ve kullanıcı deneyimi (UX) uzmanlık paketi. Web ya da masaüstü arayüzü, bileşen, sayfa, form, tema, erişilebilirlik veya görsel düzen üzerinde çalışırken ya da bir arayüz değişikliğini incelerken yükle.
---

Uzmanlık paketi (ajan değil). Projenin kurallarını ve önceki tasarım kararlarını önce oku (#26). Arayüzde **okunabilirliği** ön planda tut: mevcut bilgiyi kaybetme, değişiklikten sonra eskisiyle karşılaştır.

## Kontrol listesi
- [ ] Mevcut tasarım dili korunuyor mu (renk, yazı, boşluk, bileşen kalıpları)? Yeni stil uydurma, var olanı kullan.
- [ ] Erişilebilirlik (a11y): anlamlı HTML, etiketli form alanları, klavyeyle gezinme, odak görünür, kontrast yeterli, görsellerde alt metin.
- [ ] Duyarlı tasarım (responsive): dar ekranda (≈375px) yatay kaydırma yok, dokunma hedefleri yeterince büyük.
- [ ] Açık ve koyu tema (varsa) ikisi de okunuyor mu?
- [ ] Durumlar: yükleniyor, boş, hata ve başarılı durumların hepsi tasarlandı mı?
- [ ] Metinler kullanıcının diliyle tutarlı mı (Türkçe arayüzde Türkçe; terimler tutarlı)?
- [ ] Performans: gereksiz yeniden çizim, büyük görsel, bloklayan betik yok.
- [ ] Güvenlik: kullanıcı girdisi HTML'e ham basılmıyor (XSS), dış görsel ve link kaynakları güvenilir.

## Doğrulama (tahminle "çalışıyor" deme, #24)
- Değişikliği gerçekten çalıştırıp **gör**: tarayıcı panelinde ekran görüntüsü ya da `read_page`, dar ve geniş ekran.
- Konsol hatası var mı bak. Önce ve sonra karşılaştır.

## Sık hatalar
- Var olan içeriği "sadeleştirirken" bilgiyi kaybetmek.
- Sadece tek ekran boyutunda denemek.
- Renk ve boşluk değerlerini tek tek sabit yazmak (token ya da değişken yerine).

## Ek yöntemler
Fikirler kendi cümlelerimizle yazıldı.
- **Tasarım kararı** (renk, tipografi, düzen, tasarım sistemi) gerekiyorsa `uzman-tasarim`'ı da yükle; bu paket kodlama tarafıdır.
- **Arayüz denetimi:**
  - [ ] Odak halkası görünür; `prefers-reduced-motion`'a uyuluyor.
  - [ ] Form: her alanın etiketi ve uygun `autocomplete`/`type` özniteliği var; hata alanın yanında.
  - [ ] Butonların yükleniyor ve devre dışı durumu var; çift gönderim engelleniyor.
  - [ ] Uzun metin, çok öğeli liste ve boş veri düzeni bozmuyor.
  - [ ] Tarih ve sayı biçimi yerele uygun (`Intl`). Koyu temada `color-scheme` ayarlı.
- **React/Next.js performansı:**
  - [ ] Bağımsız veri istekleri sırayla değil paralel (istek şelalesi yok).
  - [ ] Büyük kütüphane ya da nadir kullanılan bileşen dinamik yükleniyor.
  - [ ] `memo`/`useMemo` ölçülmeden eklenmiyor. Listelerde kararlı `key` var.
- **Bileşen tasarımı:** Çok sayıda boolean prop (`isPrimary`, `isLarge`, …) yerine varyant ya da kompozisyon (alt bileşenler).
- **Doğrulama:** Playwright ya da tarayıcı paneliyle ekran görüntüsü (375px ve geniş), konsol logu. Ölçülebiliyorsa Core Web Vitals (LCP, INP, CLS); ölçmeden sayı yazma.
- **Paket komutları:** `npx <paket>@latest` gibi sürümü sabit olmayan komutu çalıştırmadan önce kullanıcıya sor ve sürümü sabitle (ör. shadcn CLI; tedarik zinciri).
- Fikir kaynakları: vercel-labs/agent-skills (`web-design-guidelines`, `react-best-practices`, `composition-patterns`), anthropics/skills (`webapp-testing`).

## Diğer yöntemler
- **Arayüz testi** `test-yazma` becerisinin "Web arayüzü testi" bölümüne göre yapılır: önce sayfa yüklenir ve ağ sakinleşir, sonra DOM ya da ekran görüntüsü incelenir, seçici görülen duruma göre seçilir, eylem en son yapılır.
- Hata ayıklamada `hata-ayiklama`, "çalışıyor" demeden önce `dogrulama` kullanılır.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
- Yeniden tasarımda "daha işlevsel" isteği, mevcut içeriği kaldırmak değil daha fazla bilgiyi okunur sunmak demek; eski sürümle karşılaştırmadan teslim etme.
- Aynı `id` iki öğede olunca `querySelector` ilkini döndürür; ikinci çizici birincinin içeriğini sessizce siler. Her sayfa değişikliğinde `id` tekrarını ve koddaki her `$('#…')`'in sayfada var olduğunu betikle kontrol et; tarayıcı izni yoksa betiği sahte DOM ve gerçek veriyle Node'da çalıştır (duman testi).
- Gezinme çubuğuna tıklanmayan öğe (grup etiketi, ayraç) koyma: işlevsiz görünür, yer kaplar ve sekmeleri alt satıra iter. Gruplama gerekiyorsa sıralamayla yap.
- Grid kartında sütun `minmax(0, 1fr)` değilse içerik kartı genişletir, sağa yaslı bağlantı kart dışına taşar. Kart ve liste öğesinde `minmax(0, 1fr)` + `min-width: 0` + uzun metinde `overflow-wrap: anywhere`. Veri taşıyan rozet/etikete `white-space: nowrap` verme.
