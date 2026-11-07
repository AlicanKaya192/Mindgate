---
name: sentetik-musteri-testi
description: Bir ürün ya da iş fikrini, teklifi, fiyatı veya mesajı gerçek müşteriyle görüşmeden önce sanal müşteri paneline (sentetik persona) sınatırken kullan. "Bu fikir tutar mı", "müşteri ne itiraz eder", "hangi fikir daha güçlü", "fiyatı kaldırır mı" soruları ve fikir karşılaştırması dahil. Ana sohbet (merkezî ajan) yükler.
---

Yöntem becerisi (ajan değil). Bağlı kurallar: #24 (uydurma yok), #10 ve #28 (ajanlar), #27 (dış veri), #3 (kişisel veri yok).

**Temel uyarı:** Sentetik müşteri talep kanıtı değildir. Yalnızca itiraz, zayıf nokta ve hipotez üretir; dil modelleri olumluya kayar. Rapor "tutar" dese bile son adım gerçek müşteriyle ucuz bir testtir. Sonuç yüzde ya da pazar payı diye sunulmaz; sayılar "N personanın K'sı" diye yazılır.

## 1. Fikri test edilebilir yaz
Her fikir için tek kart: müşteri (rol, şirket büyüklüğü, ülke), sorun, bugünkü çözüm, teklif (bir cümle), fiyat, kanal. Kart yoksa önce kartı yaz; belirsiz alanı "varsayım" diye işaretle.

## 2. Personaları kanıttan kur
- Her persona bir kanıta dayanır: mağaza yorumu, topluluk gönderisi, mevzuat verisi, araştırma notu. Kanıtın notu ya da URL'si kartta durur; kanıtsız alan "varsayım" diye işaretlenir. Pazar tarifinden uydurulan persona aynı akıcılıkla cevap verir ama arkasında bir şey yoktur.
- Alanlar: rol, şirket (büyüklük, ülke, sektör), bugün kullandığı araç ve harcama, son yaşadığı somut olay, karar biçimi, tutum.
- **Tutum karışımı zorunlu:** Her panelde en az bir şüpheci, bir "rakibi zaten kullanıyor", bir "bütçesi yok ya da öncelik değil" olur. Hepsi hevesli panel geçersizdir.
- Gerçek kişi adı, şirket adı ya da iletişim bilgisi kullanılmaz; adlar uydurma ve açıkça sanal.
- Panel kontrolü: rol ve ülke tekrarı yok, tutum karışımı tam, her kartta kanıt ya da "varsayım" etiketi var. Eksikse paneli yeniden kur.

## 3. Bağımsız sor
- Her persona ayrı bir ajanda cevap verir (`gorev-yazma`; model açık yazılır, varsayılan Haiku; aynı anda en çok 3). Persona diğerlerini, bizim hangi fikri tuttuğumuzu ve öteki fikirleri görmez.
- Görev metni: persona kartı, fikir kartı, sorular, "araç kullanma, web'e çıkma, dosya yazma", "kibar olmak zorunda değilsin; ilgini çekmiyorsa söyle", JSON cevap biçimi.
- **Soru sırası (Mom Test usulü):** Önce geçmiş davranış, sonra teklif.
  1. Bu sorunu en son ne zaman yaşadın, ne yaptın?
  2. Sana neye mal oluyor (zaman, para, ceza)? Bugün kime ne ödüyorsun?
  3. Daha önce çözmeye çalıştın mı, neden bıraktın?
  4. (Teklif gösterilir) İlk tepkin? En büyük itirazın?
  5. Bu fiyata bugün ne yapardın: hiçbir şey / denemeye bakarım / ücretsiz pilot isterim / ön ödeme yaparım?
  6. Seni vazgeçirecek tek şey ne? Fikrini değiştirecek tek şey ne?
- JSON: `{"persona", "son_olay", "maliyet", "bugunku_cozum", "ilk_tepki", "en_buyuk_itiraz", "taahhut": "yok|bakarim|pilot|on_odeme", "satin_alma_1_5", "vazgecirir", "ikna_eder", "duygu"}`. Bozuk JSON bir kez yeniden istenir.

## 4. Çöz ve karar ver
- Olumlu sinyal yalnızca geçmiş davranışa ya da taahhüde bağlıysa sayılır ("son olay" somut, "maliyet" ölçülebilir, taahhüt pilot ya da ön ödeme). "Harika fikir" sinyal değildir.
- Karar kuralı (panel başına):
  - **Güçlü:** Personaların yarısından çoğunda somut son olay var ve en az biri pilot ya da ön ödeme diyor; şüpheci personanın itirazı ürünle çözülebilir.
  - **Zayıf:** Sorun gerçek ama taahhüt yok ya da itiraz "rakip zaten yapıyor" ve fark açık değil.
  - **Tutmaz:** Çoğunda somut olay yok ya da itiraz ürünün çekirdeğini vuruyor (güven, sorumluluk, bedava alternatif).
- İtirazları grupla, tekrar edenleri say, her gruba bir alıntı koy (persona adıyla, kısa).

## 5. Gerçek dünya testi öner
Her fikir için en ucuz gerçek test: 5 gerçek görüşme (kimle, nerede bulunur), açılış sayfası ve bekleme listesi, ön satış ya da ücretli pilot teklifi. Başarı ölçütü önceden yazılır (ör. "10 görüşmede 3 pilot").

## 6. Rapor
`arastirmalar/YYYY-MM-DD-<konu>-sentetik-test.md`: yöntem (model, persona sayısı, tarih), panel tablosu (kanıt sütunuyla), fikir başına karar ve gerekçe, itiraz grupları, gerçek dünya testi, sınırlar. Her fikrin başında alanı bilmeyen birinin anlayacağı sade anlatım (ne, kim için, hangi dert, para nasıl gelir, temsilî örnek) ve raporda geçen terimler için sözlük olur. Ham JSON git dışı `_sistem/cikti/`'ye. Kullanılan ajanlar ajan günlüğüne.

## Bitirmeden doğrula
- [ ] Her personada kanıt ya da "varsayım" etiketi var; tutum karışımı tam.
- [ ] Personalar ayrı ajanlarda sorgulandı; hiçbir görev metninde bizim tercih ya da öteki fikirler yok.
- [ ] Karar, kuraldaki ölçütlere göre verildi; sayılar "N'nin K'sı" biçiminde.
- [ ] Raporun başında "talep kanıtı değildir" uyarısı ve her fikir için gerçek dünya testi var.
- [ ] Gerçek kişi ya da şirket adı, kişisel veri yok.

## Fikir kaynakları
- takechanman1228/claude-persona (MIT; github.com sayfası 29 Ekim 2026'da okundu, 60 yıldız): persona başına yalıtılmış çağrı, tutum karışımı, panel doğrulaması, yapılandırılmış cevap, "yalnızca yön gösterir" uyarısı. Kodu, kurulum betiği ve `claude -p` alt süreçleri alınmadı.
- phuryn/pm-skills (MIT, 27,5 bin yıldız; sayfa okundu): riskli varsayım ve deney tasarımı fikri. Sentetik müşteri becerisi yok.
- Rob Fitzpatrick, "The Mom Test": geçmiş davranışı sor, iltifatı sinyal sayma.

## Dersler
<!-- Merkezî ajan doğrulanmış dersleri ekler: genel, yeniden kullanılabilir; proje adı ve tarih olmadan. -->
- Panel bir fikre "güçlü" dedikten sonra yapılan aramada hedef platformun kendisinin aynı servisi çok düşük fiyata çıkardığı bulundu. Rekabet ve platform taramasını panelden ÖNCE yap; özellikle son 6 ayda çıkanlara ve platformun kendi ürünlerine bak.
- Kullanıcı rapordaki alana özgü terimleri bilmediği için raporu anlayamadı. Rapor, okuyanın alanı bilmediği varsayılarak yazılır.
- Küçük model personaları "bakarım" cevabını çok veriyor; karar kuralında "bakarım" taahhüt sayılmamalı, yalnızca pilot ve ön ödeme sayılır (kural böyle, korunmalı).
