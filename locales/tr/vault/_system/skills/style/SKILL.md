---
name: stil
description: Kullanıcı bir ya da birkaç referans görsel (afiş, reklam, ekran görüntüsü, herhangi bir tasarım) verip bundan tekrar kullanılabilir bir animasyonlu anlatım (explainer) video stili çıkarılmasını, o tarzda video yapılmasını ya da görselin şablona çevrilmesini istediğinde kullan. "Bu görselden stil çıkar", "bu tarzda video yap", "şablona çevir", "bunu hareketli grafiğe çevir", "turn this poster into a video style" gibi isteklerde ve görsel verip hareketli grafik (motion graphics) istendiğinde yükle. Ana sohbet yükler.
---

İş akışı becerisi (ajan değil). Bağlı kurallar: #14, #22, #24, #32, #35, #39, #44, #45. Tasarım eleştirisi için yanında `uzman-tasarim`, kod için `temiz-kod`.

Amaç: durağan bir görselden **yaşayan bir video stili** çıkarmak. Sonuç, aynı tasarımcının yaptığı bir anlatım dizisinden çıkmış gibi görünmeli; "afişin üstünde kayan nesneler" gibi değil.

Asıl çıktı bir **stil istemi (style prompt)**: başka hiçbir bağlam olmadan taze bir Claude Code oturumunda çalıştırılınca, herhangi bir konuda bu görünümü üreten uzun ve kendi kendine yeten bir istem. Ayrıntı işin kendisidir: "krem kâğıt, kalın yazı" gibi kısa bir tarif ortalama video verir. Görünümün nasıl kurulduğunu, nasıl hareket ettiğini ve genelde nasıl taklit edildiğini anlatan istem iyi video verir.

## 1. Bağlam ve ortam
- Referans görsel(ler) ve konu: konu verilmediyse yalnızca onu sor.
- Kullanıcının tasarım zevkini ve reddettiklerini oku (`ben/profil.md`, `fikirler/reddedilen-oneriler.md` içindeki `tasarım` satırları; #39). Bu bilgiler beceriye ve stil istemine kişisel bilgi olarak yazılmaz (#44).
- **Proje klasörü vault dışında olur** (vault'a html, js ve video girmez). Klasör verilmediyse sor.
- Araç denetimi: `ffmpeg -version`, `node --version`, kurulu ekransız tarayıcı (Edge ya da Chrome yolu), proje klasöründe `puppeteer-core` (ya da Playwright). Eksik olanı **kendin kurma**. Neyin eksik olduğunu, neden gerektiğini ve kaynağını yazıp izin iste (#35, #19). npm kurulumu `--ignore-scripts` ile yapılır; tarayıcı indirilmez, kurulu olan kullanılır.
- Docker: tarayıcı GPU ile çizdiği için iş yerel donanıma bağlı, #45'e göre Docker'a uygun değil; bunu tek satırla söyle.

## 2. Görselleri oku
- Her görsele tam boyda ve kırpılmış parçalar hâlinde bak (köşeler, yazı, doku, kenarlar). Kırpmayı betikle yap (ffmpeg `crop` ya da Pillow).
- **Renkleri gözle tahmin etme:** baskın renkleri betikle örnekle (ör. küçültülmüş görselde k-ortalama ya da histogram). Hex değerleri ve yaklaşık oranları çıktıdan al (#24).
- Neyin malzeme (kâğıt, mürekkep, cam, ışık, piksel), neyin kompozisyon, neyin metin olduğunu ayır. Alınacak olan malzeme ve alışkanlıklardır; yerleşim, metin ve logo alınmaz.

## 3. Stil istemini yaz
`<proje>/stil-prompt.md` şu sırayla yazılır:
1. **Görev:** stilin adı ve hedef tek paragrafta: bu görsel dilde birinci sınıf bir animasyonlu anlatım videosu, slayt gösterisi değil.
2. **Ortak gövde:** `references/ortak-govde.md`'deki blok **aynen**, `{{…}}` yer tutucularıyla.
3. **Stil bölümleri:** senin yazdığın 2.000–4.000 kelime. Her bölümün içeriği ve ölçütü `references/stil-bolumleri.md`'de; yazmadan önce oku. Bölümler: görsel dil ve palet, malzeme ve yüzey, tipografi, kompozisyon alışkanlıkları, imza unsurları, teknik uygulama, imza hareketi, geçişler, bilgi tasarımı, ses, kaçınılacak ucuz kısa yollar.

Stil istemi, uzman bir tasarımcının çırağına aktardığı zanaat bilgisi gibi yazılır: inşa edilebilecek kadar somut. En çok emek **teknik uygulama** bölümüne gider; ortalama çıktıyı iyi çıktıdan ayıran odur.

## 4. İstemi sına, yalnızca videoyu değil
1. Config'i kullanıcının konusuyla doldur: süre 8 sn, storyboard kapalı, ses ve efekt kapalı.
2. İstemi **yazıldığı gibi** taze bir bağlamda çalıştır: alt ajan (`general-purpose`, `model` açık yazılır). Görev metnine yalnızca istemi, proje klasörünü ve kuralları ver: silme yok (yalnızca kendi çıktı dosyalarının üstüne yazar), web'e çıkma yok, paket kurma yok, süreç öldürme yok. Alt ajan kullanılamıyorsa yalnızca isteme bakarak kendin uygula.
3. Videodan kareler çıkar (`ffmpeg -vf fps=2`) ve referansla yan yana bir montaj yap. Dürüstçe değerlendir: biri ikisini aynı tasarımcının yaptığına inanır mı? Değerlendirmede `uzman-tasarim` eleştiri adımlarını kullan.
4. İnanmazsa en büyük farkı yaratan **istem satırını** düzelt (videoyu elle düzeltme) ve yeniden çalıştır. Her turda "fark → istemde değişen satır" kaydını tut.
5. İlk taslak bitmiş istem değildir: 2–3 tur bekle. Stil, taze ve yardımsız bir çalıştırma referans kadar iyi çıkınca hazırdır.

## 5. Teslim ve öğrenme
- Test videosunu ve `stil-prompt.md`'yi göster; tur kayıtlarını kısaca özetle.
- Kullanıcı geri bildirim verince videoyu düzelt ve dersi istemin sonundaki **"Notlar"** bölümüne kullanıcının kendi sözleriyle ekle; bir sonraki video aynı düzeltmeyi istemesin. Reddedilen öneri ayrıca `reddedilen-oneriler`'e yazılır (#39).
- Video ve kredilerde yapay zekâ imzası olmaz (#14).

## Telif ve marka
- **Stili al, resmi alma:** görsel dil kullanılır; özgün çizim, kompozisyon, metin ve logolar asla. Her kare konuya göre kurulmuş yeni bir yerleşimdir.
- Konu gerçek bir ürün ya da şirket adı geçiriyorsa logo ve renk **uydurulmaz**: kullanıcının proje klasörüne koyduğu dosya kullanılır; yoksa marka logosuz, adıyla yazılır ve kullanıcıya söylenir. Logo web'den izinsiz indirilmez (#32).

## Bitirmeden doğrula
- [ ] Hex değerleri betik çıktısından; stil bölümleri 2.000–4.000 kelime, 11 bölümün hepsi var.
- [ ] Ortak gövde değiştirilmeden kopyalandı; yer tutucular yerinde.
- [ ] En az bir taze çalıştırma yapıldı; referansla yan yana montaj görüldü; tur kayıtları var.
- [ ] Referanstan metin, logo ya da yerleşim kopyalanmadı.
- [ ] Kurulum, indirme ve web erişimi yalnızca alınan izinle yapıldı; proje dışında dosya silinmedi.

## Fikir kaynakları
- `/stil` becerisi: herkese açık bir /stil beceri metninden uyarlandı (metinle birlikte verilen kaynak adresi: `smokich.gosem.dev/stil`). Site açılmadı; sahibi ve lisansı doğrulanmadı. Fikir alındı, metin kendi cümlelerimizle ve kurallarımıza göre yeniden yazıldı (#35). Değişenler: eksik aracı kendiliğinden kurma yerine izin, ses ve font indirme izinle, logo yalnızca kullanıcı dosyasından, çıktı vault dışında.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
