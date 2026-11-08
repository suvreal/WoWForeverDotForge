---
name: wow-forever-addons
description: Spravuje addony WoW Forever ve Faugus na Linuxu pomocí lokální aplikace Forever Addons. Použij pro instalaci, aktualizaci a kontrolu integrity těchto addonů i pro hledání v katalogu CurseForge.
---

Příkazy spouštěj systémovým Pythonem 3 z kořene projektu (`python3 app.py …`). Lokální instalace uživatele může být v `~/Applications/ForeverAddons`.

- `list`: inventář složek, verzí a zdrojů.
- `verify`: porovnání souborů se SHA-256 manifestem instalovaného balíčku; nenulový návrat při změnách. Nespravované addony nemají důvěryhodný výchozí manifest.
- `curse-search "dotaz" [--index 20]`: katalog CurseForge filtrovaný podle klienta; název, autor nebo číselné ID. Prázdný dotaz nabídne populární addony.
- `install-curseforge ID`: instalace nejnovějšího dostupného stabilního vydání pro klienta. Chybějící povinné závislosti vypíše názvem a ID; nainstaluj je nejdřív.
- `check`: kontrola kompatibilních stabilních vydání GitHubu a CurseForge.
- `update`: aktualizace spravovaných GitHub a CurseForge balíčků.
- `install-github OWNER/REPO`: distribuční ZIP ze stabilního vydání GitHubu.
- `install-zip /absolutní/cesta.zip`: import vybraného distribučního ZIPu, nové vydání se importuje stejně.
- `remove KLÍČ`: odstranění spravovaného balíčku se zálohou; klíč získáš z `list`.
- `restore`: vrácení poslední změny ze zálohy. Nahrazuje i lokální změny dotčených addonů; před použitím vysvětli dopad.
- `startup check|update|off`: režim při otevření aplikace, nikoli start systému.
- `gui`: desktopová aplikace.

Výchozí hra: `~/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_`; alternativně `FOREVER_GAME_DIR`. Cílem je pouze `Interface/AddOns`; nepřepisuj WTF, klienta, Battle.net ani `_classic_beta_`. Rozhraní se načítá z `WTF/Config.wtf`. Neobcházej kompatibilitu úpravou TOC. Deklarace TOC neprokazuje funkčnost API ve hře.

Nejdřív zkontroluj inventář a integritu. Lokální změny reportuj, neobcházej jejich ochranu. Při běžícím WoW neměň addony. Manifesty a zálohy v `~/.local/share/forever-addons` nemaž bez požadavku. Po instalaci spusť `verify` a reportuj výsledek. Integrita znamená porovnání s instalovaným balíčkem, ne kontrolu škodlivosti kódu.

CurseForge používá oficiální API. Klíč zadává uživatel v aplikaci nebo interaktivně přes `curse-key`; nikdy jej nepožaduj do chatu, nečti jeho obsah do výstupu a nepřidávej jej do Git repozitáře. Soubor `~/.config/forever-addons/curseforge.key` má oprávnění 0600; `CURSEFORGE_API_KEY` má přednost. Bez klíče reportuj chybějící připojení katalogu, nevydávej simulované výsledky za skutečné. Zákazy distribuce ani chybějící download URL neobcházej.

GitHub používá veřejné Releases API bez tokenu a prohlíží posledních 15 vydání. Nepřijímá prerelease ani source ZIP bez distribuční struktury. Při nedostupné síti nepotvrzuj aktuálnost ze samotného lokálního inventáře. Konkrétní addony instaluj podle uživatelova výběru nebo zadání.
