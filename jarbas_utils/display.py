import os
import subprocess


def can_display():
    have_display = "DISPLAY" in os.environ
    if not have_display:
        # fallback check using matplotlib if available
        try:
            import matplotlib.pyplot as plt
            try:
                plt.figure()
                have_display = True
            except:
                have_display = False
        except ImportError:
            pass
    return have_display


def is_gui_installed():
    return bool(subprocess.check_output(
        "which mycroft-gui-app", shell=True).decode("utf-8").strip())


def is_gui_connected():
    # TODO bus api for https://github.com/MycroftAI/mycroft-core/pull/2682
    return False
