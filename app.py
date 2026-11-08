#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys
import threading
import webbrowser
from core import Manager


def gui():
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, GLib, Gio, Gdk

    class App(Gtk.Application):
        def __init__(self):
            super().__init__(application_id='cz.local.ForeverAddons', flags=Gio.ApplicationFlags.FLAGS_NONE)
            self.manager = Manager()
            self.busy = False

        def do_activate(self):
            if self.get_active_window():
                self.get_active_window().present()
                return
            win = Gtk.ApplicationWindow(application=self, title='Forever Addons')
            win.set_default_size(1050, 740)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            for side in ['top', 'bottom', 'start', 'end']:
                getattr(box, 'set_margin_' + side)(22)
            win.set_child(box)
            title = Gtk.Label(label='Forever Addons', xalign=0)
            title.add_css_class('title-1')
            box.append(title)
            box.append(Gtk.Label(label=f'Tvůj správce addonů • WoW Forever • Interface {self.manager.interface}', xalign=0))
            location = Gtk.Label(label=str(self.manager.addons), xalign=0, selectable=True, wrap=True)
            location.add_css_class('dim-label')
            box.append(location)
            entryrow = Gtk.Box(spacing=8)
            self.entry = Gtk.Entry(placeholder_text='GitHub: vlastník/repozitář nebo https://github.com/…', hexpand=True)
            entryrow.append(self.entry)
            self.buttons = []
            notebook = Gtk.Notebook(vexpand=True)
            box.append(notebook)
            installed = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            installed.set_margin_top(12)
            notebook.append_page(installed, Gtk.Label(label='Nainstalované addony'))
            self.button(entryrow, 'Nainstalovat z GitHubu', self.install_repository)
            self.button(entryrow, 'Import ZIPu', self.choose_zip)
            installed.append(entryrow)
            bar = Gtk.Box(spacing=8)
            self.button(bar, 'Zkontrolovat aktualizace', lambda: self.run_task(self.manager.updates))
            self.button(bar, 'Aktualizovat vše', lambda: self.run_task(lambda: self.manager.updates(True)))
            self.button(bar, 'Ověřit soubory', lambda: self.run_task(self.verify))
            self.button(bar, 'Obnovit poslední zálohu', self.confirm_restore)
            installed.append(bar)
            links = Gtk.Box(spacing=8)
            self.button(links, 'Procházet CurseForge', lambda: notebook.set_current_page(1))
            self.button(links, 'Složka addonů', lambda: Gio.AppInfo.launch_default_for_uri(self.manager.addons.as_uri(), None))
            links.append(Gtk.Label(label='Při spuštění aplikace:', hexpand=True, xalign=1))
            self.mode = Gtk.DropDown.new_from_strings(['Pouze kontrola', 'Automaticky aktualizovat', 'Nic'])
            self.mode.set_selected({'check': 0, 'update': 1, 'off': 2}[self.manager.state.get('startup', 'check')])
            self.mode.connect('notify::selected', lambda *_: self.manager.startup(['check', 'update', 'off'][self.mode.get_selected()]))
            links.append(self.mode)
            installed.append(links)
            self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
            self.listbox.add_css_class('boxed-list')
            scroll = Gtk.ScrolledWindow(vexpand=True, min_content_height=220)
            scroll.set_child(self.listbox)
            installed.append(scroll)
            from catalog import Catalog
            self.catalog = Catalog(self, notebook)
            box.append(Gtk.Label(label='ZIPy se aktualizují opětovným importem. Kontrola integrity porovnává soubory s instalovaným balíčkem; není to antivir.', wrap=True, xalign=0))
            self.log = Gtk.TextView(editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD_CHAR)
            logscroll = Gtk.ScrolledWindow(min_content_height=110)
            logscroll.set_child(self.log)
            box.append(logscroll)
            self.refresh()
            win.connect('close-request', self.close_requested)
            win.present()
            mode = self.manager.state.get('startup', 'check')
            if mode != 'off':
                self.run_task(lambda: self.verify() + '\n\n' + self.manager.updates(mode == 'update'))

        def button(self, box, label, callback):
            b = Gtk.Button(label=label)
            b.connect('clicked', lambda *_: callback())
            box.append(b)
            self.buttons.append(b)

        def refresh(self):
            self.buttons = [b for b in self.buttons if b.get_ancestor(Gtk.ListBox) != self.listbox]
            while self.listbox.get_first_child():
                self.listbox.remove(self.listbox.get_first_child())
            rows = self.manager.inventory()
            if not rows:
                self.listbox.append(Gtk.Label(label='Zatím žádné addony. Přidej repozitář nebo importuj ZIP pro Forever.', margin_top=35, margin_bottom=35))
            for row in rows:
                b = Gtk.Box(spacing=18, margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
                b.append(Gtk.Label(label=row['folder'], hexpand=True, xalign=0))
                b.append(Gtk.Label(label=row['version']))
                b.append(Gtk.Label(label=row['status']))
                b.set_tooltip_text(row['source'] + '\nInterface: ' + row['interface'])
                if row['source'] in self.manager.state['packages']:
                    key = row['source']
                    self.button(b, 'Odstranit', lambda k=key: self.confirm_remove(k))
                self.listbox.append(b)

        def install_repository(self):
            repository = self.entry.get_text().strip()
            self.run_task(lambda: self.manager.github(repository))

        def confirm_remove(self, key):
            dialog = Gtk.MessageDialog(transient_for=self.get_active_window(), modal=True, buttons=Gtk.ButtonsType.OK_CANCEL,
                text='Odstranit balíček ' + key + '?', secondary_text='Odstraní všechny složky tohoto balíčku. Vytvoří zálohu; nastavení WTF zůstane.')
            def response(d, code):
                d.destroy()
                if code == Gtk.ResponseType.OK:
                    self.run_task(lambda: self.manager.remove(key))
            dialog.connect('response', response)
            dialog.present()

        def verify(self):
            rows = self.manager.inventory()
            return '\n'.join(r['folder'] + ': ' + r['status'] for r in rows) or 'Složka addonů je prázdná.'

        def close_requested(self, *_):
            if self.busy:
                self.log.get_buffer().set_text('Probíhá operace. Počkej na dokončení, než zavřeš aplikaci.')
            return self.busy

        def run_task(self, operation, on_done=None):
            if self.busy:
                return
            self.busy = True
            for b in self.buttons:
                b.set_sensitive(False)
            self.mode.set_sensitive(False)
            self.catalog.search_entry.set_sensitive(False)
            self.catalog.sort.set_sensitive(False)
            self.entry.set_sensitive(False)
            self.log.get_buffer().set_text('Pracuji…')
            def worker():
                try:
                    message = operation()
                    success = True
                except Exception as e:
                    message = 'Operace zastavena: ' + str(e)
                    success = False
                GLib.idle_add(done, message, success)
            def done(message, success):
                try:
                    if success and on_done:
                        message = on_done(message)
                    self.refresh()
                    self.log.get_buffer().set_text(str(message))
                except Exception as error:
                    self.log.get_buffer().set_text('Nelze obnovit zobrazení: ' + str(error))
                finally:
                    self.busy = False
                    for b in self.buttons:
                        b.set_sensitive(True)
                    self.mode.set_sensitive(True)
                    self.catalog.search_entry.set_sensitive(True)
                    self.catalog.sort.set_sensitive(True)
                    self.entry.set_sensitive(True)
                    self.catalog.sync_buttons()
                return False
            threading.Thread(target=worker, daemon=True).start()

        def choose_zip(self):
            chooser = Gtk.FileChooserNative(title='Vyber distribuční ZIP addonu pro Forever', transient_for=self.get_active_window(), action=Gtk.FileChooserAction.OPEN, accept_label='Nainstalovat', cancel_label='Zrušit')
            filt = Gtk.FileFilter()
            filt.set_name('ZIP archivy')
            filt.add_pattern('*.zip')
            chooser.add_filter(filt)
            def selected(dialog, response):
                if response == Gtk.ResponseType.ACCEPT:
                    path = dialog.get_file().get_path()
                    self.run_task(lambda: self.manager.install_zip(path))
                dialog.destroy()
            chooser.connect('response', selected)
            chooser.show()

        def confirm_restore(self):
            dialog = Gtk.MessageDialog(transient_for=self.get_active_window(), modal=True, buttons=Gtk.ButtonsType.OK_CANCEL,
                text='Obnovit poslední stav před instalací?', secondary_text='Soubory dotčených addonů budou nahrazeny zálohou. Nastavení ve WTF se nemění.')
            def response(d, code):
                d.destroy()
                if code == Gtk.ResponseType.OK:
                    self.run_task(self.manager.restore)
            dialog.connect('response', response)
            dialog.present()

    Gtk.init_check()
    if Gdk.Display.get_default() is None:
        raise RuntimeError('Grafická relace není dostupná. Spusť aplikaci z nabídky svého desktopu.')
    return App().run([])


def main():
    parser = argparse.ArgumentParser(description='Forever Addons — lokální správce addonů')
    parser.add_argument('command', nargs='?', default='gui', choices=['gui', 'list', 'verify', 'check', 'update', 'install-zip', 'install-github', 'install-curseforge', 'curse-search', 'curse-key', 'restore', 'startup', 'remove'])
    parser.add_argument('value', nargs='?')
    parser.add_argument('--index', type=int, default=0, help='Index stránky katalogu CurseForge (0, 20, 40…)')
    args = parser.parse_args()
    if args.command == 'gui':
        return gui()
    if args.command == 'curse-key':
        import getpass
        from curseforge import save_key
        save_key(getpass.getpass('CurseForge API klíč (prázdný smaže uložený): '))
        print('Nastavení klíče uloženo.')
        return 0
    m = Manager()
    if args.command in {'list', 'verify'}:
        rows = m.inventory()
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return int(args.command == 'verify' and any(r['status'] not in {'V pořádku', 'Nespravovaný'} for r in rows))
    if args.command == 'curse-search':
        print(json.dumps(m.curse_search(args.value or '', args.index), ensure_ascii=False, indent=2))
        return 0
    if args.command in {'install-zip', 'install-github', 'install-curseforge', 'startup', 'remove'} and not args.value:
        parser.error('Tento příkaz vyžaduje hodnotu.')
    actions = {'check': m.updates, 'update': lambda: m.updates(True), 'install-zip': lambda: m.install_zip(args.value),
               'install-github': lambda: m.github(args.value), 'install-curseforge': lambda: m.curseforge(args.value),
               'remove': lambda: m.remove(args.value), 'restore': m.restore, 'startup': lambda: m.startup(args.value)}
    result = actions[args.command]()
    if result:
        print(result)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Chyba: ' + str(error), file=sys.stderr)
        sys.exit(1)
