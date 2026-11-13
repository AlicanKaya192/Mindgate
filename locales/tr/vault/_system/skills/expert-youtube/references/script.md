# Senaryo ve açılış kancası

Bir fikri, izleyicinin sonuna kadar izleyeceği konuşma metnine çevirmek.

## İlk 15 saniye
Açılış üç iş yapar. Biri eksikse izleyici erken gider:
1. **Tıklamayı doğrula:** Başlığın vaadini ilk cümlede tekrar et, başka kelimelerle.
2. **Bir soru aç:** İzleyicinin kendi başına kapatamayacağı tek bir soru.
3. **Cevabın var olduğunu göster:** Sonuç, ekran ya da kanıt videoda gerçekten var.

Yalnızca üçüncüsünü yapan açılış bir özettir, kanca değildir.

## Akış
1. **Kanca:** Beş farklı açılış yaz, her biri farklı bir kalıpla (aşağıdaki tablo). Hepsini `hook_check.py`'den geçir. Eksik özelliği en az olan ikisini, araç çıktısıyla birlikte kullanıcıya göster. Tek seçenek sunma.
2. **Geçiş (0:15–0:45):** Videonun ne yapacağını tek cümlede söyle ve hemen başla. Kanal tanıtımı, "başlamadan önce" ve abone ol çağrısı burada olmaz; bunlar izleyiciyi erken kaybettirir.
3. **Gövde:** Her bölümde bir fikir. Her bölüme `[EKRANDA: ...]` notu yaz. İzleyecek bir şey yoksa video podcast'e döner.
4. **Teslim:** Kancanın vaadini açıkça ver ve verdiğini söyle ("işte o şablon, açıklamada").
5. **Kapanış:** Tek bir çağrı.

## Teslim edilecekler
- En iyi iki kanca ve araç çıktıları
- Bölüm bölüm senaryo, her bölümde `[EKRANDA: ...]`
- Süre tahmini: kelime sayısı ÷ dakikadaki kelime sayısı (`esikler.md`). Türkçe için hız doğrulanmadı; kullanıcının kendi hızını sor.
- Kazanan kancanın kalıbı ve bu fikre neden uyduğu, tek satır

## Araç neye bakar
| Özellik | Var sayılır | Yoksa ne yapılır |
|---|---|---|
| Somutluk | Sayı ya da ad var, belirsiz sıfat yok | Bir sıfatı sayı, ad ya da tarihle değiştir |
| Hitap | İlk 6 kelimede sen/siz, 2. kişi fiil eki (-sın, -sınız), olumsuz buyruk (-mayın) ya da ilk kelimede buyruk ("Bak,") | İzleyiciye doğrudan seslen |
| Bedel | Kayıp ya da risk kelimesi ve bir sayı | Devam etmenin neye mal olduğunu söyle |
| Merak | Soru kelimesi ya da soru işareti; cümle kendini cevaplamıyor | "Çünkü", "bu yüzden" ile başlayan yarıyı at |
| Uzunluk | Türkçe 7–20, İngilizce 9–24 kelime | Sesli oku, nefesin bittiği yerde kes |

Sıralama en zayıf özelliğe göre yapılır. Dört özelliği güçlü ama biri eksik olan açılış, eksik olan yerden izleyici kaybeder.

**Bilinen sınırlar:** "Kanalın" gibi bir kelime hem "senin kanalın" hem de "kanalın adı" (ilgi tamlaması) olabilir; araç bu eki tek başına hitap saymaz. Fiil eki (-ıyorsun, -arsın, -amazsın) yalnızca en az 7 harfli kelimede aranır; bu yüzden "dersin" (sen dersin) sayılmaz, "Bu dersin konusu" da yanlışlıkla hitap sayılmaz. "Göstersin" gibi 3. kişi emir kipi ve "Mersin" gibi özel adlar `lang_tr.json` içindeki istisna listesine eklenir.

## Kalıplar
Kalıp adı yalnızca kelimelere bakılarak verilir; videonun neden izlendiğini açıklamaz.

| Kalıp | Biçim | Ne zaman tutmaz |
|---|---|---|
| Çarpıcı sayı | Bilinmeyen bir sayı, ardından anlamı | Sayının kaynağı söylenemiyorsa |
| Sonuç kanıtı | Ulaşılan sonuç, sonra nasıl | Sonuç gösterilemiyorsa |
| Hata uyarısı | İzleyicinin şu an yaptığı hata | Hata yaygın değilse |
| Ters köşe | Herkesin öğüdü, sonra neden yanlış | Kanıt hemen gelmezse |
| Açık soru | Tek, kendi başına cevaplanamayan soru | Cevap açıksa ya da evet/hayırsa |
| Denedim | Belli bir süre denenen şey | Deneme yapılmadıysa |
| Saat işliyor | Belli bir sürede ne verileceği | Söz tutulmazsa |
| Karşılaştırma | İki seçenek yan yana | Kazanan baştan belliyse |
| Perde arkası | Anlatılmayan bir işleyiş | Zaten biliniyorsa |
| Sayılı liste | Madde sayısı, en iyisi sonda | Maddeler zayıfsa |
| Hikâye açılışı | Belli bir an: ne zaman, nerede | Başlığa 15 saniyede bağlanmazsa |
| Doğrudan hitap | "Eğer ... -sa" durumu | Durum çok genelse |

Tam tanım ve desenler: `scripts/hook_patterns.json`.
