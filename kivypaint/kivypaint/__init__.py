__all__ = ('Paint', )

from kivy.properties import (
    ObjectProperty, BooleanProperty, NumericProperty, StringProperty,
)
from kivy.event import EventDispatcher
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.clock import Clock


Builder.load_string('''
#:import theme kivypaint.theme
#:import md_icons kivymd.icon_definitions.md_icons

<Paint>:
    spacing: 4
    padding: 4
    canvas.before:
        Color:
            rgba: theme.background_color
        Rectangle:
            pos: self.pos
            size: self.size
    PaintToolbox:
        id: toolbox
        ctx: root.ctx
        pos_hint: {'top': 1, }
    BoxLayout:
        orientation: 'vertical'
        spacing: 4
        PaintCanvas:
            id: canvas
            ctx: root.ctx
        PaintHelperText:
            id: helper_text
            ctx: root.ctx

<PaintHelperText>:
    size_hint: None, None
    size: self.texture_size
    text: '' if root.ctx.operation is None else root.ctx.operation.helper_text
    color: theme.foreground_color
    font_size: theme.font_size
<PaintToolbox>:
    cols: 2
    spacing: 2
    size_hint: None, None
    size: self.minimum_size
<PaintToolboxItem>:
    color: theme.foreground_color
    font_name: 'Icon'
    font_size: theme.icon_size
    size_hint: None, None
    size: (theme.icon_size, ) * 2
    text: md_icons[root.operation.icon]
    canvas.before:
        Color:
            rgba: (1, 1, 1, 0 if self.state == 'normal' else .2)
        Rectangle:
            pos: self.pos
            size: self.size
<-PaintCanvas>:
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


class TaskGroup:
    _coros = tuple()
    def __init__(self):
        self.cancel()
    def cancel(self):
        for coro in self._coros:
            coro.close()
        self._coros = []
    def start(self, coro):
        from asynckivy import start as ak_start
        self._coros.append(coro)
        ak_start(coro)
    def add(self, coro):
        self._coros.append(coro)


class Context(EventDispatcher):
    task_group = ObjectProperty()
    operation = ObjectProperty(None, allownone=True, rebind=True)
    line_width = NumericProperty(2)
    freehand_precision = NumericProperty(20)
    @property
    def line_color(self):
        from kivy.utils import get_random_color
        return get_random_color(alpha=.8)
    @property
    def fill_color(self):
        from kivy.utils import get_random_color
        return get_random_color(alpha=.5)
DEFAULT_CONTEXT = Context()


class Paint(Factory.BoxLayout):
    ctx = ObjectProperty(DEFAULT_CONTEXT, rebind=True)

    def __init__(self, **kwargs):
        if 'ctx' not in kwargs:
            kwargs['ctx'] = Context()
        super().__init__(**kwargs)
        Clock.schedule_once(self.reset)

    def reset(self, *args):
        ctx = self.ctx
        if ctx.task_group is not None:
            ctx.task_group.cancel()
        ctx.task_group = TaskGroup()
        self.ids.canvas.canvas.clear()


class PaintToolbox(Factory.GridLayout):
    ctx = ObjectProperty(DEFAULT_CONTEXT, rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self._add_items)

    def _add_items(self, *args):
        from .canvas_operations import operations
        button_group = f"PaintToolbox.{self.uid}"
        def on_press(button):
            self.ctx.operation = None if button.state == 'normal' else button.operation
        for op in operations:
            self.add_widget(
                PaintToolboxItem(
                    operation=op, group=button_group, on_press=on_press
                )
            )


class PaintToolboxItem(Factory.ToggleButtonBehavior, Factory.Label):
    operation = ObjectProperty()


class PaintCanvas(Factory.RelativeLayout):
    ctx = ObjectProperty(DEFAULT_CONTEXT, rebind=True)
    def on_touch_down(self, touch):
        if self.collide_point(*touch.opos):
            ctx = self.ctx
            if ctx.operation is not None:
                ctx.task_group.start(ctx.operation.func(self, touch, ctx))
            return True
    def on_touch_move(self, touch):
        pass
    def on_touch_up(self, touch):
        pass


class PaintHelperText(Factory.Label):
    ctx = ObjectProperty(DEFAULT_CONTEXT, rebind=True)
