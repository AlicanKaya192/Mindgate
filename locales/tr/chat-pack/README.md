# Sohbet uygulaması paketi

**Kapılar, otomatik kayıt ve betikler sohbet uygulamalarında çalışmaz.** Bu paket Mindgate'in kurallarını ve not biçimini ChatGPT, Gemini ve benzeri sohbet uygulamalarında kullanmanızı sağlar. Orada kurallar yalnızca yazılı talimattır: hiçbir şey zararlı bir komutu engellemez, sır taraması yapmaz ve vault'unuza kendiliğinden bir şey kaydetmez.

## Pakette ne var
| Dosya | Ne yapılır |
|---|---|
| `talimat-kisa.txt` | Uygulamanın kısa talimata izin verdiği yere yapıştırın (en çok 1.500 karakter). |
| `talimat-uzun.txt` | Daha uzun talimata izin verilen yere yapıştırın (en çok 5.000 karakter); örneğin bir projenin ya da özel bir asistanın talimatına. İki metinden yalnızca birini kullanın. |
| `kurallar.md`, `sema.md`, `sablonlar.md` | Aynı projeye ya da asistana bilgi dosyası olarak yükleyin. |

Menü adları ve sınırlar uygulama sürümüne ve plana göre değişir; bu yüzden bu kılavuz menü adı vermez. Uzun metin sığmazsa kısasını kullanın.

## Paketi üretmek
`setup/` klasöründen:

```
py -3 -I chat_pack.py --language tr --out <yeni klasör>
```

Klasör yeni ya da boş olmalı. `--language en` İngilizce paketi üretir. Üretici önce her dosyayı sır taramasından geçirir, bir şey bulursa hiçbir şey yazmaz.

## Notları elle kaydetmek
1. Uygulama not önerince okuyun: doğru mu, içinde özel bir bilgi var mı?
2. Obsidian'da uygulamanın verdiği yolda (örneğin `gelen/` altında) dosyayı açın ve notu yapıştırın.
3. Log satırı `log.md`'nin sonuna, bekleyen madde `gelen/bekleyenler.md`'nin sonuna eklenir.
4. Mindgate'i Claude Code ile de kullanıyorsanız sonra yeni notları index'e eklemesini ve linklerini denetlemesini isteyebilirsiniz.

## Burada çalışmayanlar
| Mindgate parçası | Sohbet uygulamalarında |
|---|---|
| Komut, yazma ve site kapıları | Yok. Uygulama zararlı bir komut önerebilir; çalıştırıp çalıştırmamak size kalır. |
| Sır taraması | Yok. Notları kaydetmeden önce kendiniz kontrol edin. |
| Oturum kayıtları, devir kartları, bağlam ölçümü | Yok. |
| Betikler (arama, sağlık, graf) | Yok. Uygulama vault'unuzu okuyamaz. |
| Beceriler ve ajanlar | Kurulmaz. |
