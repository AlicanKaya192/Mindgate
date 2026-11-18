# Godot

Kaynak paket Godot 4.7.2'yi hedefliyor; sürüm ve davranış bilgileri sahibin 11 Kasım 2026 beyanıdır, bağımsız doğrulanmadı. Projenin sürümünü `project.godot`'tan oku; farklıysa bu dosyadaki API'yi körü körüne uygulama.

## Doğrulama zinciri
**Kapsam:** Godot projesinde genel merdivenin (SKILL.md §4) karşılığı.

1. **İçe aktarma:** Taze klonda `godot --headless --path . --import`.
2. **Statik denetim:** Kırık `res://` yolları, uid tutarlılığı, yetim `.import` ve `.uid` dosyaları, sahnelerdeki ExtResource ve `[connection]` satırları, autoload listesi. Kaynakta bunu `check_godot_project.py` yapıyor; yoksa aynı denetimi kendi küçük betiğinle yap.
3. **Ekransız test:** `--script` ile test koşucusu. Başarısız test varsa koşucu 1 ile, yoksa 0 ile çıkar.
4. **Duman koşusu:** `--quit-after 300` ile oyunu kısa süre çalıştır; günlükte `SCRIPT ERROR|^ERROR:` ara.
5. **İnsan oyun testi.**

**Tuzaklar**
- Godot betik hatasında da 0 ile çıkar. Asıl sinyal günlüktür.
- Çıplak `assert()` testi başarısız saymaz; başarısızlığı koşucunun sayacına yaz.
- Yeşile güvenmeden bir testi bilerek boz, çıkış kodunun 1 olduğunu gör.
- CI'de iş için zaman aşımı koy (kaynakta `timeout-minutes: 5`).
- PowerShell'de stdout ve stderr'i dosyaya yönlendir, sonra dosyayı oku.
- Test betikleri hedef sahneyi yükler ve `_ready` çalışır: test, projenin kodunu çalıştırmaktır.

## GDScript
- `:=` tür çıkarımı Variant döndüren işlevlerde hata verir (`max`, `min`, `clamp`). Türlü sürümlerini kullan (`maxi`, `clampf` gibi).
- `--check-only` autoload adlarını tanımaz; autoload kullanan betikte yanlış hata gösterebilir.

## Fizik ve çarpışma
- `velocity`'yi `delta` ile çarpma; `move_and_slide` bunu kendisi yapar.
- `is_on_floor` yalnızca `move_and_slide` çağrısından sonra doğrudur.
- `position +=` çarpışmayı atlar; gövdeyi fizik yöntemleriyle taşı.
- Katman "ben neyim", maske "neyi tararım". n. katmanın biti `1 << (n - 1)`.
- Fizik geri çağrısında sahne ağacını değiştirme (düğüm ekleme, silme, taşıma); `call_deferred` kullan.

## Sinyal ve grup
- Aynı lambda her bağlamada yeni bir Callable üretir; bağlantıyı koparmak için Callable'ı bir değişkende sakla.
- `call_group`, metodu olmayan düğümü sessizce atlar; adı yanlış yazılırsa hiçbir şey olmaz.

## Animasyon ve tween
- Döngülü klip `animation_finished` sinyali yaymaz.
- Saydamlık tween'inde `modulate` yerine `modulate:a` kullan; renk bozulmaz.

## Kaynak (resource) ve dosya
- Resource örnekler arasında paylaşılır. Bir örneği değiştirmeden önce `duplicate_deep` ile kopyala.
- `res://` dışa aktarılmış oyunda salt okunurdur; kayıt ve ayar `user://`'a yazılır.
- JSON 2^53'ün üstündeki tamsayıyı kaybeder. `str_to_var` güvenilmeyen veride betik çalıştırabilir (`kayit-diyalog-girdi-arayuz.md`).

## Gölgelendirici
- `TIME` 3600 s'de başa döner; uzun oturumda sıçrama olur.
- Spatial gölgelendiricide `ALPHA`'ya yazmak nesneyi saydam boru hattına alır.

## Ses
- Olmayan bir veriyoluna (bus) atanmış ses Master'da çalar, hata vermez.
- `volume_db` doğrusal değildir; kaydırıcı değerini dB'ye çevir.
- `max_polyphony` 1'dir: sık çalan seste yeni çalış öncekini keser.

## Ağ
- `@rpc` varsayılan olarak yalnızca authority'nin çağırmasına izin verir.
- RPC tanımı sunucu ve istemci yapılarında aynı olmalı.

## Dışa aktarma
- Dışa aktarma şablonu motor sürümüyle tam eşleşmeli.
- Çıktı klasörü dışa aktarmadan önce var olmalı.
- Web yapısında iş parçacığı kullanılıyorsa sunucu COOP/COEP başlıklarını göndermeli.
- C# kullanan proje web'e aktarılamaz.
- `export_credentials.cfg` git'e girmez; `.gitignore`'da olduğunu denetle.

## Godot 3'ten 4'e
| Godot 3 | Godot 4 |
|---|---|
| `export`, `onready`, `tool` | `@export`, `@onready`, `@tool` |
| `yield` | `await` |
| `setget` | özellik içinde `set` / `get` |
| `connect("x", self, "m")` | `x.connect(m)` |
| `instance()` | `instantiate()` |
| `move_and_slide(v, up)` | `velocity` ve `up_direction` özellikleri, argümansız çağrı |
| `rect_*` | `size`, `position` |
| Tween düğümü | `create_tween()` |
| `SCREEN_TEXTURE` | `hint_screen_texture` ile tanımlanan örnekleyici |
| `hint_color` | `source_color` |
| TileMap | TileMapLayer (4.3) |
