# Ortak gövde (her stil istemine aynen kopyalanır)

`stil` becerisinin 3. adımında `stil-prompt.md`'ye "Görev" paragrafından hemen sonra, aşağıdaki çit içindeki blok değiştirilmeden kopyalanır. Yer tutucular (`{{…}}`) yalnızca 1. bölümde doldurulur.

```
# 1. PROJE AYARLARI — AYARLAR YALNIZCA BURADA DEĞİŞİR

**Konu:** {{KONU}}

- Storyboard: {{STORYBOARD}}            (Açık | Kapalı)
- Seslendirme: {{SES}}                  (Kapalı | klasördeki kayıt dosyasının adı)
- Altyazı: Kapalı
- Seslendirme yoksa süre: {{SURE}} saniye (varsayılan 30)
- Biçim: {{BICIM}}                      (1080×1920 dikey | 1920×1080 yatay | 1080×1080 kare)
- Kare hızı: 30 fps
- Ses efektleri: {{EFEKT}}              (Kapalı | klasördeki efekt dosyaları | izinle Openverse)
- Arka plan müziği: {{MUZIK}}           (Kapalı | klasördeki müzik dosyasının adı)
- Çıktı: MP4 (out/final.mp4)

Tek düzenlenen bölüm ve tek doğruluk kaynağı budur. Konu serbest metindir: bir cümle ya da bir paragraf. Her nesne, bilgi, etiket, sayı ve sahne konudan ya da seslendirmeden gelir; bu istemin başka yerindeki örneklerden asla gelmez. Aynı istem birbiriyle ilgisiz konularda çalışmalıdır. Ekrandaki bütün metin konunun dilindedir. Konuda gerçek bir ürün ya da şirket geçiyorsa logo ve renkleri uydurma: klasördeki `marka/` dosyalarını kullan; dosya yoksa markayı logosuz, adıyla yaz ve raporda belirt.

# 2. NASIL ÇALIŞILIR — CLAUDE CODE

Claude Code içinde bir proje klasöründesin.

- **Sınırlar:** Yalnızca bu klasörde çalış. Kendi ürettiğin dosyaların dışında hiçbir dosyayı silme ya da taşıma. Paket ya da program kurma, web'e çıkma: eksik bir araç ya da izin gerekiyorsa dur, neyin neden gerektiğini yaz ve kullanıcıya sor. Süreç öldürme; port gerekiyorsa boş port seç. Video, kredi ve kodda yapay zekâ imzası olmaz.
- **Kur:** Animasyonu bu klasörde `index.html` olarak yaz (gerekirse ayrı JS ve CSS dosyaları). `window.seek(t)` fonksiyonunu dışa aç (t saniye cinsinden): t anının karesini deterministik çizer. requestAnimationFrame zamanlamasına, `Date.now()`'a ya da tohumsuz `Math.random()`'a bağlı olmaz; rastgelelik tohumlu bir üreteçten gelir. Zamanlama sabit saniyelerle değil, çözülen toplam süreye oranla yazılır. Fontlar `fonts/` klasöründen yerel yüklenir; klasörde yoksa sistem fontuyla yakın bir eşleşme kullan ve raporda belirt.
- **Çiz (render):** Kurulu ekransız tarayıcıyı (Edge ya da Chrome) `puppeteer-core` ile sür. Sayfayı `file://` ile aç, her kare için `seek(i / fps)` çağır, yapılandırılan doğal çözünürlükte yakala ve ffmpeg ile `out/final.mp4` olarak kodla (H.264, yuv420p). Kareleri `out/kareler/` altında tut.
- **Seslendirme açıksa:** kayıt bu klasördedir ve süresi ana saattir. Kelime zaman damgalarını kurulu bir Whisper ile al (kurulu değilse dur ve sor). Her görsel fikri söylendiği ana hizala. Kaydı son MP4'e ekle. Seslendirme metni ya da zaman damgası asla uydurulmaz.
- **Seslendirme kapalıysa:** sabit süreyi kullan; anlatımı görüntüler, kısa ekran metni ve hareket eden diyagramlar taşır.
- **Ses efektleri açıksa:** klasördeki efekt dosyalarını kullan. Ayar "izinle Openverse" ise yalnızca kullanıcının izin verdiği `api.openverse.org` adresinden CC0 lisanslı ses al (`/v1/audio/?q=<arama>&license=cc0`). Efektler seyrek ve anlamlı anlara bağlı olur; ffmpeg ile tam zaman damgalarına yerleştirilir; kaynaklar `CREDITS.md`'ye yazılır.
- **Arka plan müziği açıksa:** yalnızca kullanıcının bu klasöre koyduğu müzik dosyası kullanılır; seslendirmenin çok altında, ducking (seslendirme sırasında kısma) ile karıştırılır. Müzik sentezlenmez.
- **Storyboard açıksa:** önce bir sahne tablosu yaz (zaman, fikir, kompozisyon, hareket, ekran metni) ve önemli sahnelerin PNG önizleme karelerini çiz; sonra dur ve onay iste. Kapalıysa planı kendin yap ve bitmiş videoyu teslim et.

# 3. KALİTE ÖLÇÜTÜ

- **Gösteri değil, anlatım.** Önce izleyicinin neyi anlaması gerektiğine karar ver; sonra anlatımı grafiklerin kendisi yapsın: dönüşen nesneler, kurulan diyagramlar, hareket eden sayılar. Hiçbir şey öğretmeyen süs çıkarılır.
- **Bağlı anlatı.** Sahneler birbirinden doğar; bir fikirdeki öğe sonrakinin başlangıcı olur. Video asla ayrı kartlardan oluşan bir slayt gösterisi gibi durmaz.
- **Net hiyerarşi.** Her anda tek ana fikir, tek odak noktası, geniş kenar boşlukları; metin telefonda okunur ve okunacak kadar sabit kalır.
- **Akıcılık.** Her harekette yumuşatma (easing); titreme, birden belirme ve hiçbir şeyin karar verilmediği kare yok.

# 4. DOĞRULAMA

Zaman çizelgesinin her yerinden çok sayıda kareyi PNG olarak çiz ve bak. Taşan, üst üste binen, okunmayan, boş ya da bozuk kareleri ve bu stilde değil de sıradan görünen her şeyi düzelt; sonuçla gurur duyana kadar sürdür. Sonra son MP4'ü çiz ve neyi gösterdiğini kısaca raporla: süre, çözünürlük, sahne listesi, eksik kalan ya da varsayımla doldurulan her şey (font, logo, efekt).
```
