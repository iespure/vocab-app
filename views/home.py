"""首页：学习概览 + 操作入口"""
import flet as ft
from models import ProgressDB, WordBank


def build_home_page(page: ft.Page, go_flashcard, go_quiz):
    db = ProgressDB()
    daily_goal = int(db.get_setting("daily_goal", "20"))

    selected_raw = db.get_setting("selected_grades", "")
    selected_grades = [g for g in selected_raw.split(",") if g] if selected_raw else WordBank.available_grades()
    word_bank = WordBank(selected_grades)

    # ── 统计数据 ──
    due_count = db.get_due_count()
    today_new = db.get_today_new_count()
    learned_count = db.get_learned_count()
    total_words = len(word_bank.words)

    def refresh_stats():
        nonlocal due_count, today_new, learned_count, total_words
        due_count = db.get_due_count()
        today_new = db.get_today_new_count()
        learned_count = db.get_learned_count()
        due_text.value = f"⏰ 待复习: {due_count}"
        today_text.value = f"📖 今日新学: {today_new} / {daily_goal}"
        learned_text.value = f"✅ 已掌握: {learned_count} / {total_words}"
        page.update()

    # ── 词库选择 ──
    all_grades = WordBank.available_grades()
    grade_checkboxes = {}

    def on_grade_change(_):
        selected = [g for g, cb in grade_checkboxes.items() if cb.value]
        db.set_setting("selected_grades", ",".join(selected))
        nonlocal word_bank, total_words
        word_bank = WordBank(selected)
        total_words = len(word_bank.words)
        refresh_stats()

    grade_chips = ft.Row(
        controls=[],
        wrap=True,
        spacing=8,
        run_spacing=4,
    )
    for g in all_grades:
        cb = ft.Checkbox(
            label=g,
            value=g in selected_grades,
            on_change=on_grade_change,
            label_style=ft.TextStyle(size=13),
        )
        grade_checkboxes[g] = cb
        grade_chips.controls.append(cb)

    # ── 每日目标 ──
    goal_slider = ft.Slider(
        min=5, max=50, divisions=9, value=float(daily_goal),
        label="{value}",
        on_change=lambda e: db.set_setting("daily_goal", str(int(e.control.value))),
    )

    # ── 统计文本 ──
    due_text = ft.Text(f"⏰ 待复习: {due_count}", size=18, weight=ft.FontWeight.W_500)
    today_text = ft.Text(f"📖 今日新学: {today_new} / {daily_goal}", size=18, weight=ft.FontWeight.W_500)
    learned_text = ft.Text(f"✅ 已掌握: {learned_count} / {total_words}", size=18, weight=ft.FontWeight.W_500)

    # ── 按钮 ──
    learn_btn = ft.ElevatedButton(
        "📖 学习新词",
        on_click=lambda _: go_flashcard("learn"),
        style=ft.ButtonStyle(padding=20),
        width=280, height=50,
    )
    review_btn = ft.ElevatedButton(
        "🔄 复习旧词",
        on_click=lambda _: go_flashcard("review"),
        style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.ORANGE_200),
        width=280, height=50,
    )
    quiz_btn = ft.ElevatedButton(
        "📝 选择题测试",
        on_click=lambda _: go_quiz(),
        style=ft.ButtonStyle(padding=20, bgcolor=ft.colors.BLUE_200),
        width=280, height=50,
    )

    # ── 组合页面 ──
    return ft.Column(
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=16,
        controls=[
            ft.Text("📚 记单词", size=28, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            due_text, today_text, learned_text,
            ft.Divider(),
            ft.Text("词库范围", size=14, weight=ft.FontWeight.W_500),
            grade_chips,
            ft.Text(f"每日新词目标: {daily_goal}", size=13),
            goal_slider,
            ft.Divider(),
            learn_btn, review_btn, quiz_btn,
        ],
    )
