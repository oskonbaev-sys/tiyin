"""Выбор валюты (сом / $) при вводе дохода в мини-приложении.
Доллары пересчитываются в сомы по курсу НБКР (fx.py), исходная сумма сохраняется в orig_*."""
import re, sys
from pathlib import Path
R = Path("/opt/tiyin/tiyin-bot") if len(sys.argv) < 2 else Path(sys.argv[1])
srv, web = R / "tiyin/server.py", R / "webapp/index.html"
S, W = srv.read_text(), web.read_text()
assert "hcur" not in W, "уже применено"


def sub1(pat, repl, s, name):
    s2, n = re.subn(pat, repl, s, count=1, flags=re.M)
    assert n == 1, "не найдено: " + name
    return s2


# --- сервер: /api/tx принимает currency ---
S = sub1(r'^(\s*)res = service\.add_tx\(db, user, kind=p\.kind, amount_minor=p\.amount_minor, merchant=p\.title,\n\s*source="manual", ts=p\.ts\)\n',
         lambda m: (
             f'{m.group(1)}cur = normalize_currency(b.get("currency"), user["currency"]) if b.get("currency") else None\n'
             f'{m.group(1)}if cur and cur != user["currency"]:\n'
             f'{m.group(1)}    from . import fx as _fx\n'
             f'{m.group(1)}    if not _fx.convert(db, p.amount_minor, cur, user["currency"], int(p.ts or now)):\n'
             f'{m.group(1)}        raise ApiError(503, "Нет курса валюты, попробуйте позже")\n'
             f'{m.group(1)}res = service.add_tx(db, user, kind=p.kind, amount_minor=p.amount_minor, merchant=p.title,\n'
             f'{m.group(1)}                     source="manual", ts=p.ts, currency=cur)\n'),
         S, "api/tx add_tx")

# --- мини-приложение: переключатель с / $ в окне дохода ---
W = sub1(r'^(\s*)function homeSheet\(kind, cat\) \{\n', lambda m: m.group(0) +
         f'{m.group(1)}  let hcur = "KGS";\n'
         f'{m.group(1)}  const curSeg = el("div", {{class: "seg", style: "margin:0"}});\n'
         f'{m.group(1)}  const curBox = kind === "income" ? el("div", {{style: "text-align:right;margin-top:6px"}}, curSeg) : null;\n'
         f'{m.group(1)}  const drawCur = () => curSeg.replaceChildren(...[["KGS", "с"], ["USD", "$"]].map(([v, n]) =>\n'
         f'{m.group(1)}    el("button", {{class: v === hcur ? "on" : "", text: n, onclick: () => {{ hcur = v; drawCur(); paint(); }}}})));\n'
         f'{m.group(1)}  drawCur();\n', W, "homeSheet")

W = sub1(r'view\.textContent = \(amt === "" \? "0" : amt\)\.replace\("\.", ","\);',
         lambda m: 'view.textContent = (hcur === "USD" ? "$" : "") + (amt === "" ? "0" : amt).replace(".", ",");', W, "paint")

W = sub1(r'api\("/api/tx", "POST", \{text\}\)',
         lambda m: 'api("/api/tx", "POST", kind === "income" ? {text, currency: hcur} : {text})', W, "post")

W = sub1(r'toast\(r\.duplicate \? "Уже записано" : "Записано"\);(\s*close\(\);)',
         lambda m: 'toast((r.duplicate ? "Уже записано" : "Записано") + (r.tx && r.tx.orig_currency ? " ≈ " + money(r.tx.amount_minor, r.tx.currency) : ""));' + m.group(1),
         W, "toast")

W = sub1(r'^(\s*)view,\n(\s*el\("div", \{class: "hm-keys"\})',
         lambda m: f'{m.group(1)}...(curBox ? [curBox] : []),\n{m.group(1)}view,\n{m.group(2)}', W, "insert seg")

srv.write_text(S)
web.write_text(W)
print("PATCH OK")
