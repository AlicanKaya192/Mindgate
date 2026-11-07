# Sohbet uygulaması paketi

**Kapılar, otomatik kayıt ve betikler sohbet uygulamalarında çalışmaz.** Bu paket Mindgate'in kurallarını ve not biçimini ChatGPT, Gemini ve benzeri sohbet uygulamalarında kullanmanı sağlar. Orada kurallar yalnızca yazılı talimattır: hiçbir şey zararlı bir komutu engellemez, sır taraması yapmaz ve vault'una kendiliğinden bir şey kaydetmez.

## Pakette ne var
| Dosya | Ne yapılır |
|---|---|
| `talimat-kisa.txt` | Uygulamanın kısa talimata izin verdiği yere yapıştır (en çok 1.500 karakter). |
| `talimat-uzun.txt` | Daha uzun talimata izin verilen yere yapıştır (en çok 5.000 karakter); örneğin bir projenin ya da özel bir asistanın talimatına. İki metinden yalnızca birini kullan. |
| `kurallar.md`, `sema.md`, `sablonlar.md` | Aynı projeye ya da asistana bilgi dosyası olarak yükle. |

Menü adları ve sınırlar uygulama sürümüne ve plana göre değişir; bu yüzden bu kılavuz menü adı vermez. Uzun metin sığmazsa kısasını kullan.

## Paketi üretmek
`setup/` klasöründen:

```
py -3 -I chat_pack.py --language tr --out <yeni klasör>
```

Klasör yeni ya da boş olmalı. `--language en` İngilizce paketi üretir. Üretici önce her dosyayı sır taramasından geçirir, bir şey bulursa hiçbir şey yazmaz.

## Notları elle kaydetmek
1. Uygulama not önerince oku: doğru mu, içinde özel bir bilgi var mı?
2. Obsidian'da uygulamanın verdiği yolda (örneğin `gelen/` altında) dosyayı aç ve notu yapıştır.
3. Log satırı `log.md`'nin sonuna, bekleyen madde `gelen/bekleyenler.md`'nin sonuna eklenir.
4. Mindgate'i Claude Code ile de kullanıyorsan sonra yeni notları index'e eklemesini ve linklerini denetlemesini isteyebilirsin.

## Burada çalışmayanlar
| Mindgate parçası | Sohbet uygulamalarında |
|---|---|
| Komut, yazma ve site kapıları | Yok. Uygulama zararlı bir komut önerebilir; çalıştırıp çalıştırmamak sana kalır. |
| Sır taraması | Yok. Notları kaydetmeden önce kendin kontrol et. |
| Oturum kayıtları, devir kartları, bağlam ölçümü | Yok. |
| Betikler (arama, sağlık, graf) | Yok. Uygulama vault'unu okuyamaz. |
| Beceriler ve ajanlar | Kurulmaz. |
