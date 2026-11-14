# v1.2.0 — Security update

**This release is a security update. Updating is recommended.**

It tightens the command, write and site guards. On the same test inputs, the shell commands the command guard let
through without a word fell from 68 of 72 to 7 of 72, and its slowest decision fell from 123 s to under 1 s.

## What it closes

- **The guards' own files could be changed.** One shell command or file write could change the hook and permission
  settings of any supported assistant, the guard scripts, agent definitions, git hooks, the blocklist, the rules or the
  instructions. One list (`common.DEFENSE_SET`) now serves both guards, and such a change is asked.
- **Network calls from the shell went around the site guard.** Download tools, sockets and remote shells, remote
  paths, .NET network classes, network code in Python or node, opening an address in the browser, `git clone` and
  `gh api` are now asked, with the address in the reason. Piping a download into an interpreter is refused, also
  through other pipes, process substitution or base64.
- **Hidden command names blinded the command guard** (`"r""m"`, `c''url`, `command curl`, `$(echo curl)`). They are
  now opened or asked.
- **Slow inputs ran past the hook's time limit.** The backtracking patterns were rewritten, and a command over 20,000
  characters is asked (refused in an unrecorded chat).
- **More risky commands are asked or refused:** skipping the commit hook, emptying files, more ways to delete files or
  kill processes, printing secrets, persistence and execution-policy changes, installing packages, applying patches,
  moving vault files to a temporary folder.
- **Web searches and the terminal tool now pass the guards**, and a broken helper module or a `json.py` beside the
  guards no longer switches them off.
- **The health check** reports missing or narrowed security hooks, broad permission patterns, a bypassed commit hook
  and uncommitted changes in the guard scripts.

## How to update

The installer does not overwrite existing files, so an existing install is updated by hand: copy every
`vault/_system/*.py` file of this release into your vault's `_system/` folder (`_sistem/` in a Turkish install) with
Claude Code closed, add `mcp__terminal__run_in_terminal` to the command guard's matcher and `WebSearch` to the site
guard's PreToolUse matcher in `~/.claude/settings.json`, then run `health.py`. The steps are in
[CHANGELOG.md](../CHANGELOG.md#how-to-update).

## Known limits

A script that writes a file indirectly is not seen by the command guard (`health.py` shows the change afterwards); a
path or command name kept in a variable or joined from strings is not resolved; web searches are guarded only in Claude
Code. See [SECURITY.md](../SECURITY.md#known-limits).

---

# v1.2.0 — Güvenlik güncellemesi

**Bu sürüm bir güvenlik güncellemesidir. Güncellemeniz önerilir.**

Komut, yazma ve site kapılarını sıkılaştırır. Aynı sınama girdilerinde komut kapısının sessiz kaldığı kabuk komutu
72'de 68'den 72'de 7'ye indi; en yavaş kapı kararı 123 sn'den 1 sn'nin altına indi.

## Neyi kapatıyor

- **Kapıların kendi dosyaları değiştirilebiliyordu.** Tek bir kabuk komutu ya da dosya yazımı, desteklenen herhangi
  bir asistanın hook ve izin ayarlarını, kapı betiklerini, ajan tanımlarını, git kancalarını, kara listeyi, kuralları
  ya da talimatları değiştirebiliyordu. Artık iki kapıya da tek liste (`common.DEFENSE_SET`) hizmet eder ve böyle bir
  değişiklik sorulur.
- **Kabuktan ağa çıkış site kapısını dolanıyordu.** İndirme araçları, soket ve uzak kabuk, uzak yol, .NET ağ
  sınıfları, Python ya da node içindeki ağ kodu, tarayıcıda adres açma, `git clone` ve `gh api` artık gerekçede
  adresle sorulur. İndirileni yorumlayıcıya bağlamak, araya başka borular, süreç ikamesi ya da base64 girse de
  reddedilir.
- **Gizlenmiş komut adları komut kapısını kör ediyordu** (`"r""m"`, `c''url`, `command curl`, `$(echo curl)`). Artık
  açılır ya da sorulur.
- **Yavaş girdiler hook'un süre sınırını aşıyordu.** Geri izleyen desenler yeniden yazıldı; 20.000 karakteri geçen
  komut sorulur (kayıtsız sohbette reddedilir).
- **Daha fazla riskli komut sorulur ya da reddedilir:** commit kancasını atlama, dosya içeriğini boşaltma, silmenin ve
  süreç öldürmenin başka yolları, sır gösterme, kalıcılık ve yürütme politikası değişiklikleri, paket kurulumu, yama
  uygulama, vault dosyasını geçici klasöre taşıma.
- **Web araması ve terminal aracı artık kapılardan geçer;** bozuk bir yardımcı modül ya da kapıların yanındaki bir
  `json.py` onları artık kapatamaz.
- **Sağlık denetimi** eksik ya da daralmış güvenlik hook'larını, geniş izin kalıplarını, atlatılmış commit kancasını
  ve kapı betiklerindeki commit edilmemiş değişikliği gösterir.

## Nasıl güncellenir

Kurucu var olan dosyaların üzerine yazmaz; var olan kurulum elle güncellenir: Claude Code kapalıyken bu sürümdeki
bütün `vault/_system/*.py` dosyalarını vault'unuzun `_sistem/` klasörüne (İngilizce kurulumda `_system/`) kopyalayın,
`~/.claude/settings.json` içinde komut kapısının eşleştiricisine `mcp__terminal__run_in_terminal`, site kapısının
PreToolUse eşleştiricisine `WebSearch` ekleyin, sonra `health.py` çalıştırın. Adımlar
[CHANGELOG.tr.md](../CHANGELOG.tr.md#nasıl-güncellenir) dosyasında.

## Bilinen sınırlar

Dosyayı dolaylı yazan bir betik komut kapısından görülmez (`health.py` değişikliği sonradan gösterir); değişkende
tutulan ya da dizgi birleştirerek kurulan yol veya komut adı çözülmez; web araması yalnızca Claude Code'da denetlenir.
Bkz. [SECURITY.tr.md](../SECURITY.tr.md#bilinen-sınırlar).
