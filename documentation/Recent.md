Design ta dekhe mone hocche dark theme, teal accent, card layout niye ekta solid foundation ache. Kintu kichu jaygay polish dorkar. Screenshot dhore dhore bolchi.

1. Text size ar readability (sobcheye boro issue)

Onek label ar helper text khub choto (8-10px mone hocche), dark background e grey text, contrast kom. “Settlement locked”, “Ext. net P/L”, table header gulo porte kosto hoy.
Fix: minimum body text 12px, secondary text 11px. Muted grey ke ektu light koro, WCAG AA (4.5:1) contrast target koro.

2. Layout ar space use

Screen 1 e Chat panel (right side) onek jayga nei kintu majhe ta khali, shudhu ekta intro text. Main content er jayga kombe jachche. Chat panel collapsible ache, kintu default e ektu narrow rakho (jemon 320px) ar chat shuru hole expand koro.
Screen 2 e Market Map heatmap ta cut hoye geche, ar upore Watchlist ar Position Inspector er majhe onek vertical gap. Heatmap ke alada tab/page e nile better.
Screen 4 (Settings) e API key section er input gulo ar toggle tight, “Master Buy/Sell Automation” er pashe ekta extra faka toggle dekha jachche (ekta bug mone hoy).

3. Color ar semantic consistency

Teal dhoroner accent onek jaygay: buttons, active states, positive P/L, “Active Buy” badge. Sob ek rong hole meaning haray. Positive profit er jonno green, brand/active er jonno teal, alada kore dao.
Screen 1 e “Est. Unrealized Net P/L” red ar “Realized P/L” teal, ei pair ta ektu confusing. Profit/loss er jonno same green/red pair use koro sob jaygay.
Screen 3 e SELL badge ar BUY badge duto-i green, buy/sell alada hobe (jemon BUY green, SELL red/amber).

4. Hierarchy

Screen 1 e 4ta metric card equal weight. Net Liquidation Equity highlight kora ache, bhalo. Kintu number gulor size aro boro hole dashboard glance e pora jabe.
“Decision stream” e symbol, badge, reason er hierarchy weak. Symbol bold, badge color-coded (blocked = red, wait = grey, buy = green) korle scan kora shohoj hobe.
Section heading er pashe “.” (jemon “Portfolio overview.”) stylish, kintu sob page e consistent ache, eta thik. Tobe subtitle gulo onek halka.

5. Charts

Watchlist pulse chart e Support/Resistance label gulo line er upor overlap kore. Label ke chart er kone te ba legend e nao.
Y axis label (₹104.5, ₹100.0) ar x axis date khub halka. Gridline o subtle, thik ache, kintu axis text ektu bold koro.
Currency symbol ₺ dekhacche (Turkish Lira jeno) BDT er jaygay. Mone hocche font fallback issue, ₺ er bodole "৳" use koro.

6. Table (Trade ledger, Company watchlist)

Column gulo onek wide spaced, number right-aligned korle compare kora shohoj. Price, Fee, Net Realized sob right-align koro, ar monospace/tabular-nums use koro.
Row hover state ar zebra striping halka kore dile onek better.
Sticky header dao, long table e scroll korle header hariye jay.

7. Settings page

“Primary Reasoning Model (Tier 1)” dropdown khali dekhacche, selected value nei, ekta bug ba missing default.
API key masked field e visible/hide eye icon ache, bhalo. Telegram Bot Token er placeholder asol value moto dekhacche (bot123456:••••), placeholder ke clearly alada koro (italic/lighter).
Section gulor majhe “Save” button shudhu ekta card e, user bujhbe na onno section (polling interval, toggle) auto-save na manual. Ekta clear save indicator dao.

8. Chat panel (Hermes)

Intro text center-aligned ar onek spacing, “Bangla, Banglish, or English” line ta orphan hoye ache. Quick action chips (Portfolio status, Alert bankruptcy threat) khub choto, boro koro.
Markdown (“### Status Report”) raw dekhacche screen 5 e, ekhane heading render hoyni. Eta ekta rendering bug, markdown renderer fix korte hobe.
“Served via 1st Fallback” notice ta bhalo transparency, kintu style ta ektu aro subtle koro.

9. Navigation

Left sidebar e icon shudhu, label nei. Hover tooltip ache kina check koro, na thakle add koro. Notun user er jonno icon gulo vague.
“DSE CLOSED” status pill ar “Next: 58h 30m 4s” top bar e bhalo, kintu top bar e onek gulo control (Background Polling, Pause engine, Run cycle, Dark) ekdom crowded. Secondary control gulo overflow menu te nao.

10. Misc

Light mode e switch korle sob chart ar badge thik thake kina test koro, dark theme e heavily tuned mone hocche.
Empty/closed market state e (DSE closed) clear messaging dao ki hocche ar kokhon abar shuru hobe.

Priority order amar hishebe: (1) text size/contrast, (2) ₺ currency symbol fix, (3) markdown rendering bug, (4) empty dropdown bug, (5) buy/sell color separation, (6) top bar declutter.|


# Humming Bird: UI/UX polish and bug fix pass

You are working on the Humming Bird trading cockpit (FastAPI backend, vanilla JS frontend, `frontend/index.html`, `frontend/styles.css`, `frontend/theme_light_hermes.css`, `frontend/app.js`, `frontend/charts.js`, `frontend/hermes_ui.js`). Read `documentation/About_Project.md`, `documentation/Backlog.md` and `documentation/CODEBASE_MAP.md` first. Line numbers below come from CODEBASE_MAP and may have drifted, so locate code by function name or selector with grep.

I reviewed 5 screens (Overview, Watchlist + Market Map, Strategy + Ledger, Settings, Hermes chat panel) in dark theme. Below is everything I want fixed, grouped in phases. Work phase by phase.

---

## 0. Ground rules (strict)

1. **Surgical edits only.** No full file rewrites, no refactors, no moving code between files. Use small targeted replacements. Do not rename or remove any existing element ID, CSS class or function that JS or tests reference (index.html has 233 IDs).
2. **Do not touch** `backend/engine/*`, `money.py`, `t2_ledger.py`, ledger math, DB schema, or trading rules. Backend edits are allowed only where a bug item below says so (B1, B5, B6, B7).
3. **Both themes.** Every visual change must work in dark (`:root`) and light (`[data-theme="light"]`). Add or change design tokens in both places. Do not add hardcoded hex values inside component rules. Do not add new `!important`.
4. **Code comments:** short English, one line, only where needed.
5. **UI copy:** do not use em dashes or en dashes in any text you add to the UI or to chat strings.
6. **VERIFY items:** where an item says VERIFY, first inspect the code, reproduce the issue, and report whether it is real. Do not "fix" something that is not actually broken. If my diagnosis is wrong, say so and propose the right fix.
7. After each phase run the full test suite (`pytest`). Keep it green. Do not skip or weaken tests.
8. Keep Bangla/Banglish/English chat behavior unchanged.

---

## Phase 1: Bugs

- [x] **B1. Empty "Primary Reasoning Model (Tier 1)" dropdown (Settings).**
The select renders blank even though the chain below shows `xiaomi/mimo-v2-flash` as ACTIVE.
Look at `loadHermesModels()` in `hermes_ui.js` (~L423), `switchHermesModel()` (~L481) and `GET /api/hermes/models` in `routes_hermes.py` (`hermes_models`, ~L130).
Fix: populate options from the endpoint, preselect the active model, and if the active model is not in the list add it as an option. If the fetch fails show a small inline error and a disabled "Models unavailable" option. After a change, the Settings select and the Hermes header/composer drop-up must show the same model.

- [x] **B2. Markdown headings show raw in Hermes chat.**
Chat shows literal `### Status Report` and `### Watchlist Analysis`. Look at `formatChatMarkdown()` in `hermes_ui.js` (~L52).
Fix: support `#`, `##`, `###` headings in addition to what already works (bold, inline code, bullets). Escape HTML first with the existing `escapeHtml()` so model output can never inject markup. Render headings as a `.chat-h` element (13px, weight 600, small top margin) styled in both themes.
Also tighten list spacing: bullets currently have a very large gap between items. Target about 4px between bullets and 12px between blocks.

- [x] **B3. Extra toggle next to "Master Buy/Sell Automation" (Settings).**
There is a second small pill toggle to the right of the green ON switch. VERIFY in `index.html` near `#master-automation-toggle`. If it is a leftover or duplicate element, remove it. If it has a purpose, give it a label and wire it. Report which.

- [x] **B4. Currency symbol looks like Turkish lira.**
Amounts render with a glyph that looks like `₺` at small size. VERIFY first: check what `currency()` in `app.js` (~L59) actually emits. It may already be the correct Bengali taka sign `৳` (U+09F3) and the problem is only the font rendering it. Check the emitted code point and which font draws it.
Fix: make sure U+09F3 is emitted everywhere (grep for `₺`, U+20BA and any `Intl.NumberFormat` currency usage). Add a Bengali capable fallback to the numeric font stack (for example `"Noto Sans Bengali", "Nirmala UI", "Kalpurush"` after the main UI font). Wrap the symbol in `<span class="cur">` with a minimum 12px size and normal weight so it stays legible.
Consistency: UI uses `৳` as prefix. Chat summaries and the settings card use "BDT" as suffix. Keep `৳` prefix in all UI numbers, and keep "BDT" only on the small badge in the Net Liquidation Equity card and in the Initial Paper Capital row.

- [x] **B5. Daily external AI call counter is inconsistent.**
Settings shows `7 / 30 calls used` in one place and `0 / 30 calls used` in another (in the AI Copilot card, after Hermes answered through the Gemini fallback).
VERIFY in `routes_auth_settings.py` (`get_api_keys`, ~L83), `agent_loop.py` (`_conversational_inference`, ChatBudget usage) and the frontend code that fills both labels. Check: do both UI spots read the same field, do Gemini fallback calls increment `ChatBudget`, and does the label refresh after each chat turn.
Fix: one source of truth, increment on every external call (any tier except local), refresh both labels after each chat turn (refetch or SSE).

- [x] **B6. Wrong provider label on chat replies.**
A reply is labeled `OPENROUTER` in the message header while the notice above says `Served via 1st Fallback: Google Gemini API (gemini-3.1-flash-lite)`. The composer footer also says `OPENROUTER · mimo-v2-flash`.
Fix: the chat response should carry `served_by: {tier, provider, model}` (add it in `agent_loop.py` `_conversational_inference` and pass it through `ChatService.respond`). The frontend uses it for the message header label. When a fallback was used, the notice should include a short reason (quota, timeout, auth). The composer footer keeps showing the selected Tier 1 model, but add a tooltip "Last reply served by: ...".

- [x] **B7. Hermes text contradicts the UI (VERIFY).**
- Hermes said BXPHARMA has a "35.56% session drop", but the watchlist Day column shows BXPHARMA +0.80%. VERIFY whether 35.56% is a multi-session peak to latest drop from `curve_analyzer.py`. If yes, change wording everywhere it is generated (`chat.py` `local_summary`, `tools_dispatcher.py` formatters, the LLM context snapshot) to say "35.56% drop over N sessions" and show the same number in a tooltip on the CRASH GUARD pill.
- Hermes said BANKASIA is "nearing support (19.80)" while the price is 19.64, which is already below 19.80. Fix the wording logic: below support, at support, near support (within 1%), above.

- [x] **B8. Overview chart labels overlap the price line.**
In "Watchlist pulse", the `RESISTANCE` and `SUPPORT` text sits on top of the curve near the right edge. Move these labels into small tags outside the plot area on the right edge (reserve about 64px right padding in `renderMainChart()` in `charts.js`), not on the line. Keep dashed lines. Also fix the header: `92.44 -7.56%` in red next to a legend that wraps. Put the legend in one row below the value.

- [x] **B9. Market map small tiles are unreadable.**
Tiles like MUNABANI, UBALIBAN, TRUSTBANK clip or overlap their labels. In `renderMarketMap()` (`charts.js`, ~L473): hide percent and turnover text when a tile is smaller than about 56x34px, hide the symbol too when smaller than about 36x22px (tooltip still works). Use a `ResizeObserver` so it re-lays out when the Hermes panel width changes.
Color: the 0% bucket is blue, which reads like a positive or special state. Make 0% neutral slate (use a token), keep green and red scale for +/-. Update the legend to match.

- [x] **B10. Telegram placeholders look like real values.**
`bot123456:••••` and `@channel / 123456` look filled in. Make them real placeholders: italic, `--dim` color, text like `123456789:ABC... (optional)`. Also confirm the field is empty when no token is saved.

- [x] **B11. Save and auto-save are unclear (Settings).**
Only "Save API Configuration" is a manual save. The master toggle, ingestion mode tiles, and polling interval save immediately through `/api/automation/config`. Users cannot tell which is which.
Fix: add a tiny "Auto-saved" tag next to the master toggle, ingestion tiles and polling interval header. For the API card: keep Save disabled until a field changes, show "Unsaved changes" next to it when dirty, and show a green "Saved" check for 2 seconds after success. Show an inline error if it fails.

---

## Phase 2: Readability

Measured contrast in dark theme: `--dim #586b80` on panel `#101822` is only **3.26:1** (fails WCAG AA 4.5:1). `--muted #8393a6` is 5.69:1 but is used at very small sizes.

- [x] **2.1. Raise tokens in dark theme:** `--dim` to about `#8393a6` (5.69:1) and `--muted` to about `#9aabbd` (7.6:1). Recheck light theme values and make sure both pass 4.5:1 for body text.
- [x] **2.2. Add a type scale in `:root`:** `--fs-xs: 11px; --fs-sm: 12px; --fs-md: 13px; --fs-lg: 14px;`. Grep `styles.css` and `theme_light_hermes.css` for every `font-size` below 11px (8px, 9px, 10px, and tiny rem values) and map them to the scale. Nothing visible should be smaller than 11px. Uppercase eyebrow labels keep their letter spacing but follow the same minimum. Table headers, bucket captions ("SETTLED CASH"), badges, tab counters, chat footer text ("External AI used demo portfolio context") and quick action chips are the worst offenders.
- [x] **2.3. Add `font-variant-numeric: tabular-nums`** to all numeric UI: metric cards, tables, ledger, bucket amounts, chart axis text, clock and countdown.
- [x] **2.4. Metric cards on Overview:** hero number (Net Liquidation Equity) to about 30px, the other three to 24px, with the small caption lines at 12px and `--muted`.
- [x] **2.5. Chart axis text (y values and dates)** to 11px `--muted`, slightly heavier weight than now.
- [x] **2.6. Subtitles under page headings** ("A clear view. A measured next move.", "Live 3-tier company tracking...") to 13px `--muted`.

---

## Phase 3: Semantic color system

Problem: teal is used for brand, active state, primary buttons, positive P/L, BUY badges and BUY ZONE. Meaning is lost. Also Realized P/L is teal while Unrealized is red.

- [x] **3.1. Add tokens (dark and light):** `--green` (profit, up), `--red` (loss, down), `--brand` (teal, UI accent only), `--amber` (warning, locked, waiting), `--buy` (blue, order side BUY), `--sell` (amber, order side SELL), plus a `-bg` variant for each. Pick values by computing contrast against panel backgrounds (4.5:1 for text).
- [x] **3.2. Rule: green and red are only for money direction.** Positive P/L, up percentages and up sparklines use `--green`. Negative use `--red`. Teal stays for brand: active nav item, primary buttons, focus ring, selected row accent, active bucket, toggles.
- [x] **3.3. Apply to: Realized P/L card** (currently teal, make green), Est. Unrealized (red when negative), Net Return in what-if, ledger Net Realized column, watchlist Day column, sparklines (color by direction), Position Inspector values, chart header change.
- [x] **3.4. Order side badges (Strategy/Ledger):** BUY uses `--buy` (blue), SELL uses `--sell` (amber). Reason: sells in this strategy are profit locks, so a red SELL would read as a loss. P/L numbers carry the green/red meaning. Use the same tokens for the B and S markers on charts and the chart legend.
- [x] **3.5. Decision stream badges:** BUY (buy blue), BUY BLOCKED (red), WAIT NO CHURN and WAIT BUDGET (neutral grey), SETTLEMENT LOCK (amber). Curve signal pills in the watchlist: BUY ZONE (buy blue), MID RANGE (grey), SELL ZONE (amber), CRASH GUARD (red).
- [x] **3.6. Light theme: confirm all of the above** look right and pass contrast. No leftover dark backgrounds.

---

## Phase 4: Per screen fixes

**Global / top bar**
- [ ] **4.1. Top bar declutter:** Group into: [status pill + countdown] | [Background Polling / Onscreen Live segmented] | [Pause engine icon button + Run automation cycle primary] | [theme toggle]. Pause engine becomes an icon button with tooltip. Below 1280px collapse the segmented control into a compact version, below 1100px move secondary controls into an overflow menu. Use media queries on the existing `.topbar` rules, do not restructure the DOM beyond what is needed.
- [ ] **4.2. DSE CLOSED pill & Run cycle tooltips:** "DSE opens Sun 10:00 (Asia/Dhaka)" computed from the scheduler status that already exists. The Run automation cycle button gets a tooltip "Market closed: runs on demo data" when closed.
- [ ] **4.3. Left nav rail tooltips & active indicator:** on hover and keyboard focus (CSS tooltip, plus `aria-label`), a 3px active indicator bar on the left edge, and `:focus-visible` rings. Labels: Overview, Watchlist, Strategy, Ledger, Settings.
- [ ] **4.4. Global focus-visible ring & reduced motion:** using `--brand` for buttons, inputs, tabs, table rows that are clickable. Add `@media (prefers-reduced-motion: reduce)` to cut animations and transitions.
- [ ] **4.5. Skeleton placeholders:** for metric cards, tables and charts until the first `/api/portfolio` response, so zeros do not flash.

**Screen 1: Overview**
- [ ] **4.6. Overview Metric cards styling:** Keep the highlighted Net Liquidation card.
- [ ] **4.7. Rolling capital progress bar:** per bucket showing locked vs settled share if the data is in the snapshot (do not add backend fields). Caption text 12px.
- [ ] **4.8. Decision stream hierarchy:** badge next to it, reason line 12px `--muted`, timestamp right aligned and 11px. Increase row padding slightly. Keep the internal scroll.

**Screen 2: Watchlist and Market Map**
- [ ] **4.9. Watchlist table alignment & sticky header:** Price, Day, Held/Mature, Buy Cap. Left align text. Sticky `thead`. Subtle row hover. Keep the selected row accent. Sparkline colors by direction (Phase 3).
- [ ] **4.10. Position Inspector spacing & alignment:** and Position Inspector to 16px. In Position Inspector align the three stat blocks on a grid and right align the lot table numbers.
- [ ] **4.11. Market map polish (B9):**

**Screen 3: Strategy rules and Trade ledger**
- [ ] **4.12. What-if simulator breakeven marker:** Add a visible breakeven marker at +1.005% on the slider track with a small label. Keep existing calculation.
- [ ] **4.13. Company Rules card layout & toggle:** `%` suffix inside the input, Apply button aligned right, "Automation enabled" checkbox converted to the same toggle component used in Settings. Profit tier chips at least 11px.
- [ ] **4.14. Trade ledger alignment & sticky header:** PRICE, FEE, NET REALIZED. Net Realized uses green/red by sign, "no value" rows show a muted dash. Sticky header. Zebra striping very subtle (about 2 to 3% lighter) or hover only. SIDE badges per Phase 3.

**Screen 4: Settings**
- [ ] **4.15. Settings cards equal height & spacing:** and consistent inner spacing (use one spacing unit, 12px between a label and its input, 20px between groups).
- [ ] **4.16. Settings API card badge alignment & gaps:** sits on the label row, aligned right, never overlapping the input. Add a 16px gap above the Daily External AI Call Limit block and above the Save button (they currently touch the inputs above).
- [ ] **4.17. Polling interval disabled state in Method B:** (Onscreen Live) is active, show it in a clearly disabled state (reduced opacity, `aria-disabled`, helper text "Used only in Method A"). Do not hide it.
- [ ] **4.18. StockNow Bridge spinner & toast feedback:** and disabled state while the request is running, then a toast with the result. Make "Sync Humming Bird Portfolio" visually the primary one, others secondary.

**Screen 5: Hermes chat panel**
- [ ] **4.19. Hermes empty state & chips placement:** merge the orphan "Bangla, Banglish, or English" line into the intro paragraph, remove the large empty gaps, and show the quick action chips directly under the intro while the conversation is empty. Once messages exist, chips return to the composer area.
- [ ] **4.20. Hermes chips typography:** 6px by 10px padding, keep teal hover.
- [ ] **4.21. Hermes tab counters contrast:** at least 11px with readable badge contrast.
- [ ] **4.22. Hermes composer footer model caret:** and hover state so it looks clickable (it opens the drop-up).
- [ ] **4.23. Hermes message typography:** line-height 1.5, assistant text full width.
- [ ] **4.24. Hermes fallback notice styling:** subtle amber outline, with the reason (B6).

---

## Phase 5: Small extras (only after phases 1 to 4 pass)

- [ ] **5.1. 7-session sparkline in Net Liquidation Equity card:** the Net Liquidation Equity card using data already in the snapshot.
- [ ] **5.2. Filter chips on Decision stream:** (All, Buys, Sells, Blocked, Locks), client side only.
- [ ] **5.3. Copy button on Hermes replies:** (skip per spec) or number heavy Hermes replies is NOT required. Skip anything that needs new backend fields.

---

## Phase 6: Verification and report

1. Run `pytest`. Add small tests for: `GET /api/hermes/models` includes the active model; chat response contains `served_by`; the daily call counter increments on a fallback call; `formatChatMarkdown` heading handling if there is an existing JS test setup (otherwise skip).
2. Manual check at widths 1024, 1280, 1440, 1920, in dark and light, on all 5 views. No horizontal page scroll. Wide tables scroll inside their own container. Take screenshots if a browser tool is available.
3. Regenerate the map: `python scripts/generate_code_map.py`.
4. Add a "Sprint 2.6: UI polish and bug fixes" section to `documentation/Backlog.md` with a checkbox list of what was done.
5. Final report as a table: ID, status (fixed / not reproducible / partial / skipped), files and approximate line ranges touched, one line on what changed. For every VERIFY item state clearly what you found. List anything you skipped and why.