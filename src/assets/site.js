(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var BASE = document.documentElement.getAttribute("data-base") || "/";
  var CLEAN = document.documentElement.getAttribute("data-links") === "clean";
  function href(path) { return BASE + path + (CLEAN ? "" : "index.html"); }

  /* Hero: slow contour field, like survey lines over Texas land. */
  var cv = document.getElementById("contours");
  if (cv && cv.getContext) {
    var ctx = cv.getContext("2d"), w = 0, h = 0, t = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    var size = function () { w = cv.clientWidth; h = cv.clientHeight; cv.width = w * dpr; cv.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); };
    var draw = function () {
      ctx.clearRect(0, 0, w, h);
      var lines = 34, step = 14;
      for (var i = 0; i < lines; i++) {
        var base = (h / lines) * i + 20;
        ctx.beginPath();
        for (var x = 0; x <= w + step; x += step) {
          var y = base
            + Math.sin(x * 0.0042 + i * 0.21 + t) * 22
            + Math.sin(x * 0.0011 - i * 0.13 + t * 0.6) * 38
            + Math.cos(x * 0.0077 + i * 0.05 - t * 0.4) * 7;
          if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        var a = 0.05 + 0.10 * Math.pow(i / lines, 1.4);
        ctx.strokeStyle = i % 6 === 0 ? "rgba(140,195,160," + (a + 0.08) + ")" : "rgba(166,173,185," + a + ")";
        ctx.lineWidth = i % 6 === 0 ? 1.1 : 0.7;
        ctx.stroke();
      }
    };
    size(); draw();
    window.addEventListener("resize", function () { size(); draw(); });
    if (!reduce) {
      var loop = function () { t += 0.0022; draw(); requestAnimationFrame(loop); };
      requestAnimationFrame(loop);
    }
  }

  /* Mobile menu */
  var mb = document.querySelector(".menu-btn"), nv = document.getElementById("main-nav");
  if (mb && nv) mb.addEventListener("click", function () { var o = nv.classList.toggle("open"); mb.setAttribute("aria-expanded", String(o)); mb.textContent = o ? "Close" : "Menu"; });

  /* Formatting helpers */
  var money = function (n) { return "$" + Math.round(Math.max(0, n)).toLocaleString("en-US"); };
  var fmtDate = function (d) { return d.toLocaleDateString("en-US", { weekday: "short", month: "long", day: "numeric", year: "numeric" }); };
  var parseDate = function (v) { if (!v) return null; var p = v.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); };
  var addDays = function (d, n) { var x = new Date(d.getTime()); x.setDate(x.getDate() + n); return x; };
  var num = function (id) { var el = document.getElementById(id); var v = el ? parseFloat(String(el.value).replace(/[^0-9.]/g, "")) : 0; return isNaN(v) ? 0 : v; };
  var set = function (id, txt) { var el = document.getElementById(id); if (el) el.textContent = txt; };

  /* Days until 1/1/2027 */
  document.querySelectorAll("[data-qoz-days]").forEach(function (el) {
    var now = new Date(); var target = new Date(2027, 0, 1);
    el.textContent = String(Math.max(0, Math.ceil((target - now) / 86400000)));
  });

  /* Strategy builder */
  var sb = document.getElementById("builder");
  if (sb) {
    var state = { source: "re", timing: "now", accred: "yes" };
    var lib = {
      dst: ["1031 exchange into a DST", "Defer capital gains and depreciation recapture by moving into professionally managed real estate.", "alternatives/1031-exchange-dst/"],
      qoz: ["Qualified Opportunity Fund", "Defer a capital gain from almost any source and exclude growth on the fund after 10 years.", "alternatives/opportunity-zones/"],
      crt: ["Charitable remainder trust or donor-advised fund", "Turn appreciated assets into income or a deduction while supporting causes you care about.", "tax-strategies/charitable-giving/"],
      inst: ["Installment sale structuring", "Spread the gain across the years you are paid.", "who-we-serve/business-owners/"],
      cbp: ["Cash balance plan", "Deductible contributions well above 401(k) limits for owners and partners.", "tax-strategies/cash-balance-plans/"],
      energy: ["Energy working interests", "Intangible drilling costs are generally deductible in the year incurred.", "alternatives/energy/"],
      tlh: ["Tax-loss harvesting and diversification", "Offset gains with losses while reducing a concentrated position.", "portfolio-management/"],
      digital: ["Digital asset planning", "Allocation, custody and tax treatment for a Bitcoin or crypto position.", "alternatives/digital-assets/"],
      core: ["Core portfolio management", "A diversified, tax-aware portfolio built around your goals.", "portfolio-management/"]
    };
    var map = { re: ["dst", "qoz", "core"], biz: ["qoz", "inst", "crt", "cbp"], sec: ["qoz", "crt", "tlh", "digital"], inc: ["cbp", "energy", "crt"] };
    var altOnly = { dst: 1, qoz: 1, energy: 1 };
    var render = function () {
      sb.querySelectorAll(".choice").forEach(function (b) { b.setAttribute("aria-pressed", String(state[b.dataset.key] === b.dataset.val)); });
      var keys = map[state.source].slice(), notice = "";
      if (state.accred === "no") {
        keys = keys.filter(function (k) { return !altOnly[k]; });
        if (keys.indexOf("core") < 0) keys.push("core");
        notice = "DSTs, Opportunity Zone funds and energy programs are limited to accredited investors, so they are not shown.";
      } else if (state.accred === "unsure") {
        notice = "These strategies require accredited investor status. Read the definition or use the eligibility check.";
      }
      var out = document.getElementById("builder-results");
      out.innerHTML = "";
      keys.forEach(function (k) {
        var d = document.createElement("div"); d.className = "rec";
        var b = document.createElement("b"); b.textContent = lib[k][0];
        var s = document.createElement("span"); s.textContent = lib[k][1];
        var a = document.createElement("a"); a.href = href(lib[k][2]); a.textContent = "How it works";
        d.appendChild(b); d.appendChild(s); d.appendChild(a); out.appendChild(d);
      });
      var n = document.getElementById("builder-notice"); n.textContent = notice; n.hidden = !notice;
      var clock = "";
      if (state.accred !== "no" && state.timing === "now") {
        if (state.source === "re") clock = "Your 45-day identification window starts the day the sale closes. Talk to us before closing.";
        if (state.source === "biz" || state.source === "sec") clock = "A gain generally must be invested in an Opportunity Fund within 180 days of the sale.";
      }
      var c = document.getElementById("builder-clock"); c.textContent = clock; c.hidden = !clock;
    };
    sb.addEventListener("click", function (e) {
      var b = e.target.closest(".choice"); if (!b) return;
      state[b.dataset.key] = b.dataset.val; render();
    });
    render();
  }

  /* 1031 deadline calculator */
  var dl = document.getElementById("t1031");
  if (dl) {
    var run1031 = function () {
      var d = parseDate(document.getElementById("t1031-date").value);
      if (!d) return;
      var id45 = addDays(d, 45), close180 = addDays(d, 180);
      var due = new Date(d.getFullYear() + 1, 3, 15);
      var ext = document.getElementById("t1031-ext").checked;
      set("t1031-45", fmtDate(id45));
      var limit = close180, note = "You have the full 180 days.";
      if (!ext && due < close180) { limit = due; note = "Your tax return due date (April 15) comes first. File an extension to keep the full 180 days."; }
      set("t1031-180", fmtDate(limit));
      set("t1031-note", note + " Dates that fall on a weekend or holiday are not extended.");
    };
    dl.addEventListener("input", run1031); dl.addEventListener("change", run1031); run1031();
  }

  /* 1031 replacement calculator */
  var rc = document.getElementById("tboot");
  if (rc) {
    var runBoot = function () {
      var sale = num("tb-sale"), costs = num("tb-costs"), debt = num("tb-debt"), repl = num("tb-repl"), cashIn = num("tb-cash");
      var netSale = sale - costs, equity = netSale - debt;
      var newDebt = Math.max(0, repl - cashIn);
      var cashBoot = Math.max(0, equity - cashIn);
      var extraCash = Math.max(0, cashIn - equity);
      var mortBoot = Math.max(0, debt - newDebt - extraCash);
      set("tb-min", money(netSale)); set("tb-equity", money(equity)); set("tb-newdebt", money(newDebt));
      set("tb-boot", money(cashBoot + mortBoot));
      set("tb-note", (cashBoot + mortBoot) > 0
        ? "Estimated boot: " + money(cashBoot) + " cash kept and " + money(mortBoot) + " of debt not replaced. Boot is taxable to the extent of your gain."
        : "On these numbers, the exchange replaces all value, equity and debt.");
    };
    rc.addEventListener("input", runBoot); runBoot();
  }

  /* QOZ timing checker */
  var qz = document.getElementById("tqoz");
  if (qz) {
    var runQoz = function () {
      var d = parseDate(document.getElementById("tq-date").value); if (!d) return;
      var type = document.getElementById("tq-type").value;
      var end = addDays(d, 180);
      var newRules = new Date(2027, 0, 1);
      set("tq-end", fmtDate(end));
      var rule;
      if (end < newRules) rule = "Your whole window falls under the current rules. Under those rules, deferred gain is recognized by December 31, 2026, so the main remaining benefit is the 10-year exclusion.";
      else if (d >= newRules) rule = "Your window falls under the new rules: a five-year rolling deferral and a 10% basis step-up (30% for rural funds) after five years.";
      else rule = "Your window spans January 1, 2027. Investing on or after that date puts you under the new rules: a five-year rolling deferral and a 10% step-up after five years.";
      set("tq-rule", rule);
      set("tq-k1", type === "k1" ? "For gains reported on a K-1, the 180 days can also start on the last day of the partnership's tax year or on the partnership's return due date. Ask us which start date helps you most." : "");
    };
    qz.addEventListener("input", runQoz); qz.addEventListener("change", runQoz); runQoz();
  }

  /* Accredited investor check */
  var ac = document.getElementById("tai");
  if (ac) {
    var runAi = function () {
      var any = Array.prototype.some.call(ac.querySelectorAll("input[type=checkbox]"), function (c) { return c.checked; });
      set("tai-result", any ? "You likely meet the accredited investor definition." : "Based on these answers, you may not meet the definition yet.");
      set("tai-note", any ? "Each offering's sponsor verifies status before you invest. We can walk you through what they will ask for." : "Our portfolio management may still fit. Alternative strategies require accredited status.");
    };
    ac.addEventListener("change", runAi); runAi();
  }

  /* Glossary filter */
  var gq = document.getElementById("glossary-q");
  if (gq) {
    var items = document.querySelectorAll("#glossary-list a");
    var runQ = function () {
      var q = gq.value.trim().toLowerCase(), shown = 0;
      items.forEach(function (a) { var m = !q || a.textContent.toLowerCase().indexOf(q) >= 0; a.hidden = !m; if (m) shown++; });
      set("glossary-count", shown + " of " + items.length + " terms");
    };
    gq.addEventListener("input", runQ); runQ();
  }

  /* Contact form */
  var cf = document.getElementById("contact-form");
  if (cf) {
    cf.addEventListener("submit", function (e) {
      var msg = document.getElementById("contact-status");
      if (!cf.checkValidity()) { e.preventDefault(); msg.textContent = "Please fill in your name, email and the reason for your call."; cf.reportValidity(); return; }
      if (cf.getAttribute("data-preview") === "1") {
        e.preventDefault();
        msg.textContent = "Preview only. At launch this form will send your request to Jeff and Denver by email.";
      }
    });
  }
})();
