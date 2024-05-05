"""Arabic Label

Support for Arabic script
"""

from typing import Any

from kivymd.uix.label import MDLabel
from arabic_reshaper import reshape
from bidi.algorithm import get_display


# Don't really have control over the ancestors--ignoring
# pylint: disable = too-many-ancestors, too-few-public-methods
class ArabicLabel(MDLabel):
    """Superclasses MDLabel to attach a new style"""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.text = ""
        self.font_name = "fonts/KacstPenE"

    def update_font_style(self, instance_label: Any, font_style: str) -> None:
        """Updates the font style with a differnet default font"""
        super().update_font_style(instance_label, font_style)
        self.text = get_display(reshape(self.text))
