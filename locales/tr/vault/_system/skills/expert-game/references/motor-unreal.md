# Unreal Engine

Kaynak paket UE 5.8'i hedefliyor (5.9 önizlemede); sürüm ve davranış bilgileri sahibin 11 Kasım 2026 beyanıdır, bağımsız doğrulanmadı.

## Önce projeyi oku
- Motor sürümü `*.uproject` dosyasında. Modüller `Build.cs` dosyalarında; modül eklemeden önce kullanıcıya sor.
- `.uasset` ikili dosyadır, grep ile okunmaz. Değişikliği komut satırı ve ekransız testle doğrula; bu olmuyorsa kullanıcıya düğüm düğüm tarif ver ve sonucu ondan iste.

## Doğrulama
**Kapsam:** Derleme, paketleme ve test.

- Yeniden üretilebilir derleme ve paketleme UAT (Unreal Automation Tool) ile yapılır.
- Shipping yapısında günlük yoktur. Hatayı Development ya da Test yapısında üret.
- Niagara testini `-nullrhi` ile değil `-RenderOffscreen` ile çalıştır; `-nullrhi` hiç çizim yapmaz.
- 5.8'de Zen Server ile pişirilen (cook) gevşek dosyalar dağıtılamaz; `-pak` ile paketle.

## Tuzaklar
- `.generated.h` include'u başlık dosyasında en son include olmalı.
- `UPROPERTY` ile işaretlenmeyen UObject işaretçisi çöp toplayıcıda (GC) serbest kalır; işaretçi geçersiz olur.
- Enhanced Input bağlamı `BeginPlay`'de eklenirse istemcide çalışmaz. Bağlamı eklediğin yeri istemci rolünde sına.
- Davranış ağacında `Observer Aborts None` ayarlı dekoratör, Blackboard anahtarı değişince dalı kesmez.
- Yanlış yazılmış ad sessizce başarısız olur: Blackboard anahtarı, Niagara User değişkeni, girdi eylemi.
- Play-in-Editor sırasında yapılan değişiklik varlıklara sızabilir.
