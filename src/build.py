#!/usr/bin/env python3
"""Static site generator for nashionalinvestments.com.

python3 build.py preview  -> out/preview  (relative links ending in index.html, flags visible, noindex)
python3 build.py prod     -> out/prod     (clean absolute links, indexable)
"""
import html, json, os, re, shutil, sys
from glossary import TERMS

MODE = sys.argv[1] if len(sys.argv) > 1 else "preview"
PREVIEW = MODE == "preview"
STAGING = MODE == "staging"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "..", "out", MODE)
SITE = "https://www.nashionalinvestments.com"
TODAY = "2026-10-13"
FLAGS = []

FIRM = {
    "legal": "Nashional Independent Investment Management LLC",
    "addr1": "5900 S Lake Forest Dr, Suite 300", "city": "McKinney", "state": "TX", "zip": "75070",
    "email": "jeff@nashionalinvestments.com",
    "jeff_email": "jeff@nashionalinvestments.com", "denver_email": "dmcclure@nashionalinvestments.com",
    "iapd_firm": "https://adviserinfo.sec.gov/firm/summary/289955",
    "iapd_jeff": "https://adviserinfo.sec.gov/individual/summary/6031965",
    "iapd_denver": "https://adviserinfo.sec.gov/individual/summary/7319835",
    "privacy_pdf": "https://8fd02778-254e-4c6b-9457-885597ce99f4.filesusr.com/ugd/9e295d_71730603e58a41e0b800faa7c49184c5.pdf",
}

# Contact form: Wix Forms in the free Wix Headless project "Nashional Investments Contact Form".
# The client ID is a public identifier (safe in page source); it only mints anonymous visitor tokens.
WIX_FORM = {
    "client_id": "1c049085-1f93-4d33-9261-7721ec9823ca",
    "form_id": "1ff6b33f-8694-4181-9cda-3b152b5f20fa",
}

def slug(s):
    s = s.lower().replace("&", "and").replace("%", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

PAGES = {
    "home": "", "alternatives": "alternatives/", "dst": "alternatives/1031-exchange-dst/",
    "qoz": "alternatives/opportunity-zones/", "energy": "alternatives/energy/",
    "private": "alternatives/private-markets/", "digital": "alternatives/digital-assets/",
    "tax": "tax-strategies/", "cbp": "tax-strategies/cash-balance-plans/", "charitable": "tax-strategies/charitable-giving/",
    "portfolio": "portfolio-management/",
    "serve": "who-we-serve/", "serve-re": "who-we-serve/real-estate-investors/", "serve-biz": "who-we-serve/business-owners/", "serve-md": "who-we-serve/physicians/",
    "fees": "fees/", "team": "team/", "tools": "tools/",
    "tool-1031": "tools/1031-deadline-calculator/", "tool-boot": "tools/1031-replacement-calculator/",
    "tool-qoz": "tools/opportunity-zone-timing/", "tool-ai": "tools/accredited-investor-check/",
    "glossary": "glossary/", "notfound": "404/", "disclosures": "disclosures/", "insurance": "insurance-planning/", "privacy": "privacy/", "affiliates": "affiliated-companies/", "contact": "contact/",
}
for t, c, d in TERMS:
    PAGES["term:" + slug(t)] = "glossary/" + slug(t) + "/"

CURRENT = {"dir": ""}

def L(key, anchor=""):
    target = PAGES[key]
    a = ("#" + anchor) if anchor else ""
    if PREVIEW:
        rel = os.path.relpath("/" + target, "/" + CURRENT["dir"]) if target != CURRENT["dir"] else "."
        rel = "" if rel == "." else rel + "/"
        return rel + "index.html" + a
    return "/" + target + a

def T(term, text=None):
    return '<a href="%s">%s</a>' % (L("term:" + slug(term)), text or term)

def F(note):
    FLAGS.append((CURRENT["dir"] or "home", note))
    return '<mark class="flag">[%s]</mark>' % html.escape(note) if PREVIEW else ""

def base_prefix():
    if PREVIEW:
        depth = CURRENT["dir"].count("/")
        return "../" * depth
    return "/"

def jsonld(obj):
    return '<script type="application/ld+json">%s</script>' % json.dumps(obj, ensure_ascii=False)

ORG = {
    "@context": "https://schema.org", "@type": "FinancialService", "@id": SITE + "/#firm",
    "name": "Nashional Investments", "legalName": FIRM["legal"],
    "alternateName": ["Nashional Financial", "Nashional Independent Investment Management"],
    "url": SITE, "email": FIRM["email"], "foundingDate": "2017", "logo": SITE + "/assets/img/og-default.png", "image": SITE + "/assets/img/og-default.png",
    "description": "Texas-registered fiduciary investment adviser for accredited investors and high-net-worth families, focused on 1031 exchanges, DSTs, Opportunity Zone funds and tax-driven alternatives.",
    "contactPoint": [{"@type": "ContactPoint", "contactType": "customer service", "name": "Jeff Nash", "email": "jeff@nashionalinvestments.com"},
                     {"@type": "ContactPoint", "contactType": "customer service", "name": "Denver McClure", "email": "dmcclure@nashionalinvestments.com"}],
    "founder": {"@id": SITE + "/team/#jeff-nash"},
    "address": {"@type": "PostalAddress", "streetAddress": FIRM["addr1"], "addressLocality": FIRM["city"],
                "addressRegion": FIRM["state"], "postalCode": FIRM["zip"], "addressCountry": "US"},
    "areaServed": ["Texas", "New Jersey"],
    "knowsAbout": ["1031 exchanges", "Delaware Statutory Trusts", "Qualified Opportunity Zones", "Oil and gas tax strategies",
                   "Private credit", "Digital assets", "Cash balance plans", "Portfolio management"],
    "employee": [{"@id": SITE + "/team/#jeff-nash"}, {"@id": SITE + "/team/#denver-mcclure"}],
    "sameAs": [FIRM["iapd_firm"]],
}

NAV = [("alternatives", "Alternatives"), ("tax", "Tax Strategies"), ("portfolio", "Portfolio"), ("tools", "Tools"), ("glossary", "Glossary"), ("team", "Team")]

def header(active):
    links = "".join('<a href="%s"%s>%s</a>' % (L(k), ' aria-current="page"' if k == active else "", n) for k, n in NAV)
    return f'''<div class="utility"><div class="wrap"><span>Texas-registered investment adviser · Fiduciary</span><span>Services for <a href="{L('term:accredited-investor')}">accredited investors</a> and high-net-worth families</span></div></div>
<header class="site-header"><div class="wrap">
<a class="brand" href="{L('home')}" aria-label="Nashional Investments home"><b>NASHIONAL</b><span>INVESTMENTS</span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="main-nav">Menu</button>
<nav class="nav" id="main-nav" aria-label="Main">{links}<a class="nav-cta" href="{L('contact')}">Book a consultation</a></nav>
<a class="btn sm head-cta" href="{L('contact')}">Book a consultation</a>
</div></header>'''

def footer():
    return f'''<footer class="site-footer"><div class="wrap">
<div class="foot-cols">
<div><a class="brand" href="{L('home')}"><b>NASHIONAL</b><span>INVESTMENTS</span></a><span>{FIRM['addr1'].replace(', ', '<br>')}<br>{FIRM['city']}, {FIRM['state']} {FIRM['zip']}</span><span class="f-contact">Jeff Nash<br><a href="mailto:{FIRM['jeff_email']}">{FIRM['jeff_email']}</a></span><span class="f-contact">Denver McClure<br><a href="mailto:{FIRM['denver_email']}">{FIRM['denver_email']}</a></span></div>
<div><span class="label">Alternatives</span><a href="{L('dst')}">1031 Exchanges and DSTs</a><a href="{L('qoz')}">Opportunity Zones</a><a href="{L('energy')}">Energy</a><a href="{L('private')}">Private Markets</a><a href="{L('digital')}">Digital Assets</a></div>
<div><span class="label">Planning</span><a href="{L('cbp')}">Cash Balance Plans</a><a href="{L('charitable')}">Charitable Giving</a><a href="{L('insurance')}">Insurance Planning</a><a href="{L('portfolio')}">Portfolio Management</a><a href="{L('fees')}">Fees</a></div>
<div><a class="label" href="{L('serve')}" style="text-decoration:none">Who we serve</a><a href="{L('serve-re')}">Real Estate Investors</a><a href="{L('serve-biz')}">Business Owners</a><a href="{L('serve-md')}">Physicians</a></div>
<div><span class="label">Firm</span><a href="{L('team')}">Team</a><a href="{L('tools')}">Tools</a><a href="{L('glossary')}">Glossary</a><a href="{L('affiliates')}">Affiliated Companies</a><a href="{L('disclosures')}">Disclosures</a><a href="{L('privacy')}">Privacy Policy</a><a href="{L('contact')}">Contact</a></div>
</div>
<div class="legal">
<p>Investment advisory services are offered through {FIRM['legal']} ("Nashional Investments"), an investment adviser registered in Texas and New Jersey. Registration does not imply a certain level of skill or training. Firm CRD 289955 · Jeff Nash CRD 6031965 · Denver McClure CRD 7319835. Check our background at <a href="{FIRM['iapd_firm']}">adviserinfo.sec.gov</a>.</p>
<p>Alternative investments, including DSTs, Opportunity Zone funds, energy programs and private funds, are speculative, illiquid and available only to accredited investors. You may lose some or all of your investment. Tax benefits are not guaranteed and depend on your circumstances and current law. Nothing on this site is an offer to sell or a solicitation to buy any security, or tax or legal advice. See our <a href="{L('disclosures')}">disclosures</a> and Form ADV.</p>
<p>We use software tools, including artificial intelligence, to support research and operations. All recommendations are made and reviewed by our advisers. © 2026 {FIRM['legal']}.</p>
</div></div></footer>'''

def crumbs(trail):
    parts = ['<a href="%s">Home</a>' % L("home")]
    for k, n in trail[:-1]:
        parts.append('<a href="%s">%s</a>' % (L(k), n))
    parts.append('<span aria-current="page">%s</span>' % trail[-1][1])
    return '<nav class="crumbs" aria-label="Breadcrumb">' + '<span aria-hidden="true">/</span>'.join(parts) + "</nav>"

def crumbs_ld(trail):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"}]
    for i, (k, n) in enumerate(trail):
        items.append({"@type": "ListItem", "position": i + 2, "name": n, "item": SITE + "/" + PAGES[k]})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}

def page_hero(trail, eyebrow, h1, lede, ctas=True):
    btns = f'<div class="btns"><a class="btn" href="{L("contact")}">Book a consultation</a><a class="btn ghost" href="{L("home", "builder-band")}">Build your strategy</a></div>' if ctas else ""
    return f'''<section class="hero page-hero"><div class="wrap">{crumbs(trail)}<span class="eyebrow">{eyebrow}</span><h1>{h1}</h1><p class="lede">{lede}</p>{btns}<p class="label">Nashional Investments · Updated October 2026</p></div></section>'''

def important(extra=""):
    return band(f'''<div class="note" role="note" aria-label="Important information"><span class="eyebrow">Important information</span><p>{extra}Alternative investments are speculative, illiquid and intended only for accredited investors who can bear the loss of their entire investment. Tax benefits are not guaranteed and depend on your situation and current law. Offerings are made only by the sponsor's private placement memorandum. Nashional Investments is not a broker-dealer and does not sell securities. Consult your tax and legal advisers before investing. <a href="{L('disclosures')}">Read our disclosures</a>.</p></div>''', "tight")

def faq(items):
    blocks = "".join(f'<details><summary>{q}</summary><div class="a">{a}</div></details>' for q, a in items)
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": re.sub("<[^>]+>", "", q), "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in items]}
    return f'<div class="faq">{blocks}</div>', ld

def band(inner, cls=""):
    return f'<section class="band {cls}"><div class="wrap">{inner}</div></section>'

def head_block(eyebrow, h2, lede=""):
    return f'<div class="head"><span class="eyebrow">{eyebrow}</span><h2>{h2}</h2>' + (f'<p class="lede">{lede}</p>' if lede else "") + "</div>"

SELL = ("Talk to us before you sell.", "Tax outcomes are usually best when they are planned months before a closing date. Your first conversation with us is complimentary.")

def cta_band(h="Start with a conversation.", p="Your first conversation with us is complimentary. We will tell you which strategies fit your situation, and which do not."):
    return band(f'<div class="head" style="margin-bottom:0"><h2>{h}</h2><p class="lede">{p}</p><div class="btns"><a class="btn" href="{L("contact")}">Book a consultation</a><a class="btn ghost" href="{L("tools")}">Use our planning tools</a></div></div>')

def risk(text):
    return f'<p class="risk">{text}</p>'

PAGES_OUT = {}

def page(key, title, desc, body, schema=None, active=None):
    path = PAGES[key]
    CURRENT["dir"] = path
    lds = [ORG] if key == "home" else [{"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": SITE + "/" + path,
            "description": desc, "dateModified": TODAY, "publisher": {"@id": SITE + "/#firm"}}]
    lds += schema or []
    robots = '<meta name="robots" content="noindex,nofollow">' if (PREVIEW or STAGING) else '<meta name="robots" content="index,follow,max-snippet:-1">'
    canonical = SITE + "/" + path
    if key == "home":
        full_title = title
    elif len(title) + 24 <= 62:
        full_title = f"{title} | Nashional Investments"
    elif len(title) + 12 <= 62:
        full_title = f"{title} | Nashional"
    else:
        full_title = title
    PAGES_OUT[path] = (full_title, body, desc, lds, robots, canonical, active)

def render_all():
    for path, (full_title, body_fn, desc, lds, robots, canonical, active) in PAGES_OUT.items():
        CURRENT["dir"] = path
        body = body_fn() if callable(body_fn) else body_fn
        doc = f'''<!doctype html>
<html lang="en" data-base="{base_prefix()}" data-links="{'rel' if PREVIEW else 'clean'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(desc)}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="Nashional Investments">
<meta property="og:image" content="{SITE}/assets/img/og-default.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(full_title)}">
<meta name="twitter:description" content="{html.escape(desc)}">
<meta name="twitter:image" content="{SITE}/assets/img/og-default.png">
<meta name="theme-color" content="#090B10">
<link rel="icon" href="{base_prefix()}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Manrope:wght@300;500;600;700&display=swap">
<link rel="stylesheet" href="{base_prefix()}assets/site.css">
{''.join(jsonld(x) for x in lds)}
</head>
<body>
<a href="#main" class="label" style="position:absolute;left:-9999px">Skip to content</a>
{header(active)}
<main id="main">
{body}
</main>
{footer()}
<script src="{base_prefix()}assets/site.js" defer></script>
</body>
</html>
'''
        dest = os.path.join(OUT, path, "index.html")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w") as f:
            f.write(doc)


def art(kind):
    """Original line illustrations, used until photography is ready."""
    import math
    g = []
    if kind == "skyline":
        xs = [(40,150,260),(160,120,330),(255,90,220),(320,140,380),(430,100,290),(500,130,410),(600,90,250),(660,110,340)]
        for x,w,h in xs:
            y = 460-h
            g.append(f'<rect x="{x}" y="{y}" width="{w-10}" height="{h}" />')
            for wy in range(y+18, 450, 22):
                g.append(f'<line x1="{x+10}" y1="{wy}" x2="{x+w-20}" y2="{wy}" opacity="0.35"/>')
        g.append('<line class="ac" x1="0" y1="460" x2="800" y2="460"/>')
    elif kind == "development":
        g.append('<path d="M120 460 V140 H560 V460" />')
        for y in range(160, 460, 40):
            g.append(f'<line x1="120" y1="{y}" x2="560" y2="{y}" opacity="0.5"/>')
        for x in range(160, 560, 55):
            g.append(f'<line x1="{x}" y1="140" x2="{x}" y2="460" opacity="0.5"/>')
        g.append('<path d="M640 460 V70 M600 70 H760 M640 70 L700 110 M700 70 V250" />')
        g.append('<line class="ac" x1="700" y1="250" x2="700" y2="300"/><rect class="ac" x="684" y="300" width="32" height="20"/>')
        g.append('<line x1="0" y1="460" x2="800" y2="460"/>')
    elif kind == "energy":
        for i in range(9):
            y = 330 + i*16
            pts = " ".join(f"{x},{y + 10*math.sin(x/90 + i*0.6):.1f}" for x in range(0, 801, 20))
            g.append(f'<polyline points="{pts}" opacity="{0.25+0.07*i:.2f}"/>')
        g.append('<path d="M330 330 L400 200 L470 330 M360 270 H440 M400 200 L520 160 M520 160 L560 230 M520 160 L300 230" />')
        g.append('<circle class="ac" cx="520" cy="160" r="6"/><circle class="ac" cx="640" cy="110" r="38" opacity="0.6"/>')
    return f'<svg class="art" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" stroke-width="1.4">{"".join(g)}</g></svg>'

def monogram(initials):
    return f'<div class="plate portrait mono" aria-hidden="true"><span>{initials}</span></div>'

# ---------------------------------------------------------------- HOME
def home():
    return f'''
<section class="hero"><canvas id="contours" aria-hidden="true"></canvas><div class="wrap">
<a class="badge" href="{L('term:accredited-investor')}">For accredited investors and high-net-worth families</a>
<h1>Fiduciary advice for DSTs, Opportunity Zones and tax-driven alternatives.</h1>
<p class="lede">A Texas-registered investment adviser led by a CFP® and CPA. Flat, disclosed fees. One coordinated plan for your alternatives and your core portfolio.</p>
<div class="btns"><a class="btn" href="#builder-band">Build your strategy</a><a class="btn ghost" href="{L('contact')}">Book a consultation</a></div>
</div>
<div class="creds"><div class="wrap"><span>Texas-registered investment adviser</span><span>CFP® · CPA · CBDA</span><span>Fiduciary on every recommendation</span><span>McKinney, Texas</span></div></div>
</section>

<section class="band tight paper"><div class="wrap grid two" style="align-items:center">
<div style="display:flex;flex-direction:column;gap:12px"><span class="eyebrow">Who we serve</span><h2 style="font-size:clamp(28px,3vw,42px)">Our alternative strategies are available only to accredited investors.</h2></div>
<div style="display:flex;flex-direction:column;gap:16px"><p class="muted">Most DSTs, Opportunity Zone funds and private offerings are sold only to {T('Accredited Investor', 'accredited investors')} under SEC rules. We work with individuals, families and business owners who meet that standard, and we confirm eligibility in our first conversation.</p>
<div class="btns"><a class="btn sm" href="{L('tool-ai')}">Check if you qualify</a></div></div>
</div></section>

{band(head_block('Where we start', 'Three moments that call for more than a stock portfolio.') + f"""<div class="grid">
<article class="card">{art("skyline")}<div class="body"><span class="eyebrow">Real estate</span><h3>Selling investment property</h3><p>Defer the gain through a {T('1031 Exchange', '1031 exchange')} into a {T('Delaware Statutory Trust')}, and step away from landlord duties.</p><a class="more" href="{L('dst')}">1031 exchanges and DSTs</a></div></article>
<article class="card">{art("development")}<div class="body"><span class="eyebrow">Capital gains</span><h3>Sitting on a large gain</h3><p>Defer the gain from a business or stock sale and exclude future growth through a {T('Qualified Opportunity Fund')}.</p><a class="more" href="{L('qoz')}">Opportunity Zones</a></div></article>
<article class="card">{art("energy")}<div class="body"><span class="eyebrow">Income</span><h3>High income, high tax bill</h3><p>{T('Cash Balance Plan', 'Cash balance plans')}, energy deductions and charitable strategies, coordinated with your CPA.</p><a class="more" href="{L('tax')}">Tax strategies</a></div></article>
</div>""")}

<section class="band" aria-label="1031 exchange deadlines"><div class="wrap numbers">
<div><div class="big">45</div><div class="big-cap">Days to identify</div></div>
<div><div class="big">180</div><div class="big-cap">Days to close</div></div>
<p class="lede">A 1031 exchange runs on a federal clock that starts the day your sale closes. We plan the replacement before you list, so the deadlines do not make the decision for you. <a href="{L('tool-1031')}">Calculate your dates</a>.</p>
</div></section>

<section class="band" id="builder-band"><div class="wrap">
{head_block('Strategy builder', 'Build your strategy in three choices.', 'See which strategies are worth a conversation. Nothing you choose here is stored or sent.')}
{builder()}
</div></section>

<section class="band paper"><div class="wrap numbers">
<div><div class="big" data-qoz-days>80</div><div class="big-cap">Days until the new Opportunity Zone rules</div></div>
<div style="display:flex;flex-direction:column;gap:16px;grid-column:span 2;min-width:0"><h2 style="font-size:clamp(28px,3vw,42px)">Opportunity Zone rules change on January 1, 2027.</h2><p class="muted">Gains invested on or after that date get a five-year rolling deferral and a 10% {T('QOZ Basis Step-Up', 'basis step-up')} (30% in rural funds). Gains invested before it follow the current rules. Which side of the line you land on matters.</p><div class="btns"><a class="btn sm" href="{L('tool-qoz')}">Check your timing</a></div></div>
</div></section>

{band(head_block('Why Nashional', 'Advice that sits on your side of the table.') + f"""<div class="ruled">
<div><h3>Independent of the sponsors we review</h3><p>Our alternative assets fee is a flat amount based on the size of your investment, agreed in writing before work begins. It is the same whichever offering you choose.</p></div>
<div><h3>CPA-led tax analysis</h3><p>Recommendations are reviewed for their tax effect before we make them, because your after-tax return is what you keep.</p></div>
<div><h3>One coordinated plan</h3><p>Your alternatives and your core portfolio are managed together, so nothing is decided in isolation.</p></div>
</div>""")}

{band(head_block('The team', 'Two advisers. One plan.') + team_cards(short=True))}

<section class="band paper"><div class="wrap grid two">
<div style="display:flex;flex-direction:column;gap:18px"><span class="eyebrow">Glossary</span><h2 style="font-size:clamp(28px,3.2vw,44px)">Plain-English definitions from our advisers.</h2><p class="muted">{len(TERMS)} terms covering 1031 exchanges, Opportunity Zones, energy, private markets, tax and digital assets.</p><div class="chips">{''.join(T(t) for t in ['Accredited Investor','Delaware Statutory Trust','Boot','Qualified Opportunity Fund','10-Year Exclusion','Intangible Drilling Costs','Qualified Purchaser','Depreciation Recapture'])}</div><p><a href="{L('glossary')}">Browse all terms</a></p></div>
{accredited_card()}
</div></section>

{band(head_block("Questions", "About Nashional Investments.") + HOME_FAQ[0])}

{cta_band(*SELL)}
'''

HOME_FAQ = faq([
    ("What is Nashional Investments?", "Nashional Investments is a fiduciary investment adviser based in McKinney, Texas, registered with the Texas State Securities Board and in New Jersey. Its legal name is Nashional Independent Investment Management LLC. The firm advises accredited investors and high-net-worth families on 1031 exchanges, DSTs, Opportunity Zone funds and other tax-driven alternatives, alongside portfolio management."),
    ("Is Nashional Investments a fiduciary?", "Yes. As a registered investment adviser, Nashional owes clients a fiduciary duty of care and loyalty, which means advice in the client's best interest and disclosure of conflicts of interest."),
    ("Who do you work with?", "Our alternative strategies are available only to accredited investors. We work with high-net-worth individuals and families, business owners, real estate investors and physicians."),
    ("How are you paid?", "Portfolio management is billed as a percentage of assets. Alternative assets are billed as a one-time flat fee based on the size of the investment, under a written agreement. We do not charge advisory fees for insurance recommendations."),
    ("Who leads the firm?", "Jeff Nash, CFP®, CPA, founded the firm in 2017 and serves as President and Chief Investment Officer. Denver McClure, CBDA, a Marine Corps veteran and real estate investor, is a Partner and leads the alternatives practice."),
    ("How do I get started?", "Email Jeff Nash at jeff@nashionalinvestments.com or Denver McClure at dmcclure@nashionalinvestments.com, or use the contact form. The first conversation is complimentary."),
])

def builder():
    def choices(key, opts):
        return "".join(f'<button type="button" class="choice" data-key="{key}" data-val="{v}" aria-pressed="false">{l}{("<small>" + h + "</small>") if h else ""}</button>' for v, l, h in opts)
    return f'''<div class="builder" id="builder">
<div class="steps">
<fieldset><legend class="legend">1 · What is happening</legend><div class="choices pair">{choices('source', [('re','Selling investment real estate','Rental, commercial or land'),('biz','Selling a business','Full or partial sale'),('sec','A large stock or crypto gain','Concentrated or appreciated positions'),('inc','High income, high tax bill','Owners and professionals')])}</div></fieldset>
<fieldset><legend class="legend">2 · Timing</legend><div class="choices">{choices('timing', [('now','Closing within 6 months, or already closed',''),('plan','Planning a year or more ahead','')])}</div></fieldset>
<fieldset><legend class="legend">3 · Do you meet the <a href="{L('term:accredited-investor')}">accredited investor</a> definition?</legend><div class="choices">{choices('accred', [('yes','Yes',''),('no','No',''),('unsure','Not sure','')])}</div></fieldset>
</div>
<aside aria-live="polite" aria-label="Strategies to discuss">
<span class="eyebrow">Strategies to discuss</span>
<p class="warn" id="builder-notice" hidden></p>
<div id="builder-results"></div>
<p class="muted" id="builder-clock" hidden style="font-size:14.5px"></p>
<a class="btn" href="{L('contact')}">Discuss these with an adviser</a>
<p class="risk" style="font-size:12.5px">Educational only. Not a recommendation or an offer of any security. Suitability is determined in a consultation.</p>
</aside></div>'''

def accredited_card():
    return f'''<article class="note" style="padding:clamp(24px,3vw,40px);gap:16px" aria-labelledby="ai-card-h">
<span class="eyebrow">Definition · Private markets</span>
<h3 id="ai-card-h" style="font-size:30px">Accredited Investor</h3>
<p>An individual the SEC allows to invest in private offerings such as DSTs, Opportunity Zone funds and private credit. Under Rule 501 of {T('Regulation D')}, you generally qualify if you meet one of these:</p>
<ul style="margin:0;padding-left:20px;display:flex;flex-direction:column;gap:8px">
<li>Income above $200,000 ($300,000 with a spouse or partner) in each of the last two years, with the same expected this year.</li>
<li>Net worth above $1 million, alone or with a spouse or partner, not counting your primary home.</li>
<li>A Series 7, Series 65 or Series 82 license in good standing.</li>
</ul>
<p style="font-size:14px">The sponsor of each offering verifies status before you invest.</p>
<div class="btns"><a class="btn sm" href="{L('tool-ai')}">Check your eligibility</a><a class="btn sm ghost" href="{L('term:accredited-investor')}">Full definition</a></div>
</article>'''

def team_cards(short=False):
    people = [
        {"id": "jeff-nash", "name": "Jeff Nash, CFP®, CPA", "role": "Founder · President and Chief Investment Officer", "mono": "JN", "photo": "assets/img/jeff-nash.webp", "crd": "CRD 6031965", "iapd": FIRM["iapd_jeff"],
         "short": "Jeff founded Nashional in 2017. A CFP® professional and CPA with more than 20 years in tax planning, retirement planning and investment management, he models the tax effect of every recommendation before it is made.",
         "long": ["Jeff Nash founded Nashional Investments in 2017 and serves as its President and Chief Investment Officer. He is a CERTIFIED FINANCIAL PLANNER® professional and a Certified Public Accountant with more than 20 years of experience in tax planning, financial advising, retirement planning and investment management.",
                  "Jeff oversees the firm's investment strategy across alternative and traditional portfolios, from DSTs, Opportunity Zone funds, private markets and structured notes to stocks, bonds and ETFs. His Master of Taxation shapes how the firm works: every recommendation is weighed for its after-tax result, not just its headline return.",
                  "Jeff is also a founding partner of Nashional Tax Planning and a co-founder of Fiduciary Financing. He is based in McKinney, Texas."],
         "creds": ["CERTIFIED FINANCIAL PLANNER®", "Certified Public Accountant, Texas", "Investment Adviser Representative, Series 65 and Series 66", "General Lines Agent, life insurance and annuities"],
         "edu": ["Master of Taxation, Mississippi State University", "BA, Political Science, University of Oklahoma"]},
        {"id": "denver-mcclure", "name": "Denver McClure, CBDA", "role": "Partner", "mono": "DM", "photo": "assets/img/denver-mcclure.webp", "crd": "CRD 7319835", "iapd": FIRM["iapd_denver"],
         "short": "Denver leads the firm's real estate and alternatives practice. A Marine Corps veteran and active DFW real estate investor, he brings an owner's perspective to every 1031 exchange, DST and Opportunity Zone decision.",
         "long": ["Denver McClure is a Partner at Nashional Investments, where he leads the firm's real estate and alternative investment practice, including 1031 exchanges, DSTs, Opportunity Zone funds and digital assets. He is a United States Marine Corps veteran and an Investment Adviser Representative.",
                  "Denver owns multiple investment properties across Dallas-Fort Worth and has worked through acquisitions, refinances, renovations and long-term holds as an owner himself. When a client is deciding whether to sell, exchange or hold, he has been on that side of the table.",
                  "He holds the Certified in Blockchain and Digital Assets (CBDA) designation from the Digital Assets Council of Financial Professionals and leads the firm's digital asset advice. Denver co-founded Fiduciary Financing with Jeff Nash and is Managing Partner of Christian Brothers Roofing, a veteran-owned exterior contractor serving Dallas-Fort Worth since 1983. He is based in Lewisville, Texas."],
         "creds": ["Investment Adviser Representative, Series 65", "Certified in Blockchain and Digital Assets (CBDA), DACFP", "General Lines Agent, life insurance and annuities"],
         "edu": ["BBA, Management, Midwestern State University"]},
    ]
    out = '<div class="grid two">' if short else '<div style="display:flex;flex-direction:column;gap:clamp(56px,7vw,96px)">'
    for p in people:
        if short:
            body = f'<p class="muted" style="margin-top:8px">{p["short"]}</p>'
        else:
            paras = "".join(f'<p class="muted">{x}</p>' for x in p["long"])
            creds = "".join(f"<li>{x}</li>" for x in p["creds"])
            edu = "".join(f"<li>{x}</li>" for x in p["edu"])
            body = f'''<div class="prose" style="margin-top:12px">{paras}</div>
<div class="grid two" style="margin-top:20px;gap:24px"><div><span class="label">Licenses and designations</span><ul class="plain">{creds}</ul></div><div><span class="label">Education</span><ul class="plain">{edu}</ul></div></div>'''
        pic = f'<img class="headshot" src="{base_prefix()}{p["photo"]}" alt="{p["name"].split(",")[0]}, {p["role"].split(" · ")[-1]}, Nashional Investments" width="800" height="1000" loading="lazy">' if p.get("photo") else monogram(p['mono'])
        out += f'''<article class="person" id="{p['id']}">{pic}<div class="meta"><h3>{p['name']}</h3><span class="label">{p['role']}</span>{body}<a href="{p['iapd']}" style="font-size:14px;margin-top:10px">{p['crd']} · View on IAPD</a></div></article>'''
    return out + "</div>" + ("" if not short else f'<p style="margin-top:32px"><a href="{L("team")}">Meet the team</a></p>')

# ---------------------------------------------------------------- ALTERNATIVES HUB
def alternatives():
    tiles = [
        ("dst", "1031 Exchanges and DSTs", "Defer gains on investment property by exchanging into professionally managed real estate."),
        ("qoz", "Qualified Opportunity Zones", "Defer gains from almost any source and exclude growth after 10 years."),
        ("energy", "Energy", "Oil and gas working interests with deductions that can offset active income."),
        ("private", "Private Markets", "Private credit, private equity and interval funds for qualified investors."),
        ("digital", "Digital Assets", "Advice on how Bitcoin and other digital assets fit within a diversified portfolio."),
        ("tax", "Tax Strategies", "Cash balance plans and charitable structures that work alongside your alternatives."),
    ]
    cards = "".join(f'<article class="card"><div class="body"><h3>{n}</h3><p>{d}</p><a class="more" href="{L(k)}">Learn more</a></div></article>' for k, n, d in tiles)
    return (page_hero([("alternatives", "Alternatives")], "Alternatives", "Alternative investments, chosen as a fiduciary.",
                      "We review DSTs, Opportunity Zone funds, energy programs and private funds on your behalf, then coordinate them with your core portfolio and your tax picture.")
            + band(f'<div class="grid">{cards}</div>')
            + band(head_block("Compare", "How the main strategies differ.") + f'''<div class="table-box"><table class="wide">
<thead><tr><th scope="col">Strategy</th><th scope="col">Best suited to</th><th scope="col">Tax treatment</th><th scope="col">Typical hold</th><th scope="col">Liquidity</th></tr></thead>
<tbody>
<tr><td><a href="{L('dst')}">1031 exchange into a DST</a></td><td>Selling investment real estate</td><td>Defers capital gains and depreciation recapture</td><td>5 to 10 years</td><td>Very limited</td></tr>
<tr><td><a href="{L('qoz')}">Qualified Opportunity Fund</a></td><td>Any capital gain: stock, business, real estate, crypto</td><td>Defers the gain; growth can be excluded after 10 years</td><td>10 years or more</td><td>Very limited</td></tr>
<tr><td><a href="{L('energy')}">Energy working interest</a></td><td>High active income</td><td>Large first-year deductions through intangible drilling costs</td><td>Life of the wells</td><td>Very limited</td></tr>
<tr><td><a href="{L('private')}">Private credit and equity</a></td><td>Income or growth beyond public markets</td><td>Generally taxed as ordinary income or capital gains</td><td>3 to 10 years</td><td>Limited to periodic or none</td></tr>
</tbody></table></div>''')
            + band(head_block("Before you invest", "What every alternative has in common.") + f'''<div class="ruled">
<div><h3>Accredited investors only</h3><p>Most of these offerings are sold under {T('Regulation D')} and are limited to {T('Accredited Investor', 'accredited investors')}.</p></div>
<div><h3>Illiquid for years</h3><p>Expect to hold for 5 to 10 years or more, with no public market to sell into.</p></div>
<div><h3>Costs inside the price</h3><p>Offering costs and sponsor fees are built into what you pay. We read every {T('Private Placement Memorandum', 'offering memorandum')} for them.</p></div>
</div>''', "paper")
            + important()
            + cta_band())

# ---------------------------------------------------------------- DST
def dst():
    fq, ld = faq([
        ("Can I do a 1031 exchange into a DST without a broker?", "DST interests are securities, so they are purchased through a broker-dealer that is on the sponsor's selling agreement. A fiduciary adviser can review offerings, compare them and coordinate the exchange, so your choice is not driven by who pays the commission."),
        ("What does a DST cost?", "Costs vary by offering. Selling commissions, offering and organization costs, and acquisition fees are disclosed in the private placement memorandum and are usually built into the price per unit. Ongoing asset management fees are paid from property income. We compare these line by line."),
        ("What happens when the DST sells the property?", "When the sponsor sells, you receive your share of the proceeds. You can take the cash and pay tax, or start a new 1031 exchange into another property or DST, subject to the same deadlines."),
        ("Can I exchange out of a DST early?", "Usually not. DSTs are illiquid and generally have no redemption feature. Plan on holding until the sponsor sells, which is often 5 to 10 years."),
        ("What if my sale has more debt than the DST?", "To defer fully you need to replace both value and debt. Many DSTs carry leverage that helps you meet the debt requirement, and debt-free DSTs can be paired with leveraged ones. Our replacement calculator shows the math."),
    ])
    body = (page_hero([("alternatives", "Alternatives"), ("dst", "1031 Exchanges and DSTs")], "1031 exchanges and DSTs", "DST 1031 exchange advice from a fiduciary.",
                      f"A {T('Delaware Statutory Trust')} lets you complete a 1031 exchange by buying a fractional interest in professionally managed real estate instead of a whole property. The IRS treats DST interests as like-kind real property under {T('Revenue Ruling 2004-86')}. We help accredited investors compare DST offerings and plan the exchange around your goals.")
            + band(f'''<div class="grid two"><div class="prose">
<h2>How a 1031 exchange works</h2>
<p>You sell investment or business real property and reinvest the proceeds in {T('Like-Kind Property', 'like-kind property')}. A {T('Qualified Intermediary', 'qualified intermediary')} holds the money in between so you never receive it. If you follow the rules, capital gains and {T('Depreciation Recapture', 'depreciation recapture')} taxes are deferred.</p>
<ul><li><strong>45 days</strong> after closing to identify replacements in writing, using the {T('Three-Property Rule', 'three-property rule')}, the {T('200% Rule', '200% rule')} or the {T('95% Rule', '95% rule')}.</li>
<li><strong>180 days</strong> after closing to acquire them, or your tax return due date if that comes first, unless you file an extension.</li>
<li><strong>Replace value and debt.</strong> Buy at least as much as you sold, reinvest all of your equity, and carry equal or greater debt. Anything short is {T('Boot', 'boot')}.</li></ul>
</div>
<div class="prose"><h2>Why investors choose DSTs</h2>
<ul><li><strong>No landlord duties.</strong> The sponsor manages the property. You receive distributions.</li>
<li><strong>Closes on the exchange timeline.</strong> DSTs are pre-packaged, which helps when the 45-day window is short.</li>
<li><strong>Diversification.</strong> Smaller minimums let you spread one sale across several properties and regions.</li>
<li><strong>Backup identification.</strong> A DST can sit on your identification list as a fallback if a direct purchase falls through.</li></ul>
<p class="risk">Trade-offs: DSTs are illiquid for years, you have no control over the property, returns depend on the sponsor and tenants, offering costs are built into the price, and the trust's {T('DST Operating Restrictions', 'operating restrictions')} limit how it can respond to problems.</p></div></div>''')
            + band(head_block("How we evaluate a DST", "Six things we review before any recommendation.") + '''<div class="ruled">
<div><h3>The sponsor</h3><p>Track record through full cycles, including how past programs ended.</p></div>
<div><h3>The tenant and lease</h3><p>Credit quality, lease term remaining and rent escalations.</p></div>
<div><h3>The debt</h3><p>Loan-to-value, rate, maturity and what happens if the loan comes due early.</p></div>
<div><h3>The costs</h3><p>Every load and fee in the offering memorandum, translated into what it costs you.</p></div>
<div><h3>The exit</h3><p>Expected hold period and the sponsor's realistic path to a sale.</p></div>
<div><h3>Your whole picture</h3><p>How the DST fits your income needs, estate plan and other holdings.</p></div>
</div>''', "paper")
            + band(f'''<div class="grid two"><div class="prose"><h2>How our fee works</h2><p>DST work falls under our Alternative Assets Services and Fees Agreement: a one-time flat fee based on the total amount you invest. It covers due diligence, research, meetings and closing support, and it is agreed in writing before your 45-day identification period begins. We share the agreement with you up front.</p><p><a href="{L('fees')}">See all fees</a></p></div>
<div class="note"><span class="eyebrow">Tools</span><p><a href="{L('tool-1031')}">1031 deadline calculator</a>: your 45-day and 180-day dates from a closing date.</p><p><a href="{L('tool-boot')}">1031 replacement calculator</a>: the value, equity and debt you need to replace.</p></div></div>''')
            + important()
            + band(head_block("Questions", "Common questions about DSTs.") + fq)
            + cta_band(*SELL))
    return body, [ld]

# ---------------------------------------------------------------- QOZ
def qoz():
    fq, ld = faq([
        ("Should I invest before 2027 or wait?", "It depends on when your gain occurred. Under the current rules, deferred gain is recognized by December 31, 2026, so investing now mainly preserves the 10-year exclusion. Gains whose 180-day window reaches into 2027 may be better invested on or after January 1, 2027, under the new rules. Our timing tool shows which applies to you."),
        ("Can I use crypto gains?", "Yes. Opportunity Zone deferral applies to capital gains generally, including gains on stock, a business and digital assets. The gain, not the original investment, is what gets reinvested."),
        ("What happens if I sell before 10 years?", "You lose the exclusion on the fund's growth. The deferred gain becomes taxable when you sell, if it has not been recognized already."),
        ("How is this different from a 1031 exchange?", "A 1031 exchange works only for real property and requires reinvesting the full proceeds. An Opportunity Zone investment works for almost any capital gain and requires reinvesting only the gain."),
    ])
    body = (page_hero([("alternatives", "Alternatives"), ("qoz", "Opportunity Zones")], "Qualified Opportunity Zones", "Opportunity Zone investing under the 2026 and 2027 rules.",
                      f"A {T('Qualified Opportunity Fund')} lets you defer a capital gain by reinvesting it within 180 days, and gain on the fund itself can be excluded after a 10-year hold. The One Big Beautiful Bill Act made the program permanent in July 2025 and changes the rules for money invested on or after January 1, 2027.")
            + band(head_block("Two rule sets", "Which rules apply depends on when you invest.") + '''<div class="table-box"><table>
<thead><tr><th scope="col"></th><th scope="col">Invested through 12/31/2026</th><th scope="col">Invested on or after 1/1/2027</th></tr></thead>
<tbody>
<tr><td>Deferral ends</td><td>December 31, 2026</td><td>Earlier of a sale or 5 years after investing</td></tr>
<tr><td>Basis step-up</td><td>None for new investments</td><td>10% after 5 years (30% for rural funds)</td></tr>
<tr><td>10-year exclusion</td><td>Yes</td><td>Yes, capped at fair market value on the 30th anniversary</td></tr>
<tr><td>Zone map</td><td>Current zones</td><td>New state designations from July 1, 2026; current zones keep status through 2028</td></tr>
</tbody></table></div>
<p class="risk" style="margin-top:16px">Source: Greenberg Traurig summary of the One Big Beautiful Bill Act, July 2025. Rules summarized as of October 2026 and may change.</p>''', "paper")
            + band(f'''<div class="grid two"><div class="prose"><h2>Who it fits</h2><p>Anyone with a capital gain from stock, a business sale, real estate or {T('Digital Asset', 'digital assets')}, who can commit the gain for 10 years or more. The {T('180-Day Investment Period', '180-day investment period')} generally starts on the sale date, with alternative start dates for gains reported on a K-1.</p>
<h2 style="margin-top:20px">Risks</h2><p>Funds are illiquid for 10 years or more, carry development and leasing risk, depend on the sponsor meeting the {T('Substantial Improvement Test', 'substantial improvement test')}, and face rule changes and new reporting requirements.</p></div>
<div class="numbers" style="grid-template-columns:1fr"><div><div class="big" data-qoz-days>80</div><div class="big-cap">Days until the new rules take effect</div></div><div class="btns"><a class="btn" href="{L('tool-qoz')}">Check your timing</a></div></div></div>''')
            + important()
            + band(head_block("Questions", "Common questions about Opportunity Zones.") + fq)
            + cta_band("Talk to us before your 180 days run out.", "A gain can only be reinvested inside its window. A short conversation now keeps your options open."))
    return body, [ld]

# ---------------------------------------------------------------- ENERGY
def energy():
    fq, ld = faq([
        ("Can energy deductions offset my salary or business income?", f"Losses from a {T('Working Interest', 'working interest')} held directly, not through an entity that limits your liability, are generally treated as non-passive and can offset active income. Your CPA can confirm how this applies to you."),
        ("What happens if a well is dry?", "You can lose some or all of the money invested in that well. Programs spread capital across several wells to reduce, not remove, that risk."),
    ])
    body = (page_hero([("alternatives", "Alternatives"), ("energy", "Energy")], "Energy", "Oil and gas strategies for high-income investors.",
                      f"Direct participation in oil and gas drilling can produce large first-year deductions through {T('Intangible Drilling Costs', 'intangible drilling costs')}, along with income from production. It also carries real drilling and commodity risk.")
            + band(f'''<div class="ruled">
<div><h3>{T('Intangible Drilling Costs')}</h3><p>Labor, chemicals and other non-salvageable costs, generally deductible in the year incurred.</p></div>
<div><h3>{T('Tangible Drilling Costs')}</h3><p>Equipment costs, recovered through depreciation over several years.</p></div>
<div><h3>{T('Percentage Depletion')}</h3><p>A deduction on a portion of production income for eligible small producers and royalty owners.</p></div>
</div>''')
            + band(f'<div class="prose"><h2>What we look at</h2><p>Operator experience, drilling locations, how capital is spread across wells, costs and the operator\'s carried interest, and how the deduction fits your tax year. We coordinate timing with your CPA so the deduction lands when it helps most.</p>{risk("Energy programs are speculative, illiquid and available only to accredited investors. Production and prices can fall, wells can be dry, and you can lose your entire investment. Tax benefits depend on your circumstances and current law.")}</div>', "paper")
            + important()
            + band(head_block("Questions", "Common questions about energy investing.") + fq)
            + cta_band())
    return body, [ld]

# ---------------------------------------------------------------- PRIVATE MARKETS
def private():
    fq, ld = faq([
        ("What is the difference between private credit and private equity?", "Private credit funds lend money to private companies and earn interest. Private equity funds buy ownership stakes and aim to sell them later at a gain. Credit is usually held for income, equity for growth."),
        ("How long is my money tied up?", "Traditional private funds often lock up capital for 5 to 10 years. Interval funds and some evergreen funds offer periodic repurchases, usually quarterly and limited to a set percentage of the fund."),
        ("Who can invest in private funds?", "Most private funds are limited to accredited investors. Some require qualified purchaser status, which starts at $5 million in investments."),
    ])
    body = (page_hero([("alternatives", "Alternatives"), ("private", "Private Markets")], "Private markets", "Private credit and private equity, reviewed for you.",
                      f"Private markets can add income or growth that public markets do not offer, in exchange for lockups, valuation lag and layered fees. We review funds for {T('Accredited Investor', 'accredited investors')} and {T('Qualified Purchaser', 'qualified purchasers')} and size them to your liquidity needs.")
            + band(f'''<div class="grid">
<article class="card"><div class="body"><h3>{T('Private Credit')}</h3><p>Loans to private companies, often floating rate, held for income.</p></div></article>
<article class="card"><div class="body"><h3>{T('Private Equity')}</h3><p>Ownership in private companies, held for growth over several years.</p></div></article>
<article class="card"><div class="body"><h3>{T('Interval Fund', 'Interval funds')}</h3><p>Periodic liquidity with lower minimums than traditional private funds.</p></div></article>
<article class="card"><div class="body"><h3>{T('Structured Note', 'Structured notes')}</h3><p>Bank-issued notes with returns linked to an index, where any protection depends on the issuer.</p></div></article>
</div>''')
            + band(f'<div class="prose"><h2>What we weigh</h2><p>How long your money is committed, how often the fund is valued, every layer of fees, how {T("Capital Call", "capital calls")} affect your cash, and whether the extra expected return is worth the {T("Illiquidity Premium", "loss of liquidity")}.</p>{risk("Private investments are illiquid, may be difficult to value, and can lose some or all of their value. They are available only to investors who meet eligibility standards.")}</div>', "paper")
            + important()
            + band(head_block("Questions", "Common questions about private markets.") + fq)
            + cta_band())
    return body, [ld]

# ---------------------------------------------------------------- DIGITAL ASSETS
def digital():
    fq, ld = faq([
        ("Does Nashional manage Bitcoin directly?", "We advise on how digital assets fit within your overall plan, including allocation, custody options and taxes. How and where the assets are held depends on the option you choose, such as a qualified custodian or an exchange-traded product."),
        ("How are digital assets taxed?", "The IRS treats digital assets as property. Selling, exchanging or spending them can create a capital gain or loss, and holding period determines whether the gain is short- or long-term."),
        ("Can a large crypto gain go into an Opportunity Zone fund?", "Yes. A capital gain from selling digital assets can generally be reinvested in a Qualified Opportunity Fund within 180 days to defer it."),
    ])
    body = (page_hero([("alternatives", "Alternatives"), ("digital", "Digital Assets")], "Digital assets", "Digital asset advice as part of a complete plan.",
                      f"We advise clients on how Bitcoin and other digital assets fit within a diversified portfolio, including allocation, custody options, tax treatment and risk. Denver McClure holds the {T('CBDA')} designation from the Digital Assets Council of Financial Professionals.")
            + band(f'''<div class="ruled">
<div><h3>Allocation</h3><p>How much, if any, belongs in your portfolio given your goals and the rest of your holdings.</p></div>
<div><h3>{T('Digital Asset Custody', 'Custody')}</h3><p>Self-custody, exchanges, qualified custodians and {T('Spot Bitcoin ETP', 'exchange-traded products')}, and the trade-offs of each.</p></div>
<div><h3>Taxes</h3><p>Cost basis, gains planning and how a large gain can feed an Opportunity Zone or charitable strategy.</p></div>
</div>''')
            + band(f'<div class="prose">{risk("Digital assets are highly volatile, may lose all of their value, and are not insured by the FDIC or SIPC. Regulation is evolving. Past performance does not guarantee future results.")}</div>', "paper tight")
            + band(head_block("Questions", "Common questions about digital assets.") + fq)
            + cta_band("Have a large digital asset gain?", "We can show how it fits your plan and what your options are before you sell."))
    return body, [ld]

# ---------------------------------------------------------------- TAX
def tax():
    body = (page_hero([("tax", "Tax Strategies")], "Tax strategies", "Strategies designed to help you keep more of what you earn.",
                      "Our founder is a CPA. Tax analysis is part of every recommendation we make, and these strategies often work alongside your alternatives.")
            + band(f'''<div class="grid">
<article class="card"><div class="body"><h3>Cash balance plans</h3><p>Deductible contributions far above 401(k) limits for owners and partners.</p><a class="more" href="{L('cbp')}">Learn more</a></div></article>
<article class="card"><div class="body"><h3>Charitable giving</h3><p>Donor-advised funds and charitable remainder trusts for appreciated assets.</p><a class="more" href="{L('charitable')}">Learn more</a></div></article>
<article class="card"><div class="body"><h3>Energy deductions</h3><p>Intangible drilling costs that can offset active income.</p><a class="more" href="{L('energy')}">Learn more</a></div></article>
<article class="card"><div class="body"><h3>Gain deferral</h3><p>1031 exchanges and Opportunity Zone funds for real estate, business and stock gains.</p><a class="more" href="{L('alternatives')}">Learn more</a></div></article>
<article class="card" id="hsa"><div class="body"><h3>Health savings accounts</h3><p>With an HSA-eligible health plan, a {T('Health Savings Account', 'health savings account')} offers a deduction going in, tax-free growth and tax-free withdrawals for qualified medical costs. Invested for the long term, it can work as an extra retirement account.</p></div></article>
<article class="card"><div class="body"><h3>Insurance planning</h3><p>Cash value life insurance and business coverage, offered through our separate affiliate, Nashional Insurance.</p><a class="more" href="{L('insurance')}">Learn more</a></div></article>
</div>''')
            + band(f'<div class="prose"><p>Tax preparation and stand-alone tax planning are provided by our affiliate, Nashional Tax Planning. <a href="{L("affiliates")}">About our affiliated companies</a>.</p></div>', "paper tight")
            + cta_band())
    return body, []

def cbp():
    fq, ld = faq([
        ("How much can I contribute?", "Limits depend mainly on age and income, and rise sharply after 50. An actuary sets the exact figure each year. For many owners in their 50s and 60s, combined contributions can reach several times the 401(k) limit."),
        ("Do I have to cover employees?", "Yes, a cash balance plan must meet nondiscrimination rules, which usually means some contribution for eligible employees. Plans are often paired with a 401(k) profit-sharing plan to manage that cost."),
        ("Can I stop contributing?", "These plans are meant to run for several years. You can amend or terminate a plan, but frequent changes can raise questions with the IRS."),
    ])
    body = (page_hero([("tax", "Tax Strategies"), ("cbp", "Cash Balance Plans")], "Cash balance plans", "Cash balance plans for business owners and partners.",
                      f"A {T('Cash Balance Plan', 'cash balance plan')} is a qualified retirement plan that can sit beside your 401(k) and allow far larger deductible contributions, especially for owners over 50.")
            + band('''<div class="grid two"><div class="prose"><h2>How it works</h2><p>Each participant has an account that grows by an employer contribution and a guaranteed interest credit. The employer bears the investment risk: if the plan's pooled investments earn more than the credit, future contributions can go down, and if they earn less, contributions go up.</p></div>
<div class="prose"><h2>Who it fits</h2><ul><li>Owners and partners seeking a deduction of $50,000 or more a year, with income of $250,000 or more.</li><li>Highly profitable businesses, including family-owned firms.</li><li>Medical and dental practices, law and CPA firms, engineering and consulting firms.</li><li>Owners close to retirement who want to accelerate savings.</li></ul></div></div>''')
            + band(head_block("Questions", "Common questions about cash balance plans.") + fq, "paper")
            + cta_band("See if a plan fits your practice.", "We coordinate with a plan actuary and your CPA to design, fund and manage the plan."))
    return body, [ld]

def charitable():
    body = (page_hero([("tax", "Tax Strategies"), ("charitable", "Charitable Giving")], "Charitable giving", "Give more effectively with appreciated assets.",
                      "Donating appreciated stock, real estate or digital assets instead of cash can avoid capital gains tax on the appreciation and increase what reaches the causes you support.")
            + band(f'''<div class="grid two">
<article class="card"><div class="body"><h3>{T('Donor-Advised Fund')}</h3><p>Take the deduction in a high-income year, then recommend grants to charities over time.</p></div></article>
<article class="card"><div class="body"><h3>{T('Charitable Remainder Trust')}</h3><p>Contribute an appreciated asset, receive income for a term, and leave the remainder to charity, spreading the gain over years.</p></div></article>
</div>''')
            + band(f'<div class="prose">{risk("Charitable trusts are irrevocable. Deduction limits depend on the asset, the charity and your income. Coordinate with your CPA and an estate attorney.")}</div>', "paper tight")
            + cta_band())
    return body, []

# ---------------------------------------------------------------- PORTFOLIO
def portfolio():
    body = (page_hero([("portfolio", "Portfolio Management")], "Portfolio management", "A tax-aware core portfolio around your alternatives.",
                      "Discretionary management of stocks, bonds and ETFs, built around an Investment Policy Statement and coordinated with your alternative holdings.")
            + band(f'''<div class="ruled">
<div><h3>Built for you</h3><p>Allocation set from your goals, time horizon and risk tolerance, written into an Investment Policy Statement.</p></div>
<div><h3>Tax-aware</h3><p>Asset location, {T('Tax-Loss Harvesting', 'tax-loss harvesting')} and gain planning, led by a CPA.</p></div>
<div><h3>Coordinated</h3><p>Rebalanced with your DSTs, funds and private holdings in view, not in isolation.</p></div>
</div>''')
            + band(f'<div class="prose"><h2>Fees</h2><p>0.75% a year on the first $499,999 and 0.50% on assets of $500,000 and above, billed monthly in arrears. <a href="{L("fees")}">See all fees</a>.</p><p>We also advise on group 401(k) plans for business owners for 0.25% a year, with custody through Schwab and Matrix Trust.</p>{risk("Investing involves risk, including the possible loss of principal. Diversification does not ensure a profit or protect against loss.")}</div>', "paper")
            + cta_band())
    return body, []

# ---------------------------------------------------------------- WHO WE SERVE
def serve(key, name, h1, lede, needs, strategies):
    items = "".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in needs)
    blurbs = {"dst": "Defer the gain on a property sale by reinvesting in a professionally managed DST.",
              "qoz": "Reinvest a capital gain in an Opportunity Zone fund for deferral and potential tax-free growth.",
              "tool-boot": "Estimate how much you need to reinvest, and how much debt to replace, to defer fully.",
              "cbp": "Large deductible retirement contributions for owners with high, steady income.",
              "charitable": "Give appreciated assets and potentially avoid the capital gains tax.",
              "energy": "Oil and gas programs whose drilling costs may be deductible in the first year.",
              "portfolio": "Ongoing management of your public-market portfolio alongside your alternatives."}
    links = "".join(f'<article class="card"><div class="body"><h3>{n}</h3><p>{blurbs.get(k, "")}</p><a class="more" href="{L(k)}">Learn more</a></div></article>' for k, n in strategies)
    return (page_hero([("serve", "Who We Serve"), (key, name)], "Who we serve", h1, lede)
            + band(head_block("What we hear", "The questions we help answer.") + f'<div class="ruled">{items}</div>')
            + band(head_block("Strategies to discuss", "Where we usually start.") + f'<div class="grid">{links}</div>', "paper")
            + cta_band(*(SELL if key in ("serve-re", "serve-biz") else ()))), []

def serve_hub():
    tiles = [("serve-re", "Real estate investors", "Selling investment property and deciding between a 1031 exchange, a DST or an Opportunity Zone fund."),
             ("serve-biz", "Business owners", "Planning an exit, deferring the gain and using the years before a sale well."),
             ("serve-md", "Physicians and dentists", "High income, a high tax bill and too little time to coordinate it all.")]
    cards = "".join(f'<article class="card"><div class="body"><h3>{n}</h3><p>{d}</p><a class="more" href="{L(k)}">Learn more</a></div></article>' for k, n, d in tiles)
    body = (page_hero([("serve", "Who We Serve")], "Who we serve", "Built for accredited investors and high-net-worth families.",
                      f"Our alternative strategies are available only to {T('Accredited Investor', 'accredited investors')}. These are the clients we most often work with.")
            + band(f'<div class="grid">{cards}</div>')
            + cta_band())
    return body, []

# ---------------------------------------------------------------- FEES
def fees():
    body = (page_hero([("fees", "Fees")], "Fees", "Clear, disclosed fees.",
                      "We are a fee-based fiduciary. Our current fees are below. They are negotiable, and every fee is agreed in writing before work begins.", ctas=False)
            + band(f'''<div class="table-box"><table>
<thead><tr><th scope="col">Service</th><th scope="col">Fee</th><th scope="col">How it is billed</th></tr></thead>
<tbody>
<tr><td>Portfolio management, first $499,999</td><td class="num">0.75% a year</td><td>Monthly in arrears on the average daily balance of the household</td></tr>
<tr><td>Portfolio management, $500,000 and above</td><td class="num">0.50% a year</td><td>Monthly in arrears on the average daily balance of the household</td></tr>
<tr><td>Structured notes and non-traded REITs</td><td class="num">1.00% a year</td><td>Quarterly on fair market value</td></tr>
<tr><td>Alternative assets: DSTs, Opportunity Zone funds, energy programs, private funds</td><td class="num">Flat fee by investment size</td><td>One-time, under our Alternative Assets Services and Fees Agreement, which we share before you engage us. Covers due diligence, research, meetings and closing support.</td></tr>
<tr><td>Group and employer retirement plans</td><td class="num">0.25% a year</td><td>Quarterly in arrears on the account value at quarter end</td></tr>
<tr><td>Hourly financial advice</td><td class="num">$475 an hour</td><td>Invoiced as services are performed</td></tr>
<tr><td>Insurance recommendations</td><td class="num">No advisory fee</td><td>Insurance is offered only through our affiliate, Nashional Insurance, which is paid by the insurance carrier. <a href="{L('insurance')}">How this works</a></td></tr>
</tbody></table></div>
<p class="risk" style="margin-top:16px">Custodian, brokerage and fund expenses are paid separately. Accounts we do not manage directly, such as outside 401(k), 403(b), 457, 529, TSP and HSA accounts, are not charged our asset-based fee. Full details are in our <a href="{FIRM['iapd_firm']}">Form ADV Part 2A</a>.</p>''')
            + band(f'''<div class="grid two"><div class="prose"><h2>Conflicts we disclose</h2><p>Our advisers are licensed insurance agents, and the firm is affiliated with a tax planning firm, a loan advisory firm and a futures firm. Jeff Nash is also a licensed mortgage loan officer. These affiliates can earn compensation if you use them, and you are never required to. <a href="{L('affiliates')}">Affiliated companies</a> and <a href="{L('disclosures')}">disclosures</a>.</p></div>
<div class="note"><span class="eyebrow">Fee-based, not fee-only</span><p>{T('Fee-Based Adviser', 'Fee-based')} means we charge advisory fees and affiliated persons may earn commissions on some products, such as insurance. We disclose every one.</p></div></div>''', "paper")
            + cta_band("Questions about fees?", "We will walk you through exactly what you would pay before you sign anything."))
    return body, []

# ---------------------------------------------------------------- TEAM
def team():
    persons = [
        {"@context": "https://schema.org", "@type": "Person", "@id": SITE + "/team/#jeff-nash", "name": "Jeff Nash", "jobTitle": "President and Chief Investment Officer",
         "worksFor": {"@id": SITE + "/#firm"}, "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": "CERTIFIED FINANCIAL PLANNER®"}, {"@type": "EducationalOccupationalCredential", "name": "Certified Public Accountant"}],
         "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Mississippi State University"}, {"@type": "CollegeOrUniversity", "name": "University of Oklahoma"}],
         "sameAs": [FIRM["iapd_jeff"]]},
        {"@context": "https://schema.org", "@type": "Person", "@id": SITE + "/team/#denver-mcclure", "name": "Denver McClure", "jobTitle": "Partner",
         "worksFor": {"@id": SITE + "/#firm"}, "hasCredential": [{"@type": "EducationalOccupationalCredential", "name": "Certified in Blockchain and Digital Assets (CBDA)"}, {"@type": "EducationalOccupationalCredential", "name": "Series 65"}],
         "alumniOf": [{"@type": "CollegeOrUniversity", "name": "Midwestern State University"}],
         "sameAs": [FIRM["iapd_denver"]]},
    ]
    body = (page_hero([("team", "Team")], "Team", "Two advisers. One plan.", "Tax and investment strategy from a CFP® professional and CPA, and real estate and alternatives expertise from a partner who invests alongside the asset classes he advises on.")
            + band(team_cards())
            + cta_band())
    return body, persons

# ---------------------------------------------------------------- TOOLS
def tools():
    tl = [("tool-1031", "1031 Deadline Calculator", "Your 45-day identification and 180-day closing dates from a sale date."),
          ("tool-boot", "1031 Replacement Calculator", "The value, equity and debt you need to replace to defer fully, and any boot."),
          ("tool-qoz", "Opportunity Zone Timing Checker", "Your 180-day window and which Opportunity Zone rules apply."),
          ("tool-ai", "Accredited Investor Check", "A quick, private check against the SEC definition.")]
    cards = "".join(f'<article class="card"><div class="body"><h3>{n}</h3><p>{d}</p><a class="more" href="{L(k)}">Open the tool</a></div></article>' for k, n, d in tl)
    body = (page_hero([("tools", "Tools")], "Planning tools", "Tools for the decisions that run on deadlines.", "Free, private calculators. Nothing you enter is stored or sent.", ctas=False)
            + band(f'<div class="grid">{cards}</div>')
            + band(head_block("Strategy builder", "Not sure where to start?") + builder(), "")
            + cta_band())
    return body, []

def tool_page(key, name, h1, lede, tool_html, about):
    ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": name, "applicationCategory": "FinanceApplication",
          "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "publisher": {"@id": SITE + "/#firm"}}
    body = (page_hero([("tools", "Tools"), (key, name)], "Planning tool", h1, lede, ctas=False)
            + band(f'<div class="grid two"><div style="min-width:0">{tool_html}</div><div class="prose">{about}</div></div>')
            + cta_band())
    return body, [ld]

def tool_1031():
    t = '''<div class="tool" id="t1031"><div class="fields">
<div class="field"><label for="t1031-date">Sale closing date</label><input type="date" id="t1031-date" value="2026-11-20"></div>
<label class="check" for="t1031-ext" style="border:0;align-items:center"><input type="checkbox" id="t1031-ext"><span>I will file a tax return extension</span></label>
</div>
<div class="result"><div class="out"><div><span class="label">Identify replacements by</span><b id="t1031-45">-</b></div><div><span class="label">Close on replacements by</span><b id="t1031-180">-</b></div></div><p class="muted" id="t1031-note" style="font-size:15px"></p>
<p class="risk" style="font-size:12.5px">Example date shown. Illustration only. Confirm deadlines with your qualified intermediary and CPA.</p></div></div>'''
    about = f'<h2>How the dates work</h2><p>The {T("45-Day Identification Period", "45-day identification period")} and the {T("180-Day Exchange Period", "180-day exchange period")} both start the day your sale closes and run at the same time. The 180-day limit is cut short by your tax return due date unless you file an extension. Neither deadline moves for weekends or holidays.</p>'
    return tool_page("tool-1031", "1031 Deadline Calculator", "1031 exchange deadline calculator.", "Enter your closing date to see your identification and closing deadlines.", t, about)

def tool_boot():
    t = '''<div class="tool" id="tboot"><div class="fields">
<div class="field"><label for="tb-sale">Sale price</label><input type="text" inputmode="numeric" id="tb-sale" value="2,400,000"></div>
<div class="field"><label for="tb-costs">Selling costs</label><input type="text" inputmode="numeric" id="tb-costs" value="120,000"></div>
<div class="field"><label for="tb-debt">Mortgage paid off at sale</label><input type="text" inputmode="numeric" id="tb-debt" value="900,000"></div>
<div class="field"><label for="tb-repl">Planned replacement price</label><input type="text" inputmode="numeric" id="tb-repl" value="2,280,000"></div>
<div class="field"><label for="tb-cash">Cash you will reinvest</label><input type="text" inputmode="numeric" id="tb-cash" value="1,380,000"></div>
</div>
<div class="result"><div class="out">
<div><span class="label">Buy at least</span><b id="tb-min">-</b></div>
<div><span class="label">Equity to reinvest</span><b id="tb-equity">-</b></div>
<div><span class="label">New debt on these numbers</span><b id="tb-newdebt">-</b></div>
<div><span class="label">Estimated boot</span><b id="tb-boot">-</b></div>
</div><p class="muted" id="tb-note" style="font-size:15px"></p>
<p class="risk" style="font-size:12.5px">Example figures shown. Illustration only, not a tax calculation. Confirm with your CPA and qualified intermediary.</p></div></div>'''
    about = f'<h2>The three tests</h2><p>To defer all of the tax, buy replacement property worth at least your net sale price, reinvest all of your equity, and carry at least as much debt as you paid off. Added cash can make up for less debt, but less debt cannot make up for cash you keep. Anything short is {T("Boot", "boot")}.</p><p>Leveraged DSTs can help meet the {T("Debt Replacement", "debt requirement")}.</p>'
    return tool_page("tool-boot", "1031 Replacement Calculator", "1031 exchange replacement and boot calculator.", "See the value, equity and debt you need to replace to defer fully.", t, about)

def tool_qoz():
    t = '''<div class="tool" id="tqoz"><div class="fields">
<div class="field"><label for="tq-date">Date of the sale that created the gain</label><input type="date" id="tq-date" value="2026-09-15"></div>
<div class="field"><label for="tq-type">Type of gain</label><select id="tq-type"><option value="direct">Gain from my own sale</option><option value="k1">Gain reported on a K-1</option></select></div>
</div>
<div class="result"><div class="out"><div><span class="label">Invest the gain by</span><b id="tq-end">-</b></div></div><p id="tq-rule" style="font-size:16px"></p><p class="muted" id="tq-k1" style="font-size:15px"></p>
<p class="risk" style="font-size:12.5px">Example date shown. Illustration only. Rules summarized as of October 2026.</p></div></div>'''
    about = f'<h2>Why the date matters</h2><p>Gains invested in a {T("Qualified Opportunity Fund")} on or after January 1, 2027 receive a five-year rolling deferral and a {T("QOZ Basis Step-Up", "basis step-up")}. Gains invested earlier follow the current rules, under which deferred gain is recognized by December 31, 2026. Both keep the {T("10-Year Exclusion", "10-year exclusion")}.</p><p><a href="{L("qoz")}">Read the full comparison</a></p>'
    return tool_page("tool-qoz", "Opportunity Zone Timing Checker", "Opportunity Zone timing checker.", "Find your 180-day window and which rules apply to your gain.", t, about)

def tool_ai():
    t = '''<div class="tool" id="tai"><fieldset style="border:0;margin:0;padding:0"><legend class="legend" style="margin-bottom:6px">Check any that apply</legend>
<label class="check" for="ai1"><input type="checkbox" id="ai1"><span>My income was over $200,000 in each of the last two years, and I expect the same this year.</span></label>
<label class="check" for="ai2"><input type="checkbox" id="ai2"><span>Our joint income with a spouse or partner was over $300,000 in each of the last two years, and we expect the same this year.</span></label>
<label class="check" for="ai3"><input type="checkbox" id="ai3"><span>My net worth, alone or with a spouse or partner, is over $1 million, not counting my primary home.</span></label>
<label class="check" for="ai4"><input type="checkbox" id="ai4"><span>I hold a Series 7, Series 65 or Series 82 license in good standing.</span></label>
</fieldset>
<div class="result"><b id="tai-result" style="font-family:var(--display);font-size:22px;font-weight:600"></b><p class="muted" id="tai-note" style="font-size:15px"></p>
<p class="risk" style="font-size:12.5px">Nothing you check is stored or sent. This is a general guide to SEC Rule 501, not a determination of status.</p></div></div>'''
    about = f'<h2>Why it matters</h2><p>Most DSTs, Opportunity Zone funds, energy programs and private funds are sold under {T("Regulation D")} and are limited to {T("Accredited Investor", "accredited investors")}. Some private funds require {T("Qualified Purchaser", "qualified purchaser")} status, which starts at $5 million in investments.</p><p><a href="{L("term:accredited-investor")}">Read the full definition</a></p>'
    return tool_page("tool-ai", "Accredited Investor Check", "Do you qualify as an accredited investor?", "A quick, private check against the SEC definition.", t, about)

# ---------------------------------------------------------------- GLOSSARY
CAT_PAGE = {"Insurance": "insurance", "1031 and DST": "dst", "Opportunity Zones": "qoz", "Energy": "energy", "Private Markets": "private", "Tax": "tax", "Digital Assets": "digital", "Regulatory": "disclosures"}

def glossary_index():
    items = "".join(f'<a href="{L("term:" + slug(t))}"><b style="font-weight:500">{t}</b><span>{c}</span></a>' for t, c, d in sorted(TERMS, key=lambda x: x[0].lower()))
    ld = {"@context": "https://schema.org", "@type": "DefinedTermSet", "@id": SITE + "/glossary/#set", "name": "Nashional Investments Glossary",
          "hasDefinedTerm": [{"@type": "DefinedTerm", "name": t, "url": SITE + "/glossary/" + slug(t) + "/"} for t, c, d in TERMS]}
    body = (page_hero([("glossary", "Glossary")], "Glossary", "Glossary of alternative investment and tax terms.", f"{len(TERMS)} plain-English definitions from our advisers. Updated October 2026.", ctas=False)
            + band(f'''<div class="field" style="max-width:520px;margin-bottom:28px"><label for="glossary-q">Search terms</label><input type="search" id="glossary-q" placeholder="Try DST, boot or accredited"><span class="label" id="glossary-count" aria-live="polite"></span></div>
<div class="terms" id="glossary-list">{items}</div>''')
            + cta_band())
    return body, [ld]

def term_page(t, c, d):
    key = "term:" + slug(t)
    related = [x for x in TERMS if x[1] == c and x[0] != t][:4]
    rel = "".join(T(x[0]) for x in related)
    strat = CAT_PAGE[c]
    sname = {"dst": "1031 exchanges and DSTs", "qoz": "Opportunity Zones", "energy": "Energy", "private": "Private markets", "tax": "Tax strategies", "digital": "Digital assets", "disclosures": "Our disclosures", "insurance": "Insurance planning"}[strat]
    ld = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": t, "description": d, "url": SITE + "/glossary/" + slug(t) + "/",
          "inDefinedTermSet": SITE + "/glossary/#set"}
    extra = ""
    if t == "Accredited Investor":
        extra = band(accredited_card(), "paper")
    body = (f'''<section class="hero page-hero"><div class="wrap">{crumbs([("glossary", "Glossary"), (key, t)])}<span class="eyebrow">Definition · {c}</span><h1>{t}</h1><p class="definition">{d}</p>
<p class="label">Nashional Investments · Updated October 2026</p><p class="risk" style="font-size:13px">Educational definition only, not investment, tax or legal advice.</p></div></section>'''
            + extra
            + band(f'''<div class="grid two"><div style="display:flex;flex-direction:column;gap:14px;min-width:0"><span class="eyebrow">Related terms</span><div class="chips">{rel}</div><p><a href="{L('glossary')}">All terms</a></p></div>
<div class="note"><span class="eyebrow">Where it applies</span><p>See how this fits into a real plan on our <a href="{L(strat)}">{sname}</a> page.</p></div></div>''')
            + cta_band("Have a question about this?", "Ask us how it applies to your situation. Your first conversation is complimentary."))
    return body, [ld]

# ---------------------------------------------------------------- DISCLOSURES / AFFILIATES / CONTACT
def disclosures():
    body = (page_hero([("disclosures", "Disclosures")], "Disclosures", "Important disclosures.", "Registration, conflicts and how we use information.", ctas=False)
            + band(f'''<div class="prose">
<h2>Registration</h2><p>Investment advisory services are offered through {FIRM['legal']}, doing business as Nashional Investments, an investment adviser registered in Texas and New Jersey. Registration does not imply a certain level of skill or training. We may only transact business in states where we are registered or qualify for an exemption. Any direct communication with a prospective client is conducted by a representative who is registered or qualifies for an exemption in that person's state.</p>
<p>Firm CRD 289955. Jeff Nash CRD 6031965. Denver McClure CRD 7319835. Our Form ADV Part 2A brochure and Part 2B supplements are available at <a href="{FIRM['iapd_firm']}">adviserinfo.sec.gov</a> or on request.</p>
<h2>General information</h2><p>This website provides general information about our services. It is not an offer to sell or a solicitation to buy any security, and it is not personalized investment, tax or legal advice. Content is developed from sources believed to be accurate. Consult your tax and legal professionals about your situation.</p>
<h2>Alternative investments</h2><p>DSTs, Opportunity Zone funds, energy programs, private funds, non-traded REITs and structured notes are speculative and illiquid, may be difficult to value, carry sponsor and issuer risk, and are generally available only to accredited investors. You may lose some or all of your investment. Tax benefits are not guaranteed and depend on your circumstances and current law.</p>
<h2>Digital assets</h2><p>Digital assets are highly volatile, may lose all of their value, and are not insured by the FDIC or SIPC.</p>
<h2>Conflicts of interest</h2><p>Persons affiliated with our firm may earn compensation from affiliated businesses, including insurance commissions through Nashional Independent Insurance Agency LLC, tax services through Nashional Independent Tax Planning PLLC, mortgage lending, a futures firm, and loan advisory through Fiduciary Financing LLC. Clients are never required to use these services. See <a href="{L('affiliates')}">affiliated companies</a> and Items 10 and 11 of our Form ADV Part 2A.</p>
<h2>Tools and calculators</h2><p>Our planning tools are for illustration only. They do not store or send what you enter, they are not tax calculations, and their results are not recommendations.</p>
<h2>Use of technology</h2><p>We use software tools, including artificial intelligence, to support research and operations. All recommendations are made and reviewed by our advisers.</p>
<h2>Investment risk</h2><p>Investing involves risk, including the possible loss of principal. Past performance does not guarantee future results. Diversification and asset allocation do not ensure a profit or protect against loss. Hypothetical examples and calculator results are for illustration only and do not represent any actual investment.</p>
<h2>Private offerings</h2><p>Nashional Investments is an investment adviser, not a broker-dealer, and does not sell securities. DSTs, Opportunity Zone funds and other private offerings are offered by their sponsors through registered broker-dealers, generally under Regulation D, and only to investors who meet the applicable eligibility standards. We do not endorse any sponsor or offering by describing it on this site.</p>
<h2>Third-party information and links</h2><p>Information from third parties is believed to be reliable but is not guaranteed. Links to other websites are provided for convenience; we are not responsible for their content.</p>
<h2>Testimonials</h2><p>This website does not contain client testimonials or endorsements.</p>
<h2>Privacy</h2><p>Read our <a href="{L('privacy')}">privacy policy</a>.</p>
</div>''')
            )
    return body, []

def affiliates():
    body = (page_hero([("affiliates", "Affiliated Companies")], "Affiliated companies", "Related services from affiliated firms.",
                      "Some strategies need help beyond investment advice. These affiliated firms can provide it. Each can earn compensation if you use them, and you are never required to.", ctas=False)
            + band(f'''<div class="grid">
<article class="card"><div class="body"><h3>Nashional Tax Planning</h3><p>Tax planning, strategy and preparation for individuals, real estate professionals and business owners.</p><p class="risk">Conflict: Jeff Nash is a founding partner and is compensated for these services.</p></div></article>
<article class="card"><div class="body"><h3>Nashional Insurance</h3><p>Life, health, property and business insurance, including cash value life insurance. <a href="{L('insurance')}">Insurance planning</a></p><p class="risk">Conflict: Jeff Nash is an owner and licensed agent and earns commissions on products sold.</p></div></article>
<article class="card"><div class="body"><h3>Fiduciary Financing</h3><p>Help comparing residential, business and commercial loans. <a href="https://www.fiduciary-financing.com/">fiduciary-financing.com</a></p><p class="risk">Conflict: Jeff Nash and Denver McClure are partners. The firm is compensated by the lending platform it uses.</p></div></article>
</div>'''))
    return body, []

def contact():
    body = (page_hero([("contact", "Contact")], "Contact", "Book a consultation.", "Your first conversation is complimentary. Tell us what is happening, or email Jeff or Denver directly, and we will reply promptly.", ctas=False)
            + band(f'''<div class="grid two">
<form class="tool" id="contact-form" name="contact" method="POST" action="#" data-preview="{'1' if PREVIEW else '0'}" data-wix-client="{WIX_FORM['client_id']}" data-wix-form="{WIX_FORM['form_id']}" novalidate>
<div aria-hidden="true" style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden"><label for="c-website">Leave this field empty</label><input type="text" id="c-website" name="website" tabindex="-1" autocomplete="off"></div>
<div class="fields">
<div class="field"><label for="c-name">Name</label><input type="text" id="c-name" name="name" required autocomplete="name"></div>
<div class="field"><label for="c-email">Email</label><input type="email" id="c-email" name="email" required autocomplete="email"></div>
<div class="field"><label for="c-phone">Phone (optional)</label><input type="tel" id="c-phone" name="phone" autocomplete="tel"></div>
<div class="field"><label for="c-who">Who would you like to speak with?</label><select id="c-who" name="adviser"><option>Either adviser</option><option>Jeff Nash</option><option>Denver McClure</option></select></div>
<div class="field"><label for="c-topic">What is happening</label><select id="c-topic" name="topic" required><option value="">Choose one</option><option>Selling investment real estate</option><option>Selling a business</option><option>A large stock or crypto gain</option><option>High income, high tax bill</option><option>Portfolio management</option><option>Something else</option></select></div>
</div>
<div class="field"><label for="c-msg">Anything else we should know (optional)</label><textarea id="c-msg" name="message"></textarea></div>
<label class="check" for="c-ai" style="border:0"><input type="checkbox" id="c-ai" name="accredited" value="yes"><span>I believe I meet the <a href="{L('term:accredited-investor')}">accredited investor</a> definition.</span></label>
<p class="risk" style="font-size:12.5px">Please do not include account numbers or Social Security numbers.</p>
<div class="btns"><button class="btn" type="submit">Request a consultation</button></div>
<p class="form-status" id="contact-status" aria-live="polite"></p>
</form>
<div class="prose"><h3>Email an adviser</h3><p><strong>Jeff Nash, CFP®, CPA</strong><br>{FIRM['jeff_email']}</p><p><strong>Denver McClure, CBDA</strong><br>{FIRM['denver_email']}</p><h3 style="margin-top:12px">Office</h3><p>{FIRM['addr1']}<br>{FIRM['city']}, {FIRM['state']} {FIRM['zip']}<br>By appointment</p><p><a href="https://maps.google.com/?q=5900+S+Lake+Forest+Dr+Suite+300+McKinney+TX+75070">Get directions</a></p></div>
</div>'''))
    return body, []

def insurance():
    fq, ld = faq([
        ("Does Nashional Investments charge for insurance advice?", "No. Nashional Investments does not bill advisory fees for advice on insurance products. Insurance is offered through Nashional Insurance, a separate entity whose licensed agents are paid commissions by the insurance carrier."),
        ("What is infinite banking?", f"Infinite banking is a name for using a {T('Cash Value Life Insurance', 'cash value life insurance')} policy, usually whole life, as a source of loans you can take and repay on your own schedule. It can make sense for some business owners and high earners. It also has real costs: premiums, policy charges, slow early cash value growth and loans that reduce the death benefit if not repaid."),
        ("Do I have to buy insurance to work with Nashional Investments?", "No. You are never required to buy insurance, or to buy it through our affiliate."),
    ])
    body = (page_hero([("insurance", "Insurance Planning")], "Insurance planning", "Insurance strategies for business owners and accredited investors.",
                      "Some plans call for life insurance: to fund a buy-sell agreement, protect a business, transfer wealth or add tax-advantaged cash value. These products are offered through Nashional Insurance, a separate licensed agency.")
            + band(f'''<div class="grid">
<article class="card"><div class="body"><h3>{T('Cash Value Life Insurance')}</h3><p>Whole and universal life policies that pair a death benefit with cash value you can access, including strategies sometimes called infinite banking.</p></div></article>
<article class="card"><div class="body"><h3>{T('Indexed Universal Life')}</h3><p>Cash value growth linked to a market index, with a floor and a cap, and policy charges that reduce credited growth.</p></div></article>
<article class="card"><div class="body"><h3>Business coverage</h3><p>Key person insurance, buy-sell funding and coverage for owners and employees.</p></div></article>
</div>''')
            + band(f'''<div class="grid two"><div class="prose"><h2>How it works with your plan</h2><p>Your Nashional adviser looks at insurance as part of your whole plan, alongside your portfolio and tax picture. If a policy makes sense, a licensed agent of Nashional Insurance handles the quote, application and policy.</p></div>
<div class="note"><span class="eyebrow">Important</span><p>Insurance products are offered through Nashional Independent Insurance Agency LLC, a separate entity from Nashional Investments. Its agents are paid commissions by insurance carriers. Nashional Investments does not charge advisory fees for insurance recommendations, and you are never required to buy insurance through our affiliate. Policy guarantees depend on the claims-paying ability of the issuing insurer.</p></div></div>''', "paper")
            + band(head_block("Questions", "Common questions about insurance planning.") + fq)
            + cta_band("Want a second look at a policy?", "We can review how an existing or proposed policy fits the rest of your plan."))
    return body, [ld]

def privacy():
    body = (page_hero([("privacy", "Privacy Policy")], "Privacy policy", "How we protect your information.", f"This policy applies to Nashional Independent Investment Management LLC, doing business as Nashional Investments, McKinney, Texas. Until our revised policy is adopted, the <a href=\"{FIRM['privacy_pdf']}\">privacy policy currently in force (PDF)</a> governs.", ctas=False)
            + band(f'''<div class="prose">
<h2>Our commitment</h2><p>Protecting your personal information is part of our duty as your adviser. We hold ourselves to professional standards of confidentiality, and we explain here what we collect, how we use it and the choices you have.</p>
<h2>What we collect</h2><p>We collect nonpublic personal information that you give us or authorize us to obtain, such as your name, address, date of birth, Social Security number, income, assets, account numbers and balances, and investment experience. We also receive information about your accounts from custodians and other firms you authorize.</p>
<h2>How we use and share it</h2><p>We use your information to provide advisory services, open and maintain accounts, process transactions and meet legal and regulatory requirements. We share it only as needed:</p>
<ul><li>With custodians, broker-dealers and service providers that support your accounts and our operations, under confidentiality terms.</li>
<li>With our affiliated companies, such as Nashional Tax Planning, Nashional Insurance and Fiduciary Financing, to better serve your needs and to tell you about services that may help you, including when we refer you to one of them.</li>
<li>With non-affiliated partner companies only with your permission, for example when you ask us to introduce you.</li>
<li>When required by law, regulators or court order.</li></ul>
<p>You may ask us at any time to stop our affiliates from using your information to market to you. Your choice applies until you tell us otherwise.</p>
<h2>Technology and service providers</h2><p>We use technology providers, including software that uses artificial intelligence, to support research and operations. They may process information only to provide services to us, under confidentiality and security obligations. We do not sell your personal information.</p>
<h2>Our website</h2><p>When you use our contact form, we receive the information you enter, which is processed by our website host. Our planning tools run in your browser and do not store or send what you enter. Our site loads fonts from Google, which may receive your IP address.</p>
<h2>Text messages</h2><p>If we communicate with you by text message, you may reply STOP at any time to opt out. Mobile numbers and text opt-in data are never shared with third parties for marketing.</p>
<h2>How we protect it</h2><p>We maintain physical, electronic and procedural safeguards, including secured systems and files and limited access to client information. If a security incident affects your information, we will notify you as required by law.</p>
<h2>Your choices and questions</h2><p>To limit sharing where the law allows, or with any questions, email Jeff Nash at {FIRM['jeff_email']} or Denver McClure at {FIRM['denver_email']}.</p>
</div>'''))
    return body, []

# ---------------------------------------------------------------- REGISTER
def reg(key, title, desc, fn, active=None):
    def lazy():
        b, s = fn()
        return b
    CURRENT["dir"] = PAGES[key]
    b, s = fn()
    page(key, title, desc, lazy, schema=s, active=active)

def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    reg("home", "Nashional Investments | DST and Opportunity Zone Advisor",
        "Texas-registered fiduciary advisor for 1031 exchanges, DSTs, Opportunity Zones and tax-driven alternatives. Led by a CFP® and CPA. Flat, disclosed fees.", lambda: (home(), [HOME_FAQ[1]]))
    reg("alternatives", "Alternative Investment Advisor", "Fiduciary review of DSTs, Opportunity Zone funds, energy programs and private funds for accredited investors.", lambda: (alternatives(), []), "alternatives")
    reg("dst", "DST 1031 Exchange Advisor in Texas", "How 1031 exchanges into Delaware Statutory Trusts work, their trade-offs, and how a fiduciary evaluates a DST.", dst, "alternatives")
    reg("qoz", "Opportunity Zone Investing: 2026 and 2027 Rules", "How Qualified Opportunity Fund investing works under the current rules and the new rules starting January 1, 2027.", qoz, "alternatives")
    reg("energy", "Oil and Gas Tax Strategies", "How oil and gas working interests and intangible drilling cost deductions work, and their risks.", energy, "alternatives")
    reg("private", "Private Credit and Private Equity Advisor", "Fiduciary review of private credit, private equity and interval funds for accredited investors.", private, "alternatives")
    reg("digital", "Digital Asset Financial Advisor in Texas", "Advice on how Bitcoin and other digital assets fit within a diversified portfolio, from a CBDA-designated adviser.", digital, "alternatives")
    reg("tax", "Tax Strategies for High-Income Investors", "Cash balance plans, charitable strategies, energy deductions and gain deferral, coordinated by a CPA-led adviser.", tax, "tax")
    reg("cbp", "Cash Balance Plans for Business Owners", "How cash balance plans allow large deductible retirement contributions for owners, partners and professionals.", cbp, "tax")
    reg("charitable", "Charitable Giving with Appreciated Assets", "Donor-advised funds and charitable remainder trusts for appreciated stock, real estate and digital assets.", charitable, "tax")
    reg("portfolio", "Portfolio Management", "Tax-aware discretionary portfolio management coordinated with your alternative investments.", portfolio, "portfolio")
    reg("serve", "Who We Serve", "Nashional Investments works with accredited investors, high-net-worth families, real estate investors, business owners and physicians.", serve_hub)
    reg("serve-re", "Selling Rental Property: Capital Gains Options", "Options for real estate investors selling investment property, from 1031 exchanges and DSTs to Opportunity Zones.",
        lambda: serve("serve-re", "Real Estate Investors", "Selling investment property without giving up the gain.", "You have built equity in real estate. We help you decide what to do with it when you sell.",
                      [("Do I have to keep being a landlord?", "A 1031 exchange into a DST lets you defer the gain while a professional sponsor manages the property."), ("How do I avoid depreciation recapture?", "A 1031 exchange can defer recapture along with the capital gain."), ("What if I want out of real estate?", "An Opportunity Zone fund can take just the gain, freeing the rest.")],
                      [("dst", "1031 exchanges and DSTs"), ("qoz", "Opportunity Zones"), ("tool-boot", "1031 replacement calculator")]))
    reg("serve-biz", "Selling a Business: Tax Strategies", "Tax strategies for business owners planning a sale, including Opportunity Zones, installment sales and charitable trusts.",
        lambda: serve("serve-biz", "Business Owners", "Plan the sale of your business before the buyer does.", "For many owners, the largest tax bill of their lives arrives with the exit. Planning a year ahead can change what you keep.",
                      [("How much of my sale will go to tax?", "We model the gain, the rates and the options before you sign a letter of intent."), ("Can I defer the gain?", "An Opportunity Zone fund or an installment sale can spread or defer it."), ("What about the years before the sale?", "A cash balance plan can shelter large contributions while you still own the business.")],
                      [("qoz", "Opportunity Zones"), ("cbp", "Cash balance plans"), ("charitable", "Charitable giving")]))
    reg("serve-md", "Financial Advisor for Physicians in Texas", "Tax and investment strategies for physicians and dentists, including cash balance plans and energy deductions.",
        lambda: serve("serve-md", "Physicians", "For physicians and dentists with a high income and a high tax bill.", "Many physicians start earning later than their peers and pay the top tax rate for most of their careers. We focus on the strategies that typically matter most for practice owners and high earners.",
                      [("How do I lower my taxes as a W-2 or practice owner?", "Cash balance plans and energy deductions are two of the most common levers."), ("Should I invest in real estate?", "Passive real estate, such as DSTs and private real estate funds, can add income without becoming a landlord."), ("How do I coordinate all of this?", "One plan that covers your practice, your portfolio and your taxes.")],
                      [("cbp", "Cash balance plans"), ("energy", "Energy"), ("portfolio", "Portfolio management")]))
    reg("fees", "Fees", "Our advisory fees for portfolio management, alternatives, 1031 and DST consulting, and hourly advice.", fees, "fees")
    reg("team", "Team", "Meet Jeff Nash, CFP®, CPA, founder and CIO, and Denver McClure, CBDA, partner and alternatives lead at Nashional Investments in McKinney, Texas.", team, "team")
    reg("tools", "Planning Tools", "Free, private calculators: 1031 exchange deadlines, 1031 replacement and boot, Opportunity Zone timing and an accredited investor check.", tools, "tools")
    reg("tool-1031", "1031 Exchange Deadline Calculator", "Calculate your 45-day identification and 180-day closing deadlines for a 1031 exchange.", tool_1031, "tools")
    reg("tool-boot", "1031 Exchange Replacement and Boot Calculator", "Calculate the value, equity and debt to replace in a 1031 exchange, and estimate boot.", tool_boot, "tools")
    reg("tool-qoz", "Opportunity Zone Timing Checker", "Find your 180-day Opportunity Zone investment window and whether the 2027 rules apply.", tool_qoz, "tools")
    reg("tool-ai", "Accredited Investor Check", "Check whether you likely meet the SEC accredited investor definition. Private and free.", tool_ai, "tools")
    reg("glossary", "Glossary", "Plain-English definitions of 1031, Opportunity Zone, energy, private market, tax and digital asset terms.", glossary_index, "glossary")
    for t, c, d in TERMS:
        reg("term:" + slug(t), f"{t}: Definition", (d if len(d) <= 158 else d[:155].rsplit(" ", 1)[0].rstrip(",;:") + "..."), (lambda t=t, c=c, d=d: term_page(t, c, d)), "glossary")
    reg("insurance", "Insurance Planning", "Cash value life insurance, indexed universal life and business coverage, offered through our affiliate Nashional Insurance.", insurance, "tax")
    reg("privacy", "Privacy Policy", "How Nashional Investments collects, uses and protects your personal information.", privacy)
    reg("notfound", "Page Not Found", "The page you were looking for has moved. Explore DSTs, Opportunity Zones and tax-driven alternatives from Nashional Investments.", lambda: (page_hero([("notfound", "Page not found")], "404", "This page has moved.", "The page you were looking for is no longer here. Try our alternatives, planning tools or glossary.", ctas=False) + band(f'<div class="btns"><a class="btn" href="{L("home")}">Go to the homepage</a><a class="btn ghost" href="{L("alternatives")}">Alternatives</a><a class="btn ghost" href="{L("glossary")}">Glossary</a></div>'), []))
    reg("disclosures", "Disclosures", "Registration, investment risk, private offering, conflict of interest and technology disclosures for Nashional Investments, a Texas-registered adviser.", disclosures)
    reg("affiliates", "Affiliated Companies", "Affiliated tax, insurance and loan advisory firms, and the conflicts of interest they create.", affiliates)
    reg("contact", "Contact", "Book a complimentary consultation with Nashional Investments in McKinney, Texas.", contact)
    FLAGS.clear()
    render_all()
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(OUT, "assets"))
    write_extras()
    if not PREVIEW:
        shutil.copy(os.path.join(OUT, "404", "index.html"), os.path.join(OUT, "404.html"))

def write_extras():
    if PREVIEW:
        open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
    else:
        bots = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot", "Googlebot"]
        if STAGING:
            open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
            open(os.path.join(OUT, "_headers"), "w").write("/*\n  X-Robots-Tag: noindex, nofollow\n")
        else:
            open(os.path.join(OUT, "robots.txt"), "w").write("".join(f"User-agent: {b}\nAllow: /\n\n" for b in bots) + f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
        urls = "".join(f"<url><loc>{SITE}/{p}</loc><lastmod>{TODAY}</lastmod></url>" for p in PAGES_OUT if p != "404/")
        open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        open(os.path.join(OUT, "_redirects"), "w").write("/cash-balance-plan /tax-strategies/cash-balance-plans/ 301\n/map /contact/ 301\n")
    llms = f"""# Nashional Investments

> Nashional Investments (legal name {FIRM['legal']}) is a fee-based, fiduciary registered investment adviser in McKinney, Texas, registered with the Texas State Securities Board and in New Jersey. The firm advises accredited investors and high-net-worth families on 1031 exchanges and Delaware Statutory Trusts (DSTs), Qualified Opportunity Zone funds, energy tax strategies, private markets and digital assets, alongside tax-aware portfolio management. Led by Jeff Nash, CFP(R), CPA (CRD 6031965) and Denver McClure, CBDA (CRD 7319835). Firm CRD 289955.

## Strategies
- [1031 Exchanges and DSTs]({SITE}/alternatives/1031-exchange-dst/)
- [Qualified Opportunity Zones]({SITE}/alternatives/opportunity-zones/)
- [Energy tax strategies]({SITE}/alternatives/energy/)
- [Private markets]({SITE}/alternatives/private-markets/)
- [Digital assets]({SITE}/alternatives/digital-assets/)
- [Cash balance plans]({SITE}/tax-strategies/cash-balance-plans/)
- [Charitable giving]({SITE}/tax-strategies/charitable-giving/)
- [Portfolio management]({SITE}/portfolio-management/)

## Tools
- [1031 deadline calculator]({SITE}/tools/1031-deadline-calculator/)
- [1031 replacement calculator]({SITE}/tools/1031-replacement-calculator/)
- [Opportunity Zone timing checker]({SITE}/tools/opportunity-zone-timing/)
- [Accredited investor check]({SITE}/tools/accredited-investor-check/)

## Firm
- [Fees]({SITE}/fees/): 0.75% on the first $499,999 and 0.50% above $500,000 for portfolio management; a one-time flat fee by investment size for alternative assets; 0.25% for group retirement plans; $475 an hour for advice. No advisory fee for insurance, which is offered through the separate affiliate Nashional Insurance.
- [Team]({SITE}/team/)
- [Glossary]({SITE}/glossary/)
- [Disclosures]({SITE}/disclosures/)

## Contact
- Jeff Nash, CFP(R), CPA: {FIRM['jeff_email']}
- Denver McClure, CBDA: {FIRM['denver_email']}
- Office: {FIRM['addr1']}, {FIRM['city']}, {FIRM['state']} {FIRM['zip']}
"""
    open(os.path.join(OUT, "llms.txt"), "w").write(llms)
    full = llms + "\n## Frequently asked questions\n" + "".join(f"\n### {q}\n{re.sub('<[^>]+>', '', a)}\n" for q, a in [(x["name"], x["acceptedAnswer"]["text"]) for x in HOME_FAQ[1]["mainEntity"]])
    full += "\n## Glossary\n" + "".join(f"\n### {t}\n{d} ({SITE}/glossary/{slug(t)}/)\n" for t, c, d in sorted(TERMS))
    open(os.path.join(OUT, "llms-full.txt"), "w").write(full)
    seen = []
    for f in FLAGS:
        if f not in seen:
            seen.append(f)
    with open(os.path.join(OUT, "..", MODE + "-flags.json"), "w") as fh:
        json.dump(seen, fh, indent=1)
    print("pages:", len(PAGES_OUT), "flags:", len(seen))

if __name__ == "__main__":
    build()
