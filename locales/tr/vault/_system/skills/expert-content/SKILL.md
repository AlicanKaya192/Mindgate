---
name: uzman-icerik
description: Kişisel teknik içerik yazımı uzmanlık paketi. Kullanıcının ağzından blog yazısı, LinkedIn gönderisi, GitHub README ya da portfolio sayfası metni taslağı yazarken veya düzenlerken, yayın hattı (taslaklar) için konu seçerken ya da bir metinden yapay zekâ izini ayıklarken yükle. Satış ve pazarlama metni için değildir.
---

Uzmanlık paketi (ajan değil). Yayın hattı kuralları önce gelir: vault `CLAUDE.md` §7.9 ve `_sablonlar/taslak.md`.
- Metin kullanıcının ağzından, birinci tekil şahısla yazılır. Yapay zekâ imzası ya da izi olmaz (#14).
- Claude hiçbir şeyi yayınlamaz, paylaşmaz, zamanlamaz. Metnin sahibi kullanıcıdır: Claude önerir, o karar verir.

## Yazmadan önce
1. **Okur kim?** Öğrenci, ML mühendisi, işe alımcı… Okurun sorunu ne, onu hangi kelimelerle anlatıyor?
2. **Tek mesaj:** Okuyan bu yazıdan ne alıp gidecek? Tek cümleyle yaz (taslak şablonundaki "Tek cümlelik mesaj").
3. **Yeni ne var?** Benzer yazılarda olmayan şeyi tek cümleyle yaz. Bu genelde kullanıcının kendi deneyimidir: ölçüm, hata, düzeltme. Yazamıyorsan konu henüz hazır değildir.
4. **Kanıt:** Vault'ta ne var? Sorun notları (`sorunlar`), deney notları, ilerleme günlükleri, komut çıktıları, ölçüm tabloları. Sayılar yalnızca bu notlardan alınır.
5. **Okurdan istenen tek şey:** denemesi, kodu incelemesi, yorum yazması.

## Yazım ilkeleri
- Önce açıklık gelir, zekice olmak sonra gelir. Basit kelime, etken çatı, kesin ifade.
- Özellik değil kazanç anlatılır: Okur ne öğrenecek, ne yapabilecek?
- **Somutluk:** Belirsiz ifade yerine ölçü yaz. "Hızlandı" değil, "eğitim süresi 40 dakikadan 12 dakikaya indi". Sayı vault notundan gelir.
- **Her iddianın kanıtı olur.** Kanıt yoksa iddiayı yumuşat ya da çıkar. Eksik kanıtı taslakta `[KANIT GEREK: …]` diye işaretle. Uydurma sayı ve kaynak yok (#24).
- Açılış okurun sorunuyla ya da varılan sonuçla başlar. "Merhaba, bugün size…" ya da uzun bir geçmiş anlatısıyla değil.
- Paragraf 2–4 cümledir; her bölümde tek fikir olur. Metni sesli okuyunca takılan yeri düzelt.
- Okurun ve hata mesajının dili aynen kullanılabilir (ör. `CUDA out of memory`).
- Duygu mesaja hizmet eder. Aciliyet, kıtlık, "kaçırma" korkusu gibi satış kalıpları kullanılmaz.

## Yapay zekâ izi: bunları yazma
- "X değil, Y" diye karşıtlıkla açmak. Y'yi gerekçesiyle doğrudan söyle.
- "X yok, Y yok, Z yok" diye olumsuzluk sıralamak. Ne olduğunu söyle.
- Cümleyi bitirdikten sonra virgülle ek ekleyip uzatmak.
- Kendi sorusunu cevaplamak ("Sonuç mu? 3 kat hız.") ya da iki noktayla sonucu açıklamak.
- Hazır açılışlar: "Günümüzün hızla değişen dünyasında", "İşte mesele şu", "…'ın yeni hâli", "…ın gücünü keşfedin".
- İçi boş sözler: "kusursuz", "güçlü", "devrim niteliğinde", "sorunsuz", "bir üst seviyeye". Yerine olguyu yaz.
- Gönderilerde uzun tire (—) kullanılmaz. Nokta ya da satır sonu kullanılır.
- Her satırda tek cümle ("broetry"), satır başında emoji, etkileşim tuzağı ("Katılıyor musunuz?", "Bunu bir daha okuyun").
- Gerçek bir hikâye yokken "açık konuşayım, çok korkmuştum" demek. Gerçek deneyim varsa yaz, yoksa yazma.
- Bölüm başına en fazla bir üçlü liste ve bir yarım cümle.

Kelime değiştirmek yeni bir iz üretir. Sorunlu cümleyi olgudan yola çıkarak yeniden yaz.

## Düzenleme: yedi geçiş
Her geçişte yalnızca bir şeye bak. Önce sorunları işaretle, sonra düzelt.
1. **Netlik:** Okur her cümleyi ilk okuyuşta anlıyor mu?
2. **Ses:** "Ben" ile "biz" karışıyor mu? Ton baştan sona kullanıcı gibi mi?
3. **"Ne olmuş yani?":** Her iddiadan sonra "bu okur için neden önemli?" sorusunun cevabı var mı?
4. **Kanıt:** Her iddianın kaynağı ya da ölçümü var mı?
5. **Somutluk:** Belirsiz kelimeler ölçüye çevrildi mi?
6. **Duygu:** Duygu mesaja hizmet ediyor mu, yoksa abartı mı?
7. **İtirazlar:** Okurun aklına gelecek "ama…" sorularına cevap var mı?

Son kontrol: taslak şablonundaki liste. Gizli bilgi yok (#18), yapay zekâ izi yok, sayılar notlarla tutarlı, bağlantılar çalışıyor.

## Platforma göre
- **Teknik blog:** Sorun → denenenler → çözüm → sonuç → öğrenilenler (vaka yapısı). Kod parçası, ölçüm tablosu ve hata çıktısı kullanılır.
  - Alt başlıklar tek başına okunduğunda da anlaşılır olsun.
  - Yayın ve güncelleme tarihi görünsün.
  - Birincil kaynağa bağlantı verilsin.
- **LinkedIn:**
  - **Kanca:** İlk satırda gerçek bir olgu, sayı ya da hikâye.
  - **Gövde:** Normal paragraflar; birden fazla liste yok.
  - **Kapanış:** Sonuç cümlesi ya da cevabı gerçekten merak edilen tek soru.
  - Bağlantıyı gövdeye değil ilk yoruma koymak kaynağın önerisidir.
  - Öğrenme yolculuğunu belgelemek, öğrenmekte olan biri için uygun bir kalıptır.
- **README / portfolio:**
  - İlk paragraf: proje ne yapar, kimin işine yarar.
  - Sonra: nasıl çalıştırılır (komutlar), sonuç ve ölçüm, mimari kısa, sınırlar.
  - Yapay zekâ ile üretildi ibaresi olmaz (#14).

## Konu seçimi (yayın hattı fikir havuzu)
- Kaynaklar: çözülen sorunlar, ölçülmüş deney sonuçları, biten proje aşamaları, güncel projelere ait notlar.
- İki tür içerik:
  - **Aranabilir:** nasıl yapılır, hata çözümü.
  - **Paylaşılabilir:** deneyim, görüş, öğrenilen ders.
- **Konu kümeleri:** 3–5 ana alan (ör. ML, LLM ajanları, Python araçları). Her yazı bir kümeye bağlanır.
- **Öncelik:** Bu sorunla kaç kez karşılaşıldı? Elde kanıt var mı? Kullanıcının hedeflerine (bkz. `ben/profil.md`) ne kadar uyuyor?
- Adaylar [[taslaklar]] sayfasındaki "Fikir havuzu"na yazılır. Kullanıcı seçerse taslak `taslaklar/`'a yazılır.

## Kalite (deneyim, uzmanlık, güven)
- **Deneyim gösterilir:** kendi kodu, ölçümü, hatası ve düzeltmesi.
- **Uzmanlık:** İddialar doğru ve kaynaklı; teknik derinlik okura uygun.
- **Güven:** tarih, düzeltme notu, birincil kaynak.
- **İnce içerik işaretleri:** genel ifadeler, özgün içgörü yok, her bölüm aynı kalıpta, yanlış bilgi.
- Kelime sayısı hedefi konmaz; konu ne kadar gerektiriyorsa o kadar yazılır.

## Fikir kaynakları
- coreyhaines31/marketingskills (MIT, Corey Haines): `copywriting`, `copy-editing` (yedi geçiş), `content-strategy`, `social`.
- agricidaniel/claude-seo (MIT): `seo-content` (deneyim, uzmanlık, güven).

İkisi de 13 Ekim 2026'da indirilen kopyalardan okundu; resmî depolarla eşleşmeleri doğrulanmadı. Şunlar alınmadı:
- satış kalıpları, soğuk ulaşım
- otomatik paylaşım ve zamanlama araçları, ücretli araçlar
- veri kazıma tarifleri
- izi gizleme betikleri
- doğrulanmamış istatistikler

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
