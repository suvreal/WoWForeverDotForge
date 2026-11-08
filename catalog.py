"""GTK catalog view; all network work runs through the application's worker."""
import urllib.parse
import webbrowser
from gi.repository import Gtk
from curseforge import KEY_FILE, PAGE_SIZE, game_version, load_key, save_key


class Catalog:
    def __init__(self, app, notebook):
        self.app = app
        self.result = None
        self.page_query = ''
        self.page_sort = 2
        self.row_buttons = []
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_margin_top(12)
        notebook.append_page(page, Gtk.Label(label='Procházet CurseForge'))
        header = Gtk.Box(spacing=10)
        self.key_status = Gtk.Label(xalign=0, hexpand=True, wrap=True)
        header.append(self.key_status)
        app.button(header, 'Nastavit API klíč', self.key_dialog)
        page.append(header)
        searchbar = Gtk.Box(spacing=8)
        self.search_entry = Gtk.Entry(placeholder_text='Název addonu, autor nebo ID projektu…', hexpand=True)
        self.search_entry.connect('activate', lambda *_: self.search())
        searchbar.append(self.search_entry)
        self.sort = Gtk.DropDown.new_from_strings(['Oblíbené', 'Naposledy aktualizované', 'Nejvíc stažené'])
        searchbar.append(self.sort)
        app.button(searchbar, 'Hledat', self.search)
        page.append(searchbar)
        version = game_version(app.manager.interface)
        page.append(Gtk.Label(label=f'WoW Forever {version} • stabilní vydání • kompatibilita ZIPu se ověří před instalací', xalign=0, wrap=True))
        self.rows = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.rows.add_css_class('boxed-list')
        scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=250)
        scroll.set_child(self.rows)
        page.append(scroll)
        navigation = Gtk.Box(spacing=8)
        app.button(navigation, '← Předchozí', lambda: self.page(-1))
        self.previous = navigation.get_last_child()
        self.page_label = Gtk.Label(label='Vyhledej addon nebo nech prázdné hledání pro populární addony.', hexpand=True, wrap=True)
        navigation.append(self.page_label)
        app.button(navigation, 'Další →', lambda: self.page(1))
        self.next = navigation.get_last_child()
        page.append(navigation)
        page.append(Gtk.Label(label='CurseForge katalog vyžaduje vlastní API klíč. Povinné závislosti se instalují zvlášť; případně je aplikace vypíše.', wrap=True, xalign=0))
        self.show_key_status()
        self.sync_buttons()

    def show_key_status(self):
        self.key_status.set_text('API klíč je nastavený. Připojení ověří první hledání.' if load_key()
                                 else 'Pro prohlížení a přímou instalaci nejdřív nastav CurseForge API klíč.')

    def sync_buttons(self):
        self.previous.set_sensitive(bool(self.result and self.result['index'] > 0))
        self.next.set_sensitive(bool(self.result and self.result['has_next']))
        for button, row in self.row_buttons:
            button.set_sensitive(row['allowed'])
            key = 'curseforge:' + str(row['id'])
            button.set_label('Aktualizovat' if key in self.app.manager.state['packages'] else 'Nainstalovat')

    def search(self):
        if self.app.busy:
            return
        query = self.search_entry.get_text().strip()
        sort = [2, 3, 6][self.sort.get_selected()]
        self.fetch_page(query, sort, 0)

    def page(self, direction):
        if self.result:
            self.fetch_page(self.page_query, self.page_sort, self.result['index'] + direction * PAGE_SIZE)

    def fetch_page(self, query, sort, index):
        self.app.run_task(lambda: self.app.manager.curse_search(query, index, sort),
                          lambda result: self.render(result, query, sort))

    def render(self, result, query, sort):
        self.result, self.page_query, self.page_sort = result, query, sort
        self.app.buttons = [b for b in self.app.buttons if b.get_ancestor(Gtk.ListBox) != self.rows]
        self.row_buttons = []
        while self.rows.get_first_child():
            self.rows.remove(self.rows.get_first_child())
        if not result['rows']:
            self.rows.append(Gtk.Label(label='Žádné výsledky pro tuto verzi hry. Zkus jiné hledání.', margin_top=25, margin_bottom=25))
        for row in result['rows']:
            content = Gtk.Box(spacing=14, margin_start=14, margin_end=14, margin_top=12, margin_bottom=12)
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, hexpand=True)
            title = Gtk.Label(label=row['name'], xalign=0, wrap=True)
            title.add_css_class('heading')
            text.append(title)
            text.append(Gtk.Label(label=row['summary'], xalign=0, wrap=True, max_width_chars=70))
            info = f"{row['authors']} • {row['downloads']:,.0f} stažení • {row['updated']} • ID {row['id']}"
            detail = Gtk.Label(label=info, xalign=0, wrap=True)
            detail.add_css_class('dim-label')
            text.append(detail)
            content.append(text)
            actions = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.app.button(actions, 'Nainstalovat', lambda mid=row['id']: self.app.run_task(lambda: self.app.manager.curseforge(mid)))
            install = actions.get_last_child()
            self.row_buttons.append((install, row))
            if not row['allowed']:
                install.set_tooltip_text('Autor nepovoluje instalaci přes jiné správce. Otevři web a stáhni ZIP ručně.')
            self.app.button(actions, 'Stránka addonu ↗', lambda url=row['url']: self.open_page(url))
            content.append(actions)
            self.rows.append(content)
        start = result['index'] + 1 if result['count'] else 0
        self.page_label.set_text(f"{start}–{result['index'] + result['count']} z {result['total']} výsledků")
        return f"Katalog CurseForge • WoW {result['version']} • načteno {len(result['rows'])} addonů"

    def open_page(self, url):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme == 'https' and parsed.hostname in {'www.curseforge.com', 'curseforge.com'}:
            webbrowser.open(url)

    def key_dialog(self):
        dialog = Gtk.Dialog(title='Připojit CurseForge katalog', transient_for=self.app.get_active_window(), modal=True)
        dialog.set_default_size(560, 260)
        dialog.add_button('Zrušit', Gtk.ResponseType.CANCEL)
        dialog.add_button('Uložit', Gtk.ResponseType.ACCEPT)
        box = dialog.get_content_area()
        box.set_spacing(12)
        for side in ['top', 'bottom', 'start', 'end']:
            getattr(box, 'set_margin_' + side)(18)
        box.append(Gtk.Label(label='Vlož svůj CurseForge API klíč. Klíč se neposílá do GitHubu ani do chatu.', wrap=True, xalign=0))
        entry = Gtk.PasswordEntry(show_peek_icon=True, hexpand=True)
        box.append(entry)
        box.append(Gtk.Label(label='Nový klíč nahradí uložený. Prázdné pole ponechá současný klíč.', wrap=True, xalign=0))
        box.append(Gtk.Label(label=f'Lokální soubor pouze pro tvého uživatele: {KEY_FILE}', wrap=True, xalign=0, selectable=True))
        link = Gtk.LinkButton(uri='https://docs.curseforge.com/rest-api/#getting-started', label='Jak požádat o vlastní API klíč ↗')
        box.append(link)
        forget = Gtk.CheckButton(label='Zapomenout uložený klíč')
        box.append(forget)
        def response(d, code):
            if code == Gtk.ResponseType.ACCEPT:
                try:
                    value = entry.get_text().strip()
                    if forget.get_active():
                        save_key('')
                    elif value:
                        save_key(value)
                    self.show_key_status()
                    self.app.log.get_buffer().set_text('Nastavení klíče uloženo. Pro načtení katalogu stiskni Hledat.')
                except Exception as error:
                    self.app.log.get_buffer().set_text('Klíč se nepodařilo uložit: ' + str(error))
            entry.set_text('')
            d.destroy()
        dialog.connect('response', response)
        dialog.present()
