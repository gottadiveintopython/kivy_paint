__all__ = ('operations', )

from typing import Callable
from dataclasses import dataclass
from functools import partial
import kivy.graphics
from kivy.graphics import Line, Color, InstructionGroup
import asynckivy as ak


@dataclass
class Operation:
    name:str = '<default>'
    func:Callable = None
    helper_text:str = ''
    icon:str = ''


@dataclass
class Box:
    x:int = 0
    y:int = 0
    right:int = 0
    top:int = 0


async def _op_rectangle_line(widget, touch, ctx, *, shape_name='rectangle'):
    to_local = widget.to_local
    ox, oy = to_local(*touch.opos)
    inst_group = InstructionGroup()
    inst_group.add(Color(*ctx.line_color))
    line = Line(width=ctx.line_width)
    inst_group.add(line)
    widget.canvas.add(inst_group)
    on_touch_move_was_fired = False
    async for __ in ak.all_touch_moves(widget, touch):
        on_touch_move_was_fired = True
        x, y = to_local(*touch.pos)
        min_x = min(x, ox)
        min_y = min(y, oy)
        max_x = max(x, ox)
        max_y = max(y, oy)
        setattr(
            line, shape_name,
            (min_x, min_y, max_x - min_x, max_y - min_y, )
        )
    if not on_touch_move_was_fired:
        widget.canvas.remove(inst_group)
        return (None, Box())
    bounding_box = Box(x=min_x, y=min_y, right=max_x, top=max_y)
    return (inst_group, bounding_box)


async def _op_rectangle_fill(widget, touch, ctx, *, shape_name='Rectangle'):
    to_local = widget.to_local
    ox, oy = to_local(*touch.opos)
    inst_group = InstructionGroup()
    inst_group.add(Color(*ctx.fill_color))
    shape = getattr(kivy.graphics, shape_name)(size=(0, 0))
    inst_group.add(shape)
    widget.canvas.add(inst_group)
    on_touch_move_was_fired = False
    async for __ in ak.all_touch_moves(widget, touch):
        on_touch_move_was_fired = True
        x, y = to_local(*touch.pos)
        min_x = min(x, ox)
        min_y = min(y, oy)
        max_x = max(x, ox)
        max_y = max(y, oy)
        shape.pos = (min_x, min_y)
        shape.size = (max_x - min_x, max_y - min_y)
    if not on_touch_move_was_fired:
        widget.canvas.remove(inst_group)
        return (None, Box())
    bounding_box = Box(x=min_x, y=min_y, right=max_x, top=max_y)
    return (inst_group, bounding_box)


async def _op_freehand(widget, touch, ctx):
    to_local = widget.to_local
    inst_group = InstructionGroup()
    inst_group.add(Color(*ctx.line_color))
    line = Line(width=ctx.line_width, points=[*to_local(*touch.opos)])
    inst_group.add(line)
    widget.canvas.add(inst_group)
    precision = ctx.freehand_precision
    last_x, last_y = touch.opos
    async for __ in ak.all_touch_moves(widget, touch):
        if abs(last_x - touch.x) + abs(last_y - touch.y) > precision:
            points = line.points
            points.extend(to_local(*touch.pos))
            line.points = points
            last_x, last_y = touch.pos
    x_list = line.points[::2]
    y_list = line.points[1::2]
    bounding_box = Box(
        x=min(x_list), y=min(y_list), right=max(x_list), top=max(y_list),
    )
    return (inst_group, bounding_box)


async def _op_polyline(widget, touch, ctx):
    from kivy.core.window import Window
    to_local = widget.to_local
    to_widget = widget.to_widget
    inst_group = InstructionGroup()
    inst_group.add(Color(*ctx.line_color))
    line = Line(
        width=ctx.line_width,
        points=[*to_local(*touch.opos), *to_local(*touch.pos)]
    )
    inst_group.add(line)
    widget.canvas.add(inst_group)

    def on_touch_down(w, t):
        if t.button == 'left':
            p = line.points
            p.extend(p[-2:])
            # line.points = p
            return True
    def on_mouse_pos(window, mouse_pos):
        x, y = to_widget(*mouse_pos)
        points = line.points
        points[-1] = y
        points[-2] = x
        line.points = points
    try:
        Window.bind(mouse_pos=on_mouse_pos)
        widget.bind(on_touch_down=on_touch_down)
        await ak.event(
            widget, 'on_touch_down',
            filter=lambda w, t: t.button == 'right',
            return_value=True)
    except:
        widget.canvas.remove(inst_group)
        raise
    finally:
        widget.unbind(on_touch_down=on_touch_down)
        Window.unbind(mouse_pos=on_mouse_pos)
    x_list = line.points[::2]
    y_list = line.points[1::2]
    bounding_box = Box(
        x=min(x_list), y=min(y_list), right=max(x_list), top=max(y_list),
    )
    return (inst_group, bounding_box)


operations = (
    Operation(
        name='rectangle(line)',
        func=_op_rectangle_line,
        icon='rectangle-outline',
    ),
    Operation(
        name='ellipse(line)',
        func=partial(_op_rectangle_line, shape_name='ellipse'),
        icon='ellipse-outline',
    ),
    Operation(
        name='rectangle(fill)',
        func=_op_rectangle_fill,
        icon='rectangle',
    ),
    Operation(
        name='ellipse(fill)',
        func=partial(_op_rectangle_fill, shape_name='Ellipse'),
        icon='ellipse',
    ),
    Operation(
        name='freehand',
        func=_op_freehand,
        icon='signature-freehand',
    ),
    Operation(
        name='polyline',
        func=_op_polyline,
        icon='vector-polyline',
        helper_text="'left-click' to plot. 'right-click' to finish."
    ),
)