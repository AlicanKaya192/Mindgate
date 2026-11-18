# Tetikleme ölçümü: uzman-oyun

Yöntem: her istek becerilerin `description` metnine karşı okunur (`beceri-yazma` § Test et, madde 4). Bu ölçüm açıklama metnini düzeltmeye yarar; gerçek oturumdaki yüklemeyi kanıtlamaz.

| # | İstek | Tetiklemeli mi | Gerekçe |
|---|---|---|---|
| 1 | Godot'ta karakterim duvara yapışıyor, `is_on_floor` hep false dönüyor | evet | Motor adı ve motorda hata ayıklama |
| 2 | Phaser ile platform oyunu yapıyorum, zıplama ve yerçekimi değerlerini önerir misin | evet | Motor adı ve platform türü |
| 3 | Unity'deki düşmanım için davranış ağacı mı durum makinesi mi kullanayım | evet | Düşman yapay zekâsı |
| 4 | Roguelike haritam aynı tohumla her seferinde farklı çıkıyor | evet | Tür ve prosedürel üretim |
| 5 | pygame oyunuma kayıt sistemi ekle, kayıt bozulunca oyun çökmesin | evet | Motor adı ve kayıt sistemi |
| 6 | Hafta sonu 48 saatlik bir game jam'e katılıyorum, nasıl planlayayım | evet | Game jam iş akışı |
| 7 | Oyunumu itch.io'ya yüklemeden önce neyi denetlemeliyim | evet | itch.io yayını |
| 8 | Roblox oyunumda oyuncular parayı hileyle artırıyor, nasıl önlerim | evet | Roblox; yanında uzman-guvenlik (oyun içi ekonomi) |
| 9 | Bu ateş topu için 8 karelik bir sprite sheet çiz | hayır | Yalnızca sprite isteği; oyun geliştirme değil |
| 10 | Patlama efektini mavi bir paletle yeniden renklendir | hayır | Var olan bir efekti yeniden renklendirme; oyun geliştirme değil |
| 11 | Oyunumun tanıtım sitesi için bir açılış sayfası tasarla | hayır | uzman-tasarim: oyun dışı sayfa tasarımı |
| 12 | Tanıtım sitemdeki iletişim formunu React ile yaz, erişilebilir olsun | hayır | uzman-frontend: oyun dışı web arayüzü |
| 13 | Turnuva sonuçlarını gösteren web panosunun renk ve yazı sistemini kur | hayır | uzman-tasarim: tasarım sistemi, oyun değil |
| 14 | Pekiştirmeli öğrenmeyle Atari oyunu oynayan bir ajan eğitmek istiyorum | hayır | uzman-ml: model eğitimi; oyun yapılmıyor |
| 15 | Satranç maçı verisinden kazananı tahmin eden model kur, sızıntıya bak | hayır | uzman-ml: veri ve model değerlendirmesi |
| 16 | Oyuncu davranış verisinde kümeleme yapıp oyuncu tiplerini çıkar | hayır | uzman-ml: veri bilimi analizi |

Tarih: 2026-11-18

Sonuç (merkez, açıklamaya karşı okuma): 15/16 doğru. 1–8 açıklamadaki durumlarla eşleşiyor; 9–10 yalnızca efekt ve sprite isteği olduğu için oyun geliştirme sayılmıyor; 11–13, 15, 16 oyun geliştirme içermiyor. 14 belirsiz: "oyun" kelimesi var, istek oyun yapmak değil model eğitmek; açıklama bunu açıkça dışlamıyor. Gerçek oturumdaki yükleme ölçülmedi. Aynı gün açıklamaya "Oyun oynayan bir ajan eğitmek ya da oyun verisini analiz etmek için uzman-ml" eklendi; 14 bununla dışlanıyor (yeniden okuma: 16/16).
