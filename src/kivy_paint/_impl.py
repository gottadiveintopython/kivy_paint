__all__ = ('KPMain', )

from functools import lru_cache
from kivy.properties import ObjectProperty, NumericProperty
from kivy.event import EventDispatcher
from kivy.factory import Factory as F
from kivy.lang import Builder
import asynckivy

Builder.load_string('''
#:import theme kivy_paint.theme
#:import md_icons kivymd.icon_definitions.md_icons

<KPMain>:
    spacing: '4dp'
    padding: '4dp'
    canvas.before:
        Color:
            rgba: theme.background_color
        Rectangle:
            pos: self.pos
            size: self.size
    GridLayout:
        id: toolbox
        spacing: '2dp'
        size: self.minimum_size
        size_hint: None, None
        pos_hint: {'top': 1, }
        cols: 2
    BoxLayout:
        orientation: 'vertical'
        spacing: 4
        size_hint: 1000, 1000
        KPTarget:
            id: target
        Label:
            id: helper_text
            color: theme.foreground_color
            font_size: theme.font_size
            height: self.texture_size[1]
            size_hint_y: None
            
<KPToolboxItem@ToggleButtonBehavior+Label>:
    color: theme.foreground_color
    font_name: 'Icons'
    font_size: theme.icon_font_size
    size_hint: None, None
    size: (theme.icon_font_size, ) * 2
    canvas.before:
        Color:
            rgba: (1, 1, 1, 0 if self.state == 'normal' else .2)
        Rectangle:
            pos: self.pos
            size: self.size

<-KPTarget@RelativeLayout>:  # drawing target i.e. canvas
    canvas.before:
        PushMatrix:
        Translate:
            xy: self.pos

        StencilPush:
        Rectangle:
            pos: 0, 0
            size: self.size
        StencilUse:
        Color:
            rgba: theme.canvas_color
        Rectangle:
            pos: 0, 0
            size: self.size
    canvas.after:
        StencilUnUse:
        Rectangle:
            pos: 0, 0
            size: self.size
        StencilPop:
        PopMatrix:
''')


class KPContext(EventDispatcher):
    op_cls = ObjectProperty(None, allownone=True, rebind=True)
    op_task = ObjectProperty(asynckivy.dummy_task, allownone=True, rebind=True)
    line_width = NumericProperty(2.)
    freehand_precision = NumericProperty(20.)

    @property
    def line_color(self):
        from kivy.utils import get_random_color
        return get_random_color(alpha=.8)
    @property
    def fill_color(self):
        from kivy.utils import get_random_color
        return get_random_color(alpha=.5)


class KPMain(F.BoxLayout):
    def on_kv_post(self, *args, **kwargs):
        _warn_if_run_on_mobile()
        super().on_kv_post(*args, **kwargs)
        self._widgets = {
            'root': self,
            **{id: w.__self__ for id, w in self.ids.items()}
        }
        self._ctx = KPContext()
        self._init_toolbox()

    def _init_toolbox(self):
        from kivymd.icon_definitions import md_icons
        from . import _operations
        toolbox = self.ids.toolbox.__self__
        button_group = f"KPMain.{self.uid}.toolbox"
        KPToolboxItem = F.KPToolboxItem
        on_state = self._on_toolbox_item_state
        add_widget = toolbox.add_widget
        for op_cls_name in _operations.__all__:
            op_cls = getattr(_operations, op_cls_name)
            item = KPToolboxItem(group=button_group, text=md_icons[op_cls.icon])
            item.bind(state=on_state)
            item._op_cls = op_cls
            add_widget(item)

    def _on_toolbox_item_state(self, item, state):
        if state == 'down':
            op_cls = item._op_cls
            ctx = self._ctx
            ctx.op_cls = op_cls
            ctx.op_task.cancel()
            ctx.op_task = asynckivy.start(op_cls.main(widgets=self._widgets, ctx=ctx))
            self.ids.helper_text.text = op_cls.helper_text


@lru_cache(maxsize=1)
def _warn_if_run_on_mobile():
    from kivy.utils import platform
    if platform not in ('linux', 'win', 'macosx', ):
        from kivy.logger import Logger
        Logger.warning(
            "kivy_paint: This module requires a 3-button mouse to be connected. "
            "Otherwise, some functions may not work properly."
        )
