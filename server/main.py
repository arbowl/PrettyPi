"""Main

Builds the touchscreen portion of the PrettyPi app
"""

#!/usr/bin/python
# -*- coding: utf8 -*-

# [MQH] 16 June 2017. It has been a while since last code I have written in Python! :-)
from sqlite3 import connect
from sys import exit as sys_exit

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.theming import ThemeManager

from server.arabic_label import ArabicLabel


KV_CONFIG = """
#:import Toolbar kivymd.toolbar.Toolbar
#:import NavigationLayout kivymd.navigationdrawer.NavigationLayout
#:import MDNavigationDrawer kivymd.navigationdrawer.MDNavigationDrawer

NavigationLayout:
	id: navLayout

	MDNavigationDrawer:
        id: navDrawer
        NavigationDrawerToolbar:
            title: "Navigation Drawer"
        NavigationDrawerIconButton:
			id: quit_button
            icon: 'checkbox-blank-circle'
            text: "Quit"

	BoxLayout:
		id: topBox
		orientation: 'vertical'
		Toolbar:
			id: toolbar
			title: 'My Pretty Pi!'
			md_bg_color: app.theme_cls.primary_color
			background_palette: 'Primary'
			background_hue: '500'
			left_action_items: [['menu', lambda x: app.root.toggle_nav_drawer()]]
			right_action_items: [['dots-vertical', lambda x: app.root.toggle_nav_drawer()]]

		Toolbar:
			id: titlebar
			title: 'Current TODO'
			md_bg_color: app.theme_cls.primary_color
			background_palette: 'Primary'
			background_hue: '900'

		ScreenManager:
			id: screenManager

			Screen:
				name: 'mainScreen'

				BoxLayout:
					id: main_box
					orientation: 'vertical'
	"""


class PrettyPiApp(App):
    """Builds the PrettyPi interface for touchscreen"""

    theme_cls = ThemeManager()
    main_box = None
    connection = None
    cursor = None
    kv_main = KV_CONFIG

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.quit_button = None

    def build(self):
        """Builds the Kivy UI"""
        main_widget = Builder.load_string(self.kv_main)
        self.connection = connect("data.db")
        self.cursor = self.connection.cursor()
        self.main_box = main_widget.ids.mainBox
        self.quit_button = main_widget.ids.quit_button
        self.quit_button.bind(on_press=lambda e: sys_exit())
        self.refresh_list()
        Clock.schedule_interval(self.check_updates, 0.5)
        return main_widget

    def refresh_list(self) -> None:
        """Updates the TODO list with new items"""
        self.main_box.clear_widgets()
        self.cursor.execute("SELECT * FROM TODO WHERE DONE = 'N'")
        tasks = self.cursor.fetchall()
        for task in tasks:
            task_text = task[1]
            if task[5] == "Y":
                task_text += " (Working On)"
            self.main_box.add_widget(
                ArabicLabel(text=task_text, halign="center", font_style="Display1")
            )

    def check_updates(self) -> None:
        """Adds results to the TODO list if found"""
        self.cursor.execute(
            "SELECT COUNT( 1 ) FROM UPDATE_REQUESTS WHERE UPDATE_TYPE = "
            "'UPDATE_TODO_LIST' AND DONE = 'N'"
        )
        result = self.cursor.fetchone()
        if result[0] > 0:
            self.refresh_list()
            self.cursor.execute(
                "UPDATE UPDATE_REQUESTS SET DONE = 'Y' WHERE UPDATE_TYPE = "
                "'UPDATE_TODO_LIST'"
            )
            self.connection.commit()


if __name__ == "__main__":
    PrettyPiApp().run()
