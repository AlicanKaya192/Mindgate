# Unity

Kaynak paket Unity 6.3 LTS'yi (6000.3) hedefliyor; sürüm ve davranış bilgileri sahibin 11 Kasım 2026 beyanıdır, bağımsız doğrulanmadı.

## Önce projeyi oku
- Sürüm: `ProjectSettings/ProjectVersion.txt`. Paketler: `Packages/manifest.json` ve kilit dosyası `Packages/packages-lock.json`.
- Paket eklemeden önce kilit dosyasına bak ve kullanıcıya sor.
- Sahne, prefab ve `.meta` dosyaları metin biçimindedir (Unity YAML). Değişikliği grep ile doğrula: referans, GUID, alan adı.

## Doğrulama
**Kapsam:** Komut satırından derleme ve test.

- Derleme `-buildTarget` ve `-executeMethod` ile yapılır. Çağrılan metot sonucu açık çıkış koduyla bildirir; bu durumda `-quit` birlikte verilmez.
- `BuildPlayer`'ın dönmesi başarı demek değildir; `BuildResult.Succeeded` olduğunu denetle.
- Test sonucunu NUnit XML'den oku, çıkış koduna tek başına güvenme. Günlükte `error CS` ara.
- Test filtresi yanlışsa hiçbir test çalışmaz ve sonuç temiz görünür; çalışan test sayısını oku.
- Kaynakta salt okur denetim betikleri var (`check_unity_project.py`, `check_unity_build_size.py`, `build_report.py`); bunlar okunmadı, kurulmadı.

## Tuzaklar
- `?.`, `??` ve `is null` yok edilmiş (Destroy) Unity nesnesini yakalamaz. `if (obj)` ile denetle.
- Serileştirilen alanın adı değişince Inspector'daki değer kaybolur. Eski adı `FormerlySerializedAs` ile bildir.
- "Missing script" uyarısı `.meta` dosyasının ya da GUID'in kaybıdır. Dosyayı `.meta`'sıyla birlikte taşı.
- IL2CPP kod soyma (stripping), yalnızca reflection ile çağrılan kodu siler. Korunacak türleri `link.xml`'e yaz.
- Animator parametresi yanlış yazılırsa hata vermez, sessizce çalışmaz. Girdi tarafında `FindAction` da öyle.
- Play modunda yapılan değişiklik ya kaybolur ya da (ScriptableObject gibi varlıklarda) kalıcı olur ve sızar. Testte varlığı kopyalayarak değiştir.
- `Lerp` 0..1 dışını keser; aşımlı easing görünmez.

## Yapı boyutu
- Doku `MaxSize` için üst sınır 2048 ile başla, gerekirse artır.
- LZ4HC sıkıştırması Steam yamasını büyütür.
- glTF içine gömülü doku Unity'nin doku sıkıştırmasını atlar.
- itch.io dosya başına 200 MB kabul eder (`is-akislari.md`).
- Kaynaktaki boyut betiği bir glTF aracını `npx` ile çalıştırmayı öneriyor. Bu beceri o aracı kurmaz ve çalıştırmaz; gerekiyorsa neyin neden gerektiğini söyle ve izin iste (#35).
