import re, sys
from pathlib import Path
R = Path("/opt/tiyin/tiyin-bot") if len(sys.argv) < 2 else Path(sys.argv[1])
srv, web = R / "tiyin/server.py", R / "webapp/index.html"
S, W = srv.read_text(), web.read_text()
assert "_receipt_save" not in S, "уже применено"

def sub1(pat, repl, s, name):
    s2, n = re.subn(pat, repl, s, count=1, flags=re.M)
    assert n == 1, "не найдено: " + name
    return s2

S = sub1(r'^(\s*)if method == "POST" and path == "/api/app/login":\n', lambda m:
    f'{m.group(1)}if method == "POST" and path == "/api/receipt":\n{m.group(1)}    return self._receipt()\n'
    f'{m.group(1)}if method == "POST" and path == "/api/receipt/save":\n{m.group(1)}    return self._receipt_save()\n' + m.group(0), S, "login route")

def methods(i):
    return f'''{i}def _big_body(self, limit=8 * 1024 * 1024):
{i}    n = int(self.headers.get("Content-Length") or 0)
{i}    if n > limit:
{i}        raise ApiError(413, "too large")
{i}    try:
{i}        data = json.loads(self.rfile.read(n) or b"{{}}")
{i}    except ValueError:
{i}        raise ApiError(400, "bad json")
{i}    if not isinstance(data, dict):
{i}        raise ApiError(400, "bad json")
{i}    return data

{i}def _receipt(self):
{i}    """Чек/скриншот из мини-приложения -> черновики операций (без сохранения)."""
{i}    import asyncio, base64
{i}    from . import vision
{i}    from .parser import ALL_CATEGORIES as _AC, INCOME_CATEGORIES as _IC
{i}    user = self._user()
{i}    b = self._big_body()
{i}    if not app.rate_ok("vision:" + str(user["tg_id"])):
{i}        raise ApiError(429, "Слишком часто, подождите минуту")
{i}    if not vision.api_key():
{i}        raise ApiError(503, "Распознавание не настроено")
{i}    mt = str(b.get("mime") or "image/jpeg")
{i}    if mt not in ("image/jpeg", "image/png", "image/webp", "image/gif"):
{i}        raise ApiError(400, "Нужно фото или скриншот (JPG, PNG)")
{i}    try:
{i}        img = base64.b64decode(str(b.get("image") or "").split(",")[-1])
{i}    except Exception:
{i}        raise ApiError(400, "Файл не читается")
{i}    if len(img) < 200:
{i}        raise ApiError(400, "Файл не читается")
{i}    try:
{i}        tz = user["tz_min"]
{i}    except (KeyError, IndexError, TypeError):
{i}        tz = app.cfg.default_tz_min
{i}    try:
{i}        items = asyncio.run(vision.extract(img, mt, tz, list(_AC)))
{i}    except Exception:
{i}        log.exception("receipt vision failed")
{i}        raise ApiError(502, "Не получилось прочитать картинку, попробуйте ещё раз")
{i}    self._json(200, {{"ok": True, "items": items, "categories": list(_AC), "income_categories": list(_IC)}})

{i}def _receipt_save(self):
{i}    user = self._user()
{i}    items = self._body().get("items")
{i}    if not isinstance(items, list):
{i}        raise ApiError(400, "bad items")
{i}    added = skipped = 0
{i}    now = int(time.time())
{i}    for it in items[:50]:
{i}        if not isinstance(it, dict):
{i}            continue
{i}        kind = "income" if it.get("kind") == "income" else "expense"
{i}        try:
{i}            amount = int(it.get("amount_minor"))
{i}            ts = int(it.get("ts") or now)
{i}        except (TypeError, ValueError):
{i}            continue
{i}        if amount <= 0:
{i}            continue
{i}        ts = min(ts, now + 300)
{i}        if db.one("SELECT 1 FROM tx WHERE user_id=? AND amount_minor=? AND kind=? AND abs(ts-?)<=120 LIMIT 1",
{i}                  (user["tg_id"], amount, kind, ts)):
{i}            skipped += 1
{i}            continue
{i}        res = service.add_tx(db, user, kind=kind, amount_minor=amount, merchant=str(it.get("merchant") or "")[:60].strip(),
{i}                             category=(str(it.get("category"))[:40] if it.get("category") else None), source="photo",
{i}                             ts=ts, currency=normalize_currency(it.get("currency"), user["currency"]))
{i}        if res["duplicate"]:
{i}            skipped += 1
{i}            continue
{i}        added += 1
{i}        if app.bot:
{i}            try:
{i}                app.bot.notify_tx(user, res)
{i}            except Exception:
{i}                log.exception("notify failed")
{i}    self._json(200, {{"ok": True, "added": added, "skipped": skipped}})

'''
S = sub1(r'^(\s*)def _app_login\(self\):\n', lambda m: methods(m.group(1)) + m.group(0), S, "_app_login")

JS = r'''let RC = {items: null, busy: false, cats: [], icats: []};
function viewReceipt(app) {
  const box = el("div", {});
  const file = el("input", {type: "file", accept: "image/*", style: "display:none"});
  file.addEventListener("change", () => { const f = file.files && file.files[0]; file.value = ""; if (f) scanReceipt(f, box); });
  app.append(el("div", {class: "card"},
    el("div", {style: "font-weight:600;font-size:17px;margin-bottom:4px", text: "Чеки и скриншоты"}),
    el("div", {class: "muted", style: "margin-bottom:10px", text: "Загрузите фото чека или скриншот перевода — AI найдёт траты и доходы, вы проверите и запишете."}),
    el("button", {text: "📎 Загрузить чек или скриншот", style: "width:100%", onclick: () => file.click()}), file, box));
  drawReceipt(box);
}
function shrinkImage(f) {
  return new Promise((ok, bad) => {
    const url = URL.createObjectURL(f), img = new Image();
    img.onload = () => {
      const k = Math.min(1, 1280 / Math.max(img.width, img.height));
      const c = document.createElement("canvas"); c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
      ok(c.toDataURL("image/jpeg", 0.8));
    };
    img.onerror = () => { URL.revokeObjectURL(url); bad(new Error("Не удалось открыть файл, нужна картинка")); };
    img.src = url;
  });
}
async function scanReceipt(f, box) {
  RC.busy = true; RC.items = null; drawReceipt(box);
  try {
    const image = await shrinkImage(f);
    const r = await (await api("/api/receipt", "POST", {image, mime: "image/jpeg"})).json();
    RC.cats = r.categories || []; RC.icats = r.income_categories || [];
    RC.items = (r.items || []).map(it => ({...it, category: it.category || ""}));
    if (!RC.items.length) toast("Не нашёл операций на картинке");
  } catch (e) { toast(e.message); RC.items = null; }
  RC.busy = false; drawReceipt(box);
}
function drawReceipt(box) {
  if (RC.busy) return box.replaceChildren(el("div", {class: "muted", style: "margin-top:12px", text: "Читаю картинку…"}));
  if (!RC.items || !RC.items.length) return box.replaceChildren();
  const rows = RC.items.map((it, i) => {
    const kindSel = el("select", {}, el("option", {value: "expense", text: "Расход"}), el("option", {value: "income", text: "Доход"}));
    kindSel.value = it.kind; kindSel.onchange = () => { it.kind = kindSel.value; it.category = ""; drawReceipt(box); };
    const amt = el("input", {inputmode: "decimal", value: String(it.amount_minor / 100).replace(".", ",")});
    amt.oninput = () => { const v = parseFloat(amt.value.replace(/\s/g, "").replace(",", ".")); it.amount_minor = isFinite(v) ? Math.round(v * 100) : 0; };
    const mer = el("input", {placeholder: "Где / от кого", value: it.merchant || ""}); mer.oninput = () => { it.merchant = mer.value; };
    const cats = it.kind === "income" ? RC.icats : RC.cats;
    const cat = el("select", {}, el("option", {value: "", text: "Категория — авто"}), cats.map(c => el("option", {value: c, text: c})));
    cat.value = it.category || ""; cat.onchange = () => { it.category = cat.value; };
    return el("div", {class: "card", style: "margin-top:10px"},
      el("div", {style: "display:flex;gap:8px;align-items:center"}, kindSel, amt,
        el("span", {class: "muted", text: it.currency || ""}),
        el("button", {text: "✕", style: "min-height:40px;padding:8px 12px;background:var(--card);color:var(--text)",
          onclick: () => { RC.items.splice(i, 1); drawReceipt(box); }})),
      el("div", {style: "height:8px"}), mer, el("div", {style: "height:8px"}), cat,
      el("div", {class: "muted", style: "margin-top:6px", text: fmtTime(it.ts)}));
  });
  const save = el("button", {text: "Записать: " + RC.items.length, style: "width:100%;margin-top:10px", onclick: () => act(async () => {
    const good = RC.items.filter(it => it.amount_minor > 0);
    if (!good.length) return toast("Нет сумм для записи");
    const r = await (await api("/api/receipt/save", "POST", {items: good})).json();
    toast("Записано: " + r.added + (r.skipped ? ", уже были: " + r.skipped : ""));
    RC.items = null; await load();
  })});
  const cancel = el("button", {text: "Отмена", style: "width:100%;margin-top:8px;background:var(--card);color:var(--text)",
    onclick: () => { RC.items = null; drawReceipt(box); }});
  box.replaceChildren(el("div", {class: "muted", style: "margin-top:12px", text: "Проверьте и поправьте, если нужно:"}), ...rows, save, cancel);
}
'''
W = sub1(r'^function drawChat\(box\) \{\n', lambda m: JS + m.group(0), W, "drawChat")
W = sub1(r'^(\s*)app\.append\(el\("div", \{class: "chips"\}, S\.suggestions\.map\(', lambda m: f'{m.group(1)}viewReceipt(app);\n' + m.group(0), W, "chips")
srv.write_text(S); web.write_text(W)
print("PATCH4 OK")
