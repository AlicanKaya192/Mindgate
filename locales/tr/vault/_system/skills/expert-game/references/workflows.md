# İş akışları: game jam, hızlı prototip, Steam, itch.io, oyun belgesi

Sayılar ve mağaza koşulları kaynak paketin sahibinin beyanıdır, bağımsız doğrulanmadı. Mağaza koşulu değişmiş olabilir; ücret ve süre gibi bilgileri kullanıcı mağazanın kendi sayfasında doğrular.

## Game jam
**Kapsam:** Süreli yarışmada oyunu bitirip teslim etmek.

**Yöntem**
- Tema açılmadan önce jam kurallarını `JAM.md`'ye yaz: süre, izin verilen hazır varlıklar, teslim biçimi, son saat.
- Dikey dilim: tek bir oynanabilir döngüyü baştan sona bitir, sonra genişlet.
- Sürenin son yaklaşık %20'si sevkiyata ayrılır: yapı, sayfa, yükleme, deneme.
- 48 saatlik jam için saat saat çizelge yaz (kaynağın dağılımı okunmadı; %20 kuralını koru).

**Tuzaklar**
- itch.io'ya yüklemek jam girişi değildir. Jam sayfasındaki gönderimi kullanıcı yapar.

**Doğrulama**
- Teslimden önce oyun temiz bir makinede ya da tarayıcıda açılıyor mu, kullanıcı dener.

## Hızlı prototip
**Kapsam:** Bir fikri yaklaşık 1 saatte sınamak.

**Yöntem**
- Başlamadan `BRIEF.md` yaz, beş alanla:
  - SORU: sınanan tek soru.
  - FİİL: oyuncunun ana eylemi.
  - TUT EĞER: fikri tutmak için görülmesi gereken.
  - ÖLDÜR EĞER: fikri bırakmak için yeten.
  - SONUÇ: oynandıktan sonra doldurulur.
- Gri kutu: grafik, ses ve menü yok; yalnızca fiil.
- Ajan eğlenceyi yargılamaz. Kullanıcı oynar, SONUÇ'u kullanıcı yazar.
- "Tut" kararı temiz yeniden yazma iznidir ve bu kararı kullanıcı verir; prototip kodu ürüne taşınmaz.

## Steam
**Kapsam:** Yapıyı Steam'e yükleme ve yayın hazırlığı.

**Yöntem**
- Yükleme kullanıcının açık izniyle yapılır; `steamcmd` kurulu değilse neyin neden gerektiğini söyle ve izin iste (#35). Yapı önce bir beta dalına gider; `default` dalını kullanıcı kendisi açar.
- Yüklemeden önce Preview (kuru çalıştırma) ile neyin gideceğini gör.
- Kaynağın beyanına göre: uygulama ücreti 100 USD, yayından önce en az 2 hafta "Coming Soon" sayfası.
- Steam kimlik bilgileri dosyaya, betiğe ya da günlüğe yazılmaz.

**Tuzaklar**
- Unity'de LZ4HC sıkıştırması Steam yamasını büyütür (`motor-unity.md`).

## itch.io
**Kapsam:** butler ile yükleme ve HTML5 sınırları.

**Yöntem**
- Her platform için ayrı kanal kullan (ör. Windows, Linux, web ayrı).
- Gerçek yüklemeden önce `--dry-run`; gerçek `butler push` kullanıcının açık izniyle yapılır. `butler` kurulu değilse neyin neden gerektiğini söyle ve izin iste (#35).
- `BUTLER_API_KEY` dosyaya, commit'e ya da günlüğe yazılmaz.

**Eşikler**
| Sınır | Değer |
|---|---|
| HTML5 dosya sayısı | 1.000 |
| HTML5 toplam boyut | 500 MB |
| Tek dosya | 200 MB |

**Tuzaklar**
- Godot web yapısında iş parçacığı kullanılıyorsa sunucu COOP/COEP başlıkları ister (`motor-godot.md`).

**Doğrulama**
- Kuru çalıştırma çıktısında dosya sayısı ve boyut sınırların altında.
- Sayfayı yayına almak kullanıcının işidir.

## Oyun belgesi
**Kapsam:** Tasarım belgesi (GDD) ve özellik notu.

**Yöntem**
- Oyun için tek sayfalık GDD; her özellik için ayrı kısa özellik notu.
- Kaynak "altı durum" kapsanmasını istiyor; durumların listesi okunmadı. Özellik notunda en azından normal akışı, hata ve boş durumları yaz.
- Kullanıcıya en çok bir tur soru sor; cevapsız kalanı varsayım olarak işaretle ve yaz (kaynakta `[ASSUMPTION]`, Türkçe belgede `[VARSAYIM]`).

**Doğrulama**
- Her varsayım işaretli; belge bağlamı bilmeyen birinin okuyup uygulayabileceği kadar açık.
