"""User-facing texts of the Mindgate installer and uninstaller, in English and Turkish.

Every text the person reads goes through `text(language, key, **values)`. Keys are the same in both languages;
`installer_test.py` checks that no key is missing on either side.
"""

LANGUAGES = ("en", "tr")

# The very first question is shown in both languages at once, before a language is chosen.
LANGUAGE_QUESTION = (
    "Which language should Mindgate use? / Mindgate hangi dilde kurulsun?\n"
    "  en = English\n"
    "  tr = Türkçe"
)
LANGUAGE_HINT = {
    "obsidian": "Suggested from your Obsidian setting / Obsidian ayarınıza göre öneri: {language}",
    "system": "Obsidian language could not be read; suggested from your system language / "
              "Obsidian dili okunamadı; sistem dilinize göre öneri: {language}",
}

MESSAGES = {
    "en": {
        "yes_no": "[y/n]",
        "yes_words": "y,yes",
        "no_words": "n,no",
        "default": "default",
        "invalid_choice": "Please answer with one of: {options}",
        "step": "\n── Step {number}/{total}: {title} ──",
        "if_no": "If you say no: {result}",

        # Safety
        "refuse_real_home": "Refused: --answers is meant for tests, but --home points to your real home folder ({home}). "
                            "Use a test folder for --home. Nothing was written.",
        "answer_missing": "The answers file has no value for '{key}'. Nothing was written.",
        "answer_invalid": "The answers file has an invalid value for '{key}': {value}. Nothing was written.",
        "answers_unreadable": "The answers file could not be read: {error}. Nothing was written.",

        # Step 2: environment
        "env_title": "Checking this computer (read only)",
        "env_what": "I look for Python, git, Claude Code and Obsidian. Nothing is installed or changed here.",
        "python_ok": "Python {version}: OK.",
        "python_old": "Python {version} is too old. Mindgate needs Python 3.10 or newer. Install a newer Python and run "
                      "the installer again. Nothing was written.",
        "git_ok": "git: found.",
        "git_missing": "git: not found. The vault works without it, but the daily and weekly tasks save their work "
                       "with git commits. You can install git later.",
        "claude_ok": "Claude Code: found ({where}).",
        "claude_missing": "Claude Code: not found (no ~/.claude folder and no `claude` command). Mindgate is a setup for "
                          "Claude Code; without it the instructions, hooks and skills are not used.",
        "claude_continue": "Continue anyway?",
        "obsidian_ok": "Obsidian: found ({where}).",
        "obsidian_missing": "Obsidian: not found. The vault is a folder of Markdown notes made for Obsidian: links between "
                            "notes, the graph view and the Bases tables of the folder entry pages are designed for it. "
                            "Please install Obsidian yourself from its official site; this installer does not install it. "
                            "You can also go on without it and open the notes in any editor.",
        "obsidian_continue": "Continue without Obsidian?",
        "obsidian_language": "Obsidian language setting: {language}.",
        "obsidian_language_unread": "Obsidian language setting: could not be read.",
        "stopped": "Stopped. Nothing was written.",

        # Step 3: Python command
        "py_title": "Python command",
        "py_what": "Hooks and tasks call the vault scripts with this command. Suggested for this system: `{suggested}`.",
        "py_question": "Python command to use",

        # Step 4 and 5: vault
        "vault_title": "Vault",
        "vault_what": "The vault is a folder of notes (your second brain). I copy the Mindgate vault into it in your "
                      "language and create empty starting pages.",
        "vault_no": "no vault is created; the later steps need a vault, so they are skipped too.",
        "vault_question": "Create the vault?",
        "vault_path_question": "Vault folder (location and name)",
        "vault_full": "This folder is not empty: {path}. Nothing is written over existing files. Please choose another "
                      "folder.",
        "vault_existing": "This folder already holds a Mindgate vault in {language}: {path}.",
        "vault_reuse_question": "Use this existing vault? (Nothing is copied into it.)",
        "vault_language_mismatch": "That vault is in another language ({language}). Please choose another folder.",
        "vault_not_dir": "This path is a file, not a folder: {path}. Please choose another folder.",
        "vault_files": "{count} files will be written to {path}.",
        "vault_skipped_rest": "No vault: the steps for instructions, hooks, skills, tasks and rules are skipped.",

        # Step 6: global instructions
        "ins_title": "Global instructions (~/.claude/CLAUDE.md)",
        "ins_what": "Claude Code reads ~/.claude/CLAUDE.md in every session and project. Mindgate's core instructions "
                    "tell Claude where the vault is and which rules to follow.",
        "ins_no": "Claude does not know about the vault unless you start it inside the vault folder.",
        "ins_yours": "Your current file: {size} bytes, {lines} lines.",
        "ins_headings": "Its headings: {headings}",
        "ins_first_lines": "Its first lines:",
        "ins_ours": "Mindgate core: {size} bytes, {lines} lines. Headings: {headings}",
        "ins_options": "Options:\n"
                       "  import = write the core to ~/.claude/mindgate/CLAUDE.md and add one marked import line at the "
                       "end of your file\n"
                       "  merge  = add the core at the end of your file between marked lines\n"
                       "  skip   = change nothing",
        "ins_new_options": "You have no ~/.claude/CLAUDE.md yet. Options:\n"
                           "  write = create it with the Mindgate core\n"
                           "  skip  = create nothing",
        "ins_question": "Your choice",
        "ins_backup": "Before any change, a copy with a time stamp is kept in ~/.claude/mindgate/backups/.",
        "ins_already": "Your file already has the Mindgate import line or block; it is not added again.",

        # Step 7: hooks
        "hooks_title": "Hooks (~/.claude/settings.json)",
        "hooks_what": "Hooks are small checks Claude Code runs on its own at certain moments. Each one calls a script "
                      "in the vault. Your own settings and hooks are not touched; only the ones you pick are added.",
        "hooks_no": "the vault works, but nothing guards commands, writes and sites, and sessions are not logged.",
        "hooks_broken": "~/.claude/settings.json is not valid JSON ({error}). I stop here so that nothing breaks it "
                        "further. Fix the file (or move it aside) and run the installer again. Nothing was written.",
        "hooks_not_object": "~/.claude/settings.json does not hold a JSON object (or its `hooks` part is not one). "
                            "I stop here. Nothing was written.",
        "hooks_item": "  {id}\n      {description}",
        "hooks_question": "Which hooks? all / none / pick",
        "hooks_pick_question": "Add this hook? {id}",
        "hooks_present": "Already installed, not added again: {count}.",

        # Step 8: skills and agents
        "skills_title": "Skills and agents",
        "skills_what": "Skills are instruction packs Claude loads for a kind of work; agents are helpers with a fixed "
                       "role. They are copied to ~/.claude/skills/ and ~/.claude/agents/.",
        "skills_no": "the vault still works, but Claude does not have the Mindgate skills and agents.",
        "skills_list": "Skills ({count}): {names}",
        "agents_list": "Agents ({count}): {names}",
        "skills_question": "Install the skills?",
        "agents_question": "Install the agents?",
        "assist_title": "Other assistants (experimental)",
        "assist_what": "Mindgate can also guard another coding assistant: its shell commands, file writes and web pages "
                       "go through the same guards, and it gets the Mindgate instructions, skills and agents. This was "
                       "tried only with sample hook data from the assistant's documents, not with the real program.",
        "assist_no": "nothing is written for that assistant; Claude Code is set up as before.",
        "assist_question": "Set up {name} too?",
        "other_hooks_broken": "{path} is not valid JSON or does not hold a JSON object ({error}). I stop here so that "
                              "nothing breaks it further. Nothing was written.",
        "assist_codex": "Codex gets: the command and write guards in {hooks} (your own hooks stay), the instructions "
                        "between marked lines in {instructions}, the skills in ~/.agents/skills and the agents as TOML "
                        "files in ~/.codex/agents. Codex runs a new hook only after you review it with /hooks. Codex "
                        "cannot ask: a single delete is left to Codex's own approval, a recursive delete is refused. "
                        "Web pages are not checked (Codex web tools do not reach hooks), and an agent file cannot limit "
                        "tools.",
        "assist_gemini": "Gemini CLI gets: the command, write and site guards in the \"hooks\" part of {hooks} (your "
                         "other settings stay), the instructions between marked lines in {instructions} (Antigravity "
                         "reads this file too), the skills in ~/.agents/skills and the agents in ~/.gemini/agents. Gemini "
                         "CLI cannot ask: what Claude would ask (an unlisted site, a delete) is refused.",
        "assist_antigravity": "Antigravity gets: the command, write and site guards in {hooks} (a hook set named "
                              "\"mindgate\"; your other hook sets stay), the instructions between marked lines in "
                              "{instructions}, and the skills and agents you chose above. Session records, the context "
                              "check and the scheduled tasks do not run in Antigravity.",
        "conflict_question": "You already have a {kind} named `{name}`. It is not overwritten. skip / rename "
                             "(install as `{new_name}`)",
        "same_present": "Already installed with the same content, skipped: {names}",
        "kind_skill": "skill",
        "kind_agent": "agent",

        # Step 9: scheduled tasks
        "tasks_title": "Scheduled tasks",
        "tasks_what": "Two tasks for the Claude desktop app. They run only while the desktop app is open.",
        "task_daily": "Daily: reads the day's Claude Code sessions, writes what is new into the vault, keeps the log and "
                      "makes a git commit.",
        "task_weekly": "Weekly: maintenance: health check, broken links, inbox, lesson candidates, memory quiz, a short "
                       "weekly summary.",
        "tasks_no": "nothing runs on its own; you can ask Claude for the same work by hand (\"keep records\").",
        "task_question": "Install the {task} task?",
        "task_daily_name": "daily",
        "task_weekly_name": "weekly",
        "scan_question": "Should the tasks read the sessions of all your Claude Code projects? (No = only the sessions "
                         "that ran in the vault.)",
        "push_question": "Should the tasks also run `git push` after the commit? (Usually no: pushing sends your notes "
                         "to a remote.)",
        "trending_what": "The weekly task has one optional web step. What: it reads a single page, "
                         "https://github.com/trending?since=weekly, and writes at most 5 projects that match your fields "
                         "into a note. Why: to see new tools without searching yourself. It opens no other site and sends "
                         "nothing; the site guard still asks you on every visit. If no: the step is skipped and the weekly "
                         "summary says \"web step off\"; you can turn it on later in _system/config.json (weekly.trending).",
        "trending_question": "Should the weekly summary read this one web page (GitHub trending)?",
        "task_exists": "A task folder with this name already exists and is not overwritten: {path}",
        "tasks_app_note": "The task files are written to ~/.claude/scheduled-tasks/. If the desktop app does not list "
                          "them, add the schedule in the app.",

        # Step 10: optional rules
        "rules_title": "Optional rules",
        "rules_what": "These rules make sense only for some setups. Pick the ones that fit you.",
        "rules_no": "the rule stays off; you can turn it on later in _system/config.json.",
        "rule_item": "  #{number}: {title}",
        "rule_question": "Turn on rule #{number}?",
        "rule_needs_dashboard": "  #{number} needs the optional dashboard, which is not part of v1; it is not offered.",
        "rule_fingerprint": "A fingerprint of this computer's name is saved so that only this computer counts. The name "
                            "itself is not saved and the fingerprint is not shown.",
        "usage_5h_question": "Usage limit for the 5-hour allowance, in percent",
        "usage_week_question": "Usage limit for the weekly allowance, in percent",
        "percent_invalid": "Please give a whole number from 1 to 100.",

        # Step 11: summary
        "summary_title": "Summary",
        "summary_what": "This is everything that will be written. Nothing has been written yet.",
        "summary_nothing": "Nothing to write.",
        "summary_new": "  new      {path}",
        "summary_new_folder": "  new      {path}{sep} ({count} files)",
        "summary_change": "  change   {path}",
        "summary_backup": "  backup   {path}",
        "summary_vault": "  vault    {count} new files in {path}",
        "summary_vault_folder": "           {folder}: {count}",
        "summary_full_list": "(Run with --dry-run to see every vault file.)",
        "confirm_question": "Write all of this now?",
        "cancelled": "Cancelled. Nothing was written.",
        "dry_run_done": "Dry run: nothing was written.",

        # Done
        "writing": "Writing…",
        "write_failed": "Writing stopped with an error: {error}. What was written so far is listed in the manifest: "
                        "{manifest}",
        "done": "Done. {count} files written.",
        "done_manifest": "The list of installed items and backups: {path}",
        "done_vault": "Your vault: {path}",
        "done_next": "Next: open the vault folder in Obsidian (Open folder as vault) and start Claude Code in it.",
        "done_uninstall": "To remove Mindgate later: {py} setup/uninstall.py",

        # Uninstall
        "un_title": "Mindgate uninstaller",
        "un_no_manifest": "No Mindgate install record was found ({path}). Nothing to do.",
        "un_manifest_broken": "The install record could not be read ({error}). Nothing was changed.",
        "un_what": "This puts back your settings.json and CLAUDE.md and moves the installed skills, agents, tasks and "
                   "~/.claude/mindgate/ into one folder. Nothing is deleted.",
        "un_vault": "Your vault is not touched (it holds your notes): {path}",
        "un_restore": "  restore  {path}  (from {backup})",
        "un_clean": "  clean    {path}  (changed after install: only the Mindgate parts are taken out)",
        "un_keep": "  keep     {path}  (changed after install; it was created by Mindgate, so it is left as it is)",
        "un_move": "  move     {path}",
        "un_missing": "  missing  {path}  (already gone, skipped)",
        "un_target": "Moved items go to: {path}",
        "un_question": "Go ahead?",
        "un_settings_broken": "{path} is not valid JSON now; it is left as it is. Remove the Mindgate hooks by hand.",
        "un_done": "Done. Moved items are in {path}. You can delete that folder yourself if you no longer need it.",
        "un_partial": "Stopped with an error: {error}. What was done so far stays in {path}.",
    },
    "tr": {
        "yes_no": "[e/h]",
        "yes_words": "e,evet,y,yes",
        "no_words": "h,hayır,hayir,n,no",
        "default": "varsayılan",
        "invalid_choice": "Lütfen şunlardan biriyle cevap verin: {options}",
        "step": "\n── Adım {number}/{total}: {title} ──",
        "if_no": "Hayır derseniz: {result}",

        "refuse_real_home": "Reddedildi: --answers testler içindir, ama --home gerçek ev klasörünüzü gösteriyor ({home}). "
                            "--home için bir test klasörü verin. Hiçbir şey yazılmadı.",
        "answer_missing": "Cevap dosyasında '{key}' için değer yok. Hiçbir şey yazılmadı.",
        "answer_invalid": "Cevap dosyasında '{key}' için geçersiz değer: {value}. Hiçbir şey yazılmadı.",
        "answers_unreadable": "Cevap dosyası okunamadı: {error}. Hiçbir şey yazılmadı.",

        "env_title": "Bilgisayarı denetleme (salt okur)",
        "env_what": "Python, git, Claude Code ve Obsidian'a bakıyorum. Burada hiçbir şey kurulmaz ya da değiştirilmez.",
        "python_ok": "Python {version}: tamam.",
        "python_old": "Python {version} çok eski. Mindgate için Python 3.10 ya da daha yenisi gerekir. Yeni bir Python "
                      "kurup kurucuyu yeniden çalıştırın. Hiçbir şey yazılmadı.",
        "git_ok": "git: bulundu.",
        "git_missing": "git: bulunamadı. Vault onsuz da çalışır, ama günlük ve haftalık görevler işlerini git commit'iyle "
                       "kaydeder. git'i sonra kurabilirsiniz.",
        "claude_ok": "Claude Code: bulundu ({where}).",
        "claude_missing": "Claude Code: bulunamadı (~/.claude klasörü yok, `claude` komutu yok). Mindgate, Claude Code "
                          "için bir kurulumdur; o olmadan talimatlar, hook'lar ve beceriler kullanılmaz.",
        "claude_continue": "Yine de devam edilsin mi?",
        "obsidian_ok": "Obsidian: bulundu ({where}).",
        "obsidian_missing": "Obsidian: bulunamadı. Vault, Obsidian için hazırlanmış bir Markdown not klasörüdür: notlar "
                            "arası bağlantılar, grafik görünümü ve klasör giriş sayfalarındaki Bases tabloları ona göre "
                            "tasarlandı. Lütfen Obsidian'ı resmî sitesinden kendiniz kurun; bu kurucu onu kurmaz. "
                            "Obsidian olmadan da devam edip notları herhangi bir düzenleyicide açabilirsiniz.",
        "obsidian_continue": "Obsidian olmadan devam edilsin mi?",
        "obsidian_language": "Obsidian dil ayarı: {language}.",
        "obsidian_language_unread": "Obsidian dil ayarı: okunamadı.",
        "stopped": "Durduruldu. Hiçbir şey yazılmadı.",

        "py_title": "Python komutu",
        "py_what": "Hook'lar ve görevler vault betiklerini bu komutla çağırır. Bu sistem için öneri: `{suggested}`.",
        "py_question": "Kullanılacak Python komutu",

        "vault_title": "Vault",
        "vault_what": "Vault bir not klasörüdür (ikinci beyniniz). Mindgate vault'unu sizin dilinizde buraya kopyalarım "
                      "ve boş başlangıç sayfalarını oluştururum.",
        "vault_no": "vault oluşturulmaz; sonraki adımlar vault'a bağlı olduğu için onlar da atlanır.",
        "vault_question": "Vault oluşturulsun mu?",
        "vault_path_question": "Vault klasörü (yeri ve adı)",
        "vault_full": "Bu klasör boş değil: {path}. Var olan dosyaların üzerine yazılmaz. Lütfen başka bir klasör seçin.",
        "vault_existing": "Bu klasörde zaten {language} bir Mindgate vault'u var: {path}.",
        "vault_reuse_question": "Bu vault kullanılsın mı? (İçine hiçbir şey kopyalanmaz.)",
        "vault_language_mismatch": "O vault başka bir dilde ({language}). Lütfen başka bir klasör seçin.",
        "vault_not_dir": "Bu yol klasör değil, dosya: {path}. Lütfen başka bir klasör seçin.",
        "vault_files": "{path} içine {count} dosya yazılacak.",
        "vault_skipped_rest": "Vault yok: talimat, hook, beceri, görev ve kural adımları atlanıyor.",

        "ins_title": "Global talimatlar (~/.claude/CLAUDE.md)",
        "ins_what": "Claude Code ~/.claude/CLAUDE.md dosyasını her oturumda ve her projede okur. Mindgate çekirdek "
                    "talimatları Claude'a vault'un nerede olduğunu ve hangi kurallara uyacağını söyler.",
        "ins_no": "Claude, vault klasöründe başlatılmadıkça vault'u bilmez.",
        "ins_yours": "Şu anki dosyanız: {size} bayt, {lines} satır.",
        "ins_headings": "Başlıkları: {headings}",
        "ins_first_lines": "İlk satırları:",
        "ins_ours": "Mindgate çekirdeği: {size} bayt, {lines} satır. Başlıklar: {headings}",
        "ins_options": "Seçenekler:\n"
                       "  import = çekirdeği ~/.claude/mindgate/CLAUDE.md dosyasına yaz, sizin dosyanızın sonuna "
                       "işaretli tek bir içe aktarma satırı ekle\n"
                       "  merge  = çekirdeği işaretli satırlar arasında sizin dosyanızın sonuna ekle\n"
                       "  skip   = hiçbir şeyi değiştirme",
        "ins_new_options": "Henüz ~/.claude/CLAUDE.md dosyanız yok. Seçenekler:\n"
                           "  write = Mindgate çekirdeğiyle oluştur\n"
                           "  skip  = hiçbir şey oluşturma",
        "ins_question": "Seçiminiz",
        "ins_backup": "Her değişiklikten önce zaman damgalı bir kopya ~/.claude/mindgate/backups/ altında saklanır.",
        "ins_already": "Dosyanızda Mindgate içe aktarma satırı ya da bloğu zaten var; yeniden eklenmez.",

        "hooks_title": "Hook'lar (~/.claude/settings.json)",
        "hooks_what": "Hook'lar, Claude Code'un belli anlarda kendiliğinden çalıştırdığı küçük denetimlerdir. Her biri "
                      "vault'taki bir betiği çağırır. Sizin ayarlarınıza ve hook'larınıza dokunulmaz; yalnızca "
                      "seçtikleriniz eklenir.",
        "hooks_no": "vault çalışır, ama komutları, yazmaları ve siteleri koruyan bir denetim olmaz, oturumlar kaydedilmez.",
        "hooks_broken": "~/.claude/settings.json geçerli bir JSON değil ({error}). Dosyayı daha çok bozmamak için burada "
                        "duruyorum. Dosyayı düzeltip (ya da kenara taşıyıp) kurucuyu yeniden çalıştırın. Hiçbir şey "
                        "yazılmadı.",
        "hooks_not_object": "~/.claude/settings.json bir JSON nesnesi tutmuyor (ya da `hooks` bölümü nesne değil). Burada "
                            "duruyorum. Hiçbir şey yazılmadı.",
        "hooks_item": "  {id}\n      {description}",
        "hooks_question": "Hangi hook'lar? all (hepsi) / none (hiçbiri) / pick (tek tek)",
        "hooks_pick_question": "Bu hook eklensin mi? {id}",
        "hooks_present": "Zaten kurulu, yeniden eklenmedi: {count}.",

        "skills_title": "Beceriler ve ajanlar",
        "skills_what": "Beceriler (skills), Claude'un bir iş türü için yüklediği talimat paketleridir; ajanlar (agents) "
                       "rolü belli yardımcılardır. ~/.claude/skills/ ve ~/.claude/agents/ altına kopyalanırlar.",
        "skills_no": "vault yine çalışır, ama Claude'da Mindgate becerileri ve ajanları olmaz.",
        "skills_list": "Beceriler ({count}): {names}",
        "agents_list": "Ajanlar ({count}): {names}",
        "skills_question": "Beceriler kurulsun mu?",
        "agents_question": "Ajanlar kurulsun mu?",
        "assist_title": "Başka asistanlar (deneysel)",
        "assist_what": "Mindgate başka bir kod asistanını da koruyabilir: kabuk komutları, dosya yazmaları ve web sayfaları "
                       "aynı kapılardan geçer; asistan Mindgate talimatlarını, becerilerini ve ajanlarını da alır. Bu, "
                       "yalnızca asistanın belgelerindeki örnek hook verisiyle denendi, gerçek programla denenmedi.",
        "assist_no": "o asistan için hiçbir şey yazılmaz; Claude Code önceki gibi kurulur.",
        "assist_question": "{name} da kurulsun mu?",
        "other_hooks_broken": "{path} geçerli bir JSON değil ya da JSON nesnesi tutmuyor ({error}). Dosyayı daha çok "
                              "bozmamak için burada duruyorum. Hiçbir şey yazılmadı.",
        "assist_codex": "Codex'e kurulacaklar: {hooks} içinde komut ve yazma kapıları (kendi hook'larınız yerinde "
                        "kalır), {instructions} içinde işaretli satırlar arasında talimatlar, ~/.agents/skills içinde "
                        "beceriler ve ~/.codex/agents içinde TOML dosyası olarak ajanlar. Codex yeni bir hook'u siz "
                        "/hooks ile inceleyip onaylayınca çalıştırır. Codex soru soramaz: tek dosya silme Codex'in "
                        "kendi onayına kalır, özyinelemeli silme reddedilir. Web sayfaları denetlenmez (Codex'in web "
                        "araçları hook'a gelmez) ve ajan dosyası araçları sınırlayamaz.",
        "assist_gemini": "Gemini CLI'a kurulacaklar: {hooks} dosyasının \"hooks\" bölümünde komut, yazma ve site "
                         "kapıları (öteki ayarlarınız yerinde kalır), {instructions} içinde işaretli satırlar arasında "
                         "talimatlar (Antigravity de bu dosyayı okur), ~/.agents/skills içinde beceriler ve "
                         "~/.gemini/agents içinde ajanlar. Gemini CLI soru soramaz: Claude'un soracağı şey (listede "
                         "olmayan site, silme) reddedilir.",
        "assist_antigravity": "Antigravity'ye kurulacaklar: {hooks} içinde komut, yazma ve site kapıları (\"mindgate\" "
                              "adlı bir hook takımı; öteki takımlarınız yerinde kalır), {instructions} içinde işaretli "
                              "satırlar arasında talimatlar ve yukarıda seçtiğiniz beceriler ve ajanlar. Oturum kayıtları, "
                              "bağlam ölçümü ve zamanlanmış görevler Antigravity'de çalışmaz.",
        "conflict_question": "`{name}` adlı bir {kind} zaten var. Üzerine yazılmaz. skip (atla) / rename (`{new_name}` "
                             "adıyla kur)",
        "same_present": "Aynı içerikle zaten kurulu, atlandı: {names}",
        "kind_skill": "beceri",
        "kind_agent": "ajan",

        "tasks_title": "Zamanlanmış görevler",
        "tasks_what": "Claude masaüstü uygulaması için iki görev. Yalnızca masaüstü uygulaması açıkken çalışırlar.",
        "task_daily": "Günlük: günün Claude Code oturumlarını okur, yeni olanı vault'a yazar, log'u tutar ve git commit'i "
                      "atar.",
        "task_weekly": "Haftalık: bakım: sağlık denetimi, kırık linkler, gelen kutusu, ders adayları, hafıza sınavı, kısa "
                       "bir haftalık özet.",
        "tasks_no": "hiçbir şey kendiliğinden çalışmaz; aynı işi Claude'dan elle isteyebilirsiniz (\"kayıtları tut\").",
        "task_question": "{task} görevi kurulsun mu?",
        "task_daily_name": "Günlük",
        "task_weekly_name": "Haftalık",
        "scan_question": "Görevler bütün Claude Code projelerinizin oturumlarını okusun mu? (Hayır = yalnızca vault'ta "
                         "çalışan oturumlar.)",
        "push_question": "Görevler commit'ten sonra `git push` da çalıştırsın mı? (Genelde hayır: push notlarınızı uzak "
                         "bir depoya gönderir.)",
        "trending_what": "Haftalık görevin isteğe bağlı tek bir web adımı var. Ne: yalnızca "
                         "https://github.com/trending?since=weekly sayfasını okur ve alanlarınıza uyan en çok 5 projeyi "
                         "bir nota yazar. Neden: yeni araçları kendiniz aramadan görmek için. Başka siteye girmez, hiçbir "
                         "şey göndermez; site kapısı her girişte yine size sorar. Hayır derseniz: adım atlanır ve haftalık "
                         "özete \"web adımı kapalı\" yazılır; sonra _sistem/config.json içinde (weekly.trending) "
                         "açabilirsiniz.",
        "trending_question": "Haftalık özet için bu tek web sayfası (GitHub trending) okunsun mu?",
        "task_exists": "Bu adla bir görev klasörü zaten var, üzerine yazılmaz: {path}",
        "tasks_app_note": "Görev dosyaları ~/.claude/scheduled-tasks/ altına yazılır. Masaüstü uygulaması onları "
                          "listelemezse zamanlamayı uygulamadan ekleyin.",

        "rules_title": "İsteğe bağlı kurallar",
        "rules_what": "Bu kurallar yalnızca bazı kurulumlarda anlamlıdır. Size uyanları seçin.",
        "rules_no": "kural kapalı kalır; sonra _sistem/config.json içinden açabilirsiniz.",
        "rule_item": "  #{number}: {title}",
        "rule_question": "#{number} kuralı açılsın mı?",
        "rule_needs_dashboard": "  #{number} isteğe bağlı panoyu gerektirir; pano v1'de yok, bu yüzden sunulmuyor.",
        "rule_fingerprint": "Yalnızca bu bilgisayar sayılsın diye bilgisayar adının parmak izi kaydedilir. Adın kendisi "
                            "kaydedilmez, parmak izi gösterilmez.",
        "usage_5h_question": "5 saatlik hak için kullanım sınırı, yüzde olarak",
        "usage_week_question": "Haftalık hak için kullanım sınırı, yüzde olarak",
        "percent_invalid": "Lütfen 1 ile 100 arasında bir tam sayı verin.",

        "summary_title": "Özet",
        "summary_what": "Yazılacak her şey bu. Henüz hiçbir şey yazılmadı.",
        "summary_nothing": "Yazılacak bir şey yok.",
        "summary_new": "  yeni      {path}",
        "summary_new_folder": "  yeni      {path}{sep} ({count} dosya)",
        "summary_change": "  değişir   {path}",
        "summary_backup": "  yedek     {path}",
        "summary_vault": "  vault     {path} içine {count} yeni dosya",
        "summary_vault_folder": "            {folder}: {count}",
        "summary_full_list": "(Vault'un bütün dosyalarını görmek için --dry-run ile çalıştırın.)",
        "confirm_question": "Bunların hepsi şimdi yazılsın mı?",
        "cancelled": "İptal edildi. Hiçbir şey yazılmadı.",
        "dry_run_done": "Kuru çalıştırma: hiçbir şey yazılmadı.",

        "writing": "Yazılıyor…",
        "write_failed": "Yazma bir hatayla durdu: {error}. O ana kadar yazılanlar kayıt dosyasında: {manifest}",
        "done": "Bitti. {count} dosya yazıldı.",
        "done_manifest": "Kurulan öğelerin ve yedeklerin listesi: {path}",
        "done_vault": "Vault'unuz: {path}",
        "done_next": "Sırada: vault klasörünü Obsidian'da açın (Klasörü vault olarak aç) ve Claude Code'u o klasörde "
                     "başlatın.",
        "done_uninstall": "Mindgate'i sonra kaldırmak için: {py} setup/uninstall.py",

        "un_title": "Mindgate kaldırıcı",
        "un_no_manifest": "Mindgate kurulum kaydı bulunamadı ({path}). Yapılacak bir şey yok.",
        "un_manifest_broken": "Kurulum kaydı okunamadı ({error}). Hiçbir şey değiştirilmedi.",
        "un_what": "settings.json ve CLAUDE.md dosyalarınızı eski hâline getirir; kurulan beceri, ajan, görev ve "
                   "~/.claude/mindgate/ içeriğini tek bir klasöre taşır. Hiçbir şey silinmez.",
        "un_vault": "Vault'unuza dokunulmaz (notlarınız orada): {path}",
        "un_restore": "  geri yükle {path}  ({backup} yedeğinden)",
        "un_clean": "  temizle    {path}  (kurulumdan sonra değişmiş: yalnızca Mindgate parçaları çıkarılır)",
        "un_keep": "  bırak      {path}  (kurulumdan sonra değişmiş; Mindgate oluşturmuştu, olduğu gibi bırakılır)",
        "un_move": "  taşı       {path}",
        "un_missing": "  yok        {path}  (zaten yok, atlandı)",
        "un_target": "Taşınanların gideceği yer: {path}",
        "un_question": "Devam edilsin mi?",
        "un_settings_broken": "{path} şu an geçerli bir JSON değil; olduğu gibi bırakıldı. Mindgate hook'larını elle "
                              "çıkarın.",
        "un_done": "Bitti. Taşınanlar {path} içinde. Artık gerekmiyorsa o klasörü kendiniz silebilirsiniz.",
        "un_partial": "Bir hatayla durdu: {error}. O ana kadar yapılanlar {path} içinde.",
    },
}

# One line per hook: what it guards and when it runs. Keys are the hook ids built by installer_lib.hook_id().
HOOK_DESCRIPTIONS = {
    "en": {
        "PreToolUse:command_guard": "Before every shell command: blocks dangerous ones (deleting outside the project, "
                                    "killing processes, system settings).",
        "PreToolUse:write_guard": "Before every file write: protects raw sources, archives and rule files.",
        "PreToolUse:site_guard": "Before a web page is opened: checks the address and asks you first.",
        "PreToolUse:agent_gate": "Before a task is given to an agent: the model must be named and the task-writing "
                                 "skill loaded.",
        "SessionEnd:session_log save": "When a session ends: writes a raw session record into the vault inbox.",
        "PreCompact:session_log save": "Before the context is compacted: writes the session record.",
        "PreCompact:context_check before": "Before compacting: adds what must be kept.",
        "Stop:context_check stop": "After each answer: measures how full the context is and reminds you in time.",
        "SessionStart:session_log remind": "When a session starts: shows rule titles and the latest handoff cards.",
        "PostToolUse:site_guard after": "After a web page is read: scans the fetched content for hidden instructions.",
        "UserPromptSubmit:search --hook": "With each message: adds a few related vault notes as context.",
        "PostCompact:context_check after": "After compacting: saves the compaction summary to the vault.",
    },
    "tr": {
        "PreToolUse:command_guard": "Her kabuk komutundan önce: tehlikelileri engeller (proje dışında silme, süreç "
                                    "öldürme, sistem ayarları).",
        "PreToolUse:write_guard": "Her dosya yazmadan önce: ham kaynakları, arşivleri ve kural dosyalarını korur.",
        "PreToolUse:site_guard": "Bir web sayfası açılmadan önce: adresi denetler ve önce size sorar.",
        "PreToolUse:agent_gate": "Bir ajana görev verilmeden önce: model açıkça yazılmalı ve görev yazma becerisi "
                                 "yüklenmiş olmalı.",
        "SessionEnd:session_log save": "Oturum bitince: ham oturum kaydını vault'un gelen kutusuna yazar.",
        "PreCompact:session_log save": "Bağlam sıkıştırılmadan önce: oturum kaydını yazar.",
        "PreCompact:context_check before": "Sıkıştırmadan önce: korunması gerekenleri ekler.",
        "Stop:context_check stop": "Her cevaptan sonra: bağlamın doluluğunu ölçer ve zamanında hatırlatır.",
        "SessionStart:session_log remind": "Oturum başlarken: kural başlıklarını ve son devir kartlarını gösterir.",
        "PostToolUse:site_guard after": "Bir web sayfası okunduktan sonra: gelen içeriği gizli talimatlara karşı tarar.",
        "UserPromptSubmit:search --hook": "Her mesajda: ilgili birkaç vault notunu bağlam olarak ekler.",
        "PostCompact:context_check after": "Sıkıştırmadan sonra: sıkıştırma özetini vault'a kaydeder.",
    },
}

# statusMessage texts of hooks.template.json in Turkish; English installs keep the template text.
HOOK_STATUS_TR = {
    "Guard is checking the command": "Koruma komutu denetliyor",
    "Write guard is checking protected files": "Yazma koruması korunan dosyaları denetliyor",
    "Site guard is checking the address": "Site kapısı adresi denetliyor",
    "Agent gate: checking task-writing and model": "Ajan kapısı: görev yazma ve model denetleniyor",
    "Writing the session record to the second brain": "Oturum kaydı ikinci beyne yazılıyor",
    "Adding what to keep when compacting": "Sıkıştırmada korunacaklar ekleniyor",
    "Measuring how full the context is": "Bağlamın doluluğu ölçülüyor",
    "Site guard is scanning the fetched content": "Site kapısı gelen içeriği tarıyor",
    "Saving the compaction summary to the vault": "Sıkıştırma özeti vault'a kaydediliyor",
}

# Starting pages of a new vault. `{date}` is filled with today's date. Keys are English base names.
STARTER_PAGES = {
    "en": {
        "pending": ("entry", "Pending",
                    "Questions, approvals and tasks waiting for the user. Add and close items only with "
                    "`records.py pending add | close | hold`; closing needs evidence.",
                    "## Open\n\n## Closed\n"),
        "handoff": ("entry", "Handoff",
                    "Short cards that tell the next session where the work stopped. Written with "
                    "`records.py handoff write`.", ""),
        "rule-violations": ("rule", "Rule violations",
                            "When a rule was broken: one line, written at once (rule #34).",
                            "| Date | Rule | What happened | Root cause | Fix and safeguard | Noticed by | Chat |\n"
                            "|---|---|---|---|---|---|---|\n"),
        "lesson-candidates": ("rule", "Lesson candidates",
                              "Patterns seen at least twice. A candidate becomes a rule only when the user approves it.",
                              "## Pending candidates\n\n| Candidate lesson | Evidence | Suggested place | Date |\n"
                              "|---|---|---|---|\n\n## Rejected\n"),
        "rejected-proposals": ("idea", "Rejected proposals",
                               "Proposals the user turned down, with their words and the reason (rule #39). Read "
                               "before proposing something new.",
                               "| Date | Proposal | User's words | Reason | Chosen instead | Status |\n"
                               "|---|---|---|---|---|---|\n"),
        "project-proposals": ("entry", "Project proposals",
                              "Ideas Claude proposes that could become projects for the user, each with its "
                              "description (rule #31). The user's own ideas go to the inbox.",
                              "| Date | Proposal | What | Goal | Use for the user | Criteria (field, learning, "
                              "already available, this computer) | Difficulty | Requirements | First step | Source "
                              "| Status |\n|---|---|---|---|---|---|---|---|---|---|---|\n"),
        "blocked-sites": ("entry", "Blocked sites",
                          "Domains the site guard blocks (rule #27). The site guard and the command guard read this "
                          "list; the site guard adds a row when it finds a clear sign of attack.",
                          "## List\n\n| Domain | Date | Reason | Evidence (shortened) |\n|---|---|---|---|\n"),
        "profile": ("profile", "Profile",
                    "The user's goals, preferences and projects, filled in over time. No sensitive information "
                    "(passwords, IDs, bank, address, health).",
                    "## Goals\n\n## Preferences\n\n## Design taste\n\n## Projects\n"),
    },
    "tr": {
        "pending": ("entry", "Bekleyenler",
                    "Kullanıcıyı bekleyen sorular, onaylar ve işler. Maddeler yalnızca "
                    "`records.py pending add | close | hold` ile eklenir ve kapatılır; kapanışta kanıt gerekir.",
                    "## Açık\n\n## Kapananlar\n"),
        "handoff": ("entry", "Devir",
                    "Sonraki oturuma işin nerede kaldığını söyleyen kısa kartlar. `records.py handoff write` ile "
                    "yazılır.", ""),
        "rule-violations": ("rule", "Kural ihlalleri",
                            "Bir kural çiğnendiğinde hemen yazılan tek satır (kural #34).",
                            "| Tarih | Kural | Ne oldu | Kök neden | Düzeltme ve önlem | Fark eden | Sohbet |\n"
                            "|---|---|---|---|---|---|---|\n"),
        "lesson-candidates": ("rule", "Ders adayları",
                              "En az iki kez görülen kalıplar. Aday, kullanıcı onaylayınca kural olur.",
                              "## Bekleyen adaylar\n\n| Aday ders | Kanıt | Önerilen yer | Tarih |\n"
                              "|---|---|---|---|\n\n## Reddedilenler\n"),
        "rejected-proposals": ("idea", "Reddedilen öneriler",
                               "Kullanıcının geri çevirdiği öneriler; sözleri ve nedeniyle (kural #39). Yeni bir şey "
                               "önermeden önce okunur.",
                               "| Tarih | Öneri | Kullanıcının sözü | Neden | Yerine seçilen | Durum |\n"
                               "|---|---|---|---|---|---|\n"),
        "project-proposals": ("entry", "Proje önerileri",
                              "Claude'un kullanıcıya önerdiği, projeye dönüşebilecek fikirler; her biri "
                              "açıklamasıyla (kural #31). Kullanıcının kendi fikirleri gelen kutusuna gider.",
                              "| Tarih | Öneri | Ne | Hedef | Kullanıcıya faydası | Ölçütler (alan, öğrenme, "
                              "elde olan, bu bilgisayar) | Zorluk | Gerekenler | İlk adım | Kaynak | Durum |\n"
                              "|---|---|---|---|---|---|---|---|---|---|---|\n"),
        "blocked-sites": ("entry", "Engelli siteler",
                          "Site kapısının engellediği alan adları (kural #27). Site kapısı ve komut kapısı bu listeyi "
                          "okur; site kapısı açık bir saldırı işareti bulunca satır ekler.",
                          "## Liste\n\n| Alan adı | Tarih | Neden | Kanıt (kısaltılmış) |\n|---|---|---|---|\n"),
        "profile": ("profile", "Profil",
                    "Kullanıcının hedefleri, tercihleri ve projeleri; zamanla doldurulur. Hassas bilgi yok (şifre, "
                    "kimlik, banka, adres, sağlık).",
                    "## Hedefler\n\n## Tercihler\n\n## Tasarım zevki\n\n## Projeler\n"),
    },
}

# Where each starting page lives (English base folder, or a tuple for a subfolder).
STARTER_FOLDERS = {"pending": "inbox", "handoff": "inbox", "rule-violations": "rules",
                   "lesson-candidates": "rules", "rejected-proposals": "ideas", "project-proposals": "ideas",
                   "blocked-sites": ("knowledge", "security"), "profile": "me"}

# Folder entry pages: English base folder -> (title, description) per language. An entry page is named after its
# folder, except where that name is already a template (`_templates/research.md`): two notes with one name make a wiki
# link such as [[research]] ambiguous in Obsidian. ENTRY_STEMS gives such a page its own English base name; its
# Turkish name comes from the `files` table of names.json.
ENTRY_STEMS = {"research": "research-notes"}
ENTRY_PAGES = {
    "en": {
        "inbox": ("Inbox", "Quick capture: new ideas and notes go here first; session records arrive in `sessions/`."),
        "projects": ("Projects", "Active projects. Each project has a main page, a progress note, its rules and "
                                 "decisions."),
        "ideas": ("Ideas", "Ideas that have matured beyond the inbox."),
        "councils": ("Councils", "Short records of work done with several agents (mode, agents, decision)."),
        "problems": ("Problems", "The central library of problems and their solutions, for every project."),
        "knowledge": ("Knowledge", "Concepts, methods, tools, source summaries and agent pages."),
        "research": ("Research", "Dated research notes."),
        "me": ("Me", "The user's profile and working environment. No sensitive information."),
        "rules": ("Rules", "The rules Claude follows, rule violations and lesson candidates."),
        "drafts": ("Drafts", "Drafts of posts and READMEs in the user's voice. Claude does not publish them."),
        "archive": ("Archive", "Everything finished or dropped. Nothing is deleted; it is moved here."),
    },
    "tr": {
        "inbox": ("Gelen", "Hızlı yakalama: yeni fikirler ve notlar önce buraya gelir; oturum kayıtları "
                           "`oturumlar/` altına düşer."),
        "projects": ("Projeler", "Aktif projeler. Her projenin ana sayfası, ilerleme notu, kuralları ve kararları "
                                 "vardır."),
        "ideas": ("Fikirler", "Gelen kutusundan olgunlaşarak çıkan fikirler."),
        "councils": ("Kurullar", "Birden çok ajanla yürüyen işlerin kısa kaydı (mod, ajanlar, karar)."),
        "problems": ("Sorunlar", "Bütün projeler için merkezî sorun ve çözüm kütüphanesi."),
        "knowledge": ("Bilgi", "Kavramlar, yöntemler, araçlar, kaynak özetleri ve ajan sayfaları."),
        "research": ("Araştırmalar", "Tarihli araştırma notları."),
        "me": ("Ben", "Kullanıcının profili ve çalışma ortamı. Hassas bilgi yok."),
        "rules": ("Kurallar", "Claude'un uyduğu kurallar, kural ihlalleri ve ders adayları."),
        "drafts": ("Taslaklar", "Kullanıcının ağzından gönderi ve README taslakları. Claude bunları yayınlamaz."),
        "archive": ("Arşiv", "Biten ya da bırakılan her şey. Hiçbir şey silinmez, buraya taşınır."),
    },
}

INDEX_PAGE = {
    "en": ("Index", "Every page of the vault, one line each. Add lines with `records.py index --section … --line …`.",
           {"start": "Start", "rules": "Rules", "inbox": "Inbox", "folders": "Folders"}),
    "tr": ("Dizin", "Vault'un her sayfası, her biri tek satır. Satırlar `records.py index --section … --line …` ile "
                    "eklenir.",
           {"start": "Başlangıç", "rules": "Kurallar", "inbox": "Gelen", "folders": "Klasörler"}),
}

LOG_PAGE = {
    "en": ("Log", "Append-only work log. Entries are added only with `records.py log`."),
    "tr": ("Log", "Yalnızca sona eklenen iş günlüğü. Girdiler yalnızca `records.py log` ile eklenir."),
}

USER_WORD = {"en": "the user", "tr": "kullanıcı"}
ASSISTANT_NAMES = {"antigravity": "Google Antigravity", "gemini": "Google Gemini CLI", "codex": "OpenAI Codex CLI"}


def text(language: str, key: str, /, **values) -> str:
    """The message `key` in `language` (English when the language is unknown), with `values` filled in."""
    table = MESSAGES.get(language) or MESSAGES["en"]
    return table[key].format(**values) if values else table[key]
