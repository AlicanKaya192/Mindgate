# Eşikler ve kaynakları

Resmî olanlar YouTube Yardım'dan okundu (13 Kasım 2026). Geri kalanlar sezgiseldir; kanal verisiyle doğrulanmadı. Bir eşik değişirse önce bu tabloyu, sonra ilgili betikteki sabiti güncelle.

| Eşik | Değer | Nerede | Kaynak | Durum |
|---|---|---|---|---|
| Başlık uzunluğu | en çok 100 karakter | `title_check.py` `YOUTUBE_TITLE_LIMIT` | YouTube Yardım, "Edit video settings" (support.google.com/youtube/answer/57404) | Resmî |
| Açıklama uzunluğu | en çok 5.000 karakter | `bolumler-arama.md` | Aynı sayfa | Resmî |
| Etiketlerin etkisi | keşifte çok küçük rol | `bolumler-arama.md` | Aynı sayfa | Resmî |
| Bölüm kuralları | ilk 00:00; en az 3, artan; her biri en az 10 sn | `chapters.py` | YouTube Yardım, "Video Chapters" (support.google.com/youtube/answer/9884579) | Resmî |
| Aramada kesilme | 60 karakter | `title_check.py` `SEARCH_CUT` | Orijinal paketteki gözlem (Fikir kaynakları) | Doğrulanmadı |
| Mobil akışta kesilme | 40 karakter | `title_check.py` `MOBILE_CUT` | Orijinal paketteki gözlem (Fikir kaynakları) | Doğrulanmadı |
| Büyük harfli kelime | en çok 2 (4+ harfli) | `title_check.py` | Yöntem | Sezgisel |
| Küçük resim metni | en çok 3 kelime | `title_check.py` | Yöntem | Sezgisel |
| Kanca uzunluğu (İngilizce) | 9–24 kelime | `lang_en.json` `hook_words` | Orijinal paket: ~150 kelime/dk ile 10 sn | Doğrulanmadı |
| Kanca uzunluğu (Türkçe) | 7–20 kelime | `lang_tr.json` `hook_words` | Eklemeli (agglutinative) dil için kısaltıldı | Doğrulanmadı |
| Hitap penceresi | ilk 6 kelime | `hook_check.py` `ADDRESS_WINDOW` | Yöntem | Sezgisel |
| Konuşma hızı | ~150 kelime/dk (İngilizce) | `senaryo.md` süre tahmini | Yaygın kabul | Türkçe için bilinmiyor; kullanıcıya sor |
| Ölü boşluk | 0,6 sn, iki yanda 0,15 sn nefes | `dead_air.py` | Bu paketin varsayılanı | Konuşmacıya göre ayarla |
| Short uzunluğu | 20–55 sn | `kurgu.md` | Yöntem | Sezgisel |
| Açılış kaybı | ilk 30 sn | `kanal.md` | Yöntem | Sezgisel; "sağlıklı" oran verilmez |
| Ortanca için video | kanal başına en az 4 | `kanal.md` | Yöntem | Sezgisel |
| Haftalık yükleme | 1 ana + 1 hafif + 3 Short | `kanal.md` | Yöntem | Sezgisel |
