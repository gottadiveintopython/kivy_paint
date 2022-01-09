def _main():
    from kivy.config import Config
    Config.set('input', 'mouse', 'mouse,disable_multitouch')
    from kivy.app import App
    class PaintApp(App):
        def build(self):
            from kivy_paint import KPMain
            return KPMain()
    PaintApp().run()


if __name__ == "__main__":
    _main()
