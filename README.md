# WoWForeverDotForge

**Forever Addons** je lokální linuxový správce addonů pro World of Warcraft Forever ve Faugus. Nabízí nativní okno v GTK 4, katalog CurseForge, instalaci z GitHub Releases a ZIPů, aktualizace, kontrolu souborů a zálohy. Není přidružen k Blizzardu ani CurseForge.

## Co potřebuješ

- Linux s Pythonem 3.10 nebo novějším. Pro okno aplikace také PyGObject, GTK 4 a přihlášenou grafickou relaci.
- Nainstalovaný WoW Forever, který jsi alespoň jednou spustil a normálně ukončil. Musí existovat `_forever_/Wow.exe` a `_forever_/WTF/Config.wtf` s údajem `engineSurveyPatch`.
- Právo zápisu do `Interface/AddOns` a volné místo pro stažení, rozbalení i zálohu předchozí verze. Správce spouštěj jako svůj běžný linuxový uživatel.
- Připojení k internetu pro katalog a aktualizace. Lokální inventář, ověření souborů, import již staženého ZIPu a obnova fungují bez internetu.
- Vlastní schválený CurseForge API klíč pro vestavěný katalog. GitHub instalace a ruční ZIPy jej nepotřebují.

Battle.net ani Faugus nemusí být při správě addonů otevřené. Samotnou hru před instalací, aktualizací, odstraněním nebo obnovou ukonči a během operace ji nespouštěj.

## 1. Instalace aplikace

### Pop!_OS 22.04, Ubuntu a Debian

```bash
sudo apt update
sudo apt install git python3 python3-gi gir1.2-gtk-4.0 xdg-user-dirs
mkdir -p "$HOME/Applications"
git clone https://github.com/suvreal/WoWForeverDotForge.git "$HOME/Applications/WoWForeverDotForge"
cd "$HOME/Applications/WoWForeverDotForge"
/usr/bin/python3 --version
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk; print("GTK 4 dostupné")'
/usr/bin/python3 install.py --desktop
/usr/bin/python3 app.py
```

Na jiných distribucích nainstaluj jejich balíčky poskytující Python 3.10+, modul `gi`, introspekční data GTK 4 a `xdg-user-dir`. Hlavní příkazy dál používej z adresáře s `app.py`. Aplikace nevyžaduje `pip install`, Wine ani Windows verzi CurseForge. Použij systémový Python: virtuální prostředí obvykle nevidí distribuční balíček `python3-gi`.

Pokud už tento projekt máš v `~/Applications/ForeverAddons`, pracuj v tomto existujícím adresáři. Nemusíš vytvářet druhou instalaci. Je-li cílový adresář neprázdný, `git clone` do něj nepoužívej.

Instalátor pouze zaregistruje aplikaci z aktuálního umístění. Vytvoří `~/.local/share/applications/forever-addons.desktop` a s `--desktop` také `Forever Addons.desktop` ve složce vrácené příkazem `xdg-user-dir DESKTOP`. Zdrojové soubory nikam nekopíruje. Po přesunu projektu spusť instalátor znovu. Pokud desktop vyžaduje důvěru, klikni pravým tlačítkem na ikonku a zvol **Povolit spuštění**. Bez funkční složky plochy lze použít samotné `python3 install.py` a nabídku aplikací.

## 2. Nastavení instalace hry

Výchozí cesta je:

```text
~/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_
```

V záhlaví aplikace zkontroluj výslednou cestu `Interface/AddOns` a Interface načtený z klienta. Správce cílí výhradně na složku nazvanou `_forever_`; `_classic_beta_`, Classic Era ani Retail nepodporuje. Neupravuj TOC ani nastavení klienta jen proto, abys obešel kontrolu kompatibility.

### Hra na jiném disku nebo v jiném prefixu

Proměnná `FOREVER_GAME_DIR` musí obsahovat úplnou cestu ke složce `_forever_`, nikoli přímo k `Interface/AddOns`. Příklad pro jedno spuštění:

```bash
FOREVER_GAME_DIR='/mnt/hry/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_' /usr/bin/python3 app.py
```

Stejnou proměnnou používej také při příkazech `list`, `verify`, `check` a ostatních operacích pro tuto instalaci. Program si cestu do hry neukládá do nastavení.

Pro trvalé spuštění ikonou změň řádek `Exec=` v příslušném `.desktop` souboru. Například:

```ini
Exec=/usr/bin/env "FOREVER_GAME_DIR=/mnt/hry/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_" /usr/bin/python3 "/home/TVUJ_UZIVATEL/Applications/WoWForeverDotForge/app.py"
```

Nahraď cesty skutečnými absolutními cestami. `.desktop` soubor nerozbaluje `~` ani `$HOME`. Řádek uprav v položce nabídky i v kopii na ploše, pokud používáš obě. Samotné `FOREVER_GAME_DIR=… python3 install.py` cestu do spouštěče neuloží; další spuštění instalátoru vlastní řádek `Exec=` přepíše.

**Více instalací hry:** současná verze má jeden registr balíčků a záloh na linuxového uživatele. Přepínání `FOREVER_GAME_DIR` nevytváří oddělený profil. Pro běžnou správu používej jednu instalaci na uživatele; různá samostatná prostředí odděl linuxovými účty. Aplikace zatím nemá přepínač herních profilů.

## 3. CurseForge účty a API přístup

### Který účet nebo klíč je potřeba

| Přístup | Jak ho aplikace používá |
| --- | --- |
| Běžný účet na webu CurseForge | Přihlášení probíhá ve tvém prohlížeči. Aplikace z něj nepřebírá relaci ani oprávnění API. |
| Schválený přístup třetí strany k CurseForge API | Jeho klíč umožní vestavěné hledání, přímou instalaci a aktualizace. |
| Účet vydavatele hry v CurseForge for Studios | Je určen vydavatelům vlastních her. Kvůli správě WoW addonů nezakládej novou hru. |
| Účet Battle.net | Slouží hře; do tohoto správce se nezadává. |
| Účet GitHub | Pro běžné stahování veřejných GitHub Releases není potřeba. Pro push do tohoto projektu je potřeba zvlášť. |

Klient podporuje **jeden aktivní API klíč na proces**. Nemá OAuth přihlášení, seznam CurseForge účtů, cloudovou synchronizaci, import oblíbených položek ani oddělené sestavy addonů podle webového účtu. Změna přihlášení ve webovém prohlížeči aktivní klíč aplikace nezmění.

### Získání vlastního API klíče

1. Otevři [oficiální návod pro získání CurseForge API klíče](https://support.curseforge.com/support/solutions/articles/9000208346-about-the-curseforge-api-and-how-to-apply-for-a-key).
2. Použij tam odkaz na žádost pro vývojáře aplikací třetích stran. Popiš skutečný projekt, jeho GitHub adresu a zamýšlené hledání a stahování WoW addonů.
3. Dokonči požadované podmínky a schvalovací postup. API přístup není automatickým důsledkem vytvoření běžného webového účtu; dostupnost a schválení určuje CurseForge.
4. Po schválení použij klíč přidělený tvému přístupu. Řiď se podmínkami tohoto klíče, včetně jeho případného omezení na konkrétní aplikaci.

[Dokumentace API](https://docs.curseforge.com/rest-api/) rozlišuje poskytovatele her a aplikace třetích stran. Nestahuj cizí klíče ze zdrojových kódů jiných správců. Klíčem není heslo k účtu, webová cookie ani token Battle.net.

### Zadání klíče do aplikace

1. Otevři **Procházet CurseForge → Nastavit API klíč**.
2. Vlož klíč do skrytého pole a klikni **Uložit**.
3. Nech vyhledávání prázdné a klikni **Hledat**, případně zadej název addonu.
4. Úspěchem je skutečně načtený seznam nebo platná prázdná odpověď katalogu. Hláška „klíč je nastavený“ pouze potvrzuje přítomnost klíče, ne jeho platnost.

Klíč se ukládá nešifrovaně do `~/.config/forever-addons/curseforge.key` s oprávněním `0600`. Soubor je mimo repozitář, registr addonů i zálohy. Nezobrazuj jej příkazem `cat`, nevkládej ho do chatu, ticketů, `.desktop` souborů ani Git commitu. Případnou revokaci proveď u poskytovatele API a pak zadej nový klíč.

Alternativa přes terminál se skrytým vstupem:

```bash
/usr/bin/python3 app.py curse-key
/usr/bin/python3 app.py curse-search ""
```

### Přepnutí na jiný vlastní CurseForge přístup

**Běžné nahrazení uloženého klíče:** zavři aplikaci. Pokud používáš terminál, spusť `unset CURSEFORGE_API_KEY`, otevři z něj aplikaci a v dialogu nastavení ulož klíč druhého přístupu. Klíč se přepíše, ale nainstalované addony a zálohy zůstanou stejné. Přepsání souboru nerevokuje původní klíč u CurseForge.

**Zapomenutí klíče:** v dialogu zaškrtni **Zapomenout uložený klíč** a ulož. V CLI příkazu `curse-key` lze nechat vstup prázdný. Prázdné pole v grafickém dialogu naopak existující klíč ponechá.

**Proměnná prostředí má přednost:** neprázdná `CURSEFORGE_API_KEY` přebije uložený soubor. Smazání souboru nebo změna v dialogu tuto proměnnou procesu nezmění. Pro návrat k souboru aplikaci zavři, zruš proměnnou v prostředí, ze kterého ji spouštíš, a otevři ji znovu. Druhé spuštění při již běžícím okně může pouze aktivovat původní okno s původním prostředím.

### Dva nebo více klíčů pod stejným linuxovým účtem

Vestavěné pojmenované profily zatím nejsou k dispozici. Máš-li oprávněně více vlastních API klíčů, můžeš si je držet v oddělených souborech mimo projekt a vybraný předat procesu. Následující příkazy jsou pro **Bash** a nevkládají hodnotu klíče do historie příkazů:

```bash
(
    umask 077
    mkdir -p "$HOME/.config/forever-addons/accounts"
    read -r -s -p 'API klíč přístupu A: ' cf_profile_key
    printf '\n'
    printf '%s' "$cf_profile_key" > "$HOME/.config/forever-addons/accounts/pristup-a.key"
    unset cf_profile_key
)
```

Pro druhý přístup zopakuj uložení s názvem `pristup-b.key`. Před spuštěním s jiným klíčem ukonči všechna okna aplikace. Z adresáře projektu pak spusť:

```bash
CURSEFORGE_API_KEY="$(< "$HOME/.config/forever-addons/accounts/pristup-a.key")" /usr/bin/python3 app.py
```

Pro přístup B použij druhý soubor. Klíč se předává prostředím, nikoli argumentem příkazu, a aplikace jej neukládá do společného souboru. Nesdílej prostředí ani diagnostický výpis procesu s cizími lidmi. Tyto soubory spravuješ ručně; volba **Zapomenout uložený klíč** je nemaže.

Tímto se přepíná pouze API přístup. Stejný linuxový uživatel stále používá **stejné addony, manifesty, zálohy a nastavení automatických kontrol**. Pro dva lidi se samostatnými daty použij dva linuxové účty a každému nastav jeho vlastní instalaci a klíč podle pravidel CurseForge. Přístup ke složce hry musí mít každý z nich samostatně vyřešený.

### Používání bez API klíče

Přes tlačítko stránky addonu můžeš otevřít web, stáhnout kompatibilní ZIP a použít **Import ZIPu**. Bez připojeného katalogu otevři přímo [webové hledání CurseForge](https://www.curseforge.com/wow/search?class=addons). Dostupné zůstávají také GitHub Releases a místní kontrola souborů. Ručně importované ZIPy se nepropojí automaticky s CurseForge projektem a aktualizují se dalším importem.

## 4. Instalace a běžné používání

### Z katalogu CurseForge

1. V **Procházet CurseForge** vyhledej název, autora nebo číselné ID projektu. Prázdný dotaz nabídne populární výsledky. Vyber řazení a použij **Předchozí / Další** pro další stránky.
2. Klikni **Nainstalovat**. Výběr souboru přijímá dostupná stabilní vydání pro přesnou verzi klienta a poté ověří velikost, kontrolní součet z API i TOC Interface uvnitř ZIPu. Beta, alpha a early-access soubory se automaticky neinstalují. Samotný výsledek hledání tedy ještě nezaručuje instalovatelné stabilní vydání.
3. Pokud aplikace vypíše povinnou závislost názvem a ID, nainstaluj nejdřív ji a původní instalaci opakuj. Závislosti se nestahují automaticky. Ručně nebo přes GitHub instalovanou knihovnu správce nemusí rozpoznat jako splněnou závislost konkrétního CurseForge projektu.
4. Pokud autor zakázal distribuci jinými správci nebo API neposkytne stažení, použij stránku addonu a ruční ZIP. Správce zákaz neobchází.
5. Po úspěšné instalaci otevři **Nainstalované addony → Ověřit soubory**. Teprve po dokončení operací spusť WoW a ověř načtení addonu přímo ve hře.

Filtr verze a TOC jsou deklarace autora; nezaručují, že addon bez chyby funguje s aktuálním herním API.

### Z GitHub Releases

Do pole GitHub zadej `VLASTNIK/REPOZITAR` nebo hlavní URL repozitáře. Správce prohlíží posledních 15 vydání a hledá kompatibilní distribuční ZIP ve stabilním vydání. Ignoruje prerelease a `nolib` balíčky. Automatický **Source code (zip)** obvykle nemá správnou distribuční strukturu; není náhradou za publikovaný addon balíček.

### Z vlastního ZIPu

Klikni **Import ZIPu** a vyber archiv. Očekávaná struktura:

```text
Addon.zip
└── NazevAddonu/
    ├── NazevAddonu.toc
    └── ...soubory addonu...
```

Archiv může obsahovat více addonů, každý ale musí mít přijatelné TOC pro aktuální Interface. Archiv nesmí obsahovat nebezpečné cesty, symlinky ani spustitelné soubory. Limit staženého/importovaného ZIPu je 100 MB; rozbalený archiv má limit 400 MB a 25 000 položek.

Existující nespravované složky aplikace zobrazí, ale nepřevezme je ani nepřepíše automaticky. Neodstraňuj je jen kvůli obejití hlášení o kolizi; případnou migraci proveď s vlastní zálohou a ověřením zdroje.

### Aktualizace a kontrola při otevření

- **Zkontrolovat aktualizace** vyhledá kompatibilní vydání.
- **Aktualizovat vše** provede aktualizace spravovaných GitHub a CurseForge balíčků, pokud nebrání kompatibilita, chybějící závislost, síťová chyba nebo lokální změny.
- Ruční ZIP se aktualizuje opětovným importem nového distribučního ZIPu se stejnými složkami.
- Volba **Při spuštění aplikace** nabízí kontrolu, automatickou aktualizaci nebo vypnutí. Týká se otevření správce; nevytváří službu ani automatické spouštění při přihlášení do Linuxu.

Po hromadné operaci si přečti celý výpis. Jednotlivé balíčky se zpracovávají samostatně: chyba jednoho nevylučuje úspěch jiného. CLI `check` a `update` mohou vrátit kód 0 i při chybě některého balíčku uvedené ve výpisu; pro automatizaci nespoléhej jen na návratový kód.

## 5. Integrita, zálohy a obnova

**Ověřit soubory** porovnává SHA-256 souborů s manifestem vytvořeným při instalaci. Hlásí změněné, přidané a chybějící soubory. Není to antivir ani nezávislé potvrzení důvěryhodnosti autora. U nespravovaných addonů chybí výchozí manifest a stav **Nespravovaný** neznamená ověřenou integritu.

Před instalací, aktualizací nebo odstraněním vzniká záloha dotčených addonů. Při selhání zápisu se správce pokusí vrátit předchozí stav. Po přerušení procesu může zbýt `pending.json`; další změny jsou potom blokované do obnovy.

**Obnovit poslední zálohu** vrací stav před poslední operací. Nahrazuje aktuální obsah dotčených složek, včetně tvých pozdějších úprav. Při aktualizaci více balíčků postupně vrátí poslední jednotlivou operaci; nejde o jediné tlačítko pro vrácení celé dávky. Opakování obnovy neprochází automaticky starší zálohy. Lokální změny blokují aktualizaci i odstranění: nejdřív si je uchovej a rozhodni, zda je chceš zachovat, nebo obnovit předchozí stav. Současná verze nemá tlačítko pro opravu souborů ze stejného nainstalovaného archivu.

| Umístění | Obsah |
| --- | --- |
| `~/.config/forever-addons/curseforge.key` | Uložený API klíč; práva 0600, bez šifrování. |
| `~/.local/share/forever-addons/state.json` | Registry zdrojů, verze, manifesty a režim při otevření. |
| `~/.local/share/forever-addons/backups/` | Zálohy před změnami; automaticky se nemažou. |
| `~/.local/share/forever-addons/pending.json` | Záznam nedokončené operace, pokud existuje. |
| `_forever_/Interface/AddOns/` | Samotné addony. |
| `_forever_/WTF/` | Nastavení klienta, postav a addonů; správce je nepřepisuje ani nezálohuje. |

Při migraci uchovej spolu addony a celý datový adresář správce. Nesmaž `state.json` kvůli chybě integrity: ztratil bys evidenci a původní manifesty. Nastavení ve WTF zálohuj zvlášť podle své potřeby.

## 6. Ověření funkčního běhu a řešení potíží

Z kořene projektu:

```bash
/usr/bin/python3 app.py list
/usr/bin/python3 app.py verify
/usr/bin/python3 app.py curse-search ""
/usr/bin/python3 app.py check
```

`list` vypíše skutečné lokální složky; `[]` je u prázdné instalace v pořádku. `verify` vrací 1 při změně či chybě spravovaných souborů, 0 jinak; kód 0 u nespravovaných složek neznamená, že byly ověřeny. Výsledek `curse-search` musí pocházet z API bez chyby připojení. Po prvním vybraném addonu ověř soubory a pak jeho načtení ve hře. Úspěšné automatické testy samy o sobě nedokazují platný klíč, funkční síť nebo zobrazení okna.

| Potíž | Co ověřit |
| --- | --- |
| `No module named gi` / GTK není dostupné | Doinstaluj balíčky z kroku 1 a použij `/usr/bin/python3` mimo virtuální prostředí. |
| Grafická relace není dostupná | Otevři aplikaci z terminálu přihlášeného desktopu, bez `sudo`. Přes běžné SSH bez grafické relace používej CLI. |
| Není to instalace `_forever_` | Cesta musí končit `_forever_` a uvnitř mít `Wow.exe`. Zkontroluj `FOREVER_GAME_DIR` i řádek `Exec=` ikonky. |
| Nelze zjistit Interface | Spusť správnou verzi hry a ukonči ji. Ověř existenci jejího `WTF/Config.wtf`; nevymýšlej číslo ručně. |
| API klíč je nastavený, ale katalog hlásí 401/403 | Ověř schválení a platnost vlastního API přístupu a případnou přednost `CURSEFORGE_API_KEY`. Samotné přihlášení na web nestačí. |
| Změna/smazání klíče nepomohla | Ukonči původní okno, zruš proměnnou prostředí a spusť nový proces. |
| Prázdný katalog nebo chybí stabilní ZIP | Zkus jiný dotaz/ID a ověř, že autor vydává stabilní balíček pro přesnou verzi klienta. Verzi aplikace neobcházej přepsáním TOC. |
| Chybí závislost | Vyhledej a nainstaluj uvedené ID; potom původní addon opakuj. |
| Zakázaná distribuce / chybí URL | Otevři web projektu a použij povolené ruční stažení a import. |
| HTTP 429 | Počkej a opakuj později; nejde o důvod měnit účet. |
| Nedostupná síť / `Could not resolve host` | Ověř `getent hosts api.curseforge.com github.com` v normálním terminálu. Omezená síť prostředí agenta je odlišná od sítě desktopu. |
| WoW stále běží / jiná operace běží | Ukonči hru a počkej na dokončení jiné instance správce. |
| Lokální změny / nedokončená operace | Uchovej vlastní úpravy; podle situace použij obnovu. Neodstraňuj ochranné záznamy jen pro odblokování zápisu. |
| Nedostatečná oprávnění | Zkontroluj vlastnictví konkrétní herní složky. Nespouštěj celý správce přes `sudo`. |
| Dvojklik na ikonku nic neukáže | Spusť `/usr/bin/python3 app.py` v terminálu, přečti chybu a zkontroluj absolutní `Exec=`. Po přesunu projektu znovu spusť instalátor. |

## 7. Příkazová obsluha

```bash
/usr/bin/python3 app.py --help
/usr/bin/python3 app.py list
/usr/bin/python3 app.py verify
/usr/bin/python3 app.py curse-key
/usr/bin/python3 app.py curse-search "unit frames"
/usr/bin/python3 app.py curse-search "" --index 20
/usr/bin/python3 app.py install-curseforge ID_PROJEKTU
/usr/bin/python3 app.py install-github VLASTNIK/REPOZITAR
/usr/bin/python3 app.py install-zip /cesta/addon.zip
/usr/bin/python3 app.py check
/usr/bin/python3 app.py update
/usr/bin/python3 app.py remove curseforge:ID_PROJEKTU
/usr/bin/python3 app.py restore
/usr/bin/python3 app.py startup check
```

Řetězce `ID_PROJEKTU`, `VLASTNIK/REPOZITAR` a cesty jsou zástupné hodnoty. Klíč pro `remove` zjistíš z položky `source` v `list`; může začínat také `github:` nebo `zip:`. Režimy `startup` jsou `check`, `update`, `off`. Ne všechny chyby hromadných operací znamenají nenulový návratový kód; čti jejich výpis.

## 8. Aktualizace a odebrání správce

Před aktualizací aplikaci zavři a z adresáře projektu spusť:

```bash
git status --short
git pull --ff-only
/usr/bin/python3 -m unittest discover -v
/usr/bin/python3 app.py
```

Pokud máš vlastní změny kódu nebo konflikt historie, nepřepisuj je násilím; nejdřív je vyřeš. `git pull` vyžaduje publikovanou historii repozitáře. Kvůli běžné aktualizaci ve stejném adresáři není nutné znovu instalovat ikonky.

Pro odebrání aplikaci ukonči a odstraň její položku nabídky, ikonku na ploše a případně adresář zdrojového projektu. Nainstalované addony, data správce a API klíče tím automaticky nezmizí. Zachovej zálohy, dokud je můžeš potřebovat. Odstranění lokálního souboru klíče nerevokuje API klíč u CurseForge.

## 9. Vývoj, GitHub přístup a push

Použij účet s oprávněním zapisovat do `suvreal/WoWForeverDotForge`. GitHub přístup je nezávislý na CurseForge klíči i účtu Battle.net.

### Přihlášení z vlastního linuxového terminálu

Pokud chybí GitHub CLI, na systémech s dostupným balíčkem jej nainstaluj přes `sudo apt install gh`. Zkontroluj síť a přihlas se interaktivně v prohlížeči:

```bash
getent hosts github.com
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
gh auth setup-git
gh auth status
```

Přihlášení dokonči ve vlastním prohlížeči pod účtem s přístupem do projektu. Rozšíření `workflow` je potřebné pro push zdejšího `.github/workflows/tests.yml` při použití OAuth přístupu. Heslo ani token nevkládej do chatu. Pokud máš v `gh` více přihlášení, vyber správné přes `gh auth switch --hostname github.com --user suvreal`; samotné přepnutí ale neobnoví neplatný token. Postup vychází z [návodu GitHub CLI](https://cli.github.com/manual/gh_auth_login).

Používáš-li místo tohoto postupu vlastní fine-grained token, omez jej na tento repozitář a nastav potřebná oprávnění **Contents: Read and write**, pro zdejší workflow také **Workflows: Read and write** a pro vytváření PR **Pull requests: Read and write**. Respektuj jeho expiraci a případné schválení organizací. Pro přihlášení jej použij bezpečnou cestou popsanou v [dokumentaci GitHubu](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens); nedávej jej do URL `origin` ani do souborů projektu.

### První push do prázdného repozitáře

Pro již připravenou lokální Git historii, po kontrole obsahu commitu:

```bash
git status --short
git log -3 --oneline
git remote get-url origin
git ls-remote origin
git push -u origin main
```

Očekávaný remote je `https://github.com/suvreal/WoWForeverDotForge.git`. Prázdný výstup `git ls-remote origin` s návratovým kódem 0 znamená repozitář bez refů; chyba připojení nebo autentizace není potvrzením prázdného repozitáře. Jestli mezitím na serveru vznikly commity, nejdřív je načti a historii zkontroluj. Nepoužívej `--force` jako opravu chyby přihlášení nebo rozdílné historie.

### Další změny přes pull request

```bash
git switch -c docs/setup-and-accounts
# Uprav soubory a zkontroluj diff; přidej jen zamýšlené soubory.
git add README.md
git commit -m 'BEL: Document installation and account setup'
git push -u origin HEAD
gh pr create --base main --title 'BEL: Document installation and account setup' --body 'BEL: Add installation, configuration, account switching and verification instructions.'
```

PR titulky a zprávy mají formát **`BEL: {MESSAGE}`**. Pro první publikaci aplikace v dosud prázdném repozitáři musí nejdřív vzniknout výchozí větev; proti neexistující `main` nelze otevřít PR.

### Když push blokuje konektor nebo prostředí agenta

Chyba GitHub API **403 `Resource not accessible by integration`** znamená nedostatečná oprávnění integračního tokenu pro konkrétní operaci. To je jiná věc než oprávnění vlastníka repozitáře. Zkontroluj instalaci příslušné GitHub App v [nastavení GitHub aplikací](https://github.com/settings/installations), její přístup k tomuto repozitáři a případné schválení nových oprávnění. Pokud aplikace požadované oprávnění nenabízí, použij vlastní GitHub CLI přihlášení. Nastavení práv workflow v GitHub Actions neopravuje token externího konektoru. Viz [diagnostika GitHub REST API](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api#resource-not-accessible).

`gh auth status` hlásící neplatný token v prostředí bez funkční sítě není samo o sobě důkazem, že token byl na GitHubu revokován. Ověř jej z normálního terminálu s internetem. Obnovení `gh` přihlášení zároveň nezmění token samostatného konektoru. Push musí skončit potvrzením aktualizované vzdálené větve; lokální commit ani úspěšné testy nestačí.

## 10. Testy a známé hranice ověření

```bash
/usr/bin/python3 -m unittest discover -v
/usr/bin/python3 -m py_compile app.py catalog.py core.py curseforge.py install.py
```

Testy pracují s izolovanými falešnými instalacemi a simulovaným API, bez API klíče a bez změn skutečné hry. Ověřují instalaci, aktualizaci, obnovu, lokální změny, odmítnutí nebezpečných ZIPů, výběr verze a kontrolní součty CurseForge. Nevytvářejí grafické okno ani skutečně nestahují addony. End-to-end ověření vyžaduje grafickou relaci, funkční internet, vlastní schválený klíč a vybraný kompatibilní addon; postup je v části 6.

Projekt obsahuje skill `wow-forever-addons` v `skill/` a odkaz v `.agents/skills/`. Otevři projekt v Codexu pro jeho použití. Skill používá stejnou příkazovou obsluhu a stejné ochrany jako aplikace.
