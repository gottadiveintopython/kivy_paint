__all__ = ('show_yes_no_dialog', 'warn_if_run_on_mobile', 'open_file_with_default_os_app', 'temp_dir', )

from functools import lru_cache
from kivy.core.text import DEFAULT_FONT
from kivy.lang import Builder
from kivy.factory import Factory as F


Builder.load_string('''
#:import theme kivy_paint.theme

<KPYesNoDialog@ModalView>:
    size_hint: None, None
    size: content.minimum_size
    BoxLayout:
        id: content
        orientation: 'vertical'
        padding: '16dp'
        spacing: '8dp'
        Label:
            id: main
            font_size: theme.font_size
            size_hint_min: [v + dp(8) for v in self.texture_size]
        BoxLayout:
            spacing: '8dp'
            size_hint_min: self.minimum_size
            Button:
                id: yes
                font_size: theme.font_size
                size_hint_min: [v + dp(8) for v in self.texture_size]
            Button:
                id: no
                font_size: theme.font_size
                size_hint_min: [v + dp(8) for v in self.texture_size]
''')



async def show_yes_no_dialog(*, text_main='', font_name=DEFAULT_FONT, text_yes='Yes', text_no='No', _cache=[]):
    import asynckivy as ak
    try:
        dialog = _cache.pop()
    except IndexError:
        dialog = F.KPYesNoDialog()

    main_label = dialog.ids.main.__self__
    yes_button = dialog.ids.yes.__self__
    no_button = dialog.ids.no.__self__
    main_label.text = text_main
    main_label.font_name = font_name
    yes_button.text = text_yes
    yes_button.font_name = font_name
    no_button.text = text_no
    no_button.font_name = font_name

    try:
        dialog.open()
        tasks = await ak.or_(
            ak.event(yes_button, 'on_release'),
            ak.event(no_button, 'on_release'),
            ak.event(dialog, 'on_dismiss'),
        )
        if tasks[0].done:
            return 'yes'
        elif tasks[1].done:
            return 'no'
        else:
            return 'cancelled'
    finally:
        dialog.dismiss()
        _cache.append(dialog)


@lru_cache(maxsize=1)
def warn_if_run_on_mobile():
    from kivy.utils import platform
    if platform not in ('linux', 'win', 'macosx', ):
        from kivy.logger import Logger
        Logger.warning(
            "kivy_paint: This module requires a 3-button mouse to be connected. "
            "Otherwise, some functions may not work properly."
        )


def open_file_with_default_os_app(filepath):
    import subprocess
    from kivy.utils import platform
    if platform == 'linux':
        subprocess.call(('xdg-open', filepath))
    elif platform == 'macosx':
        subprocess.call(('open', filepath))
    elif platform == 'win':
        import os
        os.startfile(filepath)


@lru_cache(maxsize=1)
def temp_dir():
    from tempfile import mkdtemp
    return mkdtemp(prefix='kivy_paint.')
