# v1.2.1 — Security update

**This release is a security update. Updating is recommended.** It holds everything in
[v1.2.0](RELEASE-v1.2.0.md) and adds:

- **An update check (off by default).** Mindgate is a set of files, not a program, so nothing told you when a release
  was out. `health.py` can now ask GitHub for the latest release and say when a newer one is out, and whether it is a
  security update. Turn it on with `"update_check": {"enabled": true}` in `_system/config.json`. It asks one fixed
  address (`api.github.com/repos/AlicanKaya192/Mindgate/releases/latest`), sends nothing from the vault and uses only
  the version number of the answer.
- **Python 3.10 works again.** In v1.2.0 a pattern in the command guard used Python 3.11 syntax, so on 3.10 the command
  guard could not load. Fixed, with a test.
- **Release notices without the check:** *Watch → Custom → Releases* on GitHub.

How to update: [CHANGELOG.md](../CHANGELOG.md#how-to-update).

---

# v1.2.1 — Güvenlik güncellemesi

**Bu sürüm bir güvenlik güncellemesidir. Güncellemeniz önerilir.** [v1.2.0](RELEASE-v1.2.0.md) sürümünün tamamını
içerir ve şunları ekler:

- **Güncelleme denetimi (varsayılan kapalı).** Mindgate bir program değil, bir dosya kümesi; yeni sürüm çıktığında size
  bunu söyleyen bir şey yoktu. `health.py` artık GitHub'a son sürümü sorup daha yenisi çıktığında ve bunun bir güvenlik
  güncellemesi olup olmadığını söyleyebilir. Açmak için `_sistem/config.json` içinde `"update_check": {"enabled": true}`
  yazın. Sabit tek bir adrese sorar (`api.github.com/repos/AlicanKaya192/Mindgate/releases/latest`), vault'tan hiçbir
  şey göndermez, cevaptan yalnızca sürüm numarasını kullanır.
- **Python 3.10 yeniden çalışıyor.** v1.2.0'da komut kapısındaki bir desen Python 3.11 sözdizimi kullanıyordu; 3.10'da
  komut kapısı yüklenemiyordu. Düzeltildi, testi var.
- **Denetim olmadan sürüm bildirimi:** GitHub'da *Watch → Custom → Releases*.

Nasıl güncellenir: [CHANGELOG.tr.md](../CHANGELOG.tr.md#nasıl-güncellenir).
