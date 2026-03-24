#!/usr/bin/env python3
"""
SwapManager GTK — Control Manual de RAM y Swap
Entelequia AI Framework v2.0

Autor: Gabriel F. Cao Di Marco
Co-creadora: Daniela Cao Di Marco
Licencia: MIT © 2026
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import os, ctypes, time, threading

MADV_PAGEOUT  = 21
MADV_WILLNEED = 3
libc = ctypes.CDLL("libc.so.6", use_errno=True)

# ── /proc helpers ──────────────────────────────────────────────────────────────

def read_status(pid):
    data = {}
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if ':' in line:
                    k, v = line.split(':', 1)
                    data[k.strip()] = v.strip()
    except: pass
    return data

def get_processes():
    procs = []
    for e in os.scandir('/proc'):
        if not e.name.isdigit(): continue
        pid = int(e.name)
        s = read_status(pid)
        if not s: continue
        name    = s.get('Name','?').strip()[:24]
        rss_kb  = int(s.get('VmRSS','0 kB').split()[0]) if 'VmRSS'  in s else 0
        swap_kb = int(s.get('VmSwap','0 kB').split()[0]) if 'VmSwap' in s else 0
        virt_kb = int(s.get('VmSize','0 kB').split()[0]) if 'VmSize' in s else 0
        if rss_kb < 500: continue
        procs.append([pid, name, rss_kb//1024, swap_kb//1024, virt_kb//1024, False])
    procs.sort(key=lambda x: x[2], reverse=True)
    return procs

def get_meminfo():
    mi = {}
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if ':' in line:
                    k, v = line.split(':', 1)
                    mi[k.strip()] = int(v.split()[0])
    except: pass
    rt = mi.get('MemTotal',0)//1024
    ra = mi.get('MemAvailable',0)//1024
    st = mi.get('SwapTotal',0)//1024
    sf = mi.get('SwapFree',0)//1024
    return rt, rt-ra, st, st-sf

def get_maps(pid):
    regions = []
    try:
        with open(f"/proc/{pid}/maps") as f:
            for line in f:
                p = line.split()
                if len(p) < 2: continue
                if 'r' not in p[1] and 'w' not in p[1]: continue
                s, e = p[0].split('-')
                regions.append((int(s,16), int(e,16)))
    except: pass
    return regions

def madvise_pid(pid, advice):
    NR_pidfd_open      = 434
    NR_process_madvise = 440
    regions = get_maps(pid)
    if not regions:
        return False, "Sin acceso a mapas (permisos insuficientes)"
    pidfd = libc.syscall(ctypes.c_long(NR_pidfd_open),
                         ctypes.c_int(pid), ctypes.c_uint(0))
    if pidfd < 0:
        return False, "Requiere sudo para este proceso"
    count = 0
    IovArr = ctypes.c_uint64 * 2
    for start, end in regions:
        size = end - start
        if size <= 0 or size > 512*1024*1024: continue
        iov = IovArr(start, size)
        ret = libc.syscall(ctypes.c_long(NR_process_madvise),
                           ctypes.c_int(pidfd),
                           ctypes.pointer(iov), ctypes.c_ulong(1),
                           ctypes.c_int(advice), ctypes.c_uint(0))
        if ret >= 0: count += 1
    libc.close(pidfd)
    action = "enviado a swap" if advice == MADV_PAGEOUT else "traído a RAM"
    return count > 0, f"{count} regiones {action}"

# ── App GTK ────────────────────────────────────────────────────────────────────

class SwapManagerApp(Gtk.Window):

    def __init__(self):
        super().__init__(title="SwapManager — Entelequia AI Framework v2.0")
        self.set_default_size(900, 600)
        self.set_border_width(8)

        # CSS
        css = b"""
        window { background-color: #1e1e2e; }
        label  { color: #cdd6f4; }
        .title-label { color: #89b4fa; font-weight: bold; font-size: 14px; }
        .info-label  { color: #a6e3a1; font-size: 12px; }
        .warn-label  { color: #f9e2af; font-size: 12px; }
        .err-label   { color: #f38ba8; font-size: 12px; }
        .status-bar  { color: #cba6f7; font-size: 11px; }
        button { background: #313244; color: #cdd6f4; border: 1px solid #45475a;
                 border-radius: 4px; padding: 4px 10px; }
        button:hover { background: #45475a; }
        treeview { background-color: #181825; color: #cdd6f4; font-size: 12px; }
        treeview:selected { background-color: #313244; }
        progressbar trough { background: #313244; border-radius: 3px; min-height: 14px; }
        progressbar progress { background: #89b4fa; border-radius: 3px; }
        progressbar.warn progress { background: #f9e2af; }
        progressbar.crit progress { background: #f38ba8; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Título
        title = Gtk.Label(label="⚙  SwapManager — Control Manual de RAM y Swap")
        title.get_style_context().add_class('title-label')
        title.set_halign(Gtk.Align.START)
        vbox.pack_start(title, False, False, 2)

        # Barras de memoria
        mem_grid = Gtk.Grid(column_spacing=8, row_spacing=4)
        vbox.pack_start(mem_grid, False, False, 2)

        mem_grid.attach(Gtk.Label(label="RAM:"), 0, 0, 1, 1)
        self.ram_bar = Gtk.ProgressBar()
        self.ram_bar.set_show_text(True)
        self.ram_bar.set_hexpand(True)
        mem_grid.attach(self.ram_bar, 1, 0, 1, 1)

        mem_grid.attach(Gtk.Label(label="SWAP:"), 0, 1, 1, 1)
        self.swap_bar = Gtk.ProgressBar()
        self.swap_bar.set_show_text(True)
        self.swap_bar.set_hexpand(True)
        mem_grid.attach(self.swap_bar, 1, 1, 1, 1)

        # Botones
        btn_box = Gtk.Box(spacing=6)
        vbox.pack_start(btn_box, False, False, 0)

        for label, cb in [
            ("🔄  Actualizar",    self.on_refresh),
            ("⬇  → Swap",        self.on_swap_out),
            ("⬆  → RAM",         self.on_swap_in),
            ("🔒  Lock en RAM",   self.on_lock),
            ("☑  Sel. todo",     self.on_sel_all),
        ]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", cb)
            btn_box.pack_start(btn, False, False, 0)

        # Tabla
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scroll, True, True, 0)

        # Columnas: lock, pid, nombre, ram, swap, virt
        # store: lock(bool), pid(int), nombre(str), ram(int), swap(int), virt(int), ram_str, swap_str, virt_str, lock_ico
        self.store = Gtk.ListStore(bool, int, str, int, int, int, str, str, str, str)
        self.tv = Gtk.TreeView(model=self.store)
        self.tv.set_rules_hint(True)
        self.tv.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        scroll.add(self.tv)

        cols = [
            ("🔒", 9, False),
            ("PID",    1, False),
            ("Nombre", 2, True),
            ("RAM MB", 6, False),
            ("SWAP MB",7, False),
            ("VIRT MB",8, False),
        ]
        for title, col_idx, expand in cols:
            renderer = Gtk.CellRendererText()
            if col_idx in (6,7,8):
                renderer.set_property("xalign", 1.0)
            col = Gtk.TreeViewColumn(title, renderer, text=col_idx)
            col.set_resizable(True)
            col.set_expand(expand)
            if col_idx in (3,4):
                col.set_sort_column_id(col_idx)
            self.tv.append_column(col)

        # Status bar
        self.status = Gtk.Label(label="Listo.")
        self.status.get_style_context().add_class('status-bar')
        self.status.set_halign(Gtk.Align.START)
        vbox.pack_start(self.status, False, False, 2)

        self.locked_pids = set()
        self.refresh_data()
        GLib.timeout_add_seconds(10, self._auto_refresh)
        self.show_all()

    def _auto_refresh(self):
        self.refresh_data()
        return True

    def refresh_data(self):
        rt, ru, st, su = get_meminfo()
        rp = ru/rt if rt else 0
        sp = su/st if st else 0

        self.ram_bar.set_fraction(min(rp, 1.0))
        self.ram_bar.set_text(f"{ru:,} MB / {rt:,} MB  ({rp*100:.0f}%)")
        self.ram_bar.get_style_context().remove_class('warn')
        self.ram_bar.get_style_context().remove_class('crit')
        if rp > 0.85: self.ram_bar.get_style_context().add_class('crit')
        elif rp > 0.65: self.ram_bar.get_style_context().add_class('warn')

        self.swap_bar.set_fraction(min(sp, 1.0))
        self.swap_bar.set_text(f"{su:,} MB / {st:,} MB  ({sp*100:.0f}%)")

        sel = self._get_selected_pids()
        self.store.clear()
        for row in get_processes():
            pid, name, ram, swap, virt, _ = row
            locked = pid in self.locked_pids
            ico = "🔒" if locked else ""
            self.store.append([locked, pid, name, ram, swap, virt,
                                f"{ram:,}", f"{swap:,}", f"{virt:,}", ico])

        # Restaurar selección
        if sel:
            i = self.store.get_iter_first()
            while i:
                if self.store[i][1] in sel:
                    self.tv.get_selection().select_iter(i)
                i = self.store.iter_next(i)

    def _get_selected_pids(self):
        model, paths = self.tv.get_selection().get_selected_rows()
        return {model[p][1] for p in paths}

    def _get_targets(self):
        pids = self._get_selected_pids()
        if pids:
            return list(pids)
        model, paths = self.tv.get_selection().get_selected_rows()
        if paths:
            return [model[paths[0]][1]]
        return []

    def on_refresh(self, _):
        self.refresh_data()
        self.status.set_text(f"Actualizado — {time.strftime('%H:%M:%S')}")

    def on_swap_out(self, _):
        targets = self._get_targets()
        if not targets:
            self.status.set_text("Seleccioná al menos un proceso primero.")
            return
        msgs = []
        for pid in targets:
            if pid in self.locked_pids:
                msgs.append(f"PID {pid}: bloqueado, saltado")
                continue
            ok, msg = madvise_pid(pid, MADV_PAGEOUT)
            msgs.append(f"PID {pid}: {msg}")
        self.status.set_text("  |  ".join(msgs[:3]))
        GLib.timeout_add(600, lambda: self.refresh_data() or False)

    def on_swap_in(self, _):
        targets = self._get_targets()
        if not targets:
            self.status.set_text("Seleccioná al menos un proceso primero.")
            return
        msgs = []
        for pid in targets:
            ok, msg = madvise_pid(pid, MADV_WILLNEED)
            msgs.append(f"PID {pid}: {msg}")
        self.status.set_text("  |  ".join(msgs[:3]))
        GLib.timeout_add(600, lambda: self.refresh_data() or False)

    def on_lock(self, _):
        targets = self._get_targets()
        if not targets:
            self.status.set_text("Seleccioná al menos un proceso primero.")
            return
        msgs = []
        for pid in targets:
            if pid in self.locked_pids:
                self.locked_pids.discard(pid)
                msgs.append(f"PID {pid}: desbloqueado")
            else:
                self.locked_pids.add(pid)
                msgs.append(f"PID {pid}: PROTEGIDO en RAM")
        self.status.set_text("  |  ".join(msgs[:3]))
        self.refresh_data()

    def on_sel_all(self, _):
        sel = self.tv.get_selection()
        if sel.count_selected_rows() == len(self.store):
            sel.unselect_all()
            self.status.set_text("Selección limpiada.")
        else:
            sel.select_all()
            self.status.set_text(f"{len(self.store)} procesos seleccionados.")


def main():
    if os.geteuid() != 0:
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="SwapManager sin sudo",
            secondary_text="Sin sudo solo podés operar sobre tus propios procesos.\n¿Continuar de todos modos?"
        )
        resp = dialog.run()
        dialog.destroy()
        if resp != Gtk.ResponseType.OK:
            print("Ejecutar con: sudo python3 swap_manager_gtk.py")
            return

    app = SwapManagerApp()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()

if __name__ == '__main__':
    main()
