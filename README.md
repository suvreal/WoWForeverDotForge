# WoWForeverDotForge

Lokální linuxový správce addonů **Forever Addons** pro World of Warcraft Forever ve Faugus. Nativní aplikace v GTK 4 a příkazová obsluha bez dalších Python balíčků pro správu addonů.

Umí instalaci z GitHub Releases, distribučních ZIPů a oficiálního katalogu CurseForge, aktualizace při otevření aplikace nebo tlačítkem, kontrolu souborů, zálohy a obnovu. Není přidružen k Blizzardu ani CurseForge.

## Spuštění

Vyžaduje Python 3.10+, PyGObject, GTK 4 a grafickou relaci. Například na Debianu/Ubuntu:

```sh
sudo apt install python3 python3-gi gir1.2-gtk-4.0
git clone https://github.com/suvreal/WoWForeverDotForge.git
cd WoWForeverDotForge
python3 install.py --desktop
python3 app.py
```

Instalátor vytvoří položku nabídky aplikací a volitelně ikonku na ploše. Spouštěč odkazuje do tohoto adresáře, proto jej po instalaci nepřesouvej. Na některých desktopech je potřeba jednou zvolit „Povolit spuštění“.

Výchozí cesta hry je `~/Faugus/battlenet/drive_c/Program Files (x86)/World of Warcraft/_forever_`. Jinou instalaci nastav proměnnou `FOREVER_GAME_DIR`. Cíl musí být složka `_forever_` s `Wow.exe`; klient musí být alespoň jednou spuštěný, aby existoval `WTF/Config.wtf` s údajem `engineSurveyPatch`.

## CurseForge katalog

1. Otevři záložku **Procházet CurseForge** a **Nastavit API klíč**.
2. Zadej vlastní CurseForge API klíč. O klíč pro aplikace třetích stran lze požádat přes odkaz v [oficiální dokumentaci](https://docs.curseforge.com/rest-api/#getting-started). Přihlašovací heslo nebo běžný přihlašovací token není API klíč.
3. Hledej název, autora nebo číselné ID projektu. Prázdné hledání zobrazí populární addony pro verzi klienta. Výsledky lze řadit a procházet po stránkách.
4. Klikni **Nainstalovat**. Správce vybere nejnovější dostupné stabilní vydání pro přesnou verzi hry, ověří kontrolní součet z API a deklaraci Interface uvnitř ZIPu. Beta a alpha vydání se automaticky neinstalují.

API klíč se ukládá pouze do `~/.config/forever-addons/curseforge.key` s oprávněním `0600`, mimo zdrojové soubory a zálohy. Není šifrovaný. Lze jej smazat v nastavení; alternativně je podporována proměnná `CURSEFORGE_API_KEY`, která má přednost před souborem. Do chatu ani repozitáře klíč nevkládej.

Katalog používá oficiální API a bez vlastního platného klíče se nenačte. Pokud autor zakázal distribuci jinými správci nebo API nenabízí stažení, otevři stránku addonu a importuj ZIP ručně. Aplikace tyto zákazy neobchází. Povinné závislosti se instalují zvlášť; jejich názvy a ID aplikace vypíše. Všechny spravované CurseForge balíčky se kontrolují a aktualizují i přes **Aktualizovat vše**.

## GitHub, ZIPy a ochrana souborů

GitHub instalace používá distribuční ZIPy ze stabilních Releases, nikoli automatické archivy zdrojů. Prohlíží posledních 15 vydání. Ruční ZIPy se aktualizují opětovným importem. ZIP musí obsahovat složky addonů a jejich TOC; každý addon musí deklarovat přesný Interface klienta. Samotná deklarace nezaručuje funkčnost API ve hře.

Před změnou vznikne záloha. Kontrola integrity porovnává SHA-256 jednotlivých souborů s manifestem při instalaci. Detekuje změny, přidané a chybějící soubory; neposuzuje škodlivost addonového kódu. Lokální změny blokují přepsání. Nespravované složky se zobrazí, ale automaticky nepřebírají.

**Obnovit poslední zálohu** vrátí stav před poslední instalací, aktualizací nebo odstraněním; nahrazuje současné soubory dotčených addonů. Data jsou v `~/.local/share/forever-addons`. Zálohy se automaticky nemažou. Při přerušení zápisu je další změna blokována do obnovy. Nastavení postav ve `WTF` se nemění. Před instalací ukonči hru a během změn ji nespouštěj.

Volba „Při spuštění aplikace“ se týká otevření správce; aplikace se sama nespouští při přihlášení do Linuxu ani neběží na pozadí.

## Příkazová obsluha

```sh
python3 app.py list
python3 app.py verify
python3 app.py curse-key
python3 app.py curse-search "unit frames"
python3 app.py curse-search "" --index 20
python3 app.py install-curseforge ID_PROJEKTU
python3 app.py install-github VLASTNIK/REPOZITAR
python3 app.py install-zip /cesta/addon.zip
python3 app.py check
python3 app.py update
python3 app.py remove curseforge:ID_PROJEKTU
python3 app.py restore
python3 app.py startup check
```

## Vývoj a ověření

```sh
python3 -m unittest discover -v
python3 -m py_compile app.py catalog.py core.py curseforge.py install.py
```

Testy používají izolované falešné instalace a simulované API; nepotřebují API klíč a nemění skutečnou hru. Pokrývají instalaci, aktualizaci, obnovu, ochranu před přepsáním, validaci ZIPů, výběr verze a kontrolní součty CurseForge. Ověření skutečného katalogu vyžaduje platný klíč a internet; GUI vyžaduje desktopovou relaci.

Projekt obsahuje skill `wow-forever-addons` v `skill/` a odkaz v `.agents/skills/`. Otevři projekt v Codexu pro jeho použití. PR zprávy používají formát `BEL: {MESSAGE}`.
