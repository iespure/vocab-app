"""记单词 APP — 入口"""
import flet as ft
from views.home import build_home_page
from views.flashcard import build_flashcard_page
from views.quiz import build_quiz_page


def main(page: ft.Page):
    page.title = "📚 记单词"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.window.width = 400
    page.window.height = 750
    page.scroll = ft.ScrollMode.AUTO

    # ── 页面路由 ──
    def go_home():
        page.controls.clear()
        page.controls.append(build_home_page(page, go_flashcard, go_quiz))
        page.update()

    def go_flashcard(mode: str):
        page.controls.clear()
        page.controls.append(build_flashcard_page(page, mode, go_home))
        page.update()

    def go_quiz():
        page.controls.clear()
        page.controls.append(build_quiz_page(page, go_home))
        page.update()

    go_home()


ft.app(target=main)
