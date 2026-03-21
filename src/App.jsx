import { useState, useMemo } from "react";
import {
  LineChart, Line, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine, Cell, Legend, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis
} from "recharts";

const STYLE = `
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

  :root {
    --bg: #080c10;
    --surface: #0d1318;
    --surface2: #111820;
    --border: #1e2d3d;
    --amber: #f5a623;
    --red: #e63946;
    --green: #2ecc71;
    --blue: #4fc3f7;
    --text: #c8d8e8;
    --muted: #4a6278;
    --dim: #243040;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body, .dash-root {
    background: var(--bg);
    color: var(--text);
    font-family: 'IBM Plex Mono', monospace;
    min-height: 100vh;
  }

  .scanline {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px);
    pointer-events: none; z-index: 1000;
  }

  .header {
    padding: 20px 32px 16px;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(180deg, #0a1520 0%, var(--bg) 100%);
    display: flex; align-items: flex-end; justify-content: space-between;
  }

  .header-title {
    font-family: 'Bebas Neue', cursive;
    font-size: 38px;
    letter-spacing: 3px;
    color: #fff;
    line-height: 1;
  }

  .header-title span { color: var(--amber); }

  .header-sub {
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 2px;
    margin-top: 4px;
    text-transform: uppercase;
  }

  .header-badge {
    display: flex; align-items: center; gap: 6px;
    font-size: 10px; color: var(--green); letter-spacing: 1px;
  }

  .pulse { width: 6px; height: 6px; border-radius: 50%; background: var(--green);
    animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(46,204,113,0.4)}
    50%{opacity:.7;box-shadow:0 0 0 6px rgba(46,204,113,0)} }

  .layout { display: grid; grid-template-columns: 320px 1fr; min-height: calc(100vh - 85px); }

  .sidebar {
    border-right: 1px solid var(--border);
    background: var(--surface);
    overflow-y: auto;
    padding: 0;
  }

  .sidebar-section { padding: 16px 20px; border-bottom: 1px solid var(--border); }

  .section-label {
    font-size: 9px; letter-spacing: 2px; color: var(--muted);
    text-transform: uppercase; margin-bottom: 10px;
  }

  .filter-row { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }

  .chip {
    padding: 4px 10px; border: 1px solid var(--border); border-radius: 2px;
    font-size: 10px; cursor: pointer; background: transparent; color: var(--muted);
    font-family: 'IBM Plex Mono', monospace; transition: all .15s; letter-spacing: 1px;
  }
  .chip:hover { border-color: var(--amber); color: var(--amber); }
  .chip.active { background: var(--amber); border-color: var(--amber); color: #000; font-weight: 600; }
  .chip.danger { background: var(--red); border-color: var(--red); color: #fff; }

  .player-list { display: flex; flex-direction: column; gap: 2px; }

  .player-row {
    display: flex; align-items: center; gap: 10px; padding: 9px 12px;
    border-radius: 3px; cursor: pointer; transition: all .15s;
    border: 1px solid transparent;
  }
  .player-row:hover { background: var(--surface2); border-color: var(--border); }
  .player-row.selected { background: var(--dim); border-color: var(--amber); }

  .risk-badge {
    width: 38px; height: 22px; border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 600; flex-shrink: 0;
  }

  .player-name { font-size: 12px; color: var(--text); flex: 1; }
  .player-meta { font-size: 9px; color: var(--muted); }

  .risk-bar-bg { width: 60px; height: 4px; background: var(--dim); border-radius: 2px; flex-shrink: 0; }
  .risk-bar-fill { height: 4px; border-radius: 2px; transition: width .3s; }

  .main { padding: 24px 28px; overflow-y: auto; }

  .kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }

  .kpi-card {
    background: var(--surface); border: 1px solid var(--border);
    padding: 16px; border-radius: 3px; position: relative; overflow: hidden;
  }
  .kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  }
  .kpi-card.amber::before { background: var(--amber); }
  .kpi-card.red::before { background: var(--red); }
  .kpi-card.blue::before { background: var(--blue); }
  .kpi-card.green::before { background: var(--green); }

  .kpi-label { font-size: 9px; letter-spacing: 2px; color: var(--muted); margin-bottom: 6px; }
  .kpi-value { font-family: 'Bebas Neue', cursive; font-size: 36px; line-height: 1; letter-spacing: 2px; }
  .kpi-sub { font-size: 9px; color: var(--muted); margin-top: 4px; }
  .kpi-delta { font-size: 11px; margin-top: 6px; }

  .charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 24px; }
  .chart-full { grid-column: span 2; }

  .chart-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 3px; padding: 18px;
  }

  .chart-title {
    font-size: 11px; letter-spacing: 2px; color: var(--amber);
    text-transform: uppercase; margin-bottom: 4px;
  }
  .chart-desc { font-size: 9px; color: var(--muted); margin-bottom: 16px; letter-spacing: .5px; }

  .player-detail {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 3px; padding: 20px; margin-bottom: 24px;
  }

  .detail-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 18px; }
  .detail-name { font-family: 'Bebas Neue', cursive; font-size: 32px; letter-spacing: 3px; color: #fff; }
  .detail-meta { font-size: 10px; color: var(--muted); margin-top: 2px; }

  .risk-meter {
    text-align: right;
  }
  .risk-score-big {
    font-family: 'Bebas Neue', cursive; font-size: 52px; line-height: 1;
    letter-spacing: 2px;
  }
  .risk-label-big { font-size: 9px; letter-spacing: 2px; color: var(--muted); text-transform: uppercase; }

  .detail-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .detail-phase {
    background: var(--surface2); border: 1px solid var(--border);
    padding: 14px; border-radius: 3px;
  }
  .phase-label { font-size: 9px; letter-spacing: 2px; color: var(--muted); margin-bottom: 10px; }
  .phase-label span { color: var(--amber); }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 3px 0; border-bottom: 1px solid #1a2530; }
  .stat-key { font-size: 9px; color: var(--muted); }
  .stat-val { font-size: 12px; color: var(--text); font-weight: 600; }
  .stat-val.down { color: var(--red); }
  .stat-val.up { color: var(--green); }

  .tab-row { display: flex; gap: 2px; margin-bottom: 20px; border-bottom: 1px solid var(--border); }
  .tab {
    padding: 8px 16px; font-size: 10px; letter-spacing: 1.5px; cursor: pointer;
    color: var(--muted); border-bottom: 2px solid transparent; transition: all .15s;
    font-family: 'IBM Plex Mono', monospace; text-transform: uppercase;
    background: none; border-top: none; border-left: none; border-right: none;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--amber); border-bottom-color: var(--amber); }

  .finding-box {
    background: linear-gradient(135deg, #0d1a10 0%, #0d1318 100%);
    border: 1px solid rgba(46,204,113,0.2); border-left: 3px solid var(--green);
    padding: 12px 16px; border-radius: 3px; margin-top: 14px;
    font-size: 10px; color: #6fcf97; line-height: 1.6; letter-spacing: .3px;
  }
  .finding-box.warn {
    background: linear-gradient(135deg, #1a0d0d 0%, #130d0d 100%);
    border-color: rgba(230,57,70,0.2); border-left-color: var(--red);
    color: #e07070;
  }

  .tooltip-custom {
    background: #0a1520; border: 1px solid var(--border);
    padding: 10px 14px; border-radius: 3px;
    font-size: 11px; font-family: 'IBM Plex Mono', monospace;
  }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .flag-row { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }

  /* ── Mobile sidebar toggle ─────────────────────────────────────── */
  .menu-btn {
    display: none; background: none; border: 1px solid var(--border);
    color: var(--muted); cursor: pointer; padding: 5px 9px; font-size: 18px;
    border-radius: 2px; line-height: 1; align-self: center; flex-shrink: 0;
    font-family: 'IBM Plex Mono', monospace;
  }
  .menu-btn:hover { border-color: var(--amber); color: var(--amber); }

  .sidebar-mobile-header {
    display: none; align-items: center; justify-content: space-between;
    padding: 12px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0;
  }
  .sidebar-close-btn {
    background: none; border: 1px solid var(--border); color: var(--muted);
    cursor: pointer; width: 28px; height: 28px; font-size: 18px;
    border-radius: 2px; display: flex; align-items: center; justify-content: center;
    font-family: 'IBM Plex Mono', monospace; line-height: 1;
  }
  .sidebar-close-btn:hover { border-color: var(--amber); color: var(--amber); }

  @media (max-width: 767px) {
    .menu-btn { display: flex; }
    .sidebar-mobile-header { display: flex; }

    .header { padding: 12px 16px; }
    .header-title { font-size: 26px; letter-spacing: 2px; }

    .layout { grid-template-columns: 1fr; }

    .sidebar {
      position: fixed; top: 0; left: 0; bottom: 0;
      width: 300px; z-index: 200;
      transform: translateX(-320px);
      transition: transform 0.25s ease;
      display: flex; flex-direction: column;
      overflow-y: auto;
    }
    .sidebar.open { transform: translateX(0); }

    .main { padding: 16px 14px; }

    .kpi-row { grid-template-columns: repeat(2, 1fr); }

    .charts-grid { grid-template-columns: 1fr; }
    .chart-full { grid-column: span 1; }

    .detail-grid { grid-template-columns: 1fr; }
    .detail-header { flex-direction: column; gap: 10px; }
    .risk-meter { text-align: left; }
  }
  .flag {
    padding: 3px 8px; border-radius: 2px; font-size: 9px; letter-spacing: 1px;
    font-weight: 600;
  }
  .flag.high { background: rgba(230,57,70,.15); border: 1px solid rgba(230,57,70,.4); color: var(--red); }
  .flag.med { background: rgba(245,166,35,.1); border: 1px solid rgba(245,166,35,.3); color: var(--amber); }
  .flag.low { background: rgba(46,204,113,.1); border: 1px solid rgba(46,204,113,.3); color: var(--green); }
`;

// ─── DATA ──────────────────────────────────────────────────────────────────────
const PLAYERS = [
  { id: 1,  name: "R. Westbrook",     pos: "PG", age: 28, tier: "Max", salary: 41, contractYear: 2017,
    T1: { PER: 27.6, WS: 14.0, VORP: 6.8, PTS: 23.5, AST: 10.4, TRB: 7.8, TS: 55.4, TOV: 4.3 },
    T:  { PER: 30.6, WS: 13.1, VORP: 9.3, PTS: 31.6, AST: 10.4, TRB: 10.7, TS: 55.4, TOV: 5.4 },
    T2: { PER: 24.7, WS: 10.1, VORP: 6.1, PTS: 25.4, AST: 10.3, TRB: 10.1, TS: 52.4, TOV: 4.8 } },
  { id: 2,  name: "J. Harden",     pos: "PG", age: 29, tier: "Max", salary: 43, contractYear: 2019,
    T1: { PER: 29.8, WS: 15.4, VORP: 7.7, PTS: 30.4, AST: 8.8, TRB: 5.4, TS: 61.9, TOV: 4.4 },
    T:  { PER: 30.6, WS: 15.2, VORP: 9.3, PTS: 36.1, AST: 7.5, TRB: 6.6, TS: 61.6, TOV: 5.0 },
    T2: { PER: 29.1, WS: 13.1, VORP: 7.3, PTS: 34.3, AST: 7.5, TRB: 6.6, TS: 62.6, TOV: 4.5 } },
  { id: 3,  name: "D. Lillard",     pos: "PG", age: 31, tier: "Max", salary: 44, contractYear: 2021,
    T1: { PER: 26.9, WS: 11.6, VORP: 5.9, PTS: 30.0, AST: 8.0, TRB: 4.3, TS: 62.7, TOV: 2.9 },
    T:  { PER: 25.6, WS: 10.4, VORP: 5.0, PTS: 28.8, AST: 7.5, TRB: 4.2, TS: 62.3, TOV: 3.0 },
    T2: { PER: 18.5, WS: 1.7, VORP: 0.9, PTS: 24.0, AST: 7.3, TRB: 4.1, TS: 55.0, TOV: 2.9 } },
  { id: 4,  name: "T. Young",     pos: "PG", age: 22, tier: "Max", salary: 42, contractYear: 2021,
    T1: { PER: 23.9, WS: 5.9, VORP: 3.1, PTS: 29.6, AST: 9.3, TRB: 4.3, TS: 59.5, TOV: 4.8 },
    T:  { PER: 23.0, WS: 7.2, VORP: 3.0, PTS: 25.3, AST: 9.4, TRB: 3.9, TS: 58.9, TOV: 4.1 },
    T2: { PER: 25.4, WS: 10.0, VORP: 4.8, PTS: 28.4, AST: 9.7, TRB: 3.7, TS: 60.3, TOV: 4.0 } },
  { id: 5,  name: "Z. LaVine",     pos: "SG", age: 27, tier: "Max", salary: 43, contractYear: 2022,
    T1: { PER: 21.5, WS: 5.9, VORP: 3.1, PTS: 27.4, AST: 4.9, TRB: 5.0, TS: 63.4, TOV: 3.5 },
    T:  { PER: 20.0, WS: 5.8, VORP: 2.6, PTS: 24.4, AST: 4.5, TRB: 4.6, TS: 60.5, TOV: 2.6 },
    T2: { PER: 19.0, WS: 7.1, VORP: 2.7, PTS: 24.8, AST: 4.2, TRB: 4.5, TS: 60.7, TOV: 2.5 } },
  { id: 6,  name: "K. Towns",     pos: "C", age: 26, tier: "Max", salary: 56, contractYear: 2022,
    T1: { PER: 23.1, WS: 5.4, VORP: 2.8, PTS: 24.8, AST: 4.5, TRB: 10.6, TS: 61.2, TOV: 3.2 },
    T:  { PER: 24.1, WS: 10.3, VORP: 4.4, PTS: 24.6, AST: 3.6, TRB: 9.8, TS: 64.0, TOV: 3.1 },
    T2: { PER: 18.8, WS: 2.7, VORP: 1.2, PTS: 20.8, AST: 4.8, TRB: 8.1, TS: 61.8, TOV: 3.0 } },
  { id: 7,  name: "D. Booker",     pos: "SG", age: 25, tier: "Max", salary: 54, contractYear: 2022,
    T1: { PER: 19.2, WS: 4.9, VORP: 1.3, PTS: 25.6, AST: 4.3, TRB: 4.2, TS: 58.7, TOV: 3.1 },
    T:  { PER: 21.3, WS: 7.6, VORP: 3.6, PTS: 26.8, AST: 4.8, TRB: 5.0, TS: 57.6, TOV: 2.4 },
    T2: { PER: 22.0, WS: 6.0, VORP: 2.9, PTS: 27.8, AST: 5.5, TRB: 4.5, TS: 60.1, TOV: 2.7 } },
  { id: 8,  name: "J. Brown",     pos: "SF", age: 26, tier: "Max", salary: 61, contractYear: 2023,
    T1: { PER: 18.9, WS: 5.8, VORP: 2.2, PTS: 23.6, AST: 3.5, TRB: 6.1, TS: 57.4, TOV: 2.7 },
    T:  { PER: 19.1, WS: 5.0, VORP: 2.0, PTS: 26.6, AST: 3.5, TRB: 6.9, TS: 58.1, TOV: 2.9 },
    T2: { PER: 18.6, WS: 5.9, VORP: 1.6, PTS: 23.0, AST: 3.6, TRB: 5.5, TS: 58.0, TOV: 2.4 } },
  { id: 19,  name: "G. Hayward",     pos: "SF", age: 27, tier: "Max", salary: 32, contractYear: 2017,
    T1: { PER: 18.3, WS: 8.9, VORP: 3.3, PTS: 19.7, AST: 3.7, TRB: 5.0, TS: 55.9, TOV: 2.5 },
    T:  { PER: 22.2, WS: 10.4, VORP: 4.5, PTS: 21.9, AST: 3.5, TRB: 5.4, TS: 59.5, TOV: 1.9 },
    T2: { PER: 7.3, WS: 0.0, VORP: 0.0, PTS: 2.0, AST: 0.0, TRB: 1.0, TS: 50.0, TOV: 0.0 } },
  { id: 20,  name: "J. Wall",     pos: "PG", age: 26, tier: "Max", salary: 47, contractYear: 2017,
    T1: { PER: 19.8, WS: 5.7, VORP: 3.9, PTS: 19.9, AST: 10.2, TRB: 4.9, TS: 51.0, TOV: 4.1 },
    T:  { PER: 23.2, WS: 8.8, VORP: 4.8, PTS: 23.1, AST: 10.7, TRB: 4.2, TS: 54.1, TOV: 4.1 },
    T2: { PER: 19.1, WS: 2.7, VORP: 1.8, PTS: 19.4, AST: 9.6, TRB: 3.7, TS: 51.5, TOV: 3.9 } },
  { id: 21,  name: "B. Griffin",     pos: "PF", age: 28, tier: "Max", salary: 34, contractYear: 2018,
    T1: { PER: 22.6, WS: 7.7, VORP: 3.5, PTS: 21.6, AST: 4.9, TRB: 8.1, TS: 56.9, TOV: 2.3 },
    T:  { PER: 19.6, WS: 4.9, VORP: 2.7, PTS: 21.4, AST: 5.8, TRB: 7.4, TS: 54.4, TOV: 2.8 },
    T2: { PER: 21.0, WS: 8.0, VORP: 4.7, PTS: 24.5, AST: 5.4, TRB: 7.5, TS: 58.1, TOV: 3.4 } },
  { id: 22,  name: "A. Wiggins",     pos: "SF", age: 22, tier: "Max", salary: 30, contractYear: 2018,
    T1: { PER: 16.5, WS: 4.2, VORP: 0.2, PTS: 23.6, AST: 2.3, TRB: 4.0, TS: 53.4, TOV: 2.3 },
    T:  { PER: 13.0, WS: 2.1, VORP: -0.3, PTS: 17.7, AST: 2.0, TRB: 4.4, TS: 50.5, TOV: 1.7 },
    T2: { PER: 12.4, WS: 0.6, VORP: -0.6, PTS: 18.1, AST: 2.5, TRB: 4.8, TS: 49.3, TOV: 1.9 } },
  { id: 23,  name: "M. Conley",     pos: "PG", age: 28, tier: "Max", salary: 31, contractYear: 2016,
    T1: { PER: 18.6, WS: 6.8, VORP: 2.7, PTS: 15.8, AST: 5.4, TRB: 3.0, TS: 55.8, TOV: 2.2 },
    T:  { PER: 19.4, WS: 5.3, VORP: 2.2, PTS: 15.3, AST: 6.1, TRB: 2.9, TS: 53.8, TOV: 1.5 },
    T2: { PER: 23.2, WS: 10.0, VORP: 5.1, PTS: 20.5, AST: 6.3, TRB: 3.5, TS: 60.4, TOV: 2.3 } },
  { id: 24,  name: "B. Simmons",     pos: "PG", age: 23, tier: "Max", salary: 34, contractYear: 2020,
    T1: { PER: 20.0, WS: 8.2, VORP: 3.8, PTS: 16.9, AST: 7.7, TRB: 8.8, TS: 58.2, TOV: 3.5 },
    T:  { PER: 20.4, WS: 6.9, VORP: 2.8, PTS: 16.4, AST: 8.0, TRB: 7.8, TS: 60.2, TOV: 3.5 },
    T2: { PER: 18.3, WS: 6.0, VORP: 2.3, PTS: 14.3, AST: 6.9, TRB: 7.2, TS: 58.4, TOV: 3.0 } },
  { id: 25,  name: "T. Harris",     pos: "PF", age: 26, tier: "Max", salary: 36, contractYear: 2019,
    T1: { PER: 17.1, WS: 6.7, VORP: 2.6, PTS: 18.6, AST: 2.4, TRB: 5.5, TS: 56.5, TOV: 1.3 },
    T:  { PER: 17.2, WS: 7.1, VORP: 2.6, PTS: 20.0, AST: 2.8, TRB: 7.9, TS: 59.2, TOV: 1.8 },
    T2: { PER: 17.2, WS: 6.2, VORP: 1.8, PTS: 19.6, AST: 3.2, TRB: 6.9, TS: 55.6, TOV: 1.4 } },
  { id: 9,  name: "J. Noah",     pos: "C", age: 31, tier: "Mid", salary: 18, contractYear: 2016,
    T1: { PER: 15.3, WS: 5.6, VORP: 2.1, PTS: 7.2, AST: 4.7, TRB: 9.6, TS: 48.2, TOV: 1.8 },
    T:  { PER: 14.1, WS: 1.1, VORP: 0.6, PTS: 4.3, AST: 3.8, TRB: 8.8, TS: 40.6, TOV: 1.8 },
    T2: { PER: 15.2, WS: 2.2, VORP: 0.4, PTS: 5.0, AST: 2.2, TRB: 8.8, TS: 49.1, TOV: 1.3 } },
  { id: 10,  name: "L. Deng",     pos: "SF", age: 31, tier: "Mid", salary: 18, contractYear: 2016,
    T1: { PER: 15.5, WS: 5.4, VORP: 1.2, PTS: 14.0, AST: 1.9, TRB: 5.2, TS: 56.1, TOV: 1.5 },
    T:  { PER: 15.0, WS: 6.4, VORP: 1.7, PTS: 12.3, AST: 1.9, TRB: 6.0, TS: 54.9, TOV: 1.1 },
    T2: { PER: 10.1, WS: 0.9, VORP: 0.0, PTS: 7.6, AST: 1.3, TRB: 5.3, TS: 47.0, TOV: 0.8 } },
  { id: 11,  name: "C. Parsons",     pos: "SF", age: 27, tier: "Mid", salary: 24, contractYear: 2016,
    T1: { PER: 16.3, WS: 5.5, VORP: 2.0, PTS: 15.7, AST: 2.4, TRB: 4.9, TS: 56.7, TOV: 1.5 },
    T:  { PER: 16.2, WS: 4.3, VORP: 1.8, PTS: 13.7, AST: 2.8, TRB: 4.7, TS: 58.9, TOV: 1.6 },
    T2: { PER: 7.7, WS: 0.2, VORP: -0.3, PTS: 6.2, AST: 1.6, TRB: 2.5, TS: 43.6, TOV: 0.7 } },
  { id: 12,  name: "E. Fournier",     pos: "SG", age: 28, tier: "Mid", salary: 20, contractYear: 2021,
    T1: { PER: 16.4, WS: 4.6, VORP: 1.6, PTS: 18.5, AST: 3.2, TRB: 2.6, TS: 59.5, TOV: 1.9 },
    T:  { PER: 16.7, WS: 2.8, VORP: 1.0, PTS: 17.1, AST: 3.4, TRB: 3.0, TS: 59.8, TOV: 1.7 },
    T2: { PER: 12.3, WS: 3.7, VORP: 0.7, PTS: 14.1, AST: 2.1, TRB: 2.6, TS: 55.4, TOV: 1.3 } },
  { id: 13,  name: "T. Mozgov",     pos: "C", age: 30, tier: "Mid", salary: 16, contractYear: 2016,
    T1: { PER: 16.6, WS: 5.7, VORP: 0.7, PTS: 9.7, AST: 0.7, TRB: 7.3, TS: 59.4, TOV: 1.4 },
    T:  { PER: 14.6, WS: 3.7, VORP: 0.2, PTS: 6.3, AST: 0.4, TRB: 4.4, TS: 59.3, TOV: 0.9 },
    T2: { PER: 12.3, WS: 1.1, VORP: -0.7, PTS: 7.4, AST: 0.8, TRB: 4.9, TS: 55.3, TOV: 1.3 } },
  { id: 26,  name: "N. Batum",     pos: "SF", age: 27, tier: "Mid", salary: 24, contractYear: 2016,
    T1: { PER: 13.1, WS: 5.2, VORP: 2.4, PTS: 9.4, AST: 4.8, TRB: 5.9, TS: 51.6, TOV: 1.9 },
    T:  { PER: 15.6, WS: 5.0, VORP: 2.0, PTS: 14.9, AST: 5.8, TRB: 6.1, TS: 54.6, TOV: 2.9 },
    T2: { PER: 15.8, WS: 4.6, VORP: 1.9, PTS: 15.1, AST: 5.9, TRB: 6.2, TS: 52.9, TOV: 2.5 } },
  { id: 27,  name: "R. Anderson",     pos: "PF", age: 27, tier: "Mid", salary: 20, contractYear: 2016,
    T1: { PER: 15.6, WS: 3.5, VORP: 0.7, PTS: 13.7, AST: 0.9, TRB: 4.8, TS: 52.4, TOV: 1.0 },
    T:  { PER: 17.2, WS: 3.9, VORP: 0.9, PTS: 17.0, AST: 1.1, TRB: 6.0, TS: 54.6, TOV: 1.4 },
    T2: { PER: 13.5, WS: 5.2, VORP: 0.9, PTS: 13.6, AST: 0.9, TRB: 4.6, TS: 58.3, TOV: 0.8 } },
  { id: 28,  name: "B. Biyombo",     pos: "C", age: 23, tier: "Mid", salary: 17, contractYear: 2016,
    T1: { PER: 15.2, WS: 4.0, VORP: 0.3, PTS: 4.8, AST: 0.3, TRB: 6.4, TS: 57.8, TOV: 0.8 },
    T:  { PER: 14.9, WS: 5.9, VORP: 0.8, PTS: 5.5, AST: 0.4, TRB: 8.0, TS: 58.6, TOV: 0.9 },
    T2: { PER: 12.2, WS: 2.9, VORP: -0.6, PTS: 6.0, AST: 0.9, TRB: 7.0, TS: 54.6, TOV: 1.2 } },
  { id: 29,  name: "E. Turner",     pos: "SG", age: 27, tier: "Mid", salary: 18, contractYear: 2016,
    T1: { PER: 12.8, WS: 2.5, VORP: 0.6, PTS: 9.5, AST: 5.5, TRB: 5.1, TS: 48.2, TOV: 2.4 },
    T:  { PER: 13.6, WS: 4.0, VORP: 1.1, PTS: 10.5, AST: 4.4, TRB: 4.9, TS: 51.3, TOV: 2.1 },
    T2: { PER: 11.4, WS: 1.2, VORP: -0.2, PTS: 9.0, AST: 3.2, TRB: 3.8, TS: 49.1, TOV: 1.5 } },
  { id: 30,  name: "O. Porter Jr.",     pos: "SF", age: 23, tier: "Mid", salary: 27, contractYear: 2017,
    T1: { PER: 14.5, WS: 5.6, VORP: 1.8, PTS: 11.6, AST: 1.6, TRB: 5.2, TS: 56.4, TOV: 0.9 },
    T:  { PER: 17.3, WS: 9.4, VORP: 3.5, PTS: 13.4, AST: 1.5, TRB: 6.4, TS: 62.8, TOV: 0.6 },
    T2: { PER: 18.3, WS: 8.1, VORP: 3.4, PTS: 14.7, AST: 2.0, TRB: 6.4, TS: 60.2, TOV: 1.0 } },
  { id: 31,  name: "A. Crabbe",     pos: "SG", age: 24, tier: "Mid", salary: 19, contractYear: 2016,
    T1: { PER: 8.7, WS: 1.3, VORP: 0.2, PTS: 3.3, AST: 0.8, TRB: 1.4, TS: 52.5, TOV: 0.3 },
    T:  { PER: 12.2, WS: 4.3, VORP: 0.5, PTS: 10.3, AST: 1.2, TRB: 2.7, TS: 57.2, TOV: 0.8 },
    T2: { PER: 11.6, WS: 4.2, VORP: 0.4, PTS: 10.7, AST: 1.2, TRB: 2.9, TS: 60.2, TOV: 0.8 } },
  { id: 14,  name: "M. Dellavedova",     pos: "PG", age: 25, tier: "Low", salary: 10, contractYear: 2016,
    T1: { PER: 8.5, WS: 1.9, VORP: -0.3, PTS: 4.8, AST: 3.0, TRB: 1.9, TS: 49.3, TOV: 0.9 },
    T:  { PER: 11.3, WS: 3.8, VORP: 0.4, PTS: 7.5, AST: 4.4, TRB: 2.1, TS: 52.7, TOV: 1.5 },
    T2: { PER: 9.4, WS: 1.2, VORP: -1.1, PTS: 7.6, AST: 4.7, TRB: 1.9, TS: 50.1, TOV: 1.8 } },
  { id: 15,  name: "K. Korver",     pos: "SG", age: 33, tier: "Low", salary: 6, contractYear: 2014,
    T1: { PER: 13.9, WS: 6.4, VORP: 2.2, PTS: 10.9, AST: 2.0, TRB: 4.0, TS: 63.7, TOV: 0.9 },
    T:  { PER: 13.5, WS: 5.9, VORP: 1.9, PTS: 12.0, AST: 2.9, TRB: 4.0, TS: 65.3, TOV: 1.4 },
    T2: { PER: 14.8, WS: 7.5, VORP: 3.0, PTS: 12.1, AST: 2.6, TRB: 4.1, TS: 69.9, TOV: 1.4 } },
  { id: 16,  name: "P. Beverley",     pos: "PG", age: 29, tier: "Low", salary: 7, contractYear: 2017,
    T1: { PER: 13.0, WS: 4.4, VORP: 1.1, PTS: 9.9, AST: 3.4, TRB: 3.5, TS: 55.3, TOV: 1.3 },
    T:  { PER: 13.0, WS: 5.3, VORP: 1.6, PTS: 9.5, AST: 4.2, TRB: 5.9, TS: 54.6, TOV: 1.5 },
    T2: { PER: 12.4, WS: 0.4, VORP: 0.2, PTS: 12.2, AST: 2.9, TRB: 4.1, TS: 53.0, TOV: 2.3 } },
  { id: 17,  name: "M. Belinelli",     pos: "SG", age: 31, tier: "Low", salary: 7, contractYear: 2017,
    T1: { PER: 9.4, WS: 0.5, VORP: -0.8, PTS: 10.2, AST: 1.9, TRB: 1.7, TS: 50.0, TOV: 1.2 },
    T:  { PER: 13.3, WS: 3.2, VORP: 0.4, PTS: 10.5, AST: 2.0, TRB: 2.4, TS: 56.6, TOV: 0.9 },
    T2: { PER: 14.1, WS: 3.7, VORP: 0.8, PTS: 12.1, AST: 1.9, TRB: 1.9, TS: 58.1, TOV: 1.2 } },
  { id: 18,  name: "T. Sefolosha",     pos: "SF", age: 30, tier: "Low", salary: 6, contractYear: 2014,
    T1: { PER: 12.8, WS: 6.8, VORP: 2.5, PTS: 7.6, AST: 1.5, TRB: 3.9, TS: 61.7, TOV: 0.8 },
    T:  { PER: 10.4, WS: 3.0, VORP: 0.9, PTS: 6.3, AST: 1.5, TRB: 3.6, TS: 51.7, TOV: 0.9 },
    T2: { PER: 13.8, WS: 2.5, VORP: 0.8, PTS: 5.3, AST: 1.4, TRB: 4.3, TS: 50.6, TOV: 0.7 } },
  { id: 32,  name: "M. Carter-Williams",     pos: "PG", age: 23, tier: "Low", salary: 11, contractYear: 2015,
    T1: { PER: 15.5, WS: 1.3, VORP: 0.9, PTS: 16.7, AST: 6.3, TRB: 6.2, TS: 48.0, TOV: 3.5 },
    T:  { PER: 14.1, WS: 0.8, VORP: 0.5, PTS: 14.6, AST: 6.7, TRB: 5.3, TS: 46.1, TOV: 3.8 },
    T2: { PER: 13.9, WS: 1.2, VORP: 0.5, PTS: 11.5, AST: 5.2, TRB: 5.1, TS: 49.7, TOV: 2.8 } },
  { id: 33,  name: "C. Joseph",     pos: "PG", age: 24, tier: "Low", salary: 9, contractYear: 2016,
    T1: { PER: 15.5, WS: 4.5, VORP: 1.2, PTS: 6.8, AST: 2.4, TRB: 2.4, TS: 56.4, TOV: 0.8 },
    T:  { PER: 12.4, WS: 3.5, VORP: 0.4, PTS: 8.5, AST: 3.1, TRB: 2.6, TS: 51.2, TOV: 1.3 },
    T2: { PER: 13.2, WS: 3.4, VORP: 0.4, PTS: 9.3, AST: 3.3, TRB: 2.9, TS: 51.8, TOV: 1.4 } },
  { id: 34,  name: "J. Clarkson",     pos: "SG", age: 24, tier: "Low", salary: 13, contractYear: 2016,
    T1: { PER: 16.9, WS: 2.4, VORP: 0.8, PTS: 11.9, AST: 3.5, TRB: 3.2, TS: 52.8, TOV: 1.6 },
    T:  { PER: 14.3, WS: 2.1, VORP: 0.2, PTS: 15.5, AST: 2.4, TRB: 4.0, TS: 51.6, TOV: 1.7 },
    T2: { PER: 13.2, WS: 1.2, VORP: -0.3, PTS: 14.7, AST: 2.6, TRB: 3.0, TS: 52.6, TOV: 2.0 } },
  { id: 35,  name: "R. Hood",     pos: "SG", age: 23, tier: "Low", salary: 12, contractYear: 2016,
    T1: { PER: 12.3, WS: 2.2, VORP: 0.3, PTS: 8.7, AST: 1.7, TRB: 2.3, TS: 52.9, TOV: 0.9 },
    T:  { PER: 14.1, WS: 6.0, VORP: 1.7, PTS: 14.5, AST: 2.7, TRB: 3.4, TS: 54.2, TOV: 1.6 },
    T2: { PER: 12.4, WS: 2.6, VORP: 0.4, PTS: 12.7, AST: 1.6, TRB: 3.4, TS: 52.2, TOV: 1.1 } },
  { id: 36,  name: "LeBron James",     pos: "SF", age: 25, tier: "Max", salary: 17, contractYear: 2010,
    T1: { PER: 31.7, WS: 20.3, VORP: 11.8, PTS: 28.4, AST: 7.2, TRB: 7.6, TS: 59.1, TOV: 3.0 },
    T:  { PER: 31.1, WS: 18.5, VORP: 10.3, PTS: 29.7, AST: 8.6, TRB: 7.3, TS: 60.4, TOV: 3.4 },
    T2: { PER: 27.3, WS: 15.6, VORP: 7.8, PTS: 26.7, AST: 7.0, TRB: 7.5, TS: 59.4, TOV: 3.6 } },
  { id: 37,  name: "C. Bosh",     pos: "C", age: 26, tier: "Max", salary: 18, contractYear: 2010,
    T1: { PER: 22.1, WS: 9.7, VORP: 3.5, PTS: 22.7, AST: 2.5, TRB: 10.0, TS: 56.9, TOV: 2.3 },
    T:  { PER: 25.0, WS: 9.6, VORP: 3.6, PTS: 24.0, AST: 2.4, TRB: 10.8, TS: 59.2, TOV: 2.4 },
    T2: { PER: 19.4, WS: 10.3, VORP: 2.3, PTS: 18.7, AST: 1.9, TRB: 8.3, TS: 56.9, TOV: 1.8 } },
  { id: 38,  name: "K. Durant",     pos: "SF", age: 27, tier: "Max", salary: 27, contractYear: 2016,
    T1: { PER: 27.6, WS: 4.8, VORP: 2.8, PTS: 25.4, AST: 4.1, TRB: 6.6, TS: 63.3, TOV: 2.7 },
    T:  { PER: 28.2, WS: 14.5, VORP: 7.8, PTS: 28.2, AST: 5.0, TRB: 8.2, TS: 63.4, TOV: 3.5 },
    T2: { PER: 27.6, WS: 12.0, VORP: 5.7, PTS: 25.1, AST: 4.8, TRB: 8.3, TS: 65.1, TOV: 2.2 } },
  { id: 39,  name: "C. Paul",     pos: "PG", age: 32, tier: "Max", salary: 35, contractYear: 2017,
    T1: { PER: 26.2, WS: 12.7, VORP: 6.0, PTS: 19.5, AST: 10.0, TRB: 4.2, TS: 57.5, TOV: 2.6 },
    T:  { PER: 26.2, WS: 10.6, VORP: 5.2, PTS: 18.1, AST: 9.2, TRB: 5.0, TS: 61.4, TOV: 2.4 },
    T2: { PER: 24.4, WS: 10.2, VORP: 4.2, PTS: 18.6, AST: 7.9, TRB: 5.4, TS: 60.4, TOV: 2.2 } },
  { id: 40,  name: "C. Anthony",     pos: "SF", age: 30, tier: "Max", salary: 25, contractYear: 2014,
    T1: { PER: 24.8, WS: 9.5, VORP: 3.9, PTS: 28.7, AST: 2.6, TRB: 6.9, TS: 56.0, TOV: 2.6 },
    T:  { PER: 24.4, WS: 10.7, VORP: 5.3, PTS: 27.4, AST: 3.1, TRB: 8.1, TS: 56.1, TOV: 2.6 },
    T2: { PER: 21.5, WS: 2.9, VORP: 1.8, PTS: 24.2, AST: 3.1, TRB: 6.6, TS: 53.1, TOV: 2.2 } },
  { id: 41,  name: "P. George",     pos: "SF", age: 28, tier: "Max", salary: 34, contractYear: 2018,
    T1: { PER: 20.2, WS: 7.1, VORP: 3.4, PTS: 23.7, AST: 3.3, TRB: 6.6, TS: 58.7, TOV: 2.9 },
    T:  { PER: 18.7, WS: 8.9, VORP: 3.6, PTS: 21.9, AST: 3.3, TRB: 5.7, TS: 57.0, TOV: 2.7 },
    T2: { PER: 23.3, WS: 11.9, VORP: 6.6, PTS: 28.0, AST: 4.1, TRB: 8.2, TS: 58.3, TOV: 2.7 } },
  { id: 42,  name: "K. Leonard",     pos: "SF", age: 28, tier: "Max", salary: 36, contractYear: 2019,
    T1: { PER: 26.0, WS: 0.9, VORP: 0.6, PTS: 16.2, AST: 2.3, TRB: 4.7, TS: 57.2, TOV: 1.8 },
    T:  { PER: 25.8, WS: 9.5, VORP: 4.7, PTS: 26.6, AST: 3.3, TRB: 7.3, TS: 60.6, TOV: 2.0 },
    T2: { PER: 26.9, WS: 8.7, VORP: 5.1, PTS: 27.1, AST: 4.9, TRB: 7.1, TS: 58.9, TOV: 2.6 } },
  { id: 43,  name: "J. Butler",     pos: "SF", age: 29, tier: "Max", salary: 36, contractYear: 2019,
    T1: { PER: 23.7, WS: 8.9, VORP: 4.2, PTS: 22.2, AST: 4.9, TRB: 5.3, TS: 59.0, TOV: 1.8 },
    T:  { PER: 20.2, WS: 7.9, VORP: 3.2, PTS: 18.7, AST: 4.0, TRB: 5.3, TS: 57.1, TOV: 1.5 },
    T2: { PER: 23.6, WS: 9.0, VORP: 3.7, PTS: 19.9, AST: 6.0, TRB: 6.7, TS: 58.5, TOV: 2.2 } },
  { id: 44,  name: "L. Aldridge",     pos: "PF", age: 30, tier: "Max", salary: 21, contractYear: 2015,
    T1: { PER: 21.8, WS: 7.5, VORP: 2.7, PTS: 23.2, AST: 2.6, TRB: 11.1, TS: 50.7, TOV: 1.8 },
    T:  { PER: 22.8, WS: 8.6, VORP: 3.1, PTS: 23.4, AST: 1.7, TRB: 10.2, TS: 52.8, TOV: 1.7 },
    T2: { PER: 22.4, WS: 10.1, VORP: 2.5, PTS: 18.0, AST: 1.5, TRB: 8.5, TS: 56.5, TOV: 1.3 } },
  { id: 45,  name: "K. Love",     pos: "PF", age: 26, tier: "Max", salary: 22, contractYear: 2015,
    T1: { PER: 26.9, WS: 14.3, VORP: 7.7, PTS: 26.1, AST: 4.4, TRB: 12.5, TS: 59.1, TOV: 2.5 },
    T:  { PER: 18.8, WS: 8.7, VORP: 3.0, PTS: 16.4, AST: 2.2, TRB: 9.7, TS: 56.2, TOV: 1.6 },
    T2: { PER: 19.0, WS: 8.5, VORP: 3.3, PTS: 16.0, AST: 2.4, TRB: 9.9, TS: 55.3, TOV: 1.8 } },
  { id: 46,  name: "K. Lowry",     pos: "PG", age: 31, tier: "Max", salary: 33, contractYear: 2017,
    T1: { PER: 22.2, WS: 11.6, VORP: 5.7, PTS: 21.2, AST: 6.4, TRB: 4.7, TS: 57.8, TOV: 2.9 },
    T:  { PER: 22.9, WS: 10.1, VORP: 4.6, PTS: 22.4, AST: 7.0, TRB: 4.8, TS: 62.3, TOV: 2.9 },
    T2: { PER: 19.5, WS: 10.2, VORP: 4.5, PTS: 16.2, AST: 6.9, TRB: 5.6, TS: 59.8, TOV: 2.3 } },
  { id: 47,  name: "Giannis",     pos: "PF", age: 25, tier: "Max", salary: 39, contractYear: 2020,
    T1: { PER: 30.9, WS: 14.4, VORP: 7.4, PTS: 27.7, AST: 5.9, TRB: 12.5, TS: 64.4, TOV: 3.7 },
    T:  { PER: 31.9, WS: 11.1, VORP: 6.6, PTS: 29.5, AST: 5.6, TRB: 13.6, TS: 61.3, TOV: 3.7 },
    T2: { PER: 29.2, WS: 10.2, VORP: 5.6, PTS: 28.1, AST: 5.9, TRB: 11.0, TS: 63.3, TOV: 3.4 } },
  { id: 48,  name: "A. Davis",     pos: "PF", age: 27, tier: "Max", salary: 42, contractYear: 2020,
    T1: { PER: 30.3, WS: 9.5, VORP: 5.3, PTS: 25.9, AST: 3.9, TRB: 12.0, TS: 59.7, TOV: 2.0 },
    T:  { PER: 27.4, WS: 11.1, VORP: 5.4, PTS: 26.1, AST: 3.2, TRB: 9.3, TS: 61.0, TOV: 2.5 },
    T2: { PER: 22.1, WS: 3.7, VORP: 2.0, PTS: 21.8, AST: 3.1, TRB: 7.9, TS: 55.6, TOV: 2.1 } },
  { id: 49,  name: "M. Gasol",     pos: "C", age: 30, tier: "Mid", salary: 23, contractYear: 2015,
    T1: { PER: 18.2, WS: 5.6, VORP: 2.5, PTS: 14.6, AST: 3.6, TRB: 7.2, TS: 52.6, TOV: 1.9 },
    T:  { PER: 21.7, WS: 10.2, VORP: 4.8, PTS: 17.4, AST: 3.8, TRB: 7.8, TS: 55.8, TOV: 2.2 },
    T2: { PER: 17.7, WS: 3.7, VORP: 1.7, PTS: 16.6, AST: 3.8, TRB: 7.0, TS: 52.8, TOV: 2.3 } },
  { id: 50,  name: "D. Jordan",     pos: "C", age: 27, tier: "Mid", salary: 22, contractYear: 2015,
    T1: { PER: 18.2, WS: 11.1, VORP: 3.3, PTS: 10.4, AST: 0.9, TRB: 13.6, TS: 63.0, TOV: 1.5 },
    T:  { PER: 21.0, WS: 12.8, VORP: 3.5, PTS: 11.5, AST: 0.7, TRB: 15.0, TS: 63.8, TOV: 1.3 },
    T2: { PER: 20.6, WS: 11.5, VORP: 3.2, PTS: 12.7, AST: 1.2, TRB: 13.8, TS: 62.8, TOV: 1.4 } },
  { id: 51,  name: "H. Whiteside",     pos: "C", age: 27, tier: "Mid", salary: 25, contractYear: 2016,
    T1: { PER: 26.2, WS: 5.3, VORP: 1.8, PTS: 11.8, AST: 0.1, TRB: 10.0, TS: 61.9, TOV: 1.2 },
    T:  { PER: 25.6, WS: 10.3, VORP: 3.3, PTS: 14.2, AST: 0.4, TRB: 11.8, TS: 62.9, TOV: 1.9 },
    T2: { PER: 22.6, WS: 9.5, VORP: 2.2, PTS: 17.0, AST: 0.7, TRB: 14.1, TS: 57.9, TOV: 2.0 } },
  { id: 52,  name: "E. Kanter",     pos: "C", age: 23, tier: "Mid", salary: 18, contractYear: 2015,
    T1: { PER: 15.6, WS: 2.2, VORP: -0.9, PTS: 12.3, AST: 0.9, TRB: 7.5, TS: 52.3, TOV: 1.8 },
    T:  { PER: 20.3, WS: 6.4, VORP: 0.6, PTS: 15.5, AST: 0.7, TRB: 8.9, TS: 56.4, TOV: 1.9 },
    T2: { PER: 24.0, WS: 8.1, VORP: 1.4, PTS: 12.7, AST: 0.4, TRB: 8.1, TS: 62.6, TOV: 1.4 } },
  { id: 53,  name: "K. Middleton",     pos: "SF", age: 24, tier: "Mid", salary: 14, contractYear: 2015,
    T1: { PER: 12.5, WS: 2.7, VORP: -0.2, PTS: 12.1, AST: 2.1, TRB: 3.8, TS: 54.1, TOV: 1.5 },
    T:  { PER: 15.6, WS: 6.7, VORP: 2.2, PTS: 13.4, AST: 2.3, TRB: 4.4, TS: 56.3, TOV: 1.4 },
    T2: { PER: 16.8, WS: 6.1, VORP: 1.9, PTS: 18.2, AST: 4.2, TRB: 3.8, TS: 56.0, TOV: 2.3 } },
  { id: 54,  name: "A. Horford",     pos: "C", age: 33, tier: "Mid", salary: 27, contractYear: 2019,
    T1: { PER: 17.6, WS: 7.8, VORP: 3.7, PTS: 12.9, AST: 4.7, TRB: 7.4, TS: 57.5, TOV: 1.8 },
    T:  { PER: 20.2, WS: 7.5, VORP: 3.6, PTS: 13.6, AST: 4.2, TRB: 6.7, TS: 60.5, TOV: 1.5 },
    T2: { PER: 15.7, WS: 5.4, VORP: 2.2, PTS: 11.9, AST: 4.0, TRB: 6.8, TS: 53.6, TOV: 1.2 } },
  { id: 55,  name: "S. Ibaka",     pos: "PF", age: 27, tier: "Mid", salary: 22, contractYear: 2017,
    T1: { PER: 13.9, WS: 5.5, VORP: 0.8, PTS: 12.6, AST: 0.8, TRB: 6.8, TS: 53.3, TOV: 1.4 },
    T:  { PER: 16.4, WS: 5.1, VORP: 1.2, PTS: 14.8, AST: 0.9, TRB: 6.8, TS: 56.6, TOV: 1.3 },
    T2: { PER: 14.7, WS: 5.1, VORP: 1.0, PTS: 12.6, AST: 0.8, TRB: 6.3, TS: 57.4, TOV: 1.2 } },
  { id: 56,  name: "J. Teague",     pos: "PG", age: 29, tier: "Mid", salary: 16, contractYear: 2017,
    T1: { PER: 17.9, WS: 5.9, VORP: 1.9, PTS: 15.7, AST: 5.9, TRB: 2.7, TS: 55.1, TOV: 2.8 },
    T:  { PER: 19.2, WS: 8.1, VORP: 2.8, PTS: 15.3, AST: 7.8, TRB: 4.0, TS: 57.4, TOV: 2.6 },
    T2: { PER: 16.4, WS: 4.9, VORP: 1.4, PTS: 14.2, AST: 7.0, TRB: 3.0, TS: 55.3, TOV: 2.5 } },
  { id: 57,  name: "S. Hill",     pos: "SF", age: 24, tier: "Mid", salary: 13, contractYear: 2016,
    T1: { PER: 10.2, WS: 3.5, VORP: 0.3, PTS: 8.9, AST: 2.2, TRB: 3.8, TS: 50.7, TOV: 1.4 },
    T:  { PER: 12.2, WS: 2.1, VORP: 0.5, PTS: 4.2, AST: 1.0, TRB: 2.8, TS: 54.3, TOV: 0.6 },
    T2: { PER: 8.0, WS: 2.7, VORP: -0.4, PTS: 7.0, AST: 1.8, TRB: 3.8, TS: 52.7, TOV: 1.0 } },
  { id: 58,  name: "G. Monroe",     pos: "C", age: 25, tier: "Mid", salary: 17, contractYear: 2015,
    T1: { PER: 18.1, WS: 5.9, VORP: 1.4, PTS: 15.2, AST: 2.1, TRB: 9.3, TS: 53.1, TOV: 2.0 },
    T:  { PER: 21.2, WS: 6.8, VORP: 2.1, PTS: 15.9, AST: 2.1, TRB: 10.2, TS: 54.9, TOV: 2.2 },
    T2: { PER: 21.8, WS: 7.5, VORP: 2.4, PTS: 15.3, AST: 2.3, TRB: 8.8, TS: 56.2, TOV: 1.6 } },
  { id: 59,  name: "A. Jefferson",     pos: "C", age: 28, tier: "Mid", salary: 14, contractYear: 2013,
    T1: { PER: 22.8, WS: 7.5, VORP: 3.0, PTS: 19.2, AST: 2.2, TRB: 9.6, TS: 52.0, TOV: 1.0 },
    T:  { PER: 20.9, WS: 7.7, VORP: 2.8, PTS: 17.8, AST: 2.1, TRB: 9.2, TS: 52.2, TOV: 1.3 },
    T2: { PER: 22.7, WS: 7.8, VORP: 3.0, PTS: 21.8, AST: 2.1, TRB: 10.8, TS: 53.2, TOV: 1.7 } },
  { id: 60,  name: "T. Evans",     pos: "SG", age: 27, tier: "Mid", salary: 16, contractYear: 2017,
    T1: { PER: 17.9, WS: 1.4, VORP: 0.7, PTS: 15.2, AST: 6.6, TRB: 5.2, TS: 53.4, TOV: 2.9 },
    T:  { PER: 15.5, WS: 0.7, VORP: 0.5, PTS: 10.3, AST: 3.1, TRB: 3.4, TS: 50.1, TOV: 1.5 },
    T2: { PER: 21.1, WS: 4.2, VORP: 2.6, PTS: 19.4, AST: 5.2, TRB: 5.1, TS: 56.1, TOV: 2.3 } },
  { id: 61,  name: "D. Williams",     pos: "PG", age: 28, tier: "Mid", salary: 20, contractYear: 2012,
    T1: { PER: 21.1, WS: 7.3, VORP: 3.1, PTS: 20.1, AST: 10.3, TRB: 4.0, TS: 56.6, TOV: 3.5 },
    T:  { PER: 20.3, WS: 4.1, VORP: 2.2, PTS: 21.0, AST: 8.7, TRB: 3.3, TS: 52.7, TOV: 4.0 },
    T2: { PER: 20.3, WS: 10.9, VORP: 4.2, PTS: 18.9, AST: 7.7, TRB: 3.0, TS: 57.4, TOV: 2.8 } },
  { id: 62,  name: "T. Chandler",     pos: "C", age: 28, tier: "Mid", salary: 15, contractYear: 2011,
    T1: { PER: 12.5, WS: 2.9, VORP: 0.0, PTS: 6.5, AST: 0.3, TRB: 6.3, TS: 64.3, TOV: 1.8 },
    T:  { PER: 18.4, WS: 9.4, VORP: 1.8, PTS: 10.1, AST: 0.4, TRB: 9.4, TS: 69.7, TOV: 1.2 },
    T2: { PER: 18.7, WS: 9.5, VORP: 2.2, PTS: 11.3, AST: 0.9, TRB: 9.9, TS: 70.8, TOV: 1.6 } },
  { id: 63,  name: "E. Bledsoe",     pos: "PG", age: 25, tier: "Mid", salary: 14, contractYear: 2015,
    T1: { PER: 19.6, WS: 4.1, VORP: 1.8, PTS: 17.7, AST: 5.5, TRB: 4.7, TS: 57.8, TOV: 3.3 },
    T:  { PER: 18.4, WS: 7.0, VORP: 2.9, PTS: 17.0, AST: 6.1, TRB: 5.2, TS: 55.5, TOV: 3.4 },
    T2: { PER: 20.0, WS: 2.5, VORP: 1.4, PTS: 20.4, AST: 6.1, TRB: 4.0, TS: 55.7, TOV: 3.5 } },
  { id: 64,  name: "D. Lee",     pos: "PF", age: 27, tier: "Mid", salary: 13, contractYear: 2010,
    T1: { PER: 19.0, WS: 9.0, VORP: 2.0, PTS: 16.0, AST: 2.1, TRB: 11.7, TS: 59.0, TOV: 1.9 },
    T:  { PER: 22.2, WS: 10.3, VORP: 3.5, PTS: 20.2, AST: 3.6, TRB: 11.7, TS: 58.4, TOV: 2.3 },
    T2: { PER: 17.8, WS: 6.0, VORP: 1.1, PTS: 16.5, AST: 3.2, TRB: 9.8, TS: 54.9, TOV: 2.3 } },
  { id: 65,  name: "P. Gasol",     pos: "C", age: 34, tier: "Low", salary: 7, contractYear: 2014,
    T1: { PER: 16.7, WS: 3.7, VORP: 1.7, PTS: 13.7, AST: 4.1, TRB: 8.6, TS: 51.2, TOV: 2.1 },
    T:  { PER: 19.3, WS: 3.0, VORP: 1.5, PTS: 17.4, AST: 3.4, TRB: 9.7, TS: 52.2, TOV: 2.4 },
    T2: { PER: 22.7, WS: 10.4, VORP: 3.7, PTS: 18.5, AST: 2.7, TRB: 11.8, TS: 55.0, TOV: 2.0 } },
  { id: 66,  name: "L. Stephenson",     pos: "SG", age: 23, tier: "Low", salary: 9, contractYear: 2014,
    T1: { PER: 11.8, WS: 5.5, VORP: 1.2, PTS: 8.8, AST: 2.9, TRB: 3.9, TS: 53.0, TOV: 1.4 },
    T:  { PER: 14.7, WS: 7.4, VORP: 2.3, PTS: 13.8, AST: 4.6, TRB: 7.2, TS: 56.4, TOV: 2.7 },
    T2: { PER: 8.8, WS: -0.9, VORP: -1.0, PTS: 8.2, AST: 3.9, TRB: 4.5, TS: 41.9, TOV: 2.1 } },
  { id: 67,  name: "M. Gortat",     pos: "C", age: 30, tier: "Low", salary: 12, contractYear: 2014,
    T1: { PER: 15.4, WS: 3.4, VORP: 0.7, PTS: 11.1, AST: 1.2, TRB: 8.5, TS: 54.3, TOV: 1.6 },
    T:  { PER: 17.6, WS: 8.1, VORP: 1.8, PTS: 13.2, AST: 1.7, TRB: 9.5, TS: 56.8, TOV: 1.6 },
    T2: { PER: 18.2, WS: 8.6, VORP: 2.1, PTS: 12.2, AST: 1.2, TRB: 8.7, TS: 58.7, TOV: 1.2 } },
  { id: 68,  name: "J. Lin",     pos: "PG", age: 26, tier: "Low", salary: 12, contractYear: 2014,
    T1: { PER: 14.9, WS: 5.4, VORP: 1.5, PTS: 13.4, AST: 6.1, TRB: 3.0, TS: 53.8, TOV: 2.9 },
    T:  { PER: 14.3, WS: 4.4, VORP: 0.9, PTS: 12.5, AST: 4.1, TRB: 2.6, TS: 57.2, TOV: 2.5 },
    T2: { PER: 15.6, WS: 2.7, VORP: 0.8, PTS: 11.2, AST: 4.6, TRB: 2.6, TS: 53.9, TOV: 2.2 } }
];

function computeRisk(p) {
  const perDrop  = +((p.T.PER  - p.T2.PER)  / p.T.PER  * 100).toFixed(1);
  const tsDrop   = +((p.T.TS   - p.T2.TS)   / p.T.TS   * 100).toFixed(1);
  const wsDrop   = +((p.T.WS   - p.T2.WS)   / p.T.WS   * 100).toFixed(1);
  const ptsDiff  = +(p.T2.PTS - p.T.PTS).toFixed(1);
  const cEffect  = +((p.T.PER  - p.T1.PER)  / p.T1.PER * 100).toFixed(1);
  const riskScore = Math.min(100, Math.max(0, Math.round(
    perDrop * 2.1 + tsDrop * 2.8 + (p.age > 28 ? 14 : 0) + (p.tier === "Max" ? 6 : 0) - (p.age < 25 ? 8 : 0)
  )));
  const riskTier = riskScore >= 55 ? "HIGH" : riskScore >= 30 ? "MED" : "LOW";
  return { ...p, perDrop, tsDrop, wsDrop, ptsDiff, cEffect, riskScore, riskTier };
}

const DATA = PLAYERS.map(computeRisk);

function riskColor(score) {
  if (score >= 55) return "#e63946";
  if (score >= 30) return "#f5a623";
  return "#2ecc71";
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="tooltip-custom">
      <div style={{ color: "#f5a623", marginBottom: 4, fontSize: 10, letterSpacing: 1 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || "#c8d8e8", fontSize: 11 }}>
          {p.name}: <strong>{typeof p.value === "number" ? p.value.toFixed(1) : p.value}</strong>
        </div>
      ))}
    </div>
  );
};

export default function App() {
  const [selectedId, setSelectedId] = useState(11);
  const [tierFilter, setTierFilter] = useState("ALL");
  const [ageFilter, setAgeFilter] = useState("ALL");
  const [activeTab, setActiveTab] = useState("OVERVIEW");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const filtered = useMemo(() => DATA.filter(p =>
    (tierFilter === "ALL" || p.tier === tierFilter) &&
    (ageFilter === "ALL" || (ageFilter === "28+" ? p.age > 28 : p.age <= 28))
  ), [tierFilter, ageFilter]);

  const selected = DATA.find(p => p.id === selectedId);

  // ── Aggregate stats ──────────────────────────────────────────────
  const avgPERDrop = (DATA.reduce((s, p) => s + p.perDrop, 0) / DATA.length).toFixed(1);
  const maxAvgDrop = (DATA.filter(p => p.tier === "Max").reduce((s, p) => s + p.perDrop, 0) / DATA.filter(p => p.tier === "Max").length).toFixed(1);
  const midAvgDrop = (DATA.filter(p => p.tier === "Mid").reduce((s, p) => s + p.perDrop, 0) / DATA.filter(p => p.tier === "Mid").length).toFixed(1);
  const lowAvgDrop = (DATA.filter(p => p.tier === "Low").reduce((s, p) => s + p.perDrop, 0) / DATA.filter(p => p.tier === "Low").length).toFixed(1);
  const over28Avg  = (DATA.filter(p => p.age > 28).reduce((s, p) => s + p.perDrop, 0) / DATA.filter(p => p.age > 28).length).toFixed(1);

  // ── Chart data ───────────────────────────────────────────────────
  const perDropBar = [...DATA].sort((a, b) => b.perDrop - a.perDrop).map(p => ({
    name: p.name.split(" ")[1] || p.name,
    perDrop: p.perDrop,
    tier: p.tier,
    risk: p.riskScore,
  }));

  const tierCompare = [
    { phase: "T-1 (Pre)",  Max: DATA.filter(p=>p.tier==="Max").reduce((s,p)=>s+p.T1.PER,0)/DATA.filter(p=>p.tier==="Max").length,
      Mid: DATA.filter(p=>p.tier==="Mid").reduce((s,p)=>s+p.T1.PER,0)/DATA.filter(p=>p.tier==="Mid").length,
      Low: DATA.filter(p=>p.tier==="Low").reduce((s,p)=>s+p.T1.PER,0)/DATA.filter(p=>p.tier==="Low").length },
    { phase: "T (Peak)",   Max: DATA.filter(p=>p.tier==="Max").reduce((s,p)=>s+p.T.PER,0)/DATA.filter(p=>p.tier==="Max").length,
      Mid: DATA.filter(p=>p.tier==="Mid").reduce((s,p)=>s+p.T.PER,0)/DATA.filter(p=>p.tier==="Mid").length,
      Low: DATA.filter(p=>p.tier==="Low").reduce((s,p)=>s+p.T.PER,0)/DATA.filter(p=>p.tier==="Low").length },
    { phase: "T+1 (Deal)", Max: DATA.filter(p=>p.tier==="Max").reduce((s,p)=>s+p.T2.PER,0)/DATA.filter(p=>p.tier==="Max").length,
      Mid: DATA.filter(p=>p.tier==="Mid").reduce((s,p)=>s+p.T2.PER,0)/DATA.filter(p=>p.tier==="Mid").length,
      Low: DATA.filter(p=>p.tier==="Low").reduce((s,p)=>s+p.T2.PER,0)/DATA.filter(p=>p.tier==="Low").length },
  ];

  const efficiencyTrap = DATA.map(p => ({
    name: p.name.split(" ")[1] || p.name,
    ptsDiff: p.ptsDiff,
    tsDrop: p.tsDrop,
    risk: p.riskScore,
  }));

  const ageBuckets = [
    { age: "≤23", PERDrop: DATA.filter(p=>p.age<=23).reduce((s,p)=>s+p.perDrop,0)/Math.max(1,DATA.filter(p=>p.age<=23).length) },
    { age: "24-26", PERDrop: DATA.filter(p=>p.age>=24&&p.age<=26).reduce((s,p)=>s+p.perDrop,0)/Math.max(1,DATA.filter(p=>p.age>=24&&p.age<=26).length) },
    { age: "27-28", PERDrop: DATA.filter(p=>p.age>=27&&p.age<=28).reduce((s,p)=>s+p.perDrop,0)/Math.max(1,DATA.filter(p=>p.age>=27&&p.age<=28).length) },
    { age: "29-31", PERDrop: DATA.filter(p=>p.age>=29&&p.age<=31).reduce((s,p)=>s+p.perDrop,0)/Math.max(1,DATA.filter(p=>p.age>=29&&p.age<=31).length) },
    { age: "32+",  PERDrop: DATA.filter(p=>p.age>=32).reduce((s,p)=>s+p.perDrop,0)/Math.max(1,DATA.filter(p=>p.age>=32).length) },
  ];

  // Player trajectory
  const trajectory = selected ? [
    { phase: "T−1  Pre-Contract", PER: selected.T1.PER, TS: selected.T1.TS, PTS: selected.T1.PTS, WS: selected.T1.WS },
    { phase: "T  Contract Year",  PER: selected.T.PER,  TS: selected.T.TS,  PTS: selected.T.PTS,  WS: selected.T.WS  },
    { phase: "T+1  Payday",       PER: selected.T2.PER, TS: selected.T2.TS, PTS: selected.T2.PTS, WS: selected.T2.WS },
  ] : [];

  const radarData = selected ? [
    { metric: "PER Drop",  value: Math.min(100, selected.perDrop * 3.5) },
    { metric: "TS Drop",   value: Math.min(100, selected.tsDrop * 4.0) },
    { metric: "Age Risk",  value: selected.age > 31 ? 90 : selected.age > 28 ? 60 : 25 },
    { metric: "Tier Risk", value: selected.tier === "Max" ? 65 : selected.tier === "Mid" ? 40 : 20 },
    { metric: "C-Effect",  value: Math.min(100, selected.cEffect * 4.5) },
  ] : [];

  function getRiskFlags(p) {
    const flags = [];
    if (p.perDrop > 15)  flags.push({ label: "SEVERE PER REGRESSION", cls: "high" });
    if (p.perDrop > 8)   flags.push({ label: "PER DIP DETECTED", cls: "med" });
    if (p.tsDrop > 4)    flags.push({ label: "EFFICIENCY TRAP", cls: "high" });
    if (p.tsDrop > 2)    flags.push({ label: "TS% DECLINE", cls: "med" });
    if (p.age > 28)      flags.push({ label: "AGE RISK >28", cls: "high" });
    if (p.tier === "Max" && p.perDrop > 10) flags.push({ label: "MAX CONTRACT HAZARD", cls: "high" });
    if (p.ptsDiff > -1 && p.tsDrop > 2) flags.push({ label: "STAT-PADDING PATTERN", cls: "med" });
    if (p.riskScore < 25) flags.push({ label: "LOW RISK", cls: "low" });
    return flags;
  }

  return (
    <div className="dash-root">
      <style>{STYLE}</style>
      <div className="scanline" />

      {/* HEADER */}
      <div className="header">
        <button className="menu-btn" onClick={() => setSidebarOpen(o => !o)}>☰</button>
        <div>
          <div className="header-title">GUARANTEED <span>WEALTH</span> INDEX</div>
          <div className="header-sub">NBA Contract Moral Hazard & Performance Risk Dashboard · 2010–2025</div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
          <div className="header-badge"><div className="pulse" />LIVE MODEL · v2.4</div>
          <div style={{ fontSize: 9, color: "#2a3f52", letterSpacing: 1 }}>
            N = {DATA.length} PLAYERS · MAX + MID + LOW CONTRACTS
          </div>
        </div>
      </div>

      {sidebarOpen && (
        <div
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", zIndex: 199 }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="layout">
        {/* SIDEBAR */}
        <div className={`sidebar${sidebarOpen ? " open" : ""}`}>
          <div className="sidebar-mobile-header">
            <span style={{ fontSize: 10, letterSpacing: 2, color: "var(--muted)", textTransform: "uppercase" }}>Filters</span>
            <button className="sidebar-close-btn" onClick={() => setSidebarOpen(false)}>×</button>
          </div>
          <div className="sidebar-section">
            <div className="section-label">Contract Tier</div>
            <div className="filter-row">
              {["ALL","Max","Mid","Low"].map(t => (
                <button key={t} className={`chip ${tierFilter===t?"active":""}`} onClick={()=>setTierFilter(t)}>{t}</button>
              ))}
            </div>
            <div className="section-label">Age Bracket</div>
            <div className="filter-row">
              {["ALL","≤28","28+"].map(a => (
                <button key={a} className={`chip ${ageFilter===a?"active":""}`} onClick={()=>setAgeFilter(a==="≤28"?"28-":"ALL"?a:a)}>{a}</button>
              ))}
            </div>
          </div>

          <div className="sidebar-section" style={{ padding: "14px 12px" }}>
            <div className="section-label" style={{ paddingLeft: 8 }}>Player Risk Index</div>
            <div className="player-list">
              {filtered.sort((a,b) => b.riskScore - a.riskScore).map(p => (
                <div
                  key={p.id}
                  className={`player-row ${selectedId === p.id ? "selected" : ""}`}
                  onClick={() => { setSelectedId(p.id); setSidebarOpen(false); }}
                >
                  <div className="risk-badge" style={{
                    background: `${riskColor(p.riskScore)}18`,
                    border: `1px solid ${riskColor(p.riskScore)}40`,
                    color: riskColor(p.riskScore),
                  }}>{p.riskScore}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="player-name">{p.name}</div>
                    <div className="player-meta">{p.pos} · {p.tier} · ${p.salary}M · Age {p.age}</div>
                  </div>
                  <div>
                    <div className="risk-bar-bg">
                      <div className="risk-bar-fill" style={{ width: `${p.riskScore}%`, background: riskColor(p.riskScore) }} />
                    </div>
                    <div style={{ fontSize: 8, color: riskColor(p.riskScore), textAlign: "right", marginTop: 2, letterSpacing: 1 }}>{p.riskTier}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* MAIN */}
        <div className="main">
          {/* TABS */}
          <div className="tab-row">
            {["OVERVIEW","PLAYER PROFILE","RESEARCH FINDINGS"].map(t => (
              <button key={t} className={`tab ${activeTab===t?"active":""}`} onClick={()=>setActiveTab(t)}>{t}</button>
            ))}
          </div>

          {activeTab === "OVERVIEW" && (
            <>
              {/* KPIs */}
              <div className="kpi-row">
                <div className="kpi-card amber">
                  <div className="kpi-label">Avg PER Drop (T+1)</div>
                  <div className="kpi-value" style={{ color: "#f5a623" }}>−{avgPERDrop}%</div>
                  <div className="kpi-sub">All contracts · Sample N={DATA.length}</div>
                </div>
                <div className="kpi-card red">
                  <div className="kpi-label">Max Contract Regression</div>
                  <div className="kpi-value" style={{ color: "#e63946" }}>−{maxAvgDrop}%</div>
                  <div className="kpi-sub">Top 10% salary tier avg</div>
                </div>
                <div className="kpi-card blue">
                  <div className="kpi-label">Mid · Low Regression</div>
                  <div className="kpi-value" style={{ color: "#4fc3f7", fontSize: 26 }}>
                    {parseFloat(midAvgDrop) >= 0 ? `−${midAvgDrop}` : `+${Math.abs(parseFloat(midAvgDrop)).toFixed(1)}`}%
                    {" / "}
                    {parseFloat(lowAvgDrop) >= 0 ? `−${lowAvgDrop}` : `+${Math.abs(parseFloat(lowAvgDrop)).toFixed(1)}`}%
                  </div>
                  <div className="kpi-sub">$15–25M · $5–10M contracts</div>
                </div>
                <div className="kpi-card green">
                  <div className="kpi-label">Age 28+ PER Slump</div>
                  <div className="kpi-value" style={{ color: "#e63946" }}>−{over28Avg}%</div>
                  <div className="kpi-sub">vs −{(DATA.filter(p=>p.age<=28).reduce((s,p)=>s+p.perDrop,0)/DATA.filter(p=>p.age<=28).length).toFixed(1)}% under-28</div>
                </div>
              </div>

              {/* Charts row 1 */}
              <div className="charts-grid">
                <div className="chart-card chart-full">
                  <div className="chart-title">Q1 — THE PAYDAY DIP · PER Drop by Player (Contract Year → T+1)</div>
                  <div className="chart-desc">Sorted by magnitude of regression. Red = HIGH risk tier. Amber = MED.</div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={perDropBar} margin={{ top: 0, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" vertical={false} />
                      <XAxis dataKey="name" tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <ReferenceLine y={parseFloat(avgPERDrop)} stroke="#f5a623" strokeDasharray="4 4" label={{ value: "AVG", fill: "#f5a623", fontSize: 8 }} />
                      <Bar dataKey="perDrop" name="PER Drop %" radius={[2,2,0,0]}>
                        {perDropBar.map((e, i) => <Cell key={i} fill={riskColor(e.risk)} fillOpacity={0.85} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="chart-card">
                  <div className="chart-title">Q2 — TIER REGRESSION CURVE · Max vs Mid vs Low</div>
                  <div className="chart-desc">Average PER trajectory across all three contract windows by salary tier.</div>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={tierCompare} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                      <XAxis dataKey="phase" tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <YAxis domain={[8, 30]} tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line type="monotone" dataKey="Max" stroke="#e63946" strokeWidth={2} dot={{ fill: "#e63946", r: 4 }} name="Max ($40M+)" />
                      <Line type="monotone" dataKey="Mid" stroke="#4fc3f7" strokeWidth={2} dot={{ fill: "#4fc3f7", r: 4 }} name="Mid ($15–25M)" />
                      <Line type="monotone" dataKey="Low" stroke="#2ecc71" strokeWidth={2} dot={{ fill: "#2ecc71", r: 4 }} name="Low ($5–10M)" />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="finding-box warn">
                    Max players decline {(parseFloat(maxAvgDrop) - parseFloat(midAvgDrop)).toFixed(1)}pp more than Mid and {(parseFloat(maxAvgDrop) - parseFloat(lowAvgDrop)).toFixed(1)}pp more than Low — moral hazard scales with contract size. Low-tier players show near-zero net regression.
                  </div>
                </div>

                <div className="chart-card">
                  <div className="chart-title">Q4 — AGE INTERACTION · PER Drop by Age Bucket</div>
                  <div className="chart-desc">Physical decline compounding financial security post-29.</div>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={ageBuckets} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" vertical={false} />
                      <XAxis dataKey="age" tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <ReferenceLine y={parseFloat(avgPERDrop)} stroke="#f5a623" strokeDasharray="4 4" />
                      <Bar dataKey="PERDrop" name="Avg PER Drop %" radius={[2,2,0,0]}>
                        {ageBuckets.map((e, i) => <Cell key={i} fill={e.PERDrop > parseFloat(avgPERDrop) ? "#e63946" : "#4fc3f7"} fillOpacity={0.8} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="finding-box">
                    Age 29–31 is the highest-risk window. The &ldquo;29 cliff&rdquo; combines peak salary lock-in with onset of measurable decline.
                  </div>
                </div>
              </div>

              {/* Efficiency Trap */}
              <div className="chart-card">
                <div className="chart-title">Q3 — THE EFFICIENCY TRAP · Volume vs. Efficiency Divergence (T → T+1)</div>
                <div className="chart-desc">
                  X-axis: change in PTS (T+1 − T). Y-axis: TS% drop. Upper-left quadrant = classic stat-padding: maintained volume, falling efficiency.
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <ScatterChart margin={{ top: 10, right: 20, left: -10, bottom: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                    <XAxis dataKey="ptsDiff" type="number" name="Pts Change" tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }}
                      axisLine={false} tickLine={false} label={{ value: "PTS Change (T→T+1)", fill: "#2a4060", fontSize: 9, dy: 18 }} domain={[-4, 3]} />
                    <YAxis dataKey="tsDrop" type="number" name="TS% Drop" tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }}
                      axisLine={false} tickLine={false} label={{ value: "TS% Drop", fill: "#2a4060", fontSize: 9, angle: -90, dx: -14 }} />
                    <Tooltip content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const d = payload[0]?.payload;
                      return <div className="tooltip-custom"><div style={{ color: "#f5a623" }}>{d?.name}</div><div>Pts Δ: {d?.ptsDiff > 0 ? "+" : ""}{d?.ptsDiff?.toFixed(1)}</div><div>TS% Drop: {d?.tsDrop?.toFixed(1)}%</div></div>;
                    }} />
                    <ReferenceLine x={0} stroke="#1e2d3d" />
                    <ReferenceLine y={0} stroke="#1e2d3d" />
                    <ReferenceLine y={parseFloat((DATA.reduce((s,p)=>s+p.tsDrop,0)/DATA.length).toFixed(1))} stroke="#f5a623" strokeDasharray="3 3" />
                    <Scatter data={efficiencyTrap} name="Players">
                      {efficiencyTrap.map((e, i) => (
                        <Cell key={i} fill={riskColor(DATA.find(p => (p.name.split(" ")[1]||p.name) === e.name)?.riskScore || 50)} fillOpacity={0.8} r={6} />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
                <div className="finding-box warn" style={{ marginTop: 10 }}>
                  Upper-left cluster confirms the Efficiency Trap: players maintain scoring volume post-payday while TS% falls — optimizing for box-score visibility over winning plays.
                </div>
              </div>
            </>
          )}

          {activeTab === "PLAYER PROFILE" && selected && (
            <>
              <div className="player-detail">
                <div className="detail-header">
                  <div>
                    <div className="detail-name">{selected.name}</div>
                    <div className="detail-meta">{selected.pos} · {selected.tier} Contract · ${selected.salary}M/yr · Age {selected.age} · Contract Year {selected.contractYear}</div>
                    <div className="flag-row">{getRiskFlags(selected).map((f, i) => <span key={i} className={`flag ${f.cls}`}>{f.label}</span>)}</div>
                  </div>
                  <div className="risk-meter">
                    <div className="risk-label-big">Risk Score</div>
                    <div className="risk-score-big" style={{ color: riskColor(selected.riskScore) }}>{selected.riskScore}</div>
                    <div className="risk-label-big">{selected.riskTier} RISK</div>
                  </div>
                </div>

                <div className="detail-grid">
                  {[
                    { label: "T−1  PRE-CONTRACT", data: selected.T1, key: "T1" },
                    { label: "T  CONTRACT YEAR", data: selected.T, key: "T" },
                    { label: "T+1  GUARANTEED WEALTH", data: selected.T2, key: "T2" },
                  ].map(({ label, data, key }) => (
                    <div key={key} className="detail-phase">
                      <div className="phase-label"><span>◆</span> {label}</div>
                      {[["PER", "PER"], ["TS%", "TS"], ["PTS", "PTS"], ["AST", "AST"], ["TRB", "TRB"], ["WS", "WS"], ["VORP", "VORP"], ["TOV", "TOV"]].map(([label, field]) => {
                        const val = data[field];
                        const prevVal = key === "T2" ? selected.T[field] : key === "T" ? selected.T1[field] : null;
                        const isDown = prevVal !== null && val < prevVal;
                        const isUp   = prevVal !== null && val > prevVal;
                        return (
                          <div key={field} className="stat-row">
                            <span className="stat-key">{label}</span>
                            <span className={`stat-val ${key==="T2" ? (isDown?"down":isUp?"up":"") : ""}`}>
                              {val?.toFixed(1)}{key==="T2" && isDown ? " ▼" : key==="T2" && isUp ? " ▲" : ""}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>

              <div className="charts-grid">
                <div className="chart-card">
                  <div className="chart-title">Performance Trajectory · PER + TS%</div>
                  <div className="chart-desc">Three-phase window around contract signing.</div>
                  <ResponsiveContainer width="100%" height={210}>
                    <LineChart data={trajectory} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e2d3d" />
                      <XAxis dataKey="phase" tick={{ fill: "#4a6278", fontSize: 8, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} width={50} />
                      <YAxis tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} axisLine={false} tickLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Line type="monotone" dataKey="PER" stroke="#f5a623" strokeWidth={2.5} dot={{ fill: "#f5a623", r: 5 }} name="PER" />
                      <Line type="monotone" dataKey="TS" stroke="#e63946" strokeWidth={2} dot={{ fill: "#e63946", r: 4 }} strokeDasharray="5 3" name="TS%" />
                      <Line type="monotone" dataKey="PTS" stroke="#4fc3f7" strokeWidth={1.5} dot={{ fill: "#4fc3f7", r: 3 }} name="PTS" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="chart-card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
                  <div className="chart-title" style={{ alignSelf: "flex-start" }}>Risk Decomposition</div>
                  <div className="chart-desc" style={{ alignSelf: "flex-start" }}>Five-factor radar profile for {selected.name}.</div>
                  <ResponsiveContainer width="100%" height={210}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#1e2d3d" />
                      <PolarAngleAxis dataKey="metric" tick={{ fill: "#4a6278", fontSize: 9, fontFamily: "IBM Plex Mono" }} />
                      <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                      <Radar name="Risk" dataKey="value" stroke={riskColor(selected.riskScore)} fill={riskColor(selected.riskScore)} fillOpacity={0.2} strokeWidth={2} />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {activeTab === "RESEARCH FINDINGS" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              {[
                {
                  num: "01", color: "#f5a623",
                  title: "The Payday Dip",
                  sub: "Average PER regression in Year T+1 of non-rookie Max deals",
                  finding: `Across the ${DATA.length}-player sample, the mean PER drop post-signing is ${avgPERDrop}%. Peak performance in the contract year (T) is consistently followed by a measurable efficiency decline — not explained by age or injury alone. The incentive gradient created by guaranteed money reduces the marginal utility of effort for a subset of players.`,
                  stat: `−${avgPERDrop}%`, statLabel: "Avg PER Drop",
                },
                {
                  num: "02", color: "#e63946",
                  title: "The Safety Tier Gap",
                  sub: "Max vs. Mid vs. Low post-contract regression differential",
                  finding: `Max contract players (≥$40M/yr) show an average PER regression of ${maxAvgDrop}% vs. ${midAvgDrop}% for Mid-tier and ${lowAvgDrop}% for Low-tier signings. The gradient (Max → Mid: ${(parseFloat(maxAvgDrop)-parseFloat(midAvgDrop)).toFixed(1)}pp, Max → Low: ${(parseFloat(maxAvgDrop)-parseFloat(lowAvgDrop)).toFixed(1)}pp) confirms that moral hazard scales with contract size. Low-tier players face constant roster insecurity — the incentive to perform never fully relaxes regardless of the deal signed.`,
                  stat: `${(parseFloat(maxAvgDrop)-parseFloat(lowAvgDrop)).toFixed(1)}pp`, statLabel: "Max vs Low Gap",
                },
                {
                  num: "03", color: "#4fc3f7",
                  title: "The Efficiency Trap",
                  sub: "Scoring volume held constant while TS% falls — the stat-padding signature",
                  finding: `The critical finding: in the majority of cases, PTS volume changes minimally (avg: ${(DATA.reduce((s,p)=>s+p.ptsDiff,0)/DATA.length).toFixed(1)} pts/gm) while TS% drops by an average of ${(DATA.reduce((s,p)=>s+p.tsDrop,0)/DATA.length).toFixed(1)}%. This decoupling is the hallmark of optimized stat-accumulation — players take lower-quality shots to maintain counting stats visible to media and future contract negotiations, at the cost of team efficiency.`,
                  stat: `${(DATA.reduce((s,p)=>s+p.tsDrop,0)/DATA.length).toFixed(1)}%`, statLabel: "Avg TS% Drop",
                },
                {
                  num: "04", color: "#2ecc71",
                  title: "Age × Contract Interaction",
                  sub: "The 29-cliff: where physical decline meets financial arrival",
                  finding: `Players aged 29–31 at signing show the deepest regression, averaging ${over28Avg}% PER drop vs. ${(DATA.filter(p=>p.age<=28).reduce((s,p)=>s+p.perDrop,0)/DATA.filter(p=>p.age<=28).length).toFixed(1)}% for under-28 signings. The interaction effect of early athletic decline (proprioceptive degradation, recovery time) compounds financial security to produce the sharpest drop. Young stars (<25) show near-zero regression — career trajectory still dominant.`,
                  stat: `${over28Avg}%`, statLabel: "Age 28+ Avg Drop",
                },
              ].map(r => (
                <div key={r.num} className="chart-card" style={{ borderLeft: `3px solid ${r.color}` }}>
                  <div style={{ display: "flex", alignItems: "flex-start", gap: 24 }}>
                    <div style={{ flexShrink: 0, textAlign: "center" }}>
                      <div style={{ fontFamily: "Bebas Neue", fontSize: 48, color: r.color, lineHeight: 1, opacity: 0.3 }}>{r.num}</div>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div className="chart-title" style={{ color: r.color, fontSize: 13, marginBottom: 2 }}>{r.title}</div>
                      <div className="chart-desc" style={{ marginBottom: 10 }}>{r.sub}</div>
                      <div style={{ fontFamily: "IBM Plex Sans, sans-serif", fontSize: 12, color: "#8aabb8", lineHeight: 1.7 }}>{r.finding}</div>
                    </div>
                    <div style={{ flexShrink: 0, textAlign: "right" }}>
                      <div style={{ fontFamily: "Bebas Neue", fontSize: 40, color: r.color, lineHeight: 1 }}>{r.stat}</div>
                      <div style={{ fontSize: 9, color: "#4a6278", letterSpacing: 1, marginTop: 2 }}>{r.statLabel}</div>
                    </div>
                  </div>
                </div>
              ))}

              <div className="chart-card" style={{ borderTop: "2px solid #f5a623", background: "linear-gradient(135deg, #0d1218 0%, #111c14 100%)" }}>
                <div className="chart-title" style={{ fontSize: 13, marginBottom: 8 }}>Sportsbook Application · Underperformance Risk Thresholds</div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginTop: 8 }}>
                  {[
                    { tier: "HIGH RISK", range: "Score 55–100", color: "#e63946", criteria: "Age >28 + Max deal + prior PER drop >10% + TS% trending down", action: "FLAG for prop bet unders. Fade season-long stat projections by 12–18%." },
                    { tier: "MED RISK",  range: "Score 30–54", color: "#f5a623", criteria: "Age 25–28 + Max/Mid deal + moderate efficiency warning", action: "Monitor Q1 performance. Apply 6–10% regression discount to projection models." },
                    { tier: "LOW RISK",  range: "Score 0–29",  color: "#2ecc71", criteria: "Age <25 OR demonstrable growth trajectory + Mid-class deal", action: "No regression discount needed. Career incentives still dominate behavior." },
                  ].map(t => (
                    <div key={t.tier} style={{ background: "#0a1218", border: `1px solid ${t.color}30`, borderRadius: 3, padding: 14 }}>
                      <div style={{ color: t.color, fontSize: 10, letterSpacing: 2, fontWeight: 600, marginBottom: 4 }}>{t.tier}</div>
                      <div style={{ color: "#4a6278", fontSize: 9, marginBottom: 8 }}>{t.range}</div>
                      <div style={{ color: "#6a8898", fontSize: 9, lineHeight: 1.6, marginBottom: 8 }}>{t.criteria}</div>
                      <div style={{ color: t.color, fontSize: 9, lineHeight: 1.5, opacity: 0.8 }}>→ {t.action}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
