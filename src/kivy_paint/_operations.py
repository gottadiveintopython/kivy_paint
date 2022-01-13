__all__ = (
    'RectangleLine', 'RectangleFill',
    'EllipseLine', 'EllipseFill',
    'FreeHand', 'PolyLine',
    'Clear',
)


def _is_inside(widget, touch):
    return widget.collide_point(*touch.opos) and touch.button == 'left'


def _is_right_button(widget, touch):
    return touch.button == 'right'


class RectangleLine:
    icon = 'rectangle-outline'
    helper_text = 'left-button to draw'
    _shape_name = 'rectangle'

    @classmethod
    async def main(cls, *, widgets, ctx):
        from kivy.graphics import Line, Color, InstructionGroup
        import asynckivy as ak
        target = widgets['target']
        to_local = target.to_local
        shape_name = cls._shape_name
        is_inside = _is_inside
        while True:
            __, touch = await ak.event(target, 'on_touch_down', filter=is_inside, stop_dispatching=True)
            ox, oy = x, y = to_local(*touch.opos)
            target.canvas.add(ig := InstructionGroup())
            ig.add(Color(*ctx.line_color))
            ig.add(line := Line(width=ctx.line_width))
            async for __ in ak.rest_of_touch_moves(target, touch):
                x, y = to_local(*touch.pos)
                min_x, max_x = (x, ox) if x < ox else (ox, x)
                min_y, max_y = (y, oy) if y < oy else (oy, y)
                setattr(line, shape_name, (min_x, min_y, max_x - min_x, max_y - min_y, ))
            if x == ox and y == oy:
                target.canvas.remove(ig)


class EllipseLine(RectangleLine):
    icon = 'ellipse-outline'
    _shape_name = 'ellipse'


class RectangleFill:
    icon = 'rectangle'
    helper_text = 'left-button to draw'
    _shape_name = 'Rectangle'

    @classmethod
    async def main(cls, *, widgets, ctx):
        from kivy.graphics import Color, InstructionGroup
        import kivy.graphics
        import asynckivy as ak
        target = widgets['target']
        shape_cls = getattr(kivy.graphics, cls._shape_name)
        to_local = target.to_local
        is_inside = _is_inside
        while True:
            __, touch = await ak.event(target, 'on_touch_down', filter=is_inside, stop_dispatching=True)
            ox, oy = x, y = to_local(*touch.opos)
            target.canvas.add(ig := InstructionGroup())
            ig.add(Color(*ctx.fill_color))
            ig.add(shape := shape_cls(size=(0, 0)))
            async for __ in ak.rest_of_touch_moves(target, touch):
                x, y = to_local(*touch.pos)
                min_x, max_x = (x, ox) if x < ox else (ox, x)
                min_y, max_y = (y, oy) if y < oy else (oy, y)
                shape.pos = min_x, min_y
                shape.size = max_x - min_x, max_y - min_y
            if x == ox and y == oy:
                target.canvas.remove(ig)


class EllipseFill(RectangleFill):
    icon = 'ellipse'
    _shape_name = 'Ellipse'


class FreeHand:
    icon = 'signature-freehand'
    helper_text = 'left-button to draw'

    @classmethod
    async def main(cls, *, widgets, ctx):
        from kivy.graphics import Line, Color, InstructionGroup
        import asynckivy as ak
        abs_ = abs
        target = widgets['target']
        to_local = target.to_local
        is_inside = _is_inside
        while True:
            __, touch = await ak.event(target, 'on_touch_down', filter=is_inside, stop_dispatching=True)
            target.canvas.add(ig := InstructionGroup())
            ig.add(Color(*ctx.line_color))
            ig.add(line := Line(width=ctx.line_width, points=[*to_local(*touch.opos)]))
            precision = ctx.freehand_precision
            last_x, last_y = touch.opos
            async for __ in ak.rest_of_touch_moves(target, touch):
                if abs_(last_x - touch.x) + abs_(last_y - touch.y) > precision:
                    p = line.points
                    p.extend(to_local(*touch.pos))
                    line.points = p
                    last_x, last_y = touch.pos


class PolyLine:
    icon = 'vector-polyline'
    helper_text = "left-button to extend. right-button to finish."

    @classmethod
    async def main(cls, *, widgets, ctx):
        from kivy.graphics import Line, Color, InstructionGroup
        import asynckivy as ak
        target = widgets['target']
        to_local = target.to_local
        to_widget = target.to_widget
        window = target.get_root_window()  # NOTE: I don't know the difference from get_parent_window()
        is_inside = _is_inside
        is_right_button = _is_right_button
        while True:
            __, touch = await ak.event(target, 'on_touch_down', filter=is_inside, stop_dispatching=True)
            target.canvas.add(ig := InstructionGroup())
            ig.add(Color(*ctx.line_color))
            ig.add(line := Line(width=ctx.line_width, points=[*to_local(*touch.opos), *to_local(*touch.pos), ]))

            def on_touch_down(w, t):
                if t.button == 'left':
                    p = line.points
                    p.extend(p[-2:])
                    # line.points = p
                    return True
            def on_mouse_pos(window, mouse_pos):
                x, y = to_widget(*mouse_pos)
                p = line.points
                p[-1] = y
                p[-2] = x
                line.points = p

            try:
                window.bind(mouse_pos=on_mouse_pos)
                target.bind(on_touch_down=on_touch_down)
                await ak.event(target, 'on_touch_down', filter=is_right_button, stop_dispatching=True)
            finally:
                target.unbind(on_touch_down=on_touch_down)
                window.unbind(mouse_pos=on_mouse_pos)


class Clear:
    icon = 'delete-alert'
    helper_text = ''

    @classmethod
    async def main(cls, *, widgets, ctx):
        from ._utils import show_yes_no_dialog
        if await show_yes_no_dialog(text_main='clear the canvas ?') == 'yes':
            widgets['target'].canvas.clear()
        for c in widgets['toolbox'].children:
            c.state = 'normal'
