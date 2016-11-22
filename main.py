# from gi import require_version
import signal, glib, dbus
# require_version('Gtk', '3.0')
from os import path
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import Gtk, Gdk, GdkPixbuf

class Window(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Notify Feed")
        self.hide()
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)

        scrolled.add(self.listbox)
        self.add(scrolled)

    def update(self, item):
        # for child in self.listbox.get_children():
            # self.listbox.remove(child)

        # for key,item in notify.list():
        row = Gtk.ListBoxRow()
        grid = Gtk.Grid()
        row.add(grid)
        if item['icon'] and path.isfile(item['icon']):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(item['icon'], width=32, height=32, preserve_aspect_ratio=False)
        elif item['icon']:
            pixbuf = Gtk.IconTheme.get_default().load_icon(item['icon'], 32, 0)
        else:
            pixbuf = Gtk.IconTheme.get_default().load_icon('dialog-information', 32, 0)
        image = Gtk.Image.new_from_pixbuf(pixbuf)

        title = Gtk.Label(yalign=0.1)
        title.set_markup("<b>" + item['title'] + "</b>")
        body = Gtk.Label(item['body'])
        body.set_line_wrap(True)
        grid.add(image)
        grid.attach_next_to(title, image, Gtk.PositionType.RIGHT, 2, 1)
        grid.attach_next_to(body, title, Gtk.PositionType.BOTTOM, 1, 2)
        self.listbox.add(row)

        self.listbox.show_all()

class TrayIcon:

    def __init__(self, appid, icon):

        self.icon = icon
        self.createWindow()
        APPIND_SUPPORT = 1
        try:
            from gi.repository import AppIndicator3
        except:
            APPIND_SUPPORT = 0

        if APPIND_SUPPORT == 1:
            self.ind = AppIndicator3.Indicator.new(appid, icon, AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.ind.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.ind.set_menu(self.getMenu())
        else:
            self.ind = Gtk.StatusIcon()
            self.ind.set_from_file(icon)
            self.ind.connect('activate', self.showWindow)

    def getMenu(self):
        menu = gtk.Menu()
        item = gtk.MenuItem('Show')
        item.connect('activate', self.showWindow)
        menu.append(item)
        menu.show_all()
        return menu

    def createWindow(self):
        self.window = Window()
        self.window.connect("delete-event", self.closeWindow)
        self.window.set_icon_from_file(self.icon)

    def showWindow(self, args):
        screen = self.window.get_screen()
        m = screen.get_monitor_at_window(screen.get_active_window())
        monitor = screen.get_monitor_geometry(m)
        self.window.resize(monitor.width/3, monitor.height)
        self.window.move(monitor.width - monitor.width/3,0)
        self.window.show_all()

    def closeWindow(self, arg1, arg2):
        self.window.hide()

class Notify:

    def __init__(self):
        self.keys = ['app', 'replaces_id', 'icon', 'title', 'body', 'actions', 'hints', 'timeout']

    def setCallback(self, callback):
        self.callback = callback

    def listen(self, bus, message):
        args = message.get_args_list()
        if len(args) == 8:
            self.callback(dict([(self.keys[i], args[i]) for i in range(8)]))

# Handle pressing Ctr+C properly, ignored by default
signal.signal(signal.SIGINT, signal.SIG_DFL)
notify = Notify()
icon = TrayIcon('Notifications Feed', '/usr/share/pixmaps/xfce4_xicon.png')
notify.setCallback(lambda notification: icon.window.update(notification))
loop = DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
bus.add_match_string("type='method_call',interface='org.freedesktop.Notifications',member='Notify',eavesdrop=true")
bus.add_message_filter(lambda bus, message: notify.listen(bus, message))
glib.MainLoop().run()
Gtk.main()
