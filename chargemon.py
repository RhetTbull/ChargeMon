"""macOS StatusBar app to remind you to unplug your laptop when it's charged"""

import psutil
import rumps

ICON_PLUGGED = "chargemon_plugged.png"
ICON_UNPLUGGED = "chargemon_unplugged.png"


class ChargingMonitor(rumps.App):
    def __init__(self, *args, **kwargs):
        super(ChargingMonitor, self).__init__(*args, **kwargs)
        self.icon = ICON_PLUGGED if self.plugged_in else ICON_UNPLUGGED

        # default values for monitoring
        self.update_percent_interval = 180 
        self.update_icon_interval = 10
        self.unplug_percent = 95
        self.plug_percent = 80

        # Create menu with checkboxes to toggle notifications and alerts
        self.alert = rumps.MenuItem("Alert", callback=self.on_alert)
        self.alert.state = True
        self.notification = rumps.MenuItem(
            "Notification", callback=self.on_notification
        )
        self.notification.state = False
        self.menu = [self.alert, self.notification]

        # start timers, one for the battery percent, one for the icon
        self.percent_timer = rumps.Timer(
            self.update_percent, self.update_percent_interval
        )
        self.percent_timer.start()

        self.icon_timer = rumps.Timer(self.update_icon, self.update_icon_interval)
        self.icon_timer.start()

    def on_alert(self, sender):
        """Toggle alert/notification"""
        sender.state = not sender.state
        self.notification.state = not self.notification.state

    def on_notification(self, sender):
        """Toggle alert/notification"""
        sender.state = not sender.state
        self.alert.state = not self.alert.state

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
        if percent >= self.unplug_percent and self.plugged_in:
            # plugged in and battery is charged
            if self.alert.state:
                rumps.alert(
                    title="Unplug the charger!",
                    message=f"Battery {percent} percent charged.",
                    ok=None,
                    cancel=None,
                )
            if self.notification.state:
                rumps.notification(
                    title="Unplug the charger!",
                    subtitle="",
                    message=f"Battery {percent} percent charged.",
                )
        elif percent <= self.plug_percent and not self.plugged_in:
            # not plugged in and battery is discharged
            if self.alert.state:
                rumps.alert(
                    title="Plug in the charger!",
                    message=f"Battery {percent} percent charged.",
                    ok=None,
                    cancel=None,
                )
            if self.notification.state:
                rumps.notification(
                    title="Plug in the charger!",
                    subtitle="",
                    message=f"Battery {percent} percent charged.",
                )

    def update_icon(self, timer):
        """Update icon if necessary for plugged in/out status """
        plugged_in = self.plugged_in
        if plugged_in and self.icon != ICON_PLUGGED:
            self.icon = ICON_PLUGGED
        elif not plugged_in and self.icon != ICON_UNPLUGGED:
            self.icon = ICON_UNPLUGGED


if __name__ == "__main__":
    ChargingMonitor(name="ChargeMon").run()
