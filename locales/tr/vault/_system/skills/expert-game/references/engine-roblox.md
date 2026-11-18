# Roblox

Davranış bilgileri kaynak paketin sahibinin 11 Kasım 2026 beyanıdır, bağımsız doğrulanmadı. Ekonomi ve sunucu doğrulaması için yanında `uzman-guvenlik`.

## Luau temelleri
- Servisleri `game:GetService(...)` ile al.
- Yeni nesnenin özelliklerini önce ayarla, `Parent`'ı en son ata.
- Olay bağlantısını (Connection) bir değişkende sakla, işi bitince kes.

## DataStore
- Yükleme başarısız olduysa o oturumda kaydetmeyi reddet; yoksa boş veri oyuncunun kaydının üstüne yazılır.
- `SetAsync` yerine `UpdateAsync` ve oturum kilidi kullan; iki sunucu aynı kaydı ezmesin.
- Her DataStore çağrısını `pcall` ile sar.
- `BindToClose` içinde kaydetmeye 30 s vardır.
- NaN ya da sonsuz değer kaydetme.

## Ağ
- İstemci yalnızca kimlik ve niyet gönderir ("şu eşyayı satın almak istiyorum"), sonucu değil.
- Sunucu katmanlı doğrular: istek sıklığı, tip, sayının sonlu olması, izin, mesafe, bekleme süresi.
- `InvokeClient` kullanma.

## Karakter ve fizik
- Karakter yeniden doğunca nesil sayacını artır. Her yield'den sonra elindeki karakterin hâlâ güncel nesil olduğunu denetle.
- Çarpışma sorgusu için shapecast; hareketli parçaların sahipliği (network ownership) sunucuda.

## Studio iş akışı
- Doğruluk kaynağını düzenle: proje dosyalarla (Rojo) tutuluyorsa dosyaları, değilse Studio'daki örneği.
- Kaynak 6 basamaklı bir doğrulama merdiveni kullanıyor (basamaklar okunmadı); genel merdiven SKILL.md §4.
- Rapor "çalıştırıldı / statik denetlendi / hazırlandı ama çalıştırılmadı / doğrulanmadı" ayrımıyla yazılır.
- Test için yerleştirilen nesneleri ve deneyleri iş bitince temizle (silmeden önce kullanıcıya sor, #22).

## Ekonomi
- Maliyet büyüme çarpanı (`costGrowth`) 1,07–1,15.
- NaN ya da sonsuz değeri kaydetme ve gösterme.
- Kısaltılmış sayı biçiminde sınırı test et: 999950 "1.0M" olarak gösterilmeli.
- Kaynakta saf Luau ile yazılmış denge ve ekonomi betikleri var; okunmadı.
