---
name: graf
description: Vault'ta iki notun nasıl bağlandığı ("A ile B arasında ne var"), bir notun komşuları, hangi not kümelerinin birbirine yalnızca birkaç notla bağlandığı sorulunca ya da bir Python projesinde "bu fonksiyonu kim çağırıyor, hangi modül hangisine bağlı, import döngüsü var mı" sorusu dosya dosya okumadan cevaplanacaksa kullan. Ana sohbet ve kaşif yükler.
---

Yöntem becerisi (ajan değil). İki betik, ikisi de standart kütüphaneyle çalışır, ağa çıkmaz, vault'a yazmaz. Bağlı kurallar: #24 (çıktıyı kaynakta doğrula), #23.

## Not grafı: `_sistem/graph.py`
Vault kökünden (`{{PY}} -I`):
- `graph.py path <A> <B>`: en kısa yol; her adımda link yönü (`→` A'dan, `←` A'ya, `↔` iki yönlü).
- `graph.py neighbors <X>`: giden ve gelen linkler.
- `graph.py communities [--count N]`: not toplulukları ve topluluklar arası köprü notlar. Köprüler katılım katsayısına göre sıralanır: linkleri topluluklara dengeli dağılan not üstte.
- Ad olarak dosya adı, başlık ya da takma ad verilebilir; Türkçe karakter ve büyük harf fark etmez. Bulunamazsa en yakın 3 ad önerilir.
- `--all`: index, log, bekleyenler, devir ve giriş sayfaları varsayılan olarak dışarıda; bunlar her nota bağlandığı için yolu anlamsızlaştırır.
- `--refresh`: graf verisini önce vault'tan yeniden kurar. Vault bu sohbette değiştiyse önce yenile.
- Gizli notlar (`ben/`, `kurallar/`, `privacy: private`) grafa hiç girmez; "yol yok" sonucu bundan da olabilir.

Ne zaman işe yarar:
- Soru cevaplarken (§7.5) iki konunun hangi notlardan geçerek bağlandığını göstermek.
- Lint'te (§7.7) köprü notları ve tek notla bağlanan kümeleri görüp eksik linkleri önermek. Öneri kullanıcıya sunulur; link kendiliğinden eklenmez.

## Kod haritası: `_sistem/code_map.py`
- `code_map.py <klasör> [--exclude <yol>]...`: modül, sınıf ve fonksiyon sayıları, en çok import edilen modüller, import döngüleri, en çok çağrılanlar. JSON çıktısı `_sistem/cikti/code_map/<klasör>.json` (git dışı).
- `code_map.py <klasör> --find <ad>`: tanımın `dosya:satır`ı ve onu çağıranlar.
- Dosyalar yalnızca `ast` ile ayrıştırılır; hiçbiri çalıştırılmaz ya da import edilmez. Sanal ortam, `.git`, `build` ve `dist` atlanır. Sözdizimi hatalı ve 2 MB'tan büyük dosyalar "atlanan" listesinde görünür.
- **Kökü projenin kökü ver**, alt klasörü değil; yoksa `from app.x import y` çözülmez. Uygulama dışı klasörleri `--exclude` ile çıkar (ör. içerik ve plan klasörleri: `--exclude content --exclude Plan`; büyük bir projede modül sayısı binlerden yüzlere iner, birkaç saniyede biter).
- Kenar etiketleri (betik çıktısında İngilizce yazılır):
  - `extracted` (çıkarıldı): kaynakta açık (aynı modüldeki ad, import edilen ad ya da modül, `self`/`cls` metodu).
  - `guessed` (tahmin): `degisken.metot()` ve projede o adla tek metot var. Dış kütüphane metoduyla karışabilir; kullanmadan önce satırını aç.
  - `ambiguous` (belirsiz): birden çok tanıma uyan çağrı; kenar yapılmaz, yalnızca sayılır.
- Yalnızca Python. C# ve diğer diller kapsam dışı.

## Bitirmeden doğrula
- [ ] Karara temel olan her yol, kenar ya da çağıranı kaynak dosyada satırından açıp gördün (#24); `guessed` kenarı tek başına kanıt değildir.
- [ ] Vault bu sohbette değiştiyse `graph.py --refresh` ile çalıştırdın.
- [ ] Rapora komutu ve kullanılan `--exclude`/`--all` seçeneklerini yazdın.

## Fikir kaynakları
- graphify (Apache-2.0): bilgi grafı, en merkezi düğümlerde dosya merkezlerini dışlama, kenarda çıkarıldı/tahmin etiketi. İndirilen kopyadan okundu, kod alınmadı (#35).
- Katılım katsayısı: Guimerà ve Amaral (2005), *Functional cartography of complex metabolic networks*, Nature 433.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
- Bir grafik arayüz çerçevesi kullanan masaüstü projesinde tek `connect` metoduna yüzlerce "tahmin" çağrısı bağlandı; çağrılar aslında çerçevenin sinyalleriydi (`timer.timeout.connect`). Tahmin yalnızca `degisken.metot()` biçimine daraltıldı ve "en çok çağrılanlar" listesi yalnızca çıkarılmış kenarları sayıyor.
