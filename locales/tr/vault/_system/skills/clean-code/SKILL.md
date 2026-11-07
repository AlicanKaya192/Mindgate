---
name: temiz-kod
description: Temiz kod (clean code) kuralları ve bitirmeden kontrol listesi. Kod yazarken, değiştirirken, önerirken ya da incelerken uygulanır (kural #30). Bütün ajanlara önceden yüklenir; ana sohbet de her kod işinde buna uyar.
---

Yöntem becerisi (ajan değil). Kaynak: Robert C. Martin, *Clean Code* (Prentice Hall, 2008); Python için PEP 8 (https://peps.python.org/pep-0008/). Kendi cümlelerimizle özet.

## Öncelik sırası
1. Projenin kendi kuralları, biçimlendiricisi ve linter'ı (`<proje>-kurallar.md`, PEP 8, ESLint, Prettier, `ruff`…) ve çevredeki kodun üslubu.
2. Bu liste.

Çelişirse projeninki geçerlidir. Kural #23 ve #25 geçerli: Temiz kod, **yazdığın ve dokunduğun** kod için zorunludur. Dokunmadığın kodu "temizlemek" istenmeyen iştir; gerekiyorsa öner, yapma.

## 1. İsimler
- Niyeti anlatsın: `gun_sayisi`, `d` değil. Aranabilir ve telaffuz edilebilir olsun. Tek harf yalnızca kısa döngü sayacında.
- Sınıf ve değişken isim, fonksiyon fiil (`hesapla_ortalama`). Mantıksal değer soru gibi (`aktif_mi`, `is_valid`).
- Aynı kavrama her yerde aynı kelime (`getir` mi `al` mı, birini seç). Projenin dili (Türkçe ya da İngilizce) karışmasın.
- Sihirli sayı ya da metin yok: adlandırılmış sabit ya da yapılandırma (`MAKS_DENEME = 3`).

## 2. Fonksiyonlar
- Küçük ve **tek iş** yapar. Bir fonksiyonda tek soyutlama seviyesi olur.
- Az parametre: 0–2 ideal. 3'ten fazlaysa bir nesne ya da veri sınıfında topla.
- Bayrak (boolean) parametresiyle iki farklı iş yapma; iki fonksiyona böl.
- Gizli yan etki yok; varsa adında belli olsun. Komut (durum değiştirir) ile sorgu (değer döndürür) ayrı.
- Derin iç içe `if` yerine erken dönüş (guard clause).

## 3. Yorumlar
- Kod kendini anlatsın. Yorum **neden**i açıklar, ne yapıldığını değil.
- Yorum satırına alınmış ölü kod, yanlış ya da eskimiş yorum yok. Kodu değiştirince yorumu da güncelle.
- Herkese açık API'de kısa docstring. Yorumda ve kodda yapay zekâ izi yok (#14).

## 4. Hata yönetimi
- Hata kodu döndürmek yerine istisna (exception). Hata **yutulmaz** (`except: pass`, boş `catch` yok).
- Hata mesajı bağlam taşır (ne, hangi girdi). İçinde sır yok (#18).
- `None`/`null` döndürme ve geçirme yerine boş koleksiyon, `Optional` ya da açık bir istisna.
- Girdi sınırda (API, CLI, dosya) doğrulanır; içeride tekrar tekrar kontrol edilmez.

## 5. Sınıflar ve modüller
- Tek sorumluluk (SRP): değişmesi için tek bir sebebi olsun.
- Yüksek bağlılık (cohesion), düşük bağımlılık (coupling). Somut sınıfa değil arayüze bağımlı ol (DIP).
- Kalıtım yerine kompozisyon tercih edilir.
- Dış kütüphaneyi ince bir sarmalayıcının arkasına koy; değişince tek yer etkilensin.

## 6. Sadelik
- **DRY:** Aynı bilgi ve mantık tek yerde.
- **Erken soyutlama yok (YAGNI):** Gerçek ihtiyaç ve tekrar görülmeden genelleme yapma. Üçüncü tekrarda ortaklaştır.
- **KISS:** En basit çalışan çözüm.
- Ölü kod, kullanılmayan import, değişken ya da parametre bırakma.

## 7. Biçim
- Projenin biçimlendiricisini çalıştır. İlgili kod birbirine yakın, dosya yukarıdan aşağı okunur (önce üst düzey, sonra ayrıntı).
- Satır ve dosya uzunluğu makul; bir dosya tek konuyu taşır.

## 8. Testler
- **F.I.R.S.T.:** hızlı, birbirinden bağımsız, her ortamda tekrarlanabilir, kendi kendini doğrulayan (geçti/kaldı), kodla birlikte yazılan.
- Test başına tek kavram. Hazırla → çalıştır → doğrula (Arrange–Act–Assert) düzeni.
- Test kodu da temiz koddur.

## Bitirmeden kontrol (her kod işinde)
- [ ] İsimler niyeti anlatıyor; sihirli sayı yok.
- [ ] Her fonksiyon tek iş yapıyor; bayrak parametresi ve derin iç içelik yok.
- [ ] Hata yutulmuyor; mesajlar anlamlı.
- [ ] Tekrar yok, gereksiz soyutlama yok, ölü kod ve kullanılmayan import yok.
- [ ] Yorumlar "neden"i anlatıyor; eskimiş yorum yok.
- [ ] Biçimlendirici/linter çalıştı (varsa) ve testler geçti. Çıktı gösterildi (#24).
- [ ] Değişiklik istenen kapsamın dışına taşmadı (#23, #25).

## İncelemede (inceleyici)
Temiz kod ihlali bulgudur. Önemi genelde **düşük** ya da **orta**dır; doğruluk ve güvenlik bulgularının önüne geçmez. Her bulguda hangi kuralın çiğnendiğini yaz (ör. "2. tek iş").

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
