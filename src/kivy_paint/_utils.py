__all__ = ('show_yes_no_dialog', )

from kivy.core.text import DEFAULT_FONT
from kivy.lang import Builder
from kivy.factory import Factory as F


Builder.load_string('''
<KPYesNoDialog@ModalView>:
    size_hint: .7, .3
    BoxLayout:
        orientation: 'vertical'
        padding: '8dp'
        spacing: '8dp'
        Label:
            id: main
            font_size: max(sp(16), 30)
        BoxLayout:
            spacing: '4dp'
            size_hint_y: None
            height: self.minimum_height
            Button:
                id: yes
                font_size: max(sp(16), 30)
                size_hint_min: self.texture_size
            Button:
                id: no
                font_size: max(sp(16), 30)
                size_hint_min: self.texture_size
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
