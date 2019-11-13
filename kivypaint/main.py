def _register_icon_font():
    from pathlib import Path
    from kivy.core.text import LabelBase
    font_path = Path(__file__).parent.joinpath(
        'kivymd', 'fonts', 'materialdesignicons-webfont.ttf')
    LabelBase.register('Icon', str(font_path))


def _main():
    from kivy.app import App
    class PaintApp(App):
        def build(self):
            from kivypaint import Paint
            return Paint()
    PaintApp().run()


if __name__ == "__main__":
    _register_icon_font()
    _main()
