# Kayıt sistemi, diyalog, girdi ve oyun arayüzü

Sayılar kaynak paketin sahibinin beyanıdır, bağımsız doğrulanmadı. Her eşik başlangıç noktasıdır: ölç, oynat, ayarla.

## Kayıt sistemi
**Kapsam:** Oyun durumunu diske yazma, okuma ve sürümler arası taşıma.

**Yöntem**
- Düz veri kaydet: sözlük, liste, sayı, dize. Motor nesnesi ya da sahne düğümü kaydedilmez.
- İlk sürümden itibaren tamsayı `version` alanı koy.
- Atomik yazma: önce geçici dosyaya yaz, var olan kaydı `.bak` yap, sonra geçiciyi asıl adla yeniden adlandır. Yazma yarıda kesilirse eski kayıt sağlam kalır.
- Savunmacı yükleme:
  - Kayıt oyunun bildiğinden yeni sürümdeyse reddet, üstüne yazma.
  - Eski sürümü adım adım göç ettir (1→2→3), atlama.
  - Dosya bozuksa `.bak`'a dön.
- Otomatik kayıt en çok 60 s arayla. 3 yuvalı halka kullan; en eskisinin üstüne yazılır.
- Türetilmiş veri (toplam stat, harita önbelleği) kaydedilmez, yüklemede yeniden hesaplanır.
- Roguelike'ta koşu ve profil ayrı dosyadır (`turler.md`).

**Tuzaklar**
- Godot JSON'u 2^53'ün üstündeki tamsayıyı kaybeder; büyük kimlikleri dize olarak sakla.
- Godot `str_to_var` güvenilmeyen kayıtta betik çalıştırabilir; kayıt okumada kullanma.
- NaN ya da sonsuz değer kaydedilmez; yazmadan önce denetle.
- Roblox DataStore kuralları ayrı: `motor-roblox.md`.

**Doğrulama**
- Yaz, oku, karşılaştır: durum birebir aynı dönmeli.
- Eski sürümlü örnek kayıtları göç ettir; yeni sürümlü kaydın reddedildiğini gör.
- Yazmayı yarıda kes (geçici dosya kalsın) ve yüklemenin sağlam kayda döndüğünü gör.

## Diyalog
**Kapsam:** Diyalog grafiği, koşullar ve seçim sonuçları. Metnin kendisi için `uzman-yazarlik`.

**Yöntem**
- Aracı içeriğe göre seç: yoğun düzyazı için Ink, motorla sıkı bağ gerekiyorsa Yarn, ikisi de gerekmiyorsa küçük bir JSON grafik.
- Her satıra baştan kararlı bir kimlik ver; çeviri, seslendirme ve okunmuş işareti bu kimliğe bağlanır.
- Seçimin bedeli (para, eşya, ilişki puanı) seçim geçişinde düşülür, satır gösterilirken değil.
- Koşulları `eval()` ile çalıştırma. Yalnızca izin verilen değişken ve işlemleri tanıyan küçük bir değerlendirici yaz.

**Doğrulama**
- Her yolu otomatik yürüt: her düğüme ulaşılıyor mu, çıkmaz var mı.
- Görsel romanda erişilemez son denetimi: `turler.md`.

## Girdi
**Kapsam:** Tuş ve gamepad eşleme, tampon, ölü bölge, erişilebilirlik.

**Yöntem**
- Eylemlere niyet adı ver (`jump`, `interact`), tuş adı değil.
- Analog çubukta radyal ölü bölge 0,2.
- Girdi tamponu 0,15 s ve oyun zamanında sayılır; donmada ya da duraklatmada süresi dolmaz.
- Yeniden eşlemede fiziksel tuş konumunu kaydet; klavye düzeni değişince tuşlar kaymaz.
- Erişilebilirlik: tam yeniden eşleme, basılı tutma yerine geçiş (toggle) seçeneği, ayarlanabilir zamanlama.

**Tuzaklar**
- Yanlış yazılmış eylem adı sessizce başarısız olur (ör. Unity `FindAction`).
- Unreal'da Enhanced Input bağlamı: `motor-unreal.md`.

**Doğrulama**
- Kodda geçen her eylem adının eşleme dosyasında olduğunu denetle.
- Ajan düğmeye basamaz. Gamepad, dokunmatik ve titreşim davranışını kullanıcı dener; görülmeyen cihaz davranışı "doğrulanmadı" diye raporlanır.

## Oyun arayüzü
**Kapsam:** HUD, menü, ayar ekranı. Oyun dışı arayüz için `uzman-tasarim` ve `uzman-frontend`.

**Yöntem**
- Yerleşimi çapa (anchor) ve kapsayıcılarla kur, sabit konumla değil. Referans çözünürlük 1920×1080.
- Ekranları bir yığında (stack) tut; açık menüleri ayrı bool bayraklarla izleme.
- Açılan her ekran odağı bir öğeye versin; odak yoksa gamepad kullanan oyuncu kilitlenir.
- Çeviri payı bırak: Almanca metin yaklaşık %30 uzun gelir.

**Eşikler**
| Ölçü | Başlangıç |
|---|---|
| Yazı boyutu (1080p) | PC 18 px, konsol 26 px |
| Arayüz ölçeği | %200'e kadar bozulmadan |
| Karşıtlık | metin 4,5:1; büyük yazı ve arayüz öğesi 3:1 |
| Dokunma hedefi | yaklaşık 9 mm |

**Doğrulama**
- Üç farklı çözünürlükte ekran görüntüsü al, aç ve bak: taşma, kesilme, okunmayan yazı var mı.
- Menüyü yalnızca gamepad ile baştan sona dolaşan bir test yaz ya da kullanıcıya denet.
- Arayüz öğesinin görsel durumları: `his-kamera-seviye.md` → Oyun hissi, "Görsel varlık seti".
