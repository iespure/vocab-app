"""选择题模式：英文 → 四选一中文 → 即时判对错"""
import random
import flet as ft
from models import ProgressDB, SM2, WordBank


def build_quiz_page(page: ft.Page, go_home):
    db = ProgressDB()

    selected_raw = db.get_setting("selected_grades", "")
    selected_grades = [g for g in selected_raw.split(",") if g] if selected_raw else WordBank.available_grades()
    word_bank = WordBank(selected_grades)

    all_words = word_bank.words
    if len(all_words) < 4:
        return ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Text("⚠️", size=48),
                ft.Text("词库单词不足 4 个，至少需要 4 个才能出题", size=16),
                ft.ElevatedButton("🏠 返回首页", on_click=lambda _: go_home()),
            ],
        )

    # ── 生成题目 ──
    current_correct: dict | None = None
    options: list[str] = []
    question_index = 0
    total_questions = min(20, len(all_words))
    correct_count = 0

    def generate_question():
        nonlocal current_correct, options
        # 随机抽一个作为正确答案
        correct = random.choice(all_words)
        current_correct = correct
        # 抽 3 个干扰项
        others = [w for w in all_words if w["word"] != correct["word"]]
        distractors = random.sample(others, min(3, len(others)))
        options = [correct["meaning"]] + [d["meaning"] for d in distractors]
        random.shuffle(options)
        return correct

    back_btn = ft.TextButton("🏠 返回")
    progress_text = ft.Text("1 / 0", size=14)
    question_word = ft.Text("", size=32, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
    feedback_text = ft.Text("", size=16, text_align=ft.TextAlign.CENTER)
    stats_text = ft.Text(f"✅ {correct_count} / {question_index}", size=14, weight=ft.FontWeight.W_500)

    option_btns: list[ft.ElevatedButton] = []
    option_row = ft.Column(spacing=10, controls=option_btns)
    next_btn = ft.ElevatedButton("下一题 →", visible=False)

    def check_answer(answer: str):
        nonlocal correct_count
        is_correct = answer == current_correct["meaning"]
        if is_correct:
            correct_count += 1
            feedback_text.value = "✅ 正确！"
            feedback_text.color = ft.colors.GREEN
        else:
            feedback_text.value = f"❌ 错了！正确答案: {current_correct['meaning']}"
            feedback_text.color = ft.colors.RED

        # SM-2 更新
        w = current_correct
        progress = db.get_word_progress(w["word"])
        quality = 4 if is_correct else 1
        if progress:
            result = SM2.review(progress["interval_days"], progress["ease_factor"], progress["repetitions"], quality)
        else:
            result = SM2.review(0, 2.5, 0, quality)
        db.update_word_progress(w["word"], w["grade"], result, quality)

        stats_text.value = f"✅ {correct_count} / {question_index + 1}"
        # 高亮正确选项
        for btn in option_btns:
            btn.disabled = True
            if btn.text == current_correct["meaning"]:
                btn.style = ft.ButtonStyle(bgcolor=ft.colors.GREEN_200)
            elif btn.text == answer and not is_correct:
                btn.style = ft.ButtonStyle(bgcolor=ft.colors.RED_200)
        next_btn.visible = True
        page.update()

    def next_question(_):
        nonlocal question_index
        question_index += 1
        if question_index >= total_questions:
            # 结束
            question_word.value = "🎉"
            feedback_text.value = f"测试完成！正确率: {correct_count}/{total_questions}"
            feedback_text.color = ft.colors.BLACK
            stats_text.value = f"✅ {correct_count} / {total_questions}"
            option_row.controls.clear()
            next_btn.visible = False
            page.update()
            return

        generate_question()
        question_word.value = current_correct["word"].upper()
        feedback_text.value = ""
        progress_text.value = f"{question_index + 1} / {total_questions}"
        stats_text.value = f"✅ {correct_count} / {question_index}"

        # 重建选项按钮
        option_row.controls.clear()
        option_btns.clear()
        for opt in options:
            btn = ft.ElevatedButton(
                opt,
                width=300,
                height=48,
                style=ft.ButtonStyle(padding=15),
                on_click=lambda _, a=opt: check_answer(a),
            )
            option_btns.append(btn)
            option_row.controls.append(btn)
        next_btn.visible = False
        page.update()

    # 初始化第一题
    total_questions = min(20, len(all_words))
    generate_question()
    question_word.value = current_correct["word"].upper()
    progress_text.value = f"1 / {total_questions}"
    stats_text.value = f"✅ 0 / 0"

    for opt in options:
        btn = ft.ElevatedButton(
            opt,
            width=300,
            height=48,
            style=ft.ButtonStyle(padding=15),
            on_click=lambda _, a=opt: check_answer(a),
        )
        option_btns.append(btn)
        option_row.controls.append(btn)

    next_btn.on_click = next_question
    back_btn.on_click = lambda _: go_home()

    return ft.Column(
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        controls=[
            ft.Row(controls=[back_btn], alignment=ft.MainAxisAlignment.START),
            ft.Text("📝 选择题测试", size=20, weight=ft.FontWeight.BOLD),
            progress_text,
            stats_text,
            ft.Divider(),
            question_word,
            ft.Text("选择一个释义：", size=14, color=ft.colors.GREY),
            option_row,
            feedback_text,
            next_btn,
        ],
    )
