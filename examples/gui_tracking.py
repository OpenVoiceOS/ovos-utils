from ovos_utils.gui import GUITracker
from ovos_utils import wait_for_exit_signal


class MyGUIEventTracker(GUITracker):
    # GUI event handlers
    # user can/should subclass this
    def on_idle(self, namespace):
        print("IDLE", namespace)
        timestamp = self.idle_ts

    def on_active(self, namespace):
        # NOTE: page has not been loaded yet
        # event will fire right after this one
        print("ACTIVE", namespace)
        # check namespace values, they should all be set before this event
        values = self.gui_values[namespace]

    def on_new_page(self, page, namespace, index):
        print("NEW PAGE", namespace, index, namespace)
        # check all loaded pages
        for n in self.gui_pages:  # list of named tuples
            nspace = n.name  # namespace / skill_id
            pages = n.pages  # ordered list of page uris

    def on_gui_value(self, namespace, key, value):
        # WARNING this will pollute logs quite a lot, and you will get
        # duplicates, better to check values on a different event,
        # demonstrated in on_active
        print("VALUE", namespace, key, value)


g = MyGUIEventTracker()

print("device has screen:", g.can_display())
print("mycroft-gui installed:", g.is_gui_installed())
print("gui connected:", g.is_gui_connected())


# check registered idle screens
print("Registered idle screens:")
for name in g.idle_screens:
    namespace = g.idle_screens[name]
    print("   - ", name, ":", namespace)


# just block listening for events until ctrl + C
wait_for_exit_signal()
