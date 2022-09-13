import random
from time import sleep
import json
from telegram.message import Message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from irregular_verbs import IrregularVerbsSet


class Question:
    def __init__(self) -> None:
        self.text = ""
        self.options = ""
        self.right_option = ""
        self.explain = ""

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def get_random_question(extended=False):
    iv = IrregularVerbsSet.get_random_verb(extended)
    q = Question()
    form = random.choice(iv.forms)

    q.right_option = getattr(iv, form).spelling
    q.text = "\n".join(
        [
            f"""Choose the *{form.replace('_', ' ')}* form of the verb""",
            f"""which translates as `{iv.translation}`""",
        ]
    )

    options = [getattr(iv, x).spelling for x in iv.forms]
    random.shuffle(options)
    q.options = options
    q.explain = f"{iv}"
    return q


class Quiz:
    def __init__(self, message: Message) -> None:
        self.user = message.from_user
        self.correct = 0
        self.incorrect = 0
        self.started = False
        self.current_question = None
        self.extended = False

        keyboard = [
            [
                InlineKeyboardButton(text=" ▶️ normal", callback_data="start_normal"),
                InlineKeyboardButton(
                    text=" ▶️ extended", callback_data="start_extended"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "there should be text that explains the rules"
        if not hasattr(self, "message"):
            self.message = message.reply_text(text=text, reply_markup=reply_markup)
        else:
            self.message = message.edit_text(text=text, reply_markup=reply_markup)

    def __repr__(self) -> str:
        return f"User's {self.user.full_name} quiz"

    def process(self, update: Update = None):
        data = update.callback_query.data
        if data.startswith("start"):
            self.extended = "extended" in data
            self.next_question()
        elif data == "back":
            self.__init__(self.message)
        else:
            right_opt = self.current_question.right_option
            if data == right_opt:
                self.correct += 1
                update.callback_query.answer(text="✅ Definitely!", show_alert=True)
            else:
                self.incorrect += 1
                update.callback_query.answer(
                    text="\n".join(
                        [
                            f"""❌ Unfortunately.""",
                            f"""The correct answer is *{right_opt}*""",
                            "",
                            f"""{self.current_question.explain}""",
                        ]
                    ),
                    show_alert=True,
                )
                sleep(5)
            self.next_question()

    def next_question(self):
        self.current_question = get_random_question(self.extended)
        keyboard = [
            [
                InlineKeyboardButton(text=x, callback_data=x)
                for x in self.current_question.options
            ],
            [InlineKeyboardButton(text=" ↩️ back", callback_data="back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        self.message = self.message.edit_text(
            text="\n".join([self.current_question.text]),
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2,
        )

    def get_score_presentation(self):
        percentage = (
            ((self.incorrect + self.correct) / self.correct) * 100
            if self.correct
            else 0
        )
        return f"`{' '*22} R: {self.correct} W: {self.incorrect}; {round(percentage)}%`"


class QuizManager:
    def __init__(self) -> None:
        self.pool = []

    def get_quiz(self, user):
        f = 1
