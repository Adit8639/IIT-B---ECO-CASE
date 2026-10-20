# AI and India's tech exports: scenario dashboard (Team ARTHA)
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="ARTHA | AI and India's Tech Exports", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"], .stApp, .stMarkdown, p, label, span, div {
    font-family: 'Segoe UI', Arial, sans-serif; color: #000000;
}
.stApp { background-color: #FFFFFF; }
section[data-testid="stSidebar"] { background-color: #F3F8FB; }
h1, h2, h3 { color: #0F2B46 !important; font-weight: 700; }
h3 { font-size: 20px !important; }
[data-testid="stMetricValue"] { font-size: 30px; font-weight: 700; color: #000000; }
[data-testid="stMetricLabel"] p { font-size: 15px; color: #000000; }
</style>
""", unsafe_allow_html=True)

TEAL, BLUE, LIGHT, NAVY, RED, GREY = "#1C9AA3", "#5E8FC4", "#8FCFD5", "#0F2B46", "#B5393A", "#9AA5B1"

# ---------- base data, FY26 (RBI, Nasscom, IMF, FRED, foundit) ----------
EXP26, GDP26, FX26, HC26 = 221.4, 3920, 96.7, 5.95
YEARS = 5
# activity: (FY26 $ bn, share of work AI can do, price elasticity, revenue per worker index)
SEG = {
    "App maintenance & support": (44, 0.45, 0.30, 1.00),
    "Testing & QA": (15, 0.60, 0.30, 0.90),
    "New builds & modernisation": (32, 0.35, 1.15, 1.10),
    "Infra & cloud operations": (30, 0.30, 0.30, 1.00),
    "Consulting & integration": (26, 0.15, 0.50, 1.40),
    "Voice & customer support": (19, 0.55, 0.20, 0.55),
    "Back office (F&A, claims, data)": (25, 0.55, 0.20, 0.60),
    "Analytics & knowledge work": (12, 0.35, 0.50, 0.80),
    "Engineering R&D": (12, 0.15, 0.50, 1.20),
    "Software products & other": (6.4, 0.25, 0.50, 1.30),
}
# share of each activity in Tier-2 hub jobs (our estimate)
T2MIX = {"Voice & customer support": .20, "Back office (F&A, claims, data)": .25, "Testing & QA": .15,
         "App maintenance & support": .25, "New builds & modernisation": .05,
         "Infra & cloud operations": .05, "Analytics & knowledge work": .05}
HUBS = {"Ahmedabad": 120, "Jaipur": 95, "Coimbatore": 83, "Lucknow": 73}   # STEM postings, '000 (foundit)
AI0 = 11 * EXP26 / 315   # AI-led export revenue today, $ bn

PRESETS = {
    "Gradual": dict(A=35, aig=25, aish=30, ins=2, t2ai=1.0),
    "Rapid, slow response": dict(A=75, aig=20, aish=60, ins=10, t2ai=1.0),
    "Rapid, re-tooled": dict(A=75, aig=42, aish=70, ins=4, t2ai=2.0),
}


def run(A, aig, aish, ins, t2ai, P, G, leak, gdpg, elas, fxtr, hcg, years=YEARS):
    """Returns the FY31 result for one set of inputs (all rates as decimals)."""
    jw = {k: v[0] / v[3] for k, v in SEG.items()}
    J = sum(jw.values())
    tot, jobs, t2, segs = 0, 0, 0, {}
    for k, (v, e, el, _) in SEG.items():
        pf = 1 - e * A * P                          # price factor after AI savings passed to clients
        r = v * (1 + G) ** years * pf ** (1 - el) * (1 - ins)
        segs[k] = r
        tot += r
        jf = pf ** (-el) * (1 - e * A) * (1 - ins)  # volume rebound x labour per unit
        jobs += jw[k] / J * jf
        t2 += T2MIX.get(k, 0) * jf
    ai_extra = AI0 * (1 + aig) ** years - AI0 * (1 + G) ** years
    tot += ai_extra
    trend = EXP26 * (1 + G) ** years
    trend_net = trend - trend * 0.10 * leak
    net = tot - tot * aish * leak                   # compute bill paid abroad
    gdp = GDP26 * (1 + gdpg) ** years
    cad_shift = (trend_net - net) / gdp * 100
    fx_base = FX26 * (1 + fxtr) ** years
    fx = fx_base * (1 + cad_shift / 100 / elas)
    ai_jobs = ai_extra / 0.07 / 1000                # $70k revenue per new AI worker, mn jobs
    hc = HC26 * (1 + hcg) ** years * jobs + ai_jobs
    t2_base = 0.371 * 0.6                           # IT-BPO jobs in the four hubs, mn
    t2_31 = t2_base * t2 * (1 + hcg) ** years + ai_jobs * (t2_base / HC26) * t2ai
    return dict(exp=tot, trend=trend, cagr=(tot / EXP26) ** (1 / years) - 1, ai_extra=ai_extra,
                leak=tot * aish * leak, cad=0.6 + cad_shift, fx=fx, fx_base=fx_base, hc=hc,
                hc_trend=HC26 * (1 + hcg) ** years, t2chg=t2_31 / t2_base - 1, segs=segs)


def path(p, g):
    """Year-by-year exports with AI adoption phasing in evenly."""
    rows = []
    for t in range(0, YEARS + 1):
        if t == 0:
            rows.append(EXP26)
            continue
        r = run(p["A"] / 100 * t / YEARS, p["aig"] / 100, p["aish"] / 100 * t / YEARS,
                p["ins"] / 100 * t / YEARS, p["t2ai"], g["P"], g["G"], g["leak"], g["gdpg"],
                g["elas"], g["fxtr"], g["hcg"], years=t)
        rows.append(r["exp"])
    return rows


def style(fig, h):
    fig.update_layout(height=h, paper_bgcolor="white", plot_bgcolor="white", font=dict(color="black", size=13),
                      margin=dict(l=10, r=10, t=10, b=10))
    fig.update_xaxes(tickfont=dict(color="black"), gridcolor="#E5E5E5", automargin=True)
    fig.update_yaxes(tickfont=dict(color="black"), gridcolor="#E5E5E5", automargin=True)
    return fig


# ---------- sidebar ----------
st.sidebar.header("Scenario inputs")
choice = st.sidebar.selectbox("Start from", list(PRESETS.keys()), index=1)
p0 = PRESETS[choice]
A = st.sidebar.slider("AI adoption by 2031 (% of what is possible)", 0, 100, p0["A"], 5)
aish = st.sidebar.slider("Exports delivered with AI by FY31 (%)", 0, 100, p0["aish"], 5)
aig = st.sidebar.slider("Growth of new AI work (% a year)", 0, 60, p0["aig"], 1)
ins = st.sidebar.slider("Exposed work clients take in-house (%)", 0, 30, p0["ins"], 1)
t2ai = st.sidebar.select_slider("Tier-2 share of new AI jobs vs today", [0.5, 1.0, 1.5, 2.0, 3.0], p0["t2ai"])

with st.sidebar.expander("Macro assumptions"):
    P = st.slider("Share of AI savings passed to clients (%)", 20, 100, 60, 5) / 100
    G = st.slider("Export growth without AI (% a year)", 3, 12, 7, 1) / 100
    leak = st.slider("Model and GPU cost, paid abroad (% of AI-delivered revenue)", 0, 20, 8, 1) / 100
    gdpg = st.slider("Nominal GDP growth in $ (% a year)", 4, 12, 8, 1) / 100
    elas = st.slider("Current account to rupee elasticity (IMF: 0.18)", 0.10, 0.40, 0.18, 0.01)
    fxtr = st.slider("Rupee drift from inflation gap (% a year)", 0.0, 4.0, 2.0, 0.5) / 100
    hcg = st.slider("Headcount growth without AI (% a year)", 0.0, 5.0, 2.3, 0.1) / 100

g = dict(P=P, G=G, leak=leak, gdpg=gdpg, elas=elas, fxtr=fxtr, hcg=hcg)
r = run(A / 100, aig / 100, aish / 100, ins / 100, t2ai, **g)

# ---------- header ----------
st.title("AI and India's tech exports: FY26 to FY31")
st.write("Move the inputs on the left. Every number below is recalculated from the same model used in our deck "
         "(Appendix 1). Base year data: RBI, Nasscom, IMF, FRED and foundit.")

# ---------- top metrics ----------
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Exports FY31", f"${r['exp']:.0f} bn", f"{r['exp'] - r['trend']:+.0f} bn vs no-AI trend")
    c2.metric("Export growth", f"{r['cagr'] * 100:.1f}% a year", f"{(r['cagr'] - G) * 100:+.1f} pts vs trend")
    c3.metric("CA deficit, % of GDP", f"{r['cad']:.2f}%", f"{r['cad'] - 0.6:+.2f} pts vs FY26",
              delta_color="inverse")
    c4.metric("Rupee, Oct 2031", f"₹{r['fx']:.1f} / $", f"{r['fx'] - r['fx_base']:+.1f} vs trend",
              delta_color="inverse")
    c5.metric("Tech jobs FY31", f"{r['hc']:.2f} mn", f"{(r['hc'] / HC26 - 1) * 100:+.0f}% vs FY26")

# ---------- charts ----------
left, right = st.columns([3, 2])
with left:
    with st.container(border=True):
        st.subheader("Export path under the three cases, $ bn")
        yrs = [f"FY{26 + t}" for t in range(YEARS + 1)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=yrs, y=[EXP26 * (1 + G) ** t for t in range(YEARS + 1)], name="No-AI trend",
                                 line=dict(color=GREY, dash="dash", width=2)))
        cols = {"Gradual": BLUE, "Rapid, slow response": RED, "Rapid, re-tooled": TEAL}
        for nm, pp in PRESETS.items():
            fig.add_trace(go.Scatter(x=yrs, y=path(pp, g), name=nm, line=dict(color=cols[nm], width=2)))
        mine = dict(A=A, aig=aig, aish=aish, ins=ins, t2ai=t2ai)
        fig.add_trace(go.Scatter(x=yrs, y=path(mine, g), name="Your settings",
                                 line=dict(color=NAVY, width=4), mode="lines+markers"))
        fig.update_layout(height=380, paper_bgcolor="white", plot_bgcolor="white", font=dict(color="black", size=14),
                          legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10),
                          yaxis=dict(gridcolor="#E5E5E5"))
        st.plotly_chart(style(fig, 380), width="stretch")

with right:
    with st.container(border=True):
        st.subheader("FY31 exports by activity vs trend, $ bn")
        df = pd.DataFrame({"Activity": list(SEG.keys()),
                           "Change": [r["segs"][k] - SEG[k][0] * (1 + G) ** YEARS for k in SEG]})
        df = df.sort_values("Change")
        fig2 = go.Figure(go.Bar(x=df["Change"], y=df["Activity"], orientation="h",
                                marker_color=[RED if v < 0 else TEAL for v in df["Change"]],
                                text=[f"{v:+.1f}" for v in df["Change"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white")))
        fig2.update_layout(height=380, paper_bgcolor="white", plot_bgcolor="white", font=dict(color="black", size=13),
                           margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(gridcolor="#E5E5E5"))
        st.plotly_chart(style(fig2, 380), width="stretch")

l2, r2 = st.columns([2, 3])
with l2:
    with st.container(border=True):
        st.subheader("Dollar account, FY31")
        st.write(f"Exports below trend: **${r['trend'] - r['exp']:.0f} bn**")
        st.write(f"New AI work added: **${r['ai_extra']:.0f} bn**")
        st.write(f"Model and GPU bill paid abroad: **${r['leak']:.0f} bn**")
        st.write(f"Trend rupee without the shock: **₹{r['fx_base']:.1f}**")
with r2:
    with st.container(border=True):
        st.subheader("Four Tier-2 hubs: IT and BPO jobs by FY31")
        hub = pd.DataFrame({"Hub": list(HUBS.keys()),
                            "Jobs ('000)": [v * 0.6 * r["t2chg"] for v in HUBS.values()]})
        fig3 = go.Figure(go.Bar(x=hub["Hub"], y=hub["Jobs ('000)"],
                                marker_color=[RED if v < 0 else TEAL for v in hub["Jobs ('000)"]],
                                text=[f"{v:+.1f}k" for v in hub["Jobs ('000)"]], textposition="outside", cliponaxis=False))
        fig3.update_layout(height=260, paper_bgcolor="white", plot_bgcolor="white", font=dict(color="black", size=14),
                           margin=dict(l=10, r=10, t=10, b=10), yaxis=dict(gridcolor="#E5E5E5"))
        st.plotly_chart(style(fig3, 260), width="stretch")
        st.write(f"Change in hub IT and BPO jobs: **{r['t2chg'] * 100:+.0f}%**, against "
                 f"**{(r['hc'] / HC26 - 1) * 100:+.0f}%** for India as a whole. "
                 "Local jobs move by 1 to 2.5 times the direct change.")

# ---------- signpost dashboard ----------
with st.container(border=True):
    st.subheader("Signpost check: which playbook applies today")
    s1, s2 = st.columns(2)
    gap = s1.number_input("Revenue growth minus headcount growth, top IT firms (pts)", 0.0, 15.0, 3.8, 0.1)
    gap_q = s1.number_input("Quarters that gap has stayed above 6 pts", 0, 8, 0)
    cut = s1.number_input("Price cut at renewal on like-for-like deals (%)", 0.0, 40.0, 12.0, 0.5)
    fresh = s2.number_input("Fall in fresher hiring over the last year (%)", 0.0, 80.0, 20.0, 1.0)
    hire = s2.selectbox("US HIRE Act status", ["Stalled", "Passed one chamber", "Law"])
    tripped = {
        "Revenue minus headcount gap above 6 pts for two quarters": gap > 6 and gap_q >= 2,
        "Renewal price cut above 15%": cut > 15,
        "Fresher hiring down 30% in a year": fresh >= 30,
        "HIRE Act passes a chamber": hire != "Stalled",
    }
    n = sum(tripped.values())
    for k, v in tripped.items():
        s2.write(("🔴 " if v else "🟢 ") + k)
    if n >= 2:
        st.error(f"{n} signposts tripped. Firm, fund and state move to the rapid-case playbook.")
    else:
        st.success(f"{n} signpost(s) tripped. Stay on the gradual playbook and keep watching.")
    play = pd.DataFrame({
        "Signpost": list(tripped.keys()),
        "Firm": ["Reprice all exposed deals", "Push unit pricing", "Hold the 70% fresher floor", "Grow UK and EU"],
        "Fund": ["Hedge to 75%", "Halve mid-tier IT", "Watch talent risk", "Cut US-heavy names"],
        "State": ["Open wage insurance", "Shift incentives faster", "Add 2,000 seats", "Pitch to EU firms"],
        "Status": ["Tripped" if v else "Not yet" for v in tripped.values()],
    })
    st.dataframe(play, hide_index=True, width="stretch")

st.caption("Team ARTHA, Sri Venkateswara College. Model inputs and sources are listed in the deck appendix.")
