"""Бот: у доходов кнопка «Категория» показывает категории доходов; чеки/скриншоты получают категорию дохода."""
import re, sys
from pathlib import Path
R = Path("/opt/tiyin/tiyin-bot") if len(sys.argv) < 2 else Path(sys.argv[1])
vw, bt = R / "tiyin/views.py", R / "tiyin/bot.py"
V, B = vw.read_text(), bt.read_text()
assert "INC_BASE" not in V, "уже применено"


def sub1(pat, repl, s, name):
    s2, n = re.subn(pat, repl, s, count=1, flags=re.M)
    assert n == 1, "не найдено: " + name
    return s2


# --- views.py ---
V = sub1(r'^from \.parser import ALL_CATEGORIES, OTHER\n',
         lambda m: 'from .parser import ALL_CATEGORIES, INCOME_CATEGORIES, OTHER\n'
                   'INC_BASE = 1000  # CatCb.idx >= INC_BASE -> INCOME_CATEGORIES[idx - INC_BASE]\n'
                   'INC_EMOJI = {"Зарплата": "💼", "Подработка": "🛠", "Бизнес": "📈", "Подарки": "🎁", "Проценты": "🏦",\n'
                   '             "Возврат": "↩", "Переводы": "💸", "Другое": "🧾"}\n', V, "views import")
V = sub1(r'^def category_markup\(tx_id: int\) -> InlineKeyboardMarkup:\n(\s*)rows = _rows\(',
         lambda m: 'def category_markup(tx_id: int, income: bool = False) -> InlineKeyboardMarkup:\n'
                   f'{m.group(1)}if income:\n'
                   f'{m.group(1)}    rows = _rows((InlineKeyboardButton(text=f"{{INC_EMOJI.get(c, \'🧾\')}} {{c}}",\n'
                   f'{m.group(1)}                 callback_data=CatCb(id=tx_id, idx=INC_BASE + i).pack())\n'
                   f'{m.group(1)}                 for i, c in enumerate(INCOME_CATEGORIES)), 2)\n'
                   f'{m.group(1)}    rows.append([InlineKeyboardButton(text="↩ Назад", callback_data=TxCb(action="bk", id=tx_id).pack())])\n'
                   f'{m.group(1)}    return _kb(rows)\n'
                   f'{m.group(1)}rows = _rows(', V, "category_markup")

# --- bot.py ---
B = sub1(r'^from \.parser import ALL_CATEGORIES, OTHER, guess_category, parse_expense\n',
         lambda m: 'from .parser import ALL_CATEGORIES, INCOME_CATEGORIES, OTHER, guess_category, parse_expense\n', B, "bot import")
B = sub1(r'reply_markup=views\.category_markup\(tx\["id"\]\)\)',
         lambda m: 'reply_markup=views.category_markup(tx["id"], tx["kind"] == "income"))', B, "ed call")
B = sub1(r'^(\s*)if not 0 <= callback_data\.idx < len\(ALL_CATEGORIES\):\n\s*return await cb\.answer\(\)\n\s*cat = ALL_CATEGORIES\[callback_data\.idx\]\n'
         r'(\s*)db\.x\("UPDATE tx SET category=\? WHERE id=\? AND user_id=\?", \(cat, tx\["id"\], uid\)\)\n'
         r'\s*service\.learn_category\(db, uid, tx\["merchant"\], cat\)\n',
         lambda m: (f'{m.group(1)}income = callback_data.idx >= views.INC_BASE\n'
                    f'{m.group(1)}i = callback_data.idx - views.INC_BASE if income else callback_data.idx\n'
                    f'{m.group(1)}cats = INCOME_CATEGORIES if income else ALL_CATEGORIES\n'
                    f'{m.group(1)}if not 0 <= i < len(cats):\n'
                    f'{m.group(1)}    return await cb.answer()\n'
                    f'{m.group(1)}cat = cats[i]\n'
                    f'{m.group(1)}db.x("UPDATE tx SET category=? WHERE id=? AND user_id=?", (cat, tx["id"], uid))\n'
                    f'{m.group(1)}if not income:\n'
                    f'{m.group(1)}    service.learn_category(db, uid, tx["merchant"], cat)\n'), B, "cb_category")
B = sub1(r'vision\.extract\(data, mt, cfg\.default_tz_min, \[c for c in ALL_CATEGORIES\]\)',
         lambda m: 'vision.extract(data, mt, cfg.default_tz_min, list(ALL_CATEGORIES) + [c for c in INCOME_CATEGORIES if c not in ALL_CATEGORIES])',
         B, "vision cats")
B = sub1(r'\(it\["category"\] if it\["kind"\] == "expense" and it\["category"\] in ALL_CATEGORIES else None\)',
         lambda m: '(it["category"] if (it["category"] in ALL_CATEGORIES if it["kind"] == "expense" else it["category"] in INCOME_CATEGORIES) else None)',
         B, "photo category")

vw.write_text(V)
bt.write_text(B)
print("PATCH OK")
