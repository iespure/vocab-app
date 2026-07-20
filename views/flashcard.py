"""闪卡模式：正面英文 → 点击翻转 → 背面中文+例句 → 评分"""
import flet as ft
from models import ProgressDB, SM2, WordBank


def build_flashcard_page(page: ft.Page, mode: str, go_home):
    """
    mode: "learn" → 学习新词; "review" → 复习旧词
    """
    db = ProgressDB()

    selected_raw = db.get_setting("selected_grades", "")
    selected_grades = [g for g in selected_raw.split(",") if g] if selected_raw else WordBank.available_grades()
    word_bank = WordBank(selected_grades)

    daily_goal = int(db.get_setting("daily_goal", "20"))

    # ── 构建队列 ──
    if mode == "review":
        word_list_raw = db.get_due_reviews(selected_grades)
        word_list = []
        for w in word_list_raw:
            entry = word_bank.get_by_word(w)
            if entry:
                word_list.append(entry)
    else:
        word_list = db.get_unseen_words(word_bank, daily_goal)

    if not word_list:
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("🎉", size=48),
                ft.Text("没有需要学习的单词了！" if mode == "learn" else "没有待复习的单词！", size=20),
                ft.Text("试试调整词库范围或每日目标", size=14, color=ft.colors.GREY),
                ft.ElevatedButton("🏠 返回首页", on_click=lambda _: go_home()),
            ],
        )

    # ── 状态 ──
    card_index = 0
    is_flipped = False

    # ── 控件 ──
    progress_bar = ft.ProgressBar(value=0.0, width=300)
    progress_text = ft.Text("0 / 0", size=13)
    card_word_text = ft.Text("", size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    card_meaning_text = ft.Text("", size=22, text_align=ft.TextAlign.CENTER)
    card_example_text = ft.Text("", size=14, italic=True, color=ft.colors.GREY_700, text_align=ft.TextAlign.CENTER)
    result_text = ft.Text("", size=16, text_align=ft.TextAlign.CENTER)

    forgot_btn = ft.ElevatedButton(
        "😞 没记住",
        style=ft.ButtonStyle(bgcolor=ft.colors.RED_200),
        visible=False,
    )
    hard_btn = ft.ElevatedButton(
        "🤔 有点难",
        style=ft.ButtonStyle(bgcolor=ft.colors.ORANGE_200),
        visible=False,
    )
    good_btn = ft.ElevatedButton(
        "😊 记住了",
        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_200),
        visible=False,
    )
    easy_btn = ft.ElevatedButton(
        "😎 很简单",
        style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_400),
        visible=False,
    )
    next_btn = ft.ElevatedButton("下一个 →", visible=False)
    back_btn = ft.TextButton("🏠 返回")

    def toggle_rating_btns(visible: bool):
        forgot_btn.visible = visible
        hard_btn.visible = visible
        good_btn.visible = visible
        easy_btn.visible = visible
        next_btn.visible = False
        page.update()

    def show_current_card():
        nonlocal is_flipped
        is_flipped = False
        if card_index < len(word_list):
            w = word_list[card_index]
            card_word_text.value = w["word"].upper()
            card_meaning_text.value = ""
            card_example_text.value = ""
            result_text.value = ""
            progress_bar.value = card_index / len(word_list)
            progress_text.value = f"{card_index} / {len(word_list)}"
            toggle_rating_btns(False)
            next_btn.visible = False
        else:
            # 本轮结束
            card_word_text.value = "🎉"
            card_meaning_text.value = "本轮学习完成！"
            card_example_text.value = ""
            result_text.value = ""
            progress_bar.value = 1.0
            progress_text.value = f"{len(word_list)} / {len(word_list)}"
            toggle_rating_btns(False)
            next_btn.visible = False
        back_btn.visible = True
        page.update()

    def flip_card(_):
        nonlocal is_flipped
        if card_index >= len(word_list):
            return
        is_flipped = True
        w = word_list[card_index]
        card_word_text.value = w["word"].upper()
        card_meaning_text.value = w["meaning"]
        card_example_text.value = w.get("example", "")
        toggle_rating_btns(True)
        page.update()

    def rate(quality: int):
        nonlocal card_index
        w = word_list[card_index]
        progress = db.get_word_progress(w["word"])
        if progress:
            result = SM2.review(
                progress["interval_days"],
                progress["ease_factor"],
                progress["repetitions"],
                quality,
            )
        else:
            result = SM2.review(0, 2.5, 0, quality)

        db.update_word_progress(w["word"], w["grade"], result, quality)

        labels = {1: "没记住", 2: "有点难", 3: "有点难", 4: "记住了", 5: "很简单"}
        result_text.value = f"{'✅' if quality >= 3 else '❌'} {labels[quality]} | 下次: {result['next_review']}"
        toggle_rating_btns(False)
        next_btn.visible = True
        page.update()

    def next_card(_):
        nonlocal card_index
        card_index += 1
        show_current_card()

    # ── 绑定 ──
    forgot_btn.on_click = lambda _: rate(1)
    hard_btn.on_click = lambda _: rate(2)
    good_btn.on_click = lambda _: rate(4)
    easy_btn.on_click = lambda _: rate(5)
    next_btn.on_click = next_card
    back_btn.on_click = lambda _: go_home()

    card_container = ft.Container(
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[
                card_word_text,
                card_meaning_text,
                card_example_text,
            ],
        ),
        width=320,
        height=220,
        border_radius=16,
        bgcolor=ft.colors.WHITE,
        border=ft.border.all(2, ft.colors.BLUE_200),
        padding=20,
        shadow=ft.BoxShadow(spread_radius=1, blur_radius=8, color=ft.colors.GREY_300),
        on_click=flip_card,
        ink=True,
    )

    # 初始显示第一张卡片
    show_current_card()

    return ft.Column(
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        controls=[
            ft.Row(
                controls=[back_btn],
                alignment=ft.MainAxisAlignment.START,
            ),
            ft.Text(
                "📖 学习新词" if mode == "learn" else "🔄 复习旧词",
                size=20,
                weight=ft.FontWeight.BOLD,
            ),
            progress_bar,
            progress_text,
            card_container,
            ft.Text("👆 点击卡片翻转", size=12, color=ft.colors.GREY),
            result_text,
            ft.Row(
                controls=[forgot_btn, hard_btn, good_btn, easy_btn],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
                wrap=True,
            ),
            next_btn,
        ],
    )
