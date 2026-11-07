---
name: sorgula
description: Kullanıcı "beni sorgula", "bana soru sor", "bunu birlikte netleştirelim" dediğinde ya da yeni bir proje, hedef veya kararın vault'taki bilgisi eksik kaldığında kullanıcıya tek tek soru sorup cevapları ilgili notlara yazar. Ana sohbet yükler.
---

Yöntem becerisi (ajan değil). Kurallar: #4 (profilde olanı sorma), #3 ve #18 (hassas bilgi yok), #15 (öğretme yok), #23 (yalnızca istenen konu), #24 (cevabı uydurma). Fikir kaynağı: "grill-me" deseni; kod alınmadı, kendi yöntemimiz.

Amaç: kullanıcının kafasındakini vault'a aktarmak. Asıl eksik çoğu zaman aramada değil, hiç yazılmamış bilgide.

## Adımlar
1. **Konuyu sınırla.** Neyin sorgulanacağını bir cümleyle yaz (ör. "bir uygulamanın sıradaki sürüm hedefleri"). Konu belirsizse tek soruyla netleştir.
2. **Önce oku, sonra sor.** `ben/profil.md`, ilgili proje sayfası, ADR'ler, [[bekleyenler]] ve `search.py "konu"`. Vault'ta, kodda ya da önceki cevapta olanı sorma. Kapanmış ya da "sonra bakacağım" denen konuyu açma (#12).
3. **Soru ağacını kafanda kur:** Önce ana karar, sonra ona bağlı ayrıntılar. Kullanıcıya gösterme; sırayla ilerle.
4. **Tek seferde bir soru** (en çok 3 kısa soru). Her soruda:
   - Neden sorduğunu yarım cümleyle söyle.
   - Seçenekler belliyse `AskUserQuestion` kullan; önerin varsa ilk seçenek olsun ve "(Önerilen)" yazsın.
   - Önerin bir tahminse öyle de: "bilmiyorum, tahminim şu".
5. **Cevabı hemen yaz.** Sohbet bitmeden kaybolmasın:
   - Kişisel tercih ve hedef → `ben/profil.md` (hassas bilgi yok)
   - Proje bilgisi → proje sayfası ya da `-ilerleme.md`; teknik karar → yeni ADR
   - Kullanıcının cümlesi anlam değişmeden; frontmatter'da `source_type: stated`
   - Yeni bilgi eskisiyle çelişiyorsa eskiyi silme; `invalid` + `replaced_by` (§5)
6. **Durma koşulu:** Soru ağacının dalları kapandı, kullanıcı "yeter" dedi ya da cevaplar tekrar etmeye başladı. Cevapsız kalan soru `records.py pending add --type question` ile bekleyenlere.
7. **Kapanış:** kullanıcıya kısa özet: ne öğrenildi, hangi notlar güncellendi, açık kalan soru. Sonra log (`profil` ya da `ilerleme`, `Kanıt:` ve `Öğrenilen:`), commit (uzak depo tanımlıysa push), isteğe bağlı pano: v1'de yok, [[beceriler]] sayacı.

## Yapma
- Sorgulamayı derse ya da quiz'e çevirme (#15). Kullanıcının kararını yeniden tartışma; yalnızca eksik ve çelişkiyi sor.
- Şifre, kimlik, adres, sağlık, banka, başkalarının özel bilgisi sorulmaz ve yazılmaz.
- Soru listesini topluca döküp "hepsini cevapla" deme.

## Bitirmeden doğrula
- [ ] Her cevap bir nota yazıldı, bağlantısı var; sohbette kalan bilgi yok.
- [ ] Vault'ta zaten olan bir şey sorulmadı.
- [ ] Açık sorular bekleyenlerde.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
