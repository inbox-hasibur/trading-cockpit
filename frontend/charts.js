"use strict";

// ==========================================================================
// Project Humming Bird · Charts & Visualizations Engine
// SVG rendering, squarified treemaps, sector gainers, and deep curve trends.
// ==========================================================================

function smoothCurvePath(points) {
  if (!points || points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
  if (points.length === 2) {
    return `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)} L ${points[1].x.toFixed(2)},${points[1].y.toFixed(2)}`;
  }
  let d = `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2 < points.length ? i + 2 : points.length - 1];

    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;

    d += ` C ${cp1x.toFixed(2)},${cp1y.toFixed(2)} ${cp2x.toFixed(2)},${cp2y.toFixed(2)} ${p2.x.toFixed(2)},${p2.y.toFixed(2)}`;
  }
  return d;
}

function getBezierPointAtContinuousIndex(coords, continuousIdx) {
  if (!coords || coords.length === 0) return { x: 0, y: 0 };
  if (coords.length === 1) return coords[0];
  if (continuousIdx <= 0) return coords[0];
  if (continuousIdx >= coords.length - 1) return coords[coords.length - 1];

  const i0 = Math.floor(continuousIdx);
  const i1 = i0 + 1;
  const u = continuousIdx - i0;

  const p0 = coords[i0 === 0 ? 0 : i0 - 1];
  const p1 = coords[i0];
  const p2 = coords[i1];
  const p3 = coords[i1 + 1 < coords.length ? i1 + 1 : coords.length - 1];

  const cp1x = p1.x + (p2.x - p0.x) / 6;
  const cp1y = p1.y + (p2.y - p0.y) / 6;
  const cp2x = p2.x - (p3.x - p1.x) / 6;
  const cp2y = p2.y - (p3.y - p1.y) / 6;

  const u1 = 1 - u;
  const c0 = u1 * u1 * u1;
  const c1 = 3 * u1 * u1 * u;
  const c2 = 3 * u1 * u * u;
  const c3 = u * u * u;

  return {
    x: c0 * p1.x + c1 * cp1x + c2 * cp2x + c3 * p2.x,
    y: c0 * p1.y + c1 * cp1y + c2 * cp2y + c3 * p2.y,
  };
}

function renderMainChart() {
  const points = state.snapshot.normalized_curve;
  if (!points || points.length < 2) {
    $("main-chart").replaceChildren(element("span", "muted", "Insufficient valid history to chart."));
    return;
  }
  const allTrades = state.snapshot.trades || [];
  setText("curve-sessions", `${points.length} sessions`);
  const last = points[points.length - 1].value;
  setText("index-value", last.toFixed(2));
  const change = (last / points[0].value - 1) * 100;
  setText("index-change", percentage(change));
  $("index-change").classList.toggle("positive", change >= 0);
  $("index-change").classList.toggle("negative", change < 0);

  const values = points.map((point) => point.value);
  const support = Math.min(...values);
  const resistance = Math.max(...values);
  const buyCeiling = support + (resistance - support) * 0.25;

  if ($("pulse-support-val")) setText("pulse-support-val", `৳${support.toFixed(2)}`);
  if ($("pulse-resistance-val")) setText("pulse-resistance-val", `৳${resistance.toFixed(2)}`);

  const width = 700, height = 180, left = 45, padRight = 72, top = 16, bottom = 26;
  const chartW = width - left - padRight;
  const chartH = height - top - bottom;
  const minVal = Math.min(...values) * 0.985;
  const maxVal = Math.max(...values) * 1.015;
  const range = maxVal - minVal || 1;

  const x = (i) => left + (i / (points.length - 1)) * chartW;
  const y = (val) => top + ((maxVal - val) / range) * chartH;

  const svg = svgElement("svg", {
    viewBox: `0 0 ${width} ${height}`,
    preserveAspectRatio: "none",
    class: "main-trend-svg",
    role: "img",
    "aria-label": "Normalized watchlist price index with support, resistance, and executed orders",
  });

  const defs = svgElement("defs");
  const gradient = svgElement("linearGradient", { id: "chart-gradient", x1: "0", x2: "0", y1: "0", y2: "1" });
  gradient.append(
    svgElement("stop", { offset: "0%", "stop-color": "#5de4c7", "stop-opacity": "0.22" }),
    svgElement("stop", { offset: "100%", "stop-color": "#5de4c7", "stop-opacity": "0" })
  );
  defs.append(gradient);
  svg.append(defs);

  // Background Gridlines
  for (let step = 0; step <= 3; step++) {
    const val = minVal + (range * step) / 3;
    const yPos = y(val);
    svg.append(svgElement("line", {
      x1: left,
      y1: yPos,
      x2: left + chartW,
      y2: yPos,
      stroke: "var(--chart-grid, #23303c)",
      "stroke-width": 0.8,
      "stroke-dasharray": "2 3",
    }));
    const lbl = svgElement("text", {
      x: left - 8,
      y: yPos + 3,
      "text-anchor": "end",
      fill: "var(--muted, #63768b)",
      "font-size": 9,
    });
    lbl.textContent = `৳${val.toFixed(1)}`;
    svg.append(lbl);
  }

  // Shaded Buy Zone band: [support, buyCeiling]
  if (buyCeiling > support) {
    const yTop = Math.min(y(support), y(buyCeiling));
    const bandH = Math.abs(y(support) - y(buyCeiling));
    svg.append(svgElement("rect", {
      x: left,
      y: yTop,
      width: chartW,
      height: bandH,
      fill: "rgba(34, 197, 94, 0.08)",
      stroke: "none",
    }));
  }

  // Horizontal Support line (dashed green) with tag in right gutter
  svg.append(svgElement("line", {
    x1: left,
    y1: y(support),
    x2: left + chartW,
    y2: y(support),
    stroke: "#22c55e",
    "stroke-width": 1.5,
    "stroke-dasharray": "4 4",
  }));
  const supLbl = svgElement("text", {
    x: left + chartW + 6,
    y: y(support) + 3,
    "text-anchor": "start",
    fill: "#22c55e",
    "font-size": 8.5,
    "font-weight": 700,
  });
  supLbl.textContent = `SUP ৳${support.toFixed(1)}`;
  svg.append(supLbl);

  // Horizontal Resistance line (dashed red) with tag in right gutter
  svg.append(svgElement("line", {
    x1: left,
    y1: y(resistance),
    x2: left + chartW,
    y2: y(resistance),
    stroke: "#ef4444",
    "stroke-width": 1.5,
    "stroke-dasharray": "4 4",
  }));
  const resLbl = svgElement("text", {
    x: left + chartW + 6,
    y: y(resistance) + 3,
    "text-anchor": "start",
    fill: "#ef4444",
    "font-size": 8.5,
    "font-weight": 700,
  });
  resLbl.textContent = `RES ৳${resistance.toFixed(1)}`;
  svg.append(resLbl);

  // Price Area & Line with smooth cubic bezier curve
  const coords = points.map((pt, i) => ({ x: x(i), y: y(pt.value) }));
  const smoothPath = smoothCurvePath(coords);
  svg.append(svgElement("path", {
    d: `${smoothPath} L${x(points.length - 1).toFixed(1)},${(top + chartH).toFixed(1)} L${left},${(top + chartH).toFixed(1)} Z`,
    fill: "url(#chart-gradient)",
  }));
  svg.append(svgElement("path", {
    d: smoothPath,
    fill: "none",
    stroke: "var(--teal, #5de4c7)",
    "stroke-width": 2.2,
  }));

  // X Axis Session Dates
  const sampleIndices = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])];
  sampleIndices.forEach((idx) => {
    const xPos = x(idx);
    const dateLbl = svgElement("text", {
      x: xPos,
      y: height - 5,
      "text-anchor": idx === 0 ? "start" : idx === points.length - 1 ? "end" : "middle",
      fill: "var(--muted, #63768b)",
      "font-size": 9,
    });
    dateLbl.textContent = sessionDate(points[idx].date, true);
    svg.append(dateLbl);
  });

  // Latest Point Marker (visible when not hovering, matching Image 2 Bank Asia modal style)
  const endpointDot = svgElement("circle", {
    cx: x(points.length - 1),
    cy: y(last),
    r: 4.5,
    class: "chart-crosshair-point",
    style: "display:block;",
  });
  svg.append(endpointDot);

  // Interactive Crosshair Elements with 1:1 SVG coordinate tracking
  const crosshairV = svgElement("line", { x1: 0, y1: top, x2: 0, y2: top + chartH, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairH = svgElement("line", { x1: left, y1: 0, x2: left + chartW, y2: 0, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairDot = svgElement("circle", { cx: 0, cy: 0, r: 4.5, class: "chart-crosshair-point", style: "display:none;" });
  svg.append(crosshairV, crosshairH, crosshairDot);

  // Mouse overlay rect for continuous TradingView-style hover tracking
  const overlay = svgElement("rect", {
    x: left,
    y: top,
    width: chartW,
    height: chartH,
    fill: "transparent",
    style: "cursor: crosshair;",
  });

  overlay.addEventListener("mousemove", (e) => {
    const chartContainer = $("main-chart");
    if (!chartContainer) return;

    let svgX = 0;
    const ctm = svg.getScreenCTM();
    if (ctm) {
      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const inv = ctm.inverse();
      const p = pt.matrixTransform(inv);
      svgX = p.x;
    } else {
      const svgRect = svg.getBoundingClientRect();
      svgX = ((e.clientX - svgRect.left) / (svgRect.width || 1)) * width;
    }

    // Strictly clamp svgX within curve bounds [left, left + chartW]
    const clampedX = Math.max(left, Math.min(left + chartW, svgX));
    const normX = clampedX - left;
    const t = chartW > 0 ? normX / chartW : 0;
    const continuousIdx = t * (points.length - 1);

    // Exact Bezier curve point evaluation
    const curvePt = getBezierPointAtContinuousIndex(coords, continuousIdx);
    const ptX = clampedX;
    const ptY = curvePt.y;

    crosshairV.setAttribute("x1", ptX);
    crosshairV.setAttribute("x2", ptX);
    crosshairV.style.display = "block";

    crosshairH.setAttribute("y1", ptY);
    crosshairH.setAttribute("y2", ptY);
    crosshairH.style.display = "block";

    crosshairDot.setAttribute("cx", ptX);
    crosshairDot.setAttribute("cy", ptY);
    crosshairDot.style.display = "block";
    endpointDot.style.display = "none";

    const closestIdx = Math.min(points.length - 1, Math.max(0, Math.round(continuousIdx)));
    const pt = points[closestIdx];

    const interpolatedVal = maxVal - ((ptY - top) / chartH) * range;
    const chgFromBase = ((interpolatedVal / points[0].value - 1) * 100);
    const dateTrades = allTrades.filter((tr) => tr.date === pt.date || tr.trade_on === pt.date);
    let tradeNote = "";
    if (dateTrades.length) {
      tradeNote = `<div style="margin-top:4px;border-top:1px solid var(--soft-line);padding-top:3px;">
        ${dateTrades.map((tr) => `<strong style="color:${tr.side === "BUY" ? "#22c55e" : "#ef4444"}">${tr.side}</strong> ${tr.symbol} ${tr.quantity} qty @ ৳${tr.price}`).join("<br>")}
      </div>`;
    }

    const tooltip = $("main-chart-tooltip");
    if (tooltip) {
      tooltip.innerHTML = `
        <div style="font-weight:700;color:var(--teal);">${sessionDate(pt.date)}</div>
        <div style="font-size:11px;font-weight:600;margin-top:2px;">Rebased: ৳${interpolatedVal.toFixed(2)} (${chgFromBase >= 0 ? "+" : ""}${chgFromBase.toFixed(2)}%)</div>
        ${tradeNote}
      `;
      tooltip.hidden = false;

      const wrap = tooltip.offsetParent || chartContainer;
      const wrapRect = wrap.getBoundingClientRect();
      let screenX, screenY;
      if (ctm) {
        const pSvg = svg.createSVGPoint();
        pSvg.x = ptX;
        pSvg.y = ptY;
        const pScreen = pSvg.matrixTransform(ctm);
        screenX = pScreen.x - wrapRect.left;
        screenY = pScreen.y - wrapRect.top;
      } else {
        const svgRect = svg.getBoundingClientRect();
        screenX = svgRect.left + (ptX / width) * svgRect.width - wrapRect.left;
        screenY = svgRect.top + (ptY / height) * svgRect.height - wrapRect.top;
      }

      tooltip.style.left = `${Math.min(wrapRect.width - 100, Math.max(100, screenX))}px`;
      tooltip.style.top = `${Math.max(20, screenY - 10)}px`;
    }
  });

  overlay.addEventListener("mouseleave", () => {
    crosshairV.style.display = "none";
    crosshairH.style.display = "none";
    crosshairDot.style.display = "none";
    endpointDot.style.display = "block";
    const tooltip = $("main-chart-tooltip");
    if (tooltip) tooltip.hidden = true;
  });

  svg.append(overlay);
  $("main-chart").replaceChildren(svg);
}

function sparkline(history) {
  const values = history.map((point) => Number(point.close));
  if (values.length < 2 || values.some((value) => !Number.isFinite(value) || value <= 0)) return element("span", "muted small", "Invalid data");
  const low = Math.min(...values), high = Math.max(...values);
  const coords = values.map((val, i) => ({
    x: 2 + (i / (values.length - 1)) * 92,
    y: 25 - ((val - low) / (high - low || 1)) * 22,
  }));
  const path = smoothCurvePath(coords);
  const svg = svgElement("svg", { viewBox: "0 0 96 28", class: "sparkline", role: "img", "aria-label": "Synthetic recent price curve" });
  svg.append(svgElement("path", { d: path, class: values[values.length - 1] >= values[0] ? "spark-up" : "spark-down", fill: "none" }));
  return svg;
}

// --- DSE Market Map & Squarified Treemap Layout ---
function squarify(children, rect) {
  if (!children || !children.length || rect.w <= 0 || rect.h <= 0) return [];
  const total = children.reduce((acc, c) => acc + Math.max(0.01, Number(c.turnover_cr) || 0.01), 0);
  if (total <= 0) return [];

  const scale = (rect.w * rect.h) / total;
  const values = children.map((c) => Math.max(0.01, (Number(c.turnover_cr) || 0.01) * scale));

  const results = [];

  function layoutRow(row, rowValues, currentRect) {
    const isHorizontal = currentRect.w >= currentRect.h;
    const rowSum = rowValues.reduce((a, b) => a + b, 0);
    const rowThickness = isHorizontal ? rowSum / currentRect.h : rowSum / currentRect.w;

    let offset = 0;
    for (let i = 0; i < row.length; i++) {
      const itemVal = rowValues[i];
      const itemLen = rowThickness > 0 ? itemVal / rowThickness : 0;
      if (isHorizontal) {
        results.push({
          data: row[i],
          x: currentRect.x,
          y: currentRect.y + offset,
          w: Math.max(0, rowThickness),
          h: Math.max(0, itemLen),
        });
        offset += itemLen;
      } else {
        results.push({
          data: row[i],
          x: currentRect.x + offset,
          y: currentRect.y,
          w: Math.max(0, itemLen),
          h: Math.max(0, rowThickness),
        });
        offset += itemLen;
      }
    }

    if (isHorizontal) {
      return {
        x: currentRect.x + rowThickness,
        y: currentRect.y,
        w: Math.max(0, currentRect.w - rowThickness),
        h: currentRect.h,
      };
    } else {
      return {
        x: currentRect.x,
        y: currentRect.y + rowThickness,
        w: currentRect.w,
        h: Math.max(0, currentRect.h - rowThickness),
      };
    }
  }

  function worst(rowValues, length) {
    if (!rowValues.length || length <= 0) return Infinity;
    const s = rowValues.reduce((a, b) => a + b, 0);
    const maxVal = Math.max(...rowValues);
    const minVal = Math.min(...rowValues);
    const s2 = s * s;
    const l2 = length * length;
    return Math.max((l2 * maxVal) / s2, s2 / (l2 * minVal));
  }

  let currentRect = { ...rect };
  let currentRow = [];
  let currentRowValues = [];

  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    const val = values[i];
    const length = Math.min(currentRect.w, currentRect.h);

    const testRow = [...currentRowValues, val];
    if (currentRow.length === 0 || worst(testRow, length) <= worst(currentRowValues, length)) {
      currentRow.push(child);
      currentRowValues.push(val);
    } else {
      currentRect = layoutRow(currentRow, currentRowValues, currentRect);
      currentRow = [child];
      currentRowValues = [val];
    }
  }

  if (currentRow.length > 0) {
    layoutRow(currentRow, currentRowValues, currentRect);
  }

  return results;
}

function showTreemapTooltip(e, contentHtml) {
  const tooltip = $("treemap-tooltip");
  const container = $("treemap-container");
  if (!tooltip || !container) return;
  tooltip.innerHTML = contentHtml;
  tooltip.hidden = false;
  const rect = container.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  tooltip.style.left = `${Math.min(rect.width - 90, Math.max(90, x))}px`;
  tooltip.style.top = `${Math.max(40, y)}px`;
}

function hideTreemapTooltip() {
  const tooltip = $("treemap-tooltip");
  if (tooltip) tooltip.hidden = true;
}

function renderMarketMap() {
  const container = $("treemap-container");
  if (!container || !state.snapshot || !state.snapshot.market_map) return;

  const mm = state.snapshot.market_map;
  const sectors = mm.treemap || [];
  const backBtn = $("treemap-back-btn");
  const activeView = $("treemap-active-view");

  const sectorSelect = $("treemap-sector-select");
  if (sectorSelect && sectorSelect.options.length <= 1) {
    sectors.forEach((s) => {
      const opt = element("option", "", s.name);
      opt.value = s.name;
      sectorSelect.append(opt);
    });
  }
  if (sectorSelect) {
    sectorSelect.value = state.activeSector || "ALL";
  }

  setText("treemap-turnover-badge", `Turnover: ${mm.total_turnover_cr} cr`);

  const width = container.clientWidth || 920;
  const height = 520;

  container.innerHTML = "";

  if (state.activeSector) {
    // Single Sector Drilldown View (matching Screenshot 2)
    const sector = sectors.find((s) => s.name === state.activeSector);
    if (!sector) {
      state.activeSector = null;
      renderMarketMap();
      return;
    }

    if (backBtn) backBtn.style.display = "inline-flex";
    if (activeView) setText("treemap-active-view", `${sector.name} (${sector.turnover_cr} cr)`);

    const drillHeader = element("div", "treemap-drill-header", sector.name);
    container.append(drillHeader);

    const contentHeight = height - 26;
    const tiles = squarify(sector.companies, { x: 0, y: 26, w: width, h: contentHeight });

    tiles.forEach((t) => {
      const c = t.data;
      const tile = element("div", "treemap-tile");
      tile.style.left = `${t.x.toFixed(1)}px`;
      tile.style.top = `${t.y.toFixed(1)}px`;
      tile.style.width = `${Math.max(0, t.w - 1).toFixed(1)}px`;
      tile.style.height = `${Math.max(0, t.h - 1).toFixed(1)}px`;

      if (c.change > 0) {
        tile.classList.add("tile-up");
        if (c.change >= 3.0) tile.classList.add("tile-strong", "finviz-glow-up");
      } else if (c.change < 0) {
        tile.classList.add("tile-down");
        if (c.change <= -2.0) tile.classList.add("finviz-glow-down");
      } else {
        tile.classList.add("tile-eql");
      }

      if (t.w < 65 || t.h < 45) tile.classList.add("tile-small");
      if (t.w < 45 || t.h < 32) tile.classList.add("tile-tiny");

      if (t.w >= 36 && t.h >= 22) {
        tile.append(element("span", "tile-symbol", c.symbol));
        if (t.w >= 56 && t.h >= 34) {
          tile.append(
            element("span", "tile-change", `${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}%`),
            element("span", "tile-turnover", `${c.turnover_cr.toFixed(2)}cr`)
          );
        }
      }

      tile.addEventListener("mousemove", (e) => {
        showTreemapTooltip(
          e,
          `<div class="tt-title">${sector.name}</div>
           <div class="tt-row"><strong class="tt-symbol">${c.symbol}</strong> <span>৳${c.price}</span></div>
           <div class="tt-row"><span class="tt-bullet" style="background:${c.change > 0 ? "#22c55e" : c.change < 0 ? "#ef4444" : "var(--tile-neutral, #64748b)"}"></span> ${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}% · ${c.turnover_cr.toFixed(2)}cr turnover</div>
           <div class="tt-row muted small" style="margin-top:3px;">Click to view Deep Trend & Profile ↗</div>`
        );
      });
      tile.addEventListener("mouseleave", hideTreemapTooltip);

      // In single sector drilldown, clicking tile opens Deep Trend modal
      tile.addEventListener("click", () => {
        openDeepTrendModal(c.symbol);
      });

      container.append(tile);
    });
  } else {
    // All Sectors View (matching Screenshot 1)
    if (backBtn) backBtn.style.display = "none";
    if (activeView) setText("treemap-active-view", "All Sectors");

    const sectorRects = squarify(sectors, { x: 0, y: 0, w: width, h: height });

    sectorRects.forEach((sr) => {
      const sector = sr.data;
      const sectorBox = element("div", "treemap-sector-group");
      sectorBox.style.left = `${sr.x.toFixed(1)}px`;
      sectorBox.style.top = `${sr.y.toFixed(1)}px`;
      sectorBox.style.width = `${Math.max(0, sr.w).toFixed(1)}px`;
      sectorBox.style.height = `${Math.max(0, sr.h).toFixed(1)}px`;

      const headerHeight = sr.h > 40 ? 20 : 0;
      if (headerHeight > 0) {
        const header = element("div", "treemap-sector-header", sector.name);
        header.title = `Click to drill into ${sector.name} (${sector.turnover_cr} cr)`;
        header.addEventListener("click", () => {
          state.activeSector = sector.name;
          renderMarketMap();
        });
        sectorBox.append(header);
      }

      const compHeight = Math.max(0, sr.h - headerHeight);
      const compTiles = squarify(sector.companies, { x: 0, y: headerHeight, w: sr.w, h: compHeight });

      compTiles.forEach((ct) => {
        const c = ct.data;
        const tile = element("div", "treemap-tile");
        tile.style.left = `${ct.x.toFixed(1)}px`;
        tile.style.top = `${ct.y.toFixed(1)}px`;
        tile.style.width = `${Math.max(0, ct.w - 1).toFixed(1)}px`;
        tile.style.height = `${Math.max(0, ct.h - 1).toFixed(1)}px`;

        if (c.change > 0) {
          tile.classList.add("tile-up");
          if (c.change >= 3.0) tile.classList.add("tile-strong", "finviz-glow-up");
        } else if (c.change < 0) {
          tile.classList.add("tile-down");
          if (c.change <= -2.0) tile.classList.add("finviz-glow-down");
        } else {
          tile.classList.add("tile-eql");
        }

        if (ct.w < 65 || ct.h < 45) tile.classList.add("tile-small");
        if (ct.w < 45 || ct.h < 32) tile.classList.add("tile-tiny");

        if (ct.w >= 36 && ct.h >= 22) {
          tile.append(element("span", "tile-symbol", c.symbol));
          if (ct.w >= 56 && ct.h >= 34) {
            tile.append(
              element("span", "tile-change", `${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}%`),
              element("span", "tile-turnover", `${c.turnover_cr.toFixed(2)}cr`)
            );
          }
        }

        tile.addEventListener("mousemove", (e) => {
          showTreemapTooltip(
            e,
            `<div class="tt-title">${sector.name}</div>
             <div class="tt-row"><strong class="tt-symbol">${c.symbol}</strong> <span>৳${c.price}</span></div>
             <div class="tt-row"><span class="tt-bullet" style="background:${c.change > 0 ? "#22c55e" : c.change < 0 ? "#ef4444" : "var(--tile-neutral, #64748b)"}"></span> ${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}% · ${c.turnover_cr.toFixed(2)}cr</div>
             <div class="tt-row muted">Sector total: ${sector.turnover_cr} cr</div>`
          );
        });
        tile.addEventListener("mouseleave", hideTreemapTooltip);

        tile.addEventListener("click", () => {
          state.activeSector = sector.name;
          renderMarketMap();
        });

        sectorBox.append(tile);
      });

      container.append(sectorBox);
    });
  }
}

function renderTopSectorsChart() {
  const svg = $("sector-gainer-chart");
  if (!svg || !state.snapshot || !state.snapshot.market_map) return;

  const data = state.snapshot.market_map.top_sectors_by_gainer || [];
  if (!data.length) return;

  svg.innerHTML = "";

  const width = 940;
  const height = 330;
  const left = 45;
  const right = 20;
  const top = 25;
  const bottom = 125;

  const chartW = width - left - right;
  const chartH = height - top - bottom;

  const maxY = Math.max(25, ...data.map((d) => d.total));

  // Background gridlines and Y-axis labels
  const gridSteps = 5;
  for (let i = 0; i <= gridSteps; i++) {
    const val = Math.round((maxY / gridSteps) * i);
    const y = top + chartH - (val / maxY) * chartH;

    const line = svgElement("line", {
      x1: left,
      y1: y.toFixed(1),
      x2: width - right,
      y2: y.toFixed(1),
      class: "gainer-grid",
    });
    svg.append(line);

    const txt = svgElement("text", {
      x: left - 8,
      y: (y + 3).toFixed(1),
      "text-anchor": "end",
      class: "gainer-label",
    });
    txt.textContent = String(val);
    svg.append(txt);
  }

  // Baseline axis
  svg.append(
    svgElement("line", {
      x1: left,
      y1: top + chartH,
      x2: width - right,
      y2: top + chartH,
      class: "gainer-axis",
    })
  );

  const step = chartW / data.length;
  const barW = Math.min(26, step * 0.72);

  data.forEach((d, idx) => {
    const barX = left + idx * step + (step - barW) / 2;

    const hUp = (d.up / maxY) * chartH;
    const hDown = (d.down / maxY) * chartH;
    const hEql = (d.eql / maxY) * chartH;

    const yUp = top + chartH - hUp;
    const yDown = yUp - hDown;
    const yEql = yDown - hEql;

    const group = svgElement("g", { class: "gainer-bar-segment" });

    // Up segment (bottom, green #22c55e)
    if (hUp > 0) {
      group.append(
        svgElement("rect", {
          x: barX.toFixed(1),
          y: yUp.toFixed(1),
          width: barW.toFixed(1),
          height: hUp.toFixed(1),
          fill: "#22c55e",
          rx: hDown === 0 && hEql === 0 ? "2" : "0",
        })
      );
    }

    // Down segment (middle, red #ef4444)
    if (hDown > 0) {
      group.append(
        svgElement("rect", {
          x: barX.toFixed(1),
          y: yDown.toFixed(1),
          width: barW.toFixed(1),
          height: hDown.toFixed(1),
          fill: "#ef4444",
          rx: hEql === 0 ? "2" : "0",
        })
      );
    }

    // Eql segment (top, neutral slate var(--tile-neutral, #475569))
    if (hEql > 0) {
      group.append(
        svgElement("rect", {
          x: barX.toFixed(1),
          y: yEql.toFixed(1),
          width: barW.toFixed(1),
          height: hEql.toFixed(1),
          fill: "var(--tile-neutral, #475569)",
          rx: "2",
        })
      );
    }

    // Interactive tooltip on bar hover
    group.addEventListener("mousemove", (e) => {
      showTreemapTooltip(
        e,
        `<div class="tt-title">${d.sector}</div>
         <div class="tt-row"><span class="tt-bullet" style="background:#22c55e"></span> Up: <strong>${d.up}</strong></div>
         <div class="tt-row"><span class="tt-bullet" style="background:#ef4444"></span> Down: <strong>${d.down}</strong></div>
         <div class="tt-row"><span class="tt-bullet" style="background:var(--tile-neutral, #64748b)"></span> Eql: <strong>${d.eql}</strong></div>
         <div class="tt-row muted">Turnover: ${d.turnover_cr} cr (${d.total} companies)</div>`
      );
    });
    group.addEventListener("mouseleave", hideTreemapTooltip);

    // Clicking a bar drills down into that sector on the treemap
    group.addEventListener("click", () => {
      state.activeSector = d.sector;
      renderMarketMap();
      const treemapElem = $("market-map");
      if (treemapElem) treemapElem.scrollIntoView({ behavior: "smooth" });
    });

    svg.append(group);

    // Rotated Sector Label along X axis
    const labelX = (barX + barW / 2).toFixed(1);
    const labelY = (top + chartH + 12).toFixed(1);

    const text = svgElement("text", {
      transform: `translate(${labelX}, ${labelY}) rotate(-90)`,
      "text-anchor": "end",
      class: "gainer-label",
    });
    text.textContent = d.sector;
    text.style.cursor = "pointer";
    text.addEventListener("click", () => {
      state.activeSector = d.sector;
      renderMarketMap();
      const treemapElem = $("market-map");
      if (treemapElem) treemapElem.scrollIntoView({ behavior: "smooth" });
    });
    svg.append(text);
  });
}

// Alias for sector gainer chart
function renderGainerChart() {
  return renderTopSectorsChart();
}

// --- "What-If" Profit Simulator Logic ---
function updateWhatIfSimulator(company) {
  if (!company) {
    company = (state.snapshot && state.snapshot.companies)
      ? state.snapshot.companies.find((c) => c.symbol === state.selectedSymbol)
      : null;
  }
  if (!company) return;

  const slider = $("what-if-slider");
  const deltaPct = slider ? Number(slider.value) : 0;
  const currentPrice = Number(company.price);
  const targetPrice = currentPrice * (1 + deltaPct / 100);

  const matureQty = company.mature_qty || company.holding_qty || 100;
  const costBasis = (company.cost_basis && company.holding_qty)
    ? (company.cost_basis / company.holding_qty) * matureQty
    : currentPrice * matureQty;

  const grossExit = targetPrice * matureQty;
  const buyFee = costBasis * 0.005;
  const sellFee = grossExit * 0.005;
  const totalFees = buyFee + sellFee;
  const netProfit = grossExit - costBasis - totalFees;
  const netReturnPct = costBasis > 0 ? (netProfit / costBasis) * 100 : 0;

  if ($("sim-symbol-badge")) setText("sim-symbol-badge", `${company.symbol} (${matureQty} sh)`);
  if ($("what-if-target-price")) setText("what-if-target-price", `৳${targetPrice.toFixed(2)}`);
  if ($("what-if-target-pct")) {
    setText("what-if-target-pct", `${deltaPct >= 0 ? "+" : ""}${deltaPct.toFixed(2)}%`);
    $("what-if-target-pct").className = deltaPct >= 0 ? "positive" : "negative";
  }

  if ($("what-if-gross")) setText("what-if-gross", currency(grossExit));
  if ($("what-if-fee")) setText("what-if-fee", currency(totalFees));
  if ($("what-if-net-pnl")) {
    setText("what-if-net-pnl", currency(netProfit, true));
    $("what-if-net-pnl").className = netProfit >= 0 ? "positive" : "negative";
  }
  if ($("what-if-return-pct")) {
    setText("what-if-return-pct", percentage(netReturnPct));
    $("what-if-return-pct").className = netReturnPct >= 0 ? "positive" : "negative";
  }
}

function updateModalSimulator(company) {
  if (!company) return;
  const slider = $("modal-sim-slider");
  const deltaPct = slider ? Number(slider.value) : 0;
  const currentPrice = Number(company.price);
  const targetPrice = currentPrice * (1 + deltaPct / 100);

  const matureQty = company.mature_qty || company.holding_qty || 100;
  const costBasis = (company.cost_basis && company.holding_qty)
    ? (company.cost_basis / company.holding_qty) * matureQty
    : currentPrice * matureQty;

  const grossExit = targetPrice * matureQty;
  const buyFee = costBasis * 0.005;
  const sellFee = grossExit * 0.005;
  const totalFees = buyFee + sellFee;
  const netProfit = grossExit - costBasis - totalFees;
  const netReturnPct = costBasis > 0 ? (netProfit / costBasis) * 100 : 0;

  if ($("modal-sim-name")) setText("modal-sim-name", `${company.symbol} (${matureQty} mature shares)`);
  if ($("modal-sim-target-price")) setText("modal-sim-target-price", `৳${targetPrice.toFixed(2)}`);
  if ($("modal-sim-target-pct")) {
    setText("modal-sim-target-pct", `${deltaPct >= 0 ? "+" : ""}${deltaPct.toFixed(2)}%`);
    $("modal-sim-target-pct").className = deltaPct >= 0 ? "positive" : "negative";
  }

  if ($("modal-sim-gross")) setText("modal-sim-gross", currency(grossExit));
  if ($("modal-sim-fee")) setText("modal-sim-fee", currency(totalFees));
  if ($("modal-sim-net-pnl")) {
    setText("modal-sim-net-pnl", currency(netProfit, true));
    $("modal-sim-net-pnl").className = netProfit >= 0 ? "positive" : "negative";
  }
  if ($("modal-sim-return-pct")) {
    setText("modal-sim-return-pct", percentage(netReturnPct));
    $("modal-sim-return-pct").className = netReturnPct >= 0 ? "positive" : "negative";
  }
}

// --- Individual Company Deep-Trend View & Fundamentals Modal ---
function openDeepTrendModal(symbol) {
  if (!state.snapshot || !state.snapshot.companies) return;
  const company = state.snapshot.companies.find((c) => c.symbol === symbol)
    || state.snapshot.companies[0];
  if (!company) return;

  state.deepCompany = company;
  const modal = $("deep-trend-modal");
  if (!modal) return;

  if ($("modal-company-title")) {
    setText("modal-company-title", `${company.symbol} `);
    const sub = element("span", "modal-company-sub", company.name);
    $("modal-company-title").append(sub);
  }

  if ($("modal-company-sector")) setText("modal-company-sector", company.sector.replaceAll("_", " "));
  const catCode = company.watchlist_category || "GSC";
  if ($("modal-company-category")) setText("modal-company-category", catLabels[catCode] || catCode);

  if ($("modal-price")) setText("modal-price", currency(company.price));
  const dayChg = (company.curve && company.curve.day_change_pct) || 0;
  if ($("modal-change")) {
    setText("modal-change", percentage(dayChg));
    $("modal-change").className = `modal-change ${dayChg >= 0 ? "positive" : "negative"}`;
  }

  const signal = (company.curve && company.curve.signal) || "MID_RANGE";
  if ($("modal-signal-tag")) {
    setText("modal-signal-tag", signal.replaceAll("_", " "));
    $("modal-signal-tag").className = `signal-badge tone-${tone(signal)}`;
  }

  const f = company.fundamentals || {};
  if ($("fund-pe")) setText("fund-pe", f.pe_ratio ? f.pe_ratio.toFixed(1) : "—");
  if ($("fund-eps")) setText("fund-eps", f.eps ? `৳${f.eps.toFixed(2)}` : "—");
  if ($("fund-nav")) setText("fund-nav", f.nav ? `৳${f.nav.toFixed(2)}` : "—");
  if ($("fund-mcap")) setText("fund-mcap", f.market_cap_cr ? `${numberFormat.format(f.market_cap_cr)} cr` : "—");
  if ($("fund-div")) setText("fund-div", f.dividend_yield ? `${f.dividend_yield.toFixed(1)}%` : "—");
  if ($("fund-paidup")) setText("fund-paidup", f.paid_up_capital_cr ? `${numberFormat.format(f.paid_up_capital_cr)} cr` : "—");
  if ($("fund-52w")) setText("fund-52w", f.low_52w && f.high_52w ? `৳${f.low_52w} — ৳${f.high_52w}` : "—");
  if ($("fund-cat")) setText("fund-cat", f.category ? `Category ${f.category} (${f.listing_year || "—"})` : "—");

  document.querySelectorAll("#deep-timeframe-tabs button").forEach((b) => {
    b.classList.toggle("active", b.dataset.tf === state.deepTimeframe);
  });

  renderDeepTrendChart(company, state.deepTimeframe);
  updateModalSimulator(company);

  if (typeof modal.showModal === "function") {
    modal.showModal();
  } else {
    modal.setAttribute("open", "");
  }
}

function closeDeepTrendModal() {
  const modal = $("deep-trend-modal");
  if (!modal) return;
  if (typeof modal.close === "function") {
    modal.close();
  } else {
    modal.removeAttribute("open");
  }
}

function renderDeepTrendChart(company, timeframe = "7d") {
  const mount = $("deep-trend-chart-mount");
  if (!mount || !company) return;

  const ext = company.extended_history || {};
  let series = ext[timeframe] || company.history || [];
  if (series.length < 2) series = company.history || [];
  if (series.length < 2) {
    mount.innerHTML = `<div class="muted small" style="display:grid;place-items:center;height:100%;">Insufficient historical curve points.</div>`;
    return;
  }

  const width = 880, height = 240, left = 55, right = 15, top = 20, bottom = 30;
  const chartW = width - left - right;
  const chartH = height - top - bottom;

  const closes = series.map((pt) => Number(pt.close));
  const support = Number(company.curve.support || company.curve.low || Math.min(...closes));
  const resistance = Number(company.curve.resistance || company.curve.high || Math.max(...closes));
  const buyCeiling = Number(company.curve.buy_zone_ceiling || support);

  if ($("deep-support-val")) setText("deep-support-val", `৳${support.toFixed(2)}`);
  if ($("deep-resistance-val")) setText("deep-resistance-val", `৳${resistance.toFixed(2)}`);

  const minVal = Math.min(...closes, support) * 0.985;
  const maxVal = Math.max(...closes, resistance) * 1.015;
  const range = maxVal - minVal || 1;

  const x = (i) => left + (i / (series.length - 1)) * chartW;
  const y = (val) => top + ((maxVal - val) / range) * chartH;

  const svg = svgElement("svg", {
    viewBox: `0 0 ${width} ${height}`,
    preserveAspectRatio: "none",
    class: "deep-trend-svg",
  });

  const defs = svgElement("defs");
  const grad = svgElement("linearGradient", { id: "deep-curve-grad", x1: "0", y1: "0", x2: "0", y2: "1" });
  grad.append(
    svgElement("stop", { offset: "0%", "stop-color": "#5de4c7", "stop-opacity": "0.22" }),
    svgElement("stop", { offset: "100%", "stop-color": "#5de4c7", "stop-opacity": "0" })
  );
  defs.append(grad);
  svg.append(defs);

  // Background Gridlines
  for (let step = 0; step <= 4; step++) {
    const val = minVal + (range * step) / 4;
    const yPos = y(val);
    svg.append(svgElement("line", { x1: left, y1: yPos, x2: width - right, y2: yPos, stroke: "var(--chart-grid)", "stroke-width": 1, "stroke-dasharray": "2 3" }));
    const lbl = svgElement("text", { x: left - 8, y: yPos + 3, "text-anchor": "end", fill: "var(--muted)", "font-size": 9.5 });
    lbl.textContent = `৳${val.toFixed(1)}`;
    svg.append(lbl);
  }

  // Shaded Buy Zone band: [support, buyCeiling]
  if (buyCeiling > support) {
    const yTop = Math.min(y(support), y(buyCeiling));
    const bandH = Math.abs(y(support) - y(buyCeiling));
    svg.append(svgElement("rect", {
      x: left,
      y: yTop,
      width: chartW,
      height: bandH,
      fill: "rgba(34, 197, 94, 0.08)",
      stroke: "none",
    }));
  }

  // Horizontal Support line (dashed green)
  svg.append(svgElement("line", {
    x1: left,
    y1: y(support),
    x2: width - right,
    y2: y(support),
    stroke: "#22c55e",
    "stroke-width": 1.5,
    "stroke-dasharray": "4 4",
  }));
  const supLbl = svgElement("text", { x: width - right - 4, y: y(support) - 4, "text-anchor": "end", fill: "#22c55e", "font-size": 9, "font-weight": 700 });
  supLbl.textContent = `SUPPORT ৳${support.toFixed(1)}`;
  svg.append(supLbl);

  // Horizontal Resistance line (dashed red)
  svg.append(svgElement("line", {
    x1: left,
    y1: y(resistance),
    x2: width - right,
    y2: y(resistance),
    stroke: "#ef4444",
    "stroke-width": 1.5,
    "stroke-dasharray": "4 4",
  }));
  const resLbl = svgElement("text", { x: width - right - 4, y: y(resistance) - 4, "text-anchor": "end", fill: "#ef4444", "font-size": 9, "font-weight": 700 });
  resLbl.textContent = `RESISTANCE ৳${resistance.toFixed(1)}`;
  svg.append(resLbl);

  // Price Area & Line with smooth cubic bezier curve
  const coords = series.map((pt, i) => ({ x: x(i), y: y(Number(pt.close)) }));
  const pathD = smoothCurvePath(coords);
  svg.append(svgElement("path", {
    d: `${pathD} L${x(series.length - 1).toFixed(1)},${(top + chartH).toFixed(1)} L${left},${(top + chartH).toFixed(1)} Z`,
    fill: "url(#deep-curve-grad)",
  }));
  svg.append(svgElement("path", {
    d: pathD,
    fill: "none",
    stroke: "var(--teal)",
    "stroke-width": 2.2,
  }));

  // X Axis Session Dates
  const sampleIndices = [...new Set([0, Math.floor((series.length - 1) / 3), Math.floor((series.length - 1) * 2 / 3), series.length - 1])];
  sampleIndices.forEach((idx) => {
    const xPos = x(idx);
    const dateLbl = svgElement("text", {
      x: xPos,
      y: height - 8,
      "text-anchor": idx === 0 ? "start" : idx === series.length - 1 ? "end" : "middle",
      fill: "var(--muted)",
      "font-size": 9.5,
    });
    dateLbl.textContent = sessionDate(series[idx].date, true);
    svg.append(dateLbl);
  });

  // Bot Order Markers (B = Buy in green, S = Sell in red)
  const companyTrades = (state.snapshot.trades || []).filter((t) => t.symbol === company.symbol);
  series.forEach((pt, idx) => {
    const tradesOnDate = companyTrades.filter((t) => t.date === pt.date || t.trade_on === pt.date);
    tradesOnDate.forEach((t) => {
      const isBuy = t.side === "BUY";
      const markerX = x(idx);
      const markerY = y(Number(pt.close));

      const markerG = svgElement("g", { class: "chart-trade-marker" });
      markerG.append(svgElement("circle", {
        cx: markerX,
        cy: markerY,
        r: 7,
        fill: isBuy ? "#16a34a" : "#dc2626",
        stroke: "#ffffff",
        "stroke-width": 1.5,
      }));
      const textM = svgElement("text", {
        x: markerX,
        y: markerY + 3.5,
        "text-anchor": "middle",
        fill: "#ffffff",
        "font-size": 8.5,
        "font-weight": 800,
      });
      textM.textContent = isBuy ? "B" : "S";
      markerG.append(textM);
      markerG.title = `${t.side} ${t.quantity} shares @ ৳${t.price} (${t.reason || ""})`;
      svg.append(markerG);
    });
  });

  // Crosshair vertical & horizontal lines & tracking dot
  const crosshairV = svgElement("line", { x1: 0, y1: top, x2: 0, y2: top + chartH, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairH = svgElement("line", { x1: left, y1: 0, x2: left + chartW, y2: 0, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairPoint = svgElement("circle", { cx: 0, cy: 0, r: 4, class: "chart-crosshair-point", style: "display:none;" });
  svg.append(crosshairV, crosshairH, crosshairPoint);

  // Latest Point Marker (visible when not hovering, matching Image 2 Bank Asia modal style)
  const endpointDot = svgElement("circle", {
    cx: x(series.length - 1),
    cy: y(Number(series[series.length - 1].close)),
    r: 4.5,
    class: "chart-crosshair-point",
    style: "display:block;",
  });
  svg.append(endpointDot);

  // Overlay for mouse events
  const overlay = svgElement("rect", {
    x: left,
    y: top,
    width: chartW,
    height: chartH,
    fill: "transparent",
    style: "cursor: crosshair;",
  });

  overlay.addEventListener("mousemove", (e) => {
    const rect = mount.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    let svgX = 0;
    const ctm = svg.getScreenCTM();
    if (ctm) {
      const pt = svg.createSVGPoint();
      pt.x = e.clientX;
      pt.y = e.clientY;
      const inv = ctm.inverse();
      const p = pt.matrixTransform(inv);
      svgX = p.x;
    } else {
      const svgRect = svg.getBoundingClientRect();
      svgX = ((e.clientX - svgRect.left) / (svgRect.width || 1)) * width;
    }

    const clampedX = Math.max(left, Math.min(left + chartW, svgX));
    const normX = clampedX - left;
    const t = chartW > 0 ? normX / chartW : 0;
    const continuousIdx = t * (series.length - 1);

    const curvePt = getBezierPointAtContinuousIndex(coords, continuousIdx);
    const ptX = clampedX;
    const ptY = curvePt.y;

    crosshairV.setAttribute("x1", ptX);
    crosshairV.setAttribute("x2", ptX);
    crosshairV.style.display = "block";

    crosshairH.setAttribute("y1", ptY);
    crosshairH.setAttribute("y2", ptY);
    crosshairH.style.display = "block";

    crosshairPoint.setAttribute("cx", ptX);
    crosshairPoint.setAttribute("cy", ptY);
    crosshairPoint.style.display = "block";
    endpointDot.style.display = "none";

    const closestIdx = Math.min(series.length - 1, Math.max(0, Math.round(continuousIdx)));
    const pt = series[closestIdx];

    const val = maxVal - ((ptY - top) / chartH) * range;
    const chgFromStart = ((val / Number(series[0].close) - 1) * 100);
    const dateTrades = companyTrades.filter((t) => t.date === pt.date || t.trade_on === pt.date);
    let tradeNote = "";
    if (dateTrades.length) {
      tradeNote = `<div style="margin-top:4px;border-top:1px solid var(--soft-line);padding-top:3px;">
        ${dateTrades.map((t) => `<strong style="color:${t.side === "BUY" ? "#22c55e" : "#ef4444"}">${t.side}</strong> ${t.quantity} qty @ ৳${t.price}`).join("<br>")}
      </div>`;
    }

    const tooltip = $("deep-chart-tooltip");
    if (tooltip) {
      tooltip.innerHTML = `
        <div style="font-weight:700;color:var(--teal);">${sessionDate(pt.date)}</div>
        <div style="font-size:12px;font-weight:600;margin-top:2px;">Close: ৳${val.toFixed(2)} (${chgFromStart >= 0 ? "+" : ""}${chgFromStart.toFixed(2)}%)</div>
        ${tradeNote}
      `;
      tooltip.hidden = false;

      const wrap = tooltip.offsetParent || mount;
      const wrapRect = wrap.getBoundingClientRect();
      let screenX, screenY;
      if (ctm) {
        const pSvg = svg.createSVGPoint();
        pSvg.x = ptX;
        pSvg.y = ptY;
        const pScreen = pSvg.matrixTransform(ctm);
        screenX = pScreen.x - wrapRect.left;
        screenY = pScreen.y - wrapRect.top;
      } else {
        const svgRect = svg.getBoundingClientRect();
        screenX = svgRect.left + (ptX / width) * svgRect.width - wrapRect.left;
        screenY = svgRect.top + (ptY / height) * svgRect.height - wrapRect.top;
      }

      tooltip.style.left = `${Math.min(wrapRect.width - 100, Math.max(100, screenX))}px`;
      tooltip.style.top = `${Math.max(30, screenY - 10)}px`;
    }
  });

  overlay.addEventListener("mouseleave", () => {
    crosshairV.style.display = "none";
    crosshairH.style.display = "none";
    crosshairPoint.style.display = "none";
    endpointDot.style.display = "block";
    const tooltip = $("deep-chart-tooltip");
    if (tooltip) tooltip.hidden = true;
  });

  svg.append(overlay);
  mount.replaceChildren(svg);
}

function initCharts() {
  if ($("open-deep-trend")) {
  $("open-deep-trend").addEventListener("click", () => openDeepTrendModal(state.selectedSymbol));
}
if ($("modal-close-btn")) {
  $("modal-close-btn").addEventListener("click", closeDeepTrendModal);
}
if ($("modal-backdrop")) {
  $("modal-backdrop").addEventListener("click", closeDeepTrendModal);
}
document.querySelectorAll("#deep-timeframe-tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.deepTimeframe = btn.dataset.tf;
    document.querySelectorAll("#deep-timeframe-tabs button").forEach((b) => b.classList.toggle("active", b === btn));
    if (state.deepCompany) renderDeepTrendChart(state.deepCompany, state.deepTimeframe);
  });
});

if ($("what-if-slider")) {
  $("what-if-slider").addEventListener("input", () => updateWhatIfSimulator());
}
if ($("modal-sim-slider")) {
  $("modal-sim-slider").addEventListener("input", () => {
    if (state.deepCompany) updateModalSimulator(state.deepCompany);
  });
}
if ($("treemap-sector-select")) {
  $("treemap-sector-select").addEventListener("change", (e) => {
    const val = e.target.value;
    state.activeSector = val === "ALL" ? null : val;
    renderMarketMap();
  });
}
}
