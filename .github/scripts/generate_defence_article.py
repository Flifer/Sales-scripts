from pathlib import Path
from xml.sax.saxutils import escape
from datetime import datetime, timezone

OUT = Path("ooxml")
(OUT / "_rels").mkdir(parents=True, exist_ok=True)
(OUT / "docProps").mkdir(parents=True, exist_ok=True)
(OUT / "word" / "_rels").mkdir(parents=True, exist_ok=True)

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NAVY = "18324A"
TEAL = "19877B"
TEAL_LIGHT = "EAF5F3"
BLUE_LIGHT = "EEF4F8"
GRAY_LIGHT = "F3F5F7"
GRAY = "65717E"
ORANGE = "C66A16"
ORANGE_LIGHT = "FFF3E8"
WHITE = "FFFFFF"
BORDER = "D5DDE5"
TEXT = "27313B"


def esc(text):
    return escape(str(text), {'"': '&quot;'})


def r(text, bold=False, italic=False, color=None, size=None, caps=False):
    props = []
    if bold:
        props.append('<w:b/>')
    if italic:
        props.append('<w:i/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if caps:
        props.append('<w:caps/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def p(content="", style=None, align=None, before=0, after=120, line=276,
      keep=False, left=0, right=0, first_line=0, page_break_before=False,
      border_bottom=None, border_top=None, shading=None):
    if isinstance(content, str):
        content = r(content)
    elif isinstance(content, list):
        content = ''.join(content)
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    if before or after or line:
        ppr.append(f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>')
    if left or right or first_line:
        ppr.append(f'<w:ind w:left="{left}" w:right="{right}" w:firstLine="{first_line}"/>')
    if keep:
        ppr.append('<w:keepNext/>')
    if page_break_before:
        ppr.append('<w:pageBreakBefore/>')
    borders = []
    if border_top:
        borders.append(f'<w:top w:val="single" w:sz="8" w:space="4" w:color="{border_top}"/>')
    if border_bottom:
        borders.append(f'<w:bottom w:val="single" w:sz="8" w:space="4" w:color="{border_bottom}"/>')
    if borders:
        ppr.append(f'<w:pBdr>{"".join(borders)}</w:pBdr>')
    if shading:
        ppr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shading}"/>')
    return f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>{content}</w:p>'


def heading(text, level=1, page_break=False):
    style = "Heading1" if level == 1 else "Heading2"
    return p(r(text, bold=True, color=NAVY, size=28 if level == 1 else 24),
             style=style, before=220 if level == 1 else 120, after=100,
             keep=True, page_break_before=page_break)


def body(text, after=110):
    return p(text, style="BodyText", align="both", after=after, line=288)


def body_runs(runs, after=110):
    return p(runs, style="BodyText", align="both", after=after, line=288)


def bullet(text, level=0, bold_lead=None):
    runs = [r("•  ", bold=True, color=TEAL)]
    if bold_lead and text.startswith(bold_lead):
        runs.append(r(bold_lead, bold=True))
        runs.append(r(text[len(bold_lead):]))
    else:
        runs.append(r(text))
    return p(runs, style="BodyText", align="both", left=360 + level * 360, right=60,
             after=70, line=276)


def check_item(text):
    return p([r("✓  ", bold=True, color=TEAL), r(text)], style="BodyText", align="left",
             after=50, line=260)


def cell(paragraphs, width, fill=None, border_color=BORDER, valign="center", margins=100):
    if isinstance(paragraphs, str):
        paragraphs = [p(paragraphs, after=0)]
    tcpr = [f'<w:tcW w:w="{width}" w:type="dxa"/>', f'<w:vAlign w:val="{valign}"/>']
    if fill:
        tcpr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>')
    tcpr.append(
        f'<w:tcMar><w:top w:w="{margins}" w:type="dxa"/><w:left w:w="{margins}" w:type="dxa"/>'
        f'<w:bottom w:w="{margins}" w:type="dxa"/><w:right w:w="{margins}" w:type="dxa"/></w:tcMar>'
    )
    tcpr.append(
        f'<w:tcBorders><w:top w:val="single" w:sz="4" w:color="{border_color}"/>'
        f'<w:left w:val="single" w:sz="4" w:color="{border_color}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:color="{border_color}"/>'
        f'<w:right w:val="single" w:sz="4" w:color="{border_color}"/></w:tcBorders>'
    )
    return f'<w:tc><w:tcPr>{"".join(tcpr)}</w:tcPr>{"".join(paragraphs)}</w:tc>'


def table(rows, widths, after=120, fixed=True):
    total = sum(widths)
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    trs = []
    for row in rows:
        trs.append(f'<w:tr>{"".join(row)}</w:tr>')
    layout = '<w:tblLayout w:type="fixed"/>' if fixed else ''
    return (
        f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/>{layout}'
        f'<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="0" w:type="dxa"/>'
        f'<w:bottom w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar>'
        f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>{"".join(trs)}</w:tbl>'
        + p("", after=after)
    )


def callout(label, paragraphs, kind="teal"):
    if kind == "orange":
        fill, accent, label_color = ORANGE_LIGHT, ORANGE, ORANGE
    elif kind == "gray":
        fill, accent, label_color = GRAY_LIGHT, GRAY, NAVY
    else:
        fill, accent, label_color = TEAL_LIGHT, TEAL, TEAL
    ps = [p(r(label, bold=True, color=label_color, size=22), after=70, keep=True)]
    for item in paragraphs:
        if isinstance(item, list):
            ps.append(p(item, style="BodyText", align="both", after=70, line=276))
        else:
            ps.append(p(item, style="BodyText", align="both", after=70, line=276))
    return table([[cell(ps, 9360, fill=fill, border_color=accent, valign="top", margins=150)]], [9360], after=130)


def step_box(number, title, text):
    num_p = p(r(str(number), bold=True, color=WHITE, size=30), align="center", after=0, line=300)
    text_ps = [p(r(title, bold=True, color=NAVY, size=23), after=40, keep=True),
               p(text, style="BodyText", align="both", after=0, line=276)]
    return table([[cell([num_p], 640, fill=TEAL, border_color=TEAL, margins=80),
                   cell(text_ps, 8720, fill="FFFFFF", border_color=BORDER, valign="top", margins=125)]],
                 [640, 8720], after=90)


def example_box(label, text, kind="teal"):
    fill = TEAL_LIGHT if kind == "teal" else ORANGE_LIGHT
    accent = TEAL if kind == "teal" else ORANGE
    ps = [p(r(label.upper(), bold=True, color=accent, size=21), after=55, keep=True),
          p(text, style="BodyText", align="both", after=0, line=276)]
    return table([[cell(ps, 9360, fill=fill, border_color=accent, valign="top", margins=140)]], [9360], after=110)


def page_break():
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


parts = []

# Title block
parts.append(p(r("НАВЧАЛЬНА СТАТТЯ  |  ОБОРОННІ ЗАКУПІВЛІ", bold=True, color=TEAL, size=19),
               align="left", after=90, border_bottom=BORDER))
parts.append(p(r("ДЛЯ УПОВНОВАЖЕНИХ ОСІБ", bold=True, color=GRAY, size=18, caps=True),
               align="center", before=80, after=80))
parts.append(p([r("Оборонна закупівля військової частини,", bold=True, color=NAVY, size=36),
                r("\n")], style="Title", align="center", after=0))
parts.append(p(r("розташованої на території активних бойових дій", bold=True, color=NAVY, size=36),
               style="Title", align="center", after=100))
parts.append(p(r("Коли можна укласти прямий договір, як підтвердити підставу та що оприлюднювати",
                 italic=True, color=GRAY, size=23), style="Subtitle", align="center", after=240))

parts.append(body("У період дії правового режиму воєнного стану військові частини можуть здійснювати закупівлі безпосередньо на територіях, де тривають активні бойові дії. У такому випадку виникає питання: чи саме місце перебування військової частини дає право укласти прямий договір без використання електронної системи закупівель?"))
parts.append(body("Розташування військової частини на території активних бойових дій не означає, що всі її закупівлі автоматично можуть здійснюватися шляхом укладення прямих договорів. Водночас для оборонної закупівлі, вартість якої дорівнює або перевищує встановлені пороги, така обставина може бути самостійною правовою підставою для придбання без проведення закупівлі в електронній системі."))
parts.append(body("Нижче розглянемо правову основу, умови застосування цієї підстави, порядок дій державного замовника та практичні рекомендації щодо документування закупівлі."))

parts.append(callout("Ключове правило", [
    "Прямий договір можливий, якщо військова частина уповноважена державним замовником, закупівля здійснюється для потреб безпеки і оборони, військова частина перебуває на території активних бойових дій, які не завершені на дату укладення договору, а предмет закупівлі не належить до спеціального режиму, визначеного пунктами 43–49 Особливостей № 1275. Застосування цієї підстави є правом державного замовника, а не його обов’язком."
]))

parts.append(heading("1. Правова підстава для укладення прямого договору"))
parts.append(body("Основним документом, що регулює це питання, є постанова Кабінету Міністрів України від 11.11.2022 № 1275 «Деякі питання здійснення оборонних закупівель на період дії правового режиму воєнного стану» (далі — Особливості № 1275)."))
parts.append(body("Відповідно до підпункту 1 пункту 9 Особливостей № 1275 придбання товарів, послуг і робіт для гарантованого забезпечення потреб безпеки і оборони без проведення закупівлі в електронній системі допускається за наявності однієї з обставин, передбачених пунктом 13 Особливостей № 1178."))
parts.append(body("Для військової частини, яка перебуває на території активних бойових дій, ключовою є підстава, передбачена підпунктом 2 пункту 13 Особливостей № 1178: замовник або його відокремлений підрозділ, що здійснює закупівлю, перебуває на території активних бойових дій, які не були завершені на дату укладення договору про закупівлю."))

parts.append(callout("Правова конструкція", [
    [r("Уповноважена військова частина", bold=True, color=NAVY), r("  +  ", bold=True, color=TEAL),
     r("оборонна потреба", bold=True, color=NAVY), r("  +  ", bold=True, color=TEAL),
     r("активні бойові дії на дату договору", bold=True, color=NAVY), r("  +  ", bold=True, color=TEAL),
     r("належне документування", bold=True, color=NAVY)]
], kind="gray"))

parts.append(body_runs([r("Вартісні межі:", bold=True), r(" до цієї категорії належать закупівлі, вартість яких дорівнює або перевищує:")]))
parts.append(bullet("товари і послуги — 200 тис. грн;"))
parts.append(bullet("роботи — 1,5 млн грн."))
parts.append(body("Якщо вартість закупівлі є нижчою за ці межі, державний замовник діє відповідно до свого внутрішнього порядку. Водночас потребу, ціну та приймання доцільно документувати, а штучний поділ предмета закупівлі не допускається."))

parts.append(callout("Не плутайте режими", [
    "Якщо предметом закупівлі є товари, роботи або послуги оборонного призначення, що становлять державну таємницю, озброєння, військова чи спеціальна техніка, боєприпаси та їх складові частини, послуги з розроблення, ремонту або модернізації такого майна, а також інші предмети, прямо віднесені законодавством до спеціального порядку, застосовуються пункти 43–49 Особливостей № 1275. Підстава «активні бойові дії» не повинна підміняти цей спеціальний режим."
], kind="orange"))

parts.append(page_break())
parts.append(heading("2. Умови, які мають бути виконані одночасно"))

conditions = [
    ("1. Повноваження військової частини", "Має бути рішення державного замовника, яким військову частину уповноважено здійснювати оборонні закупівлі та укладати державні контракти (договори)."),
    ("2. Оборонний характер потреби", "Товар, робота або послуга повинні закуповуватися для гарантованого забезпечення потреб безпеки і оборони та бути включені до затвердженого переліку й обсягів закупівель."),
    ("3. Правильно визначений предмет і поріг закупівлі", "Предмет закупівлі визначається відповідно до Порядку № 708. Очікувана вартість повинна досягати порогів, установлених пунктом 9 Особливостей № 1275. Штучний поділ предмета закупівлі не допускається."),
    ("4. Перебування на території активних бойових дій", "На дату укладення договору відповідна територія повинна бути зазначена саме в розділі територій активних бойових дій чинного Переліку, затвердженого наказом Мінрозвитку від 28.02.2025 № 376, а дата завершення активних бойових дій не повинна настати."),
    ("5. Документована підстава та обґрунтована ціна", "У закупівельній справі повинні бути рішення або протокол, докази перебування військової частини на відповідній території, обґрунтування потреби та очікуваної вартості, матеріали щодо вибору постачальника і перевірки його спроможності.")
]
for title, text in conditions:
    parts.append(p(r(title, bold=True, color=NAVY, size=23), before=80, after=45, keep=True))
    parts.append(body(text, after=105))

parts.append(callout("Практичний висновок", [
    "Підпункт 2 пункту 13 Особливостей № 1178 використовує слово «перебуває», а не лише «зареєстрований». Тому найбезпечніша практика — підтвердити фактичне перебування військової частини або закупівельного підрозділу на відповідній території, а не обмежуватися юридичною адресою."
]))

parts.append(heading("3. Практичний алгоритм дій"))
steps = [
    ("Підтвердьте статус і планування", "Перевірте рішення державного замовника про уповноваження військової частини. Переконайтеся, що потребу включено до переліку та обсягів оборонних закупівель, затверджених відповідно до пункту 6 Особливостей № 1275. Закупівлі, визначені пунктами 8 і 9 Особливостей № 1275, до річного плану закупівель не включаються."),
    ("Визначте предмет закупівлі", "Сформуйте предмет закупівлі відповідно до Порядку № 708, визначте код ДК 021:2015, очікувану вартість та переконайтеся у відсутності штучного поділу. Окремо встановіть, чи не належить предмет до спеціального режиму пунктів 43–49 Особливостей № 1275."),
    ("Перевірте територіальний статус", "На дату майбутнього підписання договору перевірте чинну редакцію Переліку, затвердженого наказом № 376. Збережіть витяг або копію відповідної сторінки із зазначенням території та дат початку і, за наявності, завершення активних бойових дій."),
    ("Зафіксуйте фактичне перебування", "Долучіть до внутрішньої закупівельної справи наказ, довідку, витяг із розпорядчого документа, документ органу військового управління або інший належний доказ. Точну дислокацію, координати та оперативні відомості не оприлюднюйте."),
    ("Обґрунтуйте потребу, ціну та вибір постачальника", "Оформіть службову записку або заявку, розрахунок очікуваної вартості та матеріали перевірки постачальника. За можливості порівняйте декілька цінових джерел. Законодавство не встановлює універсальної обов’язкової кількості комерційних пропозицій, якщо інше не передбачено внутрішніми актами державного замовника."),
    ("Прийміть рішення та укладіть договір", "У рішенні прямо зазначте підпункт 1 пункту 9 Особливостей № 1275 у поєднанні з підпунктом 2 пункту 13 Особливостей № 1178. У договорі детально врегулюйте предмет, строки, вимоги до якості, порядок приймання та оплати, відповідальність, конфіденційність і заборону розкриття чутливої інформації."),
    ("Оприлюдніть звіт", "Якщо закупівля підлягає звітуванню відповідно до статті 30 Закону України «Про оборонні закупівлі» та пункту 10 Особливостей № 1275, оприлюдніть звіт про договір, укладений без використання електронної системи закупівель, протягом 10 робочих днів із дня укладення договору. Не розкривайте інформацію з обмеженим доступом та враховуйте встановлені законодавством винятки.")
]
for i, (title, text) in enumerate(steps, start=1):
    parts.append(step_box(i, title, text))

parts.append(page_break())
parts.append(heading("4. Мінімальний комплект закупівельної справи"))
checklist = [
    "рішення державного замовника про уповноваження військової частини;",
    "затверджений перелік та обсяги закупівель або зміни до них;",
    "службова записка або заявка про потребу та строк її задоволення;",
    "документи щодо визначення предмета закупівлі й очікуваної вартості;",
    "витяг із чинної на дату укладення договору редакції Переліку територій за наказом № 376;",
    "внутрішній документ, що підтверджує фактичне перебування військової частини на відповідній території;",
    "рішення або протокол про застосування прямого договору;",
    "матеріали перевірки ціни та постачальника;",
    "державний контракт (договір), документи про приймання та оплату;",
    "підтвердження оприлюднення звіту — якщо звітування є обов’язковим."
]
rows = []
for i in range(0, len(checklist), 2):
    left = [check_item(checklist[i])]
    right = [check_item(checklist[i + 1])] if i + 1 < len(checklist) else [p("")]
    rows.append([cell(left, 4680, fill="FFFFFF", border_color=BORDER, valign="top", margins=110),
                 cell(right, 4680, fill="FFFFFF", border_color=BORDER, valign="top", margins=110)])
parts.append(table(rows, [4680, 4680], after=140))

parts.append(callout("Правило інформаційної безпеки", [
    "Підстава має бути належно підтверджена, однак документ із точним місцем дислокації не обов’язково оприлюднювати. У публічному звіті зазначайте лише інформацію, оприлюднення якої вимагає законодавство. Оперативні відомості зберігайте у внутрішній справі з відповідним режимом доступу."
], kind="orange"))

parts.append(heading("5. Практичні приклади"))
parts.append(example_box("Приклад 1 — правомірне застосування підстави",
    "Військова частина уповноважена рішенням державного замовника та фактично перебуває у громаді, включеній до територій активних бойових дій без визначеної дати їх завершення. Для ремонту дизель-генераторів необхідно 460 тис. грн. Предмет закупівлі не належить до спеціального режиму пункту 43. Частина може укласти прямий договір на підставі підпункту 1 пункту 9 Особливостей № 1275 у поєднанні з підпунктом 2 пункту 13 Особливостей № 1178, зберігши підтвердні документи та оприлюднивши звіт у встановлений строк."))
parts.append(example_box("Приклад 2 — недостатньо лише місця поставки",
    "Закупівлю проводить підрозділ, який перебуває у безпечному регіоні, а товар лише доставляється до зони активних бойових дій. Саме місце поставки не підтверджує підставу, передбачену підпунктом 2 пункту 13 Особливостей № 1178. У такому разі слід застосувати спосіб закупівлі за пунктом 8 Особливостей № 1275 або іншу належну підставу пункту 9.", kind="orange"))
parts.append(example_box("Приклад 3 — статус території завершено",
    "Потреба виникла 5 серпня, коли громада мала статус території активних бойових дій, але у Переліку зазначено дату завершення таких дій 10 серпня. Договір планують підписати 15 серпня. Підстава не застосовується, оскільки статус території оцінюється саме на дату укладення договору.", kind="orange"))
parts.append(example_box("Приклад 4 — спеціальний предмет закупівлі",
    "Закуповуються боєприпаси або послуги з ремонту озброєння. Навіть якщо військова частина перебуває на території активних бойових дій, закупівля здійснюється за спеціальним режимом пунктів 43–49 Особливостей № 1275, а не за загальною логікою прямого договору, передбаченою пунктом 9.", kind="orange"))

parts.append(heading("6. Типові помилки"))
for item in [
    "посилання лише на юридичну адресу без доказів фактичного перебування;",
    "використання категорії «територія можливих бойових дій» замість території активних бойових дій;",
    "перевірка статусу території на дату виникнення потреби, а не на дату укладення договору;",
    "відсутність у закупівельній справі чинної редакції Переліку за наказом № 376;",
    "відсутність обґрунтування ціни та вибору постачальника;",
    "застосування пункту 9 до предмета закупівлі, який регулюється пунктами 43–49 Особливостей № 1275;",
    "штучний поділ предмета закупівлі;",
    "пропуск 10-денного строку звітування;",
    "розкриття інформації, оприлюднення якої може створити загрозу безпеці."
]:
    parts.append(bullet(item))

parts.append(page_break())
parts.append(heading("7. Зразок формулювання рішення"))
parts.append(callout("Робочий шаблон", [
    "«Встановлено, що військова частина [номер/найменування] уповноважена рішенням [назва державного замовника, реквізити] на здійснення оборонних закупівель та укладення державних контрактів (договорів). Потребу в закупівлі [предмет, код ДК 021:2015] включено до затвердженого переліку та обсягів закупівель. На дату укладення договору військова частина перебуває на території [найменування території], яка відповідно до чинної редакції Переліку, затвердженого наказом № 376, належить до територій активних бойових дій; дата завершення активних бойових дій не визначена/не настала. Керуючись підпунктом 1 пункту 9 Особливостей № 1275 у поєднанні з підпунктом 2 пункту 13 Особливостей № 1178, вирішено здійснити закупівлю без використання електронної системи шляхом укладення прямого державного контракту (договору) з [постачальник] на суму [сума]. Ціну підтверджено [джерела/розрахунок]. Звіт оприлюднити у строк, установлений статтею 30 Закону України «Про оборонні закупівлі», якщо закупівля не належить до встановлених законодавством винятків»."
], kind="gray"))
parts.append(body_runs([r("Примітка. ", bold=True, color=ORANGE), r("У публічній версії рішення не зазначайте координати, точне місце дислокації та інші відомості, розголошення яких може створити загрозу. За необхідності посилайтеся на внутрішній документ із відповідним грифом або режимом доступу.")]))

parts.append(heading("8. Висновок"))
parts.append(body("Військова частина, яка перебуває на території активних бойових дій, може укласти прямий договір не лише за фактом війни або місцем поставки, а за наявності чіткої правової конструкції: належних повноважень, оборонної потреби, актуального статусу території на дату укладення договору, правильно визначеного предмета закупівлі, документованого рішення, обґрунтованої ціни та своєчасного звітування."))
parts.append(body("Якщо хоча б одна з необхідних умов відсутня, безпечніше застосувати конкурентний спосіб закупівлі відповідно до пункту 8 Особливостей № 1275 або іншу належну підставу пункту 9."))

parts.append(heading("Нормативна база", level=2))
for item in [
    "Закон України «Про оборонні закупівлі» № 808-IX — статті 2, 3, 30;",
    "постанова Кабінету Міністрів України від 11.11.2022 № 1275 — пункти 6, 8–10, 43–49;",
    "постанова Кабінету Міністрів України від 12.10.2022 № 1178 — підпункт 2 пункту 13;",
    "наказ Міністерства розвитку громад та територій України від 28.02.2025 № 376 — Перелік територій;",
    "наказ Міністерства розвитку економіки, торгівлі та сільського господарства України від 15.04.2020 № 708 — Порядок визначення предмета закупівлі;",
    "Закон України «Про публічні закупівлі» № 922-VIII — загальні терміни та способи закупівель;",
    "постанова Кабінету Міністрів України від 14.09.2020 № 822 — електронний каталог і запит пропозицій постачальників."
]:
    parts.append(bullet(item))

parts.append(callout("Актуальність", [
    "Матеріал перевірено та відредаговано станом на 05.08.2026. Перелік територій та урядові Особливості змінюються, тому перед кожним рішенням необхідно перевіряти чинну редакцію нормативних актів саме на дату укладення договору."
], kind="gray"))

sect_pr = (
    '<w:sectPr>'
    '<w:headerReference w:type="default" r:id="rId1"/>'
    '<w:footerReference w:type="default" r:id="rId2"/>'
    '<w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="900" w:right="1080" w:bottom="900" w:left="1080" w:header="420" w:footer="420" w:gutter="0"/>'
    '<w:cols w:space="720"/>'
    '<w:docGrid w:linePitch="360"/>'
    '</w:sectPr>'
)

document_xml = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14">'
    '<w:body>' + ''.join(parts) + sect_pr + '</w:body></w:document>'
)

styles_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{NS_W}">
  <w:docDefaults>
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos" w:eastAsia="Aptos" w:cs="Aptos"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:color w:val="{TEXT}"/><w:lang w:val="uk-UA"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="110" w:line="288" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
  <w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="both"/><w:spacing w:after="110" w:line="288" w:lineRule="auto"/></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:jc w:val="center"/><w:spacing w:after="80"/></w:pPr><w:rPr><w:b/><w:color w:val="{NAVY}"/><w:sz w:val="36"/><w:szCs w:val="36"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr><w:rPr><w:i/><w:color w:val="{GRAY}"/><w:sz w:val="23"/><w:szCs w:val="23"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="220" w:after="100"/></w:pPr><w:rPr><w:b/><w:color w:val="{NAVY}"/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="80"/></w:pPr><w:rPr><w:b/><w:color w:val="{NAVY}"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
</w:styles>'''

settings_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{NS_W}"><w:zoom w:percent="100"/><w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/><w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>'''

font_table_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:fonts xmlns:w="{NS_W}"><w:font w:name="Aptos"><w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font><w:font w:name="Calibri"><w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font></w:fonts>'''

header_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="{NS_W}"><w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="5" w:color="{BORDER}"/></w:pBdr><w:spacing w:after="70"/></w:pPr><w:r><w:rPr><w:b/><w:color w:val="{TEAL}"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t>НАВЧАЛЬНА СТАТТЯ  |  ОБОРОННІ ЗАКУПІВЛІ</w:t></w:r></w:p></w:hdr>'''

footer_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="{NS_W}"><w:p><w:pPr><w:pBdr><w:top w:val="single" w:sz="4" w:space="5" w:color="{BORDER}"/></w:pBdr><w:tabs><w:tab w:val="right" w:pos="9360"/></w:tabs><w:spacing w:before="70"/></w:pPr><w:r><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr><w:t>Матеріал перевірено станом на 05.08.2026</w:t></w:r><w:r><w:tab/></w:r><w:r><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr><w:t>Сторінка </w:t></w:r><w:fldSimple w:instr="PAGE"><w:r><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>'''

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/fontTable.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.fontTable+xml"/>
  <Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/fontTable" Target="fontTable.xml"/>
</Relationships>'''

now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
core_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Оборонна закупівля військової частини на території активних бойових дій</dc:title>
  <dc:subject>Оборонні закупівлі</dc:subject>
  <dc:creator>OpenAI</dc:creator>
  <cp:lastModifiedBy>OpenAI</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>'''

app_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop><Company></Company><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion>
</Properties>'''

files = {
    OUT / "[Content_Types].xml": content_types,
    OUT / "_rels" / ".rels": root_rels,
    OUT / "docProps" / "core.xml": core_xml,
    OUT / "docProps" / "app.xml": app_xml,
    OUT / "word" / "document.xml": document_xml,
    OUT / "word" / "styles.xml": styles_xml,
    OUT / "word" / "settings.xml": settings_xml,
    OUT / "word" / "fontTable.xml": font_table_xml,
    OUT / "word" / "header1.xml": header_xml,
    OUT / "word" / "footer1.xml": footer_xml,
    OUT / "word" / "_rels" / "document.xml.rels": doc_rels,
}

for path, data in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")

print(f"Generated {len(files)} OOXML parts in {OUT.resolve()}")
