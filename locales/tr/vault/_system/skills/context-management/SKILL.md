---
name: baglam-yonetimi
description: Uzun bir oturumda bağlam dolmaya yaklaştığında, büyük bir okuma ya da araç çıktısı geldiğinde, oturum özeti ya da devir notu yazarken veya model önceki bilgiyi karıştırmaya başladığında kullan. Ana sohbet yükler; bakımcı oturum kaydı işlerken yükleyebilir.
---

Yöntem becerisi (ajan değil). Kural #16 (bağlam sıfırlanmadan önce kayıt) ve vault `CLAUDE.md` §7.8'in ayrıntısıdır.

## Ölçü: iş başına harcama
Mesaj başına harcamaya değil, işin baştan sona toplam harcamasına bak. Özet; dosya yolunu, hata mesajını ya da kararın gerekçesini düşürürse aynı dosyalar yeniden okunur ve kazanılandan fazlası kaybedilir. Aynı dosyayı tekrar tekrar okumak, özetin kötü olduğunun işaretidir.

## Eşikler ve otomatik düzen
- **%40 (iş sonu):** Hook bir kez "iş sürüyorsa devam et" der. Bir iş az önce bittiyse ve yeni konuya geçilecekse: devir kartı, işlenmemişleri vault'a işle, kullanıcıya yeni sohbet ya da `/clear` öner. `/clear` bedavadır; `/compact` bütün konuşmayı okuduğu için büyük bir istektir ve kullanılmış becerileri geri getirir. **Süren işte erken sıkıştırma önerilmez:** yarım işte özet dosya yollarını ve hata ayrıntısını düşürür, aynı dosyalar yeniden okunur ve kazanılandan fazlası kaybedilir.
- **%60 (uyarı):** Stop hook'u (`context_check.py stop`) bir kez "devir kartını yaz, işlenmemişleri vault'a işle" der. Yapılacaklar sırasıyla:
  1. Devir kartı: yarım kalan iş ve tam olarak kaldığın adım, sıradaki adımlar, açık sorular.
  2. Konuşulup vault'a işlenmemiş fikir, karar, sorun/çözüm, ilerleme ve kurallar.
  3. Log, commit. Sonra işe devam.
- **%70 (sıkıştırma):** Claude Code kendiliğinden sıkıştırır (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`, değer `ayarlar.json` → `context`). PreCompact hook'u özete "neyi koru" talimatını ekler, PostCompact hook'u özeti `gelen/oturumlar/` altına kaydeder. Sıkıştırmadan sonra SessionStart hatırlatmasıyla kayıt okunur, eksikler işlenir.
- **Tek sohbet, tek iş:** Bir iş (bölüm, sürüm, özellik) bitince devir kartını yaz ve kullanıcıya yeni sohbet öner. Haftalarca süren sohbet her mesajda yüz binlerce tokeni yeniden okur (ölçüm: `cost.py`).

## Zorunlu bölümlü özet
Oturum durumunu (vault'a, ilerleme dosyasına ya da devir notuna) yazarken şu bölümler **boş bırakılmaz**:
- **Amaç:** kullanıcı ne istiyor (kendi sözleriyle).
- **Dosyalar:**
  - oluşturulanlar (tam yol)
  - değişenler (ne değişti, fonksiyon adıyla)
  - okunup değişmeyenler
- **Kararlar ve gerekçeleri.**
- **Şu anki durum:**
  - kanıtıyla, ör. "94/94 test geçti"
  - açık hatalar, hata mesajı aynen
- **Bekleyenler:** kullanıcıdan beklenen onay ve sorular. `gelen/bekleyenler.md` ile aynı numaralar kullanılır.
- **Sıradaki adımlar.**

Bölüm, kontrol listesi gibi çalışır: boş kalan bölüm neyin unutulduğunu gösterir. Özet her seferinde baştan üretilmez. Yalnızca yeni kısım özetlenir ve var olan bölümlere eklenir; baştan üretmek her turda ayrıntı kaybettirir.

## Özeti sına (yoklama soruları)
Özetten sonra kendine sor; özete bakarak cevaplanamıyorsa özet eksiktir:
- Hatırlama: "Asıl hata mesajı neydi?"
- Dosya izi: "Hangi dosyaları değiştirdik?"
- Devam: "Sıradaki adım ne?"
- Karar: "X konusunda ne karar verdik, neden?"

## Büyük çıktıyı dosyaya al
- Büyük araç çıktısını (test listesi, tarama sonucu, uzun log) scratchpad'e yaz. Bağlama yalnızca kısa özet ve dosya yolu girsin, gerekince `grep` ya da satır aralığıyla oku.
- Çok dosyalı okumayı `kasif` ajanına ver. Ona kısa ve kaynaklı rapor istediğini söyle.

## Bağlam bozulması belirtileri
| Belirti | Ne yapılır |
|---|---|
| Ortada kaybolma: uzun bağlamın ortasındaki bilgi unutulur | Kritik bilgiyi (kurallar, amaç) başa ya da sona taşı; vault'tan yeniden oku |
| Zehirlenme: yanlış bir bilgi tekrar tekrar kullanılır | Yanlışın üstüne düzeltme ekleme. Yanlış kısmı açıkça geçersiz say, doğrusunu kaynaktan yeniden oku |
| Dağınıklık: alakasız içerik dikkati böler | Gereksizi yükleme, araçla gerektiğinde getir |
| Çelişki: iki kaynak farklı diyor | Kaynak önceliği: kullanıcının son sözü > vault kuralı ve ADR > eski not > hafıza. Çelişkiyi yaz (`> [!warning] Çelişki`) |

## Fikir kaynakları
- muratcankoylan/Agent-Skills-for-Context-Engineering (MIT): `context-compression`, `context-degradation`, `filesystem-context`. İndirilen kopyadan okundu; resmî depoyla eşleşmesi doğrulanmadı.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
