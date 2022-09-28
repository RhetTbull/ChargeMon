"""macOS StatusBar/MenuBar app to remind you to unplug your laptop when it's charged"""

import psutil
import rumps
from Foundation import NSLog

APP_NAME = "ChargeMon"

ICON_PLUGGED = "chargemon_plugged.png"
ICON_PLUGGED_SNOOZE = "chargemon_plugged_snooze.png"
ICON_UNPLUGGED = "chargemon_unplugged.png"
ICON_UNPLUGGED_SNOOZE = "chargemon_unplugged_snooze.png"

SNOOZE_TIME = 15 * 60

__version__ = "0.3.0"


class ChargingMonitor(rumps.App):
    def __init__(self, *args, **kwargs):
        super(ChargingMonitor, self).__init__(*args, **kwargs)
        self.icon = ICON_PLUGGED if self.plugged_in else ICON_UNPLUGGED

        # default values for monitoring
        self.update_percent_interval = 180
        self.update_icon_interval = 10
        self.unplug_percent = 80
        self.plug_percent = 75

        # Create menu items to toggle notifications and alerts
        self.alert = rumps.MenuItem("Alert", callback=self.on_alert)
        self.alert.state = True
        self.notification = rumps.MenuItem(
            "Notification", callback=self.on_notification
        )
        self.notification.state = False
        self.snooze = rumps.MenuItem("Snooze", callback=self.on_snooze)
        self.snooze.state = False

        # Create pause/resume menu item
        self.pause = rumps.MenuItem("Pause", callback=self.on_pause)

        # Create about menu item
        self.about = rumps.MenuItem("About", callback=self.on_about)

        # Add menu items
        self.menu = [
            self.alert,
            self.notification,
            self.pause,
            self.snooze,
            None,
            self.about,
        ]

        # start timers, one for the battery percent, one for the icon
        self.percent_timer = rumps.Timer(
            self.update_percent, self.update_percent_interval
        )
        self.percent_timer.start()

        self.icon_timer = rumps.Timer(self.update_icon, self.update_icon_interval)
        self.icon_timer.start()

        # snooze timer set when user clicks snooze on alert
        self.snooze_timer = None

        self.log(
            f"started: plugged_in={self.plugged_in}, battery={self.battery_percent}%%"
        )

    def on_alert(self, sender):
        """Toggle alert/notification"""
        sender.state = not sender.state
        self.notification.state = not self.notification.state

    def on_notification(self, sender):
        """Toggle alert/notification"""
        sender.state = not sender.state
        self.alert.state = not self.alert.state

    def on_pause(self, sender):
        """Pause/resume the percent timer"""
        if self.percent_timer.is_alive():
            self.percent_timer.stop()
            sender.title = "Resume"
            self.log("paused")
        else:
            self.percent_timer.start()
            sender.title = "Pause"
            self.log("resumed")

    def on_snooze(self, sender):
        """Start or stop snooze timer"""
        sender.state = not sender.state
        if sender.state:
            self.start_snooze()
        else:
            self.stop_snooze()

    def on_about(self, sender):
        """Display about dialog."""
        rumps.alert(
            title=f"About {APP_NAME}",
            message=f"{APP_NAME} Version {__version__}\n\n"
            f"{APP_NAME} is a simple utility to remind you to plugin/unplug your charger for optimum charging.\n\n"
            f"{APP_NAME} is open source and licensed under the MIT license.\n\n"
            "Copyright 2022 by Rhet Turnbull\n"
            "https://github.com/RhetTbull/ChargeMon",
            ok="OK",
        )

    def start_snooze(self):
        """Start snooze timer"""
        self.log(f"starting snooze timer for {SNOOZE_TIME} seconds")
        callback = create_run_later_timer_callback(self.stop_snooze)
        self.snooze_timer = rumps.Timer(callback, SNOOZE_TIME)
        self.snooze_timer.start()
        self.snooze.state = True
        self.snooze.title = "Snoozing (click to cancel)"
        self.icon = ICON_PLUGGED_SNOOZE if self.plugged_in else ICON_UNPLUGGED_SNOOZE
        self.log("snoozed")

    def stop_snooze(self, timer=None):
        """Stop snooze timer"""
        self.log("stopping snooze timer")
        if self.snooze_timer and self.snooze_timer.is_alive():
            self.snooze_timer.stop()
            self.snooze_timer = None
        self.snooze.state = False
        self.snooze.title = "Snooze"
        self.icon = ICON_PLUGGED if self.plugged_in else ICON_UNPLUGGED
        self.log("snooze cancelled")

    def log(self, msg: str):
        """Log a message to unified log."""
        NSLog(f"{APP_NAME} {__version__} {msg}")

    @property
    def plugged_in(self):
        """True if computer plugged in, otherwise False"""
        battery = psutil.sensors_battery()
        return getattr(battery, "power_plugged", False)

    @property
    def battery_percent(self):
        """battery percent charged"""
        battery = psutil.sensors_battery()
        return getattr(battery, "percent", 0)

    def update_percent(self, timer):
        """Create alert or notification if battery sufficiently charged or is discharged"""
        percent = self.battery_percent
        if percent >= self.unplug_percent and self.plugged_in and not self.snooze.state:
            # plugged in and battery is charged
            # alert cancel = 0, ok = 1; thus 0 means snooze was clicked
            if self.alert.state and not rumps.alert(
                title="Unplug the charger!",
                message=f"Battery {percent} percent charged.",
                ok="OK",
                cancel="Snooze",
            ):
                self.start_snooze()
            if self.notification.state:
                rumps.notification(
                    title="Unplug the charger!",
                    subtitle="",
                    message=f"Battery {percent} percent charged.",
                )
        elif (
            percent <= self.plug_percent
            and not self.plugged_in
            and not self.snooze.state
        ):
            # not plugged in and battery is discharged
            if self.alert.state and not rumps.alert(
                title="Plug in the charger!",
                message=f"Battery {percent} percent charged.",
                ok="OK",
                cancel="Snooze",
            ):
                self.start_snooze()
            if self.notification.state:
                rumps.notification(
                    title="Plug in the charger!",
                    subtitle="",
                    message=f"Battery {percent} percent charged.",
                )

    def update_icon(self, timer):
        """Update icon if necessary for plugged in/out status"""
        plugged_in = self.plugged_in
        if plugged_in:
            self.icon = ICON_PLUGGED_SNOOZE if self.snooze.state else ICON_PLUGGED
        elif self.icon != ICON_UNPLUGGED:
            self.icon = ICON_UNPLUGGED_SNOOZE if self.snooze.state else ICON_UNPLUGGED


def create_run_later_timer_callback(callback):
    """Despite what the documentation says, the rumps.Timer() runs the callback
    immediately when the timer is started. This function creates a callback that
    runs the actual callback only *after* the first time it is called."""

    # create a closure to hold the state
    called_first_time = 0

    def run_later_callback(timer):
        nonlocal called_first_time
        if called_first_time:
            callback(timer)
        else:
            called_first_time += 1

    return run_later_callback


if __name__ == "__main__":
    ChargingMonitor(name="ChargeMon").run()
