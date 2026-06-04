import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import io, os
from collections import Counter
from datetime import datetime, date

# ========================= CONFIGURATION =========================
# Ensuring fonts stay as editable text for Adobe Illustrator
mpl.rcParams['pdf.fonttype'] = 42
mpl.rcParams['svg.fonttype'] = 'none'
mpl.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif']

APP_TITLE_COLOR = '#000000'

st.set_page_config(page_title="Ranklin", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
h1 { color: #000000 !important; font-weight: 700 !important; }
[data-testid="stSidebar"] { background-color: #fafafa; }
.stDownloadButton button {
    background-color: #302A7E; color: white; border-radius: 6px;
    font-weight: 600; border: none; padding: 0.5rem 1rem; width: 100%;
    margin-bottom: 10px;
}
.apply-btn button {
    background-color: #28a745 !important;
    color: white !important;
    border: none !important;
    height: 3.5rem !important;
    font-weight: bold !important;
    font-size: 1.1rem !important;
}
</style>
""", unsafe_allow_html=True)


# ========================= BEAUHURST CANONICAL DATA =========================
# Full list of canonical Beauhurst industries and buzzwords. The smart splitter
# uses this as its primary reference: each row's tag column is scanned with a
# longest-match-wins algorithm against this list before any naive comma split
# is attempted. This means:
#   - Names that contain commas internally ("Repair, maintenance and servicing")
#     are kept atomic - no more being torn into fragments.
#   - Whatever case the user's export uses, items are normalised back to the
#     canonical Beauhurst form.
#   - Unknown values still split on commas/semicolons - the splitter is tolerant,
#     not destructive, so a new Beauhurst tag we don't know about yet still
#     comes through.
#
# Source of truth: the Industries & Buzzwords database in Notion. Refresh by
# re-running the extraction script when new tags appear.

BEAUHURST_INDUSTRIES = [
    'Accessories for tech devices',
    'Accountancy and tax',
    'Aggregates',
    'Agriculture, land farming and forestry',
    'Aircraft',
    'Airports',
    'Alcoholic beverages',
    'Alternative medicine',
    'Animal feed and pet food',
    'Appliances and kitchenware',
    'Application software',
    'Architecture',
    'Arts and crafts',
    'Assistants',
    'Auctioneering',
    'Automotive dealerships',
    'B&Bs and other short-term accommodation',
    'Baked goods',
    'Banking',
    'Beauty and cosmetics',
    'Betting and gambling',
    'Bicycles and scooters',
    'Biotechnology',
    'Boats and ships',
    'Books, comics and graphic novels',
    'Budgeting and financial management',
    'Building materials, tools and accessories',
    'Butchers',
    'Care homes',
    'Cars, motorcycles and other road vehicles',
    'Catering',
    'Chemicals',
    'Childcare and child supervision',
    'Chips and processors',
    'Cinemas',
    'Civil engineering',
    'Cleaning',
    'Clinical diagnostics',
    'Clinical research',
    'Clothes',
    'Collection and delivery',
    'Condiments and seasonings',
    'Confectionery and snacks',
    'Corner shops',
    'Courses and educational material',
    'Credit ratings and scores',
    'Currency exchange',
    'Customer support',
    'Dairy products',
    'Data aggregation',
    'Data centres',
    'Data management',
    'Data provision and analysis',
    'Demolition and decommissioning',
    'Dentistry and oral hygiene',
    'Dietary, and lifestyle, needs and choices',
    'Distribution and wholesale',
    'Electricity generation',
    'Electronics hardware',
    'Embedded systems',
    'Emergency services',
    'Energy management and reduction',
    'Energy storage',
    'Energy utilities',
    'Environmental consultancy',
    'Estate agencies',
    'Event management, booking and ticketing',
    'Fabrics and textiles',
    'Festivals, conferences, exhibitions and fairs',
    'Films and TV',
    'Fish',
    'Fishing and aquafarming',
    'Flowers, trees and other plants',
    'Food and drink processing',
    'Footwear',
    'Freight and haulage',
    'Fruit, vegetables and fungi',
    'Funerals and other posthumous products and services',
    'Furniture, furnishings and fixtures',
    'Gardening, landscaping and tree surgery',
    'Gemstones and precious metals',
    'Gifts',
    'Glass',
    'Graphic design',
    'Gyms and spas',
    'Hazard and damage control',
    'Health and safety',
    'Healthcare products, toiletries and living aids',
    'Heating, ventilation, air conditioning and mechanical and electrical systems',
    'Heavy equipment and machinery',
    'Higher education',
    'Home and garden',
    'Homecare (domiciliary care)',
    'Hospitals and clinics',
    'Hotels',
    'Human resources',
    'Insurance',
    'Interior design',
    'Investment banking and corporate finance',
    'Jewellery and other accessories',
    'Land',
    'Languages, translation and interpretation',
    'Lead generation and sales support',
    'Legal services',
    'Lighting',
    'Livestock and equine',
    'Loans',
    'Management and strategy consultancy',
    'Manufacturing',
    'Market research',
    'Marketing, branding and advertising',
    'Materials technology',
    'Mechanics and garages',
    'Medical devices and instruments',
    'Medical doctors',
    'Meetups and social clubs',
    'Mental well-being',
    'Military and defence',
    'Mining',
    'Mobile and temporary accommodation',
    'Mobile, internet and wireless hardware',
    'Music',
    'Music venues',
    'Newspapers, magazines and online publishing',
    'Nightclubs and bars',
    'Non-alcoholic beverages',
    'Non-precious metals',
    'Nurseries',
    'Office space',
    'Oil and gas',
    'Online marketplace',
    'Online retailing',
    'Ophthalmology and opticians',
    'Packaging and printing',
    'Painting, sculpture and other artworks',
    'Parking',
    'Parks',
    'Parts and components',
    'Passenger airlines',
    'Pasta',
    'Payment processing',
    'Performance art',
    'Personnel supply and contract outsourcing',
    'Pets',
    'Pharmaceuticals',
    'Pharmacies',
    'Photography and videography',
    'Physical fitness coaching and training',
    'Physical product design, testing and quality assurance',
    'Physical retailing',
    'Physical sciences research',
    'Physiotherapy and massage',
    'Plastics and rubber',
    'Pop-up stores, street markets and food trucks',
    'Ports, docks and marine infrastructure',
    'Pregnancy and parenting',
    'Private equity and venture capital',
    'Private vehicle hire (taxis and minicabs)',
    'Product rental and hire',
    'Property and environmental survey',
    'Property and land assets investment',
    'Property and land assets management',
    'Property development and construction',
    'Provision of raw materials',
    'Psychiatry, psychotherapy and counselling',
    'Public relations',
    'Radio series, podcasts, audio books and other audio content',
    'Ready meals and meal kits',
    'Recruitment',
    'Renewable energy',
    'Repair, maintenance and servicing',
    'Research tools and reagents',
    'Restaurants, pubs, cafes and takeaways',
    'Retail consultancy',
    'Rewards, loyalty schemes and vouchers',
    'Risk and compliance',
    'Roads and bridges',
    'Robots and automation',
    'Satellite hardware',
    'Scenery, sets, props and costumes',
    'Schools',
    'Second-hand and antique items',
    'Security and surveillance',
    'Self-storage',
    'Sensors',
    'Server hardware',
    'Server software',
    'Sex, dating and relationships',
    'Shipyards and shipbuilding',
    'Signage and physical advertising',
    'Smoking and vaping',
    'Social media',
    'Space infrastructure',
    'Sporting events and activities',
    'Sports clubs',
    'Sports equipment and apparel',
    'Sports venues',
    'Student accommodation',
    'Supermarkets and department stores',
    'Supply chain management',
    'Surgeries and non-surgical procedures',
    'Technology consultancy and IT and telecommunications support',
    'Telecommunication infrastructure',
    'Telecommunication utilities',
    'Tours, excursions and experiences',
    'Toys and games',
    'Tradespeople and trade services',
    'Trading platforms',
    'Trains and trams',
    'Travel agencies, travel planning and organisation',
    'Tutoring, training, coaching and skills development',
    'Venue hire',
    'Vets',
    'Video content (including pre- and post-production)',
    'Video games',
    'Vitamins and other supplements',
    'Warehouses (bonded and non-bonded)',
    'Waste management and recycling',
    'Wealth, asset and investment management',
    'Website hosting',
    'Weddings',
    'boring and drilling',
    'cards and stationery',
    'debt and grants',
    'fishmongers and greengrocers',
    'galleries',
    'headhunting and talent management',
    'meat and eggs',
    'news agents',
    'off-licences and petrol stations',
    'rice and other dry processed foods',
    'secretaries and administrative support',
    'steel and other alloys',
    'theatres and museums',
    'water and air management',
    'zoos and farm attractions',
]

BEAUHURST_BUZZWORDS = [
    '3D printing',
    'AdTech',
    'Advanced manufacturing',
    'AgeTech',
    'AgriTech',
    'Alternative finance',
    'Artificial Intelligence',
    'AssistiveTech',
    'Augmented reality',
    'Autonomous vehicles',
    'Big data',
    'Biomass and biofuels',
    'Biometrics',
    'Blockchain',
    'Cannabis',
    'Carbon capture',
    'Chatbots',
    'Clean energy',
    'CleanTech',
    'Cloud computing',
    'CollabTech',
    'ConTech',
    'Creative industries',
    'Crypto-currencies',
    'Defence',
    'Digital and technologies',
    'Digital security',
    'Drones',
    'EdTech',
    'Electric and hybrid vehicles',
    'Esports',
    'Ethical shopping',
    'EventTech',
    'FinTech',
    'Financial services',
    'FoodTech',
    'Franchise',
    'Gamification',
    'Genomics',
    'Geospatial technology',
    'HRTech',
    'Image and voice recognition',
    'InsurTech',
    'Internet of Things',
    'LawTech',
    'Life sciences',
    'MarTech',
    'Mobile apps',
    'Nudging and behavioural science',
    'Omni-channel retailing',
    'Open source',
    'Point-of-Sale (PoS)',
    'Pop-ups',
    'Precision agriculture',
    'Precision medicine',
    'Preventive care',
    'Professional and business services',
    'PropTech',
    'Quantum',
    'RegTech',
    'Robotics',
    'Services on demand',
    'Sharing economy',
    'Smart cities',
    'Smart energy',
    'Smart homes',
    'Social shopping',
    'Software-as-a-Service (SaaS)',
    'Subscription',
    'Vegan/vegetarian',
    'Virtual reality',
    'VoIP',
    'Wearables',
    'eHealth',
]
# Pre-sort by length descending once. Longest-match-wins ensures that ambiguous
# prefixes (e.g. "Repair" vs "Repair, maintenance and servicing") resolve to the
# fuller canonical name when the input genuinely contains it.
_CANONICAL_TAGS = BEAUHURST_INDUSTRIES + BEAUHURST_BUZZWORDS
_CANONICAL_SORTED = sorted(_CANONICAL_TAGS, key=len, reverse=True)

# Keep a lower-cased set for fast "is this a canonical Beauhurst tag?" checks.
_CANONICAL_LOWER = {t.lower() for t in _CANONICAL_TAGS}

# Map lowercase tag -> canonical-case form. Lets the fast path normalise case
# in O(1) per piece instead of scanning the full sorted list.
_CANONICAL_CASE_MAP = {t.lower(): t for t in _CANONICAL_TAGS}

# Backwards-compatible alias - older code expects MULTI_COMMA_INDUSTRIES.
MULTI_COMMA_INDUSTRIES = [t for t in BEAUHURST_INDUSTRIES if "," in t]
_MULTI_COMMA_SORTED = _CANONICAL_SORTED  # kept for backwards compatibility


# The UK Industrial Strategy 8 - high-level Beauhurst buzzwords used as
# umbrella categories. They aggregate many specific industries underneath
# them, so when present in a ranking they typically dominate the top of the
# chart, which can be more noise than signal. The UI exposes a toggle to
# exclude them; canonical Beauhurst case is used here so the case-insensitive
# filter matches whatever the export's casing looks like.
IS_8_BUZZWORDS = [
    "Advanced manufacturing",
    "Clean energy",
    "Creative industries",
    "Defence",
    "Digital and technologies",
    "Financial services",
    "Life sciences",
    "Professional and business services",
]
_IS_8_LOWER = {t.lower() for t in IS_8_BUZZWORDS}


def smart_split_industries(value, canonical_sorted=_CANONICAL_SORTED):
    """
    Split a separator-separated string of Beauhurst tags into a list, using the
    full Beauhurst canonical industries + buzzwords list as the primary
    reference rather than naive comma splitting.

    Algorithm:
      1. If the value contains a semicolon, split on semicolons (commas inside
         names are kept literal - this is the whole reason semicolon-separated
         exports exist).
      2. Fast path: naive comma split. If every piece is a known canonical tag,
         return them in canonical case. ~95% of rows take this path.
      3. Slow path (only when at least one piece isn't canonical): scan the
         string left-to-right looking for the LONGEST canonical Beauhurst tag
         that matches at the current position. This is the only way to keep
         multi-comma names ("Repair, maintenance and servicing") intact.

    Results are memoised per unique cell value via a module-level cache, so a
    column with many duplicate values only pays the cost once per distinct value.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return []
    # Memo cache: return a COPY so callers can mutate without polluting the cache
    cached = _SPLIT_CACHE.get(s)
    if cached is not None:
        return list(cached)
    result = _smart_split_uncached(s, canonical_sorted)
    # Bound the cache so repeated runs with very heterogeneous data don't grow
    # memory without bound. 20k unique tag-strings covers a multi-million-row
    # export comfortably.
    if len(_SPLIT_CACHE) < 20000:
        _SPLIT_CACHE[s] = tuple(result)
    return result


def _smart_split_uncached(s, canonical_sorted):
    """The actual splitting logic, called once per unique string."""
    # Semicolon-separated: unambiguous separator. Still normalise items to
    # canonical Beauhurst case where we can.
    if ";" in s:
        out = []
        for x in (p.strip() for p in s.split(";")):
            if not x or x.lower() in ("nan", "none"):
                continue
            canon = _CANONICAL_CASE_MAP.get(x.lower())
            out.append(canon if canon else x)
        return out

    # FAST PATH: naive comma split. If every piece is a canonical Beauhurst
    # tag, we're done in O(N) - no need to do the longest-match scan.
    raw_pieces = [p.strip() for p in s.split(",")]
    cleaned = [p for p in raw_pieces if p and p.lower() not in ("nan", "none")]
    if cleaned and all(p.lower() in _CANONICAL_CASE_MAP for p in cleaned):
        return [_CANONICAL_CASE_MAP[p.lower()] for p in cleaned]

    # SLOW PATH: at least one piece is not canonical. This could be either an
    # unknown tag OR a fragment of a multi-comma industry name like
    # "Repair, maintenance and servicing". Do the longest-match scan.
    items = []
    pos = 0
    n = len(s)
    while pos < n:
        # Skip leading whitespace and commas
        while pos < n and s[pos] in " ,":
            pos += 1
        if pos >= n:
            break

        # Try to match a known canonical tag at this position
        matched_name = None
        for name in canonical_sorted:
            end = pos + len(name)
            if end <= n and s[pos:end].lower() == name.lower():
                # Must end at a boundary (end of string or comma)
                if end == n or s[end] == ",":
                    matched_name = name  # use canonical form, not the raw input
                    pos = end
                    break

        if matched_name is not None:
            items.append(matched_name)
        else:
            # Plain single-comma split for everything else
            next_comma = s.find(",", pos)
            if next_comma == -1:
                items.append(s[pos:].strip())
                pos = n
            else:
                items.append(s[pos:next_comma].strip())
                pos = next_comma + 1

    return [x for x in items if x and x.lower() not in ("nan", "none")]


# Module-level memo cache for smart_split_industries. Keyed by raw cell string,
# values are tuples (immutable so the cache can't be corrupted).
_SPLIT_CACHE = {}


# ========================= CACHED ENGINES =========================
def _clean_columns(df):
    """Strip leading/trailing whitespace from column names.

    Excel and CSV exports often have headers with trailing spaces that are
    invisible in the UI ('Combined LA ' vs 'Combined LA') but produce confusing
    KeyErrors later when something matches by exact string equality. Normalising
    once on load keeps every downstream comparison straightforward.
    """
    df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]
    return df


@st.cache_data
def load_data(file, sheet_name=None):
    ext = os.path.splitext(file.name)[1].lower()
    if ext in [".xlsx", ".xls"]:
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        if sheet_name is None:
            # Defensive: pd.read_excel(..., sheet_name=None) returns a dict of all
            # sheets, which would break every df.columns call downstream. Read the
            # first non-empty sheet instead.
            all_sheets = pd.read_excel(file, sheet_name=None, engine=engine)
            for name, sheet_df in all_sheets.items():
                if not sheet_df.empty:
                    return _clean_columns(sheet_df)
            # All sheets empty - return the first one anyway so we have a frame
            return _clean_columns(next(iter(all_sheets.values())))
        return _clean_columns(pd.read_excel(file, sheet_name=sheet_name, engine=engine))
    try:
        return _clean_columns(pd.read_csv(file))
    except Exception:
        return _clean_columns(pd.read_csv(file, encoding="latin-1"))


def _explode_smart(df_in, col):
    """Apply smart_split_industries to a column and explode to long format.

    Returns a tuple of (series_of_lists, exploded_series_of_strings).
    """
    series_of_lists = df_in[col].apply(smart_split_industries)
    exploded = series_of_lists.explode()
    return series_of_lists, exploded


@st.cache_data
def process_industry_buzzword(df_active, layout, amount_choice=None):
    if layout["mode"] == "single":
        pieces_count = []
        pieces_amt = []

        ind_col = layout.get("ind_col")
        buzz_col = layout.get("buzz_col")
        # Dedupe while preserving order. When the user points both dropdowns at
        # the same column (e.g. their export has Industries + Buzzwords merged
        # into one column called 'Tags'), this prevents double-counting.
        seen = set()
        cols = []
        for c in (ind_col, buzz_col):
            if c and c not in seen:
                cols.append(c)
                seen.add(c)

        if not cols:
            return pd.Series(dtype=float)

        if amount_choice is None:
            # Pure count mode
            for c in cols:
                _, exploded = _explode_smart(df_active, c)
                pieces_count.append(exploded.dropna())
            items = pd.concat(pieces_count) if pieces_count else pd.Series(dtype=object)
            return items.value_counts() if len(items) else pd.Series(dtype=int)
        else:
            # Sum-by-amount mode: each industry/buzzword on a row attracts that
            # row's amount. We rebuild the per-item amount vector via repeat.
            amts = pd.to_numeric(df_active[amount_choice], errors="coerce").fillna(0).values
            for c in cols:
                series_of_lists, exploded = _explode_smart(df_active, c)
                lengths = series_of_lists.apply(len).values
                repeated_amts = np.repeat(amts, lengths)
                exploded = exploded.reset_index(drop=True)
                df_pair = pd.DataFrame({"item": exploded.values, "amt": repeated_amts})
                df_pair = df_pair[df_pair["item"].notna() & (df_pair["item"] != "")]
                pieces_amt.append(df_pair)
            combined = pd.concat(pieces_amt) if pieces_amt else pd.DataFrame(columns=["item", "amt"])
            return combined.groupby("item")["amt"].sum() if len(combined) else pd.Series(dtype=float)

    else:
        # Wide mode (indicator columns like "Industries - FinTech" or
        # "Buzzwords - Creative industries"). Each column carries a TRUE/FALSE
        # value per row; we count how many rows are TRUE for each tag, then
        # rank the tags.
        #
        # Dedupe defensively in case the same column got listed in both
        # ind_cols and buzz_cols (e.g. a column named "Industries - X" that
        # also matched a Buzzword pattern).
        seen = set()
        cols_to_process = []
        for c in layout.get("ind_cols", []) + layout.get("buzz_cols", []):
            if c not in seen and c in df_active.columns:
                cols_to_process.append(c)
                seen.add(c)
        if not cols_to_process:
            return pd.Series(dtype=float)

        # Build a boolean matrix: rows x tags. Each cell is whether the row was
        # tagged with that industry/buzzword, parsed robustly so TRUE/FALSE,
        # 1/0, Yes/No etc. all work the same way.
        tag_names = []
        truthy_columns = {}
        for c in cols_to_process:
            tag_name = c.split(" - ", 1)[-1].split(": ", 1)[-1].strip()
            truthy_col = _to_truthy(df_active[c])
            # If the tag appears in multiple source columns (deduped above by
            # column name, not tag name), OR them together so a row counts
            # once per tag, not once per source column.
            if tag_name in truthy_columns:
                truthy_columns[tag_name] = truthy_columns[tag_name] | truthy_col
            else:
                truthy_columns[tag_name] = truthy_col
                tag_names.append(tag_name)

        M = pd.DataFrame({name: truthy_columns[name] for name in tag_names})

        if amount_choice and amount_choice in df_active.columns:
            amt = pd.to_numeric(df_active[amount_choice], errors="coerce").fillna(0)
            # Each tag's total = sum of amounts for rows where that tag is True
            return M.multiply(amt, axis=0).sum()
        return M.sum().astype(int)


@st.cache_data
def process_generic_explode(df_active, target_col, use_smart_split=False):
    """Split and count separator-separated strings in a generic column.

    Recognises both comma and semicolon separators. If the cell contains a
    semicolon, the row is split on semicolons (commas are kept literal);
    otherwise the row is split on commas.
    """
    if use_smart_split:
        exploded = df_active[target_col].apply(smart_split_industries).explode()
        exploded = exploded.dropna()
        return exploded[exploded != ""].value_counts()
    s = df_active[target_col].dropna().astype(str)
    # Per-row: if it contains ';', split on ';'; else split on ','.
    has_semi = s.str.contains(";")
    semi_part = s[has_semi].str.split(";")
    comma_part = s[~has_semi].str.split(",")
    ex = pd.concat([semi_part, comma_part]).explode().str.strip()
    return ex[~ex.isin(["", "nan", "None"])].value_counts()


# ========================= HELPERS =========================
def money_fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)) or v == 0:
        return "£0"
    if v >= 1e9: return f"£{v/1e9:.1f}b"
    if v >= 1e6: return f"£{v/1e6:.1f}m"
    if v >= 1e3: return f"£{v/1e3:.1f}k"
    return f"£{v:.0f}"


def plot_bar(labels, values, title, highlight_first=True, right_formatter=lambda x: str(x)):
    fig, ax = plt.subplots(figsize=(10, 6))
    if not labels:
        return fig
    max_val = max(values) if values else 1
    y_pos = list(range(len(labels)))
    ax.barh(y_pos, [max_val] * len(values), color='#E0E0E0', height=0.8)
    for i, (y, v) in enumerate(zip(y_pos, values)):
        color = '#4B4897' if (highlight_first and i == 0) else '#A4A2F2'
        ax.barh(y, float(v), color=color, height=0.8)
    ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.xaxis.set_visible(False)
    offset = max_val * 0.015
    for i, (label, v) in enumerate(zip(labels, values)):
        text_c = 'white' if (highlight_first and i == 0) else 'black'
        ax.text(offset, i, str(label), va='center', color=text_c, fontsize=11)
        ax.text(max_val - offset, i, right_formatter(v), va='center', ha='right', color=text_c, fontweight='bold')
    ax.set_title(title, fontsize=14, pad=20)
    ax.invert_yaxis()
    return fig


@st.cache_data(show_spinner=False, max_entries=10)
def render_chart_bytes(labels_tuple, values_tuple, title, highlight_first, fmt_kind):
    """Render the inline chart PNG once per unique input combination.

    Returns the display PNG bytes only. 100 DPI keeps render time around
    ~80-100ms (vs ~130-200ms at 150-200 DPI) while still producing a 1000x600
    image - enough resolution for inline browser display, since st.image
    resizes to the container width.

    The SVG and 300 DPI PNG downloads are rendered LAZILY by separate
    functions, only when the user clicks their download button. This means
    that during normal chart updates (changing exclusions, top-N, ranking
    order), only the cheap 100 DPI PNG is rendered.

    Tuples are used for the labels/values arguments so the cache key is hashable.
    """
    labels = list(labels_tuple)
    values = list(values_tuple)
    fmt_fn = money_fmt if fmt_kind == "money" else (lambda x: f"{int(x):,}")
    fig = plot_bar(labels, values, title, highlight_first=highlight_first, right_formatter=fmt_fn)
    png = io.BytesIO()
    fig.savefig(png, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    return png.getvalue()


@st.cache_data(show_spinner=False, max_entries=5)
def _render_svg(labels_tuple, values_tuple, title, highlight_first, fmt_kind):
    """Render an SVG of the chart. Lazy - only called when user clicks SVG download.

    Vector format ideal for Adobe and publication-quality output. Render time
    ~80-90ms but only invoked once per download click, not per rerun.
    """
    labels = list(labels_tuple)
    values = list(values_tuple)
    fmt_fn = money_fmt if fmt_kind == "money" else (lambda x: f"{int(x):,}")
    fig = plot_bar(labels, values, title, highlight_first=highlight_first, right_formatter=fmt_fn)
    svg = io.BytesIO()
    fig.savefig(svg, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    return svg.getvalue()


@st.cache_data(show_spinner=False, max_entries=5)
def _render_hires_png(labels_tuple, values_tuple, title, highlight_first, fmt_kind):
    """Render a 300 DPI PNG for download (~3000x1800 pixels). Lazy.

    Slow - 300 DPI savefig takes ~250ms. Only invoked when the user clicks
    the 'PNG (High Res)' download button, via st.download_button's
    callable-data feature.
    """
    labels = list(labels_tuple)
    values = list(values_tuple)
    fmt_fn = money_fmt if fmt_kind == "money" else (lambda x: f"{int(x):,}")
    fig = plot_bar(labels, values, title, highlight_first=highlight_first, right_formatter=fmt_fn)
    png = io.BytesIO()
    fig.savefig(png, format="png", bbox_inches="tight", dpi=300)
    plt.close(fig)
    return png.getvalue()


def detect_layout(df):
    """Detect Industries/Buzzwords columns.

    Single mode: a column whose stripped name ends with the word "Industries",
    "Industry", "Buzzwords", or "Buzzword" (case-insensitive). Catches all of:
        Industries, (Company) Industries, (Trading Address) Industries,
        Industry, (Company) Industry, Buzzwords, (Company) Buzzwords,
        Buzzword, etc. — plus trailing-space variants.

    Beauhurst uses the plural form on company exports and the singular form on
    deal / acquisition exports, so both must be supported.

    Wide mode: any column whose name starts with "Industries - " / "Industry - "
    / "Buzzwords - " / "Buzzword - " (or ": " variants).
    """
    cols = list(df.columns.astype(str))

    def _find_single(*suffix_words):
        """Return the first column matching any of the suffix words."""
        suffix_lowers = [w.lower() for w in suffix_words]
        # Exact / parenthesised matches first
        for c in cols:
            name = c.strip().lower()
            if name in suffix_lowers:
                return c
            for s in suffix_lowers:
                if name.endswith(") " + s):
                    return c
        # Anything ending in the suffix word as the final token
        for c in cols:
            tokens = c.strip().split()
            if tokens and tokens[-1].lower() in suffix_lowers:
                return c
        return None

    ind_s = _find_single("Industries", "Industry")
    buzz_s = _find_single("Buzzwords", "Buzzword")

    # Wide-format indicator columns. The "head" is the bit before " - " or ": ";
    # we match if its last word is one of the prefix words (case-insensitive),
    # so all of these are recognised:
    #   Industries - FinTech
    #   Buzzwords - Creative industries
    #   (Company) Industries - FinTech
    #   (Trading Address) Buzzwords - Creative industries
    def _is_wide(col, *prefixes):
        if " - " not in col and ": " not in col:
            return False
        head = col.strip().split(" - ", 1)[0].split(": ", 1)[0].strip()
        if not head:
            return False
        tokens = head.split()
        last = tokens[-1].lower()
        return last in [p.lower() for p in prefixes]

    ind_w = [c for c in cols if _is_wide(c, "Industries", "Industry")]
    buzz_w = [c for c in cols if _is_wide(c, "Buzzwords", "Buzzword")]

    # Prefer wide-format when present. Per-tag indicator columns are a
    # deliberate Beauhurst export choice (usually the same export will also
    # include a comma-separated 'Industries' summary, but the user picked the
    # wide format because they want per-tag detail).
    if ind_w or buzz_w:
        return {"mode": "wide", "ind_cols": ind_w, "buzz_cols": buzz_w}
    if ind_s or buzz_s:
        return {"mode": "single", "ind_col": ind_s, "buzz_col": buzz_s}
    return {"mode": "unknown"}


# Companies House status values that count as "Active" for our purposes. The
# user definition is "Active or Dormant Company" - both mean the company is
# still on the register and operating normally.
_ACTIVE_STATUSES = {"active", "dormant company"}

# Beauhurst column names that hold Companies House / trading status. The
# canonical export uses "Companies House status", but variants exist depending
# on the export profile - hence the broader set.
_STATUS_COLUMN_HINTS = (
    "companies house status",
    "ch status",
    "trading status",
    "company status",
)


def find_companies_house_status_columns(cols):
    """Return columns that look like a Companies House / trading status field.

    Matches a few common Beauhurst column name variants (current status, status
    at time of deal, with or without owner prefix). When the export uses a
    non-standard column name, the UI still lets the user pick one manually
    from the full column list.
    """
    out = []
    for c in cols:
        lc = str(c).lower()
        if any(h in lc for h in _STATUS_COLUMN_HINTS):
            out.append(c)
    return out


def looks_like_status_values(series, threshold=0.5):
    """Heuristic: does this column's values look like CH status values?

    Used as a fallback when name-based detection misses. A column is treated
    as a status field if at least half of its non-null values are in the known
    Companies House status vocabulary.
    """
    known = {
        "active", "dormant company", "liquidation", "dissolved",
        "in administration", "in receivership", "voluntary arrangement",
        "active - proposal to strike off",
    }
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
        return False
    sample = non_null.head(500)
    lower = sample.astype(str).str.strip().str.lower()
    return (lower.isin(known).mean()) >= threshold


def rank_amount_columns(cols):
    """Return all columns, with the most plausible 'amount' columns first.

    Preference order:
      1. GBP-converted columns
      2. Other money-flavoured columns (amount raised, consideration, valuation,
         turnover, revenue, etc.)
      3. Everything else, preserving original order

    Nothing is filtered out — the user can always pick any column they like.
    """
    cols = list(cols)
    gbp = []
    money = []
    others = []
    money_hints = (
        "amount raised", "consideration", "valuation", "turnover", "revenue",
        "income", "profit", "ebitda", "cash", "funding", "investment",
        "price", "value", "cost", "salary", "spend", "fee", "£", "gbp", "usd", "eur",
    )
    for c in cols:
        lc = str(c).lower()
        if "gbp" in lc or "converted to gbp" in lc:
            gbp.append(c)
        elif any(h in lc for h in money_hints):
            money.append(c)
        else:
            others.append(c)
    return gbp + money + others


def _cell_has_data(series):
    """A row 'has data' if the cell is not NaN and not a blank/whitespace string."""
    return series.notna() & (series.astype(str).str.strip() != "") & (series.astype(str).str.lower() != "nan")


# Strings that count as TRUE / FALSE in wide-format indicator columns. Beauhurst
# exports use any of these depending on tool/format - Excel may render TRUE/FALSE,
# CSV may have "Yes"/"No", numerically-coded files may have 1/0, etc.
_TRUTHY_STRINGS = {"true", "t", "yes", "y", "1", "1.0"}
_FALSY_STRINGS = {"false", "f", "no", "n", "0", "0.0", "", "nan", "none", "null"}


def _to_truthy(series):
    """Return a boolean Series mapping the input to True/False values.

    Handles all common ways Beauhurst exports indicator columns:
      - Native booleans (True/False)
      - Numeric (1/0, 1.0/0.0)
      - Strings ("TRUE"/"FALSE", "true"/"false", "Yes"/"No", "1"/"0", etc.)
      - NaN / empty / 'nan' / 'None' -> False

    Anything not in the recognised falsy set is treated as truthy provided the
    cell has content. This is the safe default - if a user has tagged a row
    with a non-empty value, count it.
    """
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False).astype(bool)
    if pd.api.types.is_numeric_dtype(series):
        # NaN -> False, 0 -> False, anything else -> True
        return series.fillna(0).astype(bool)
    # Object / mixed dtype: normalise to lowercase string, compare to known sets
    s = series.fillna("").astype(str).str.strip().str.lower()
    # Explicit falsy strings -> False; anything non-empty otherwise -> True
    return ~s.isin(_FALSY_STRINGS)


def is_year_column(name, series):
    """Detect a 'year' column heuristically.

    Beauhurst exports use bare integer years (e.g. 2024) in columns like
    'Year of incorporation' or 'Deal year'. Pandas reads these as float because
    of any NaNs, which is what produces the dreaded '2024.0' display. We
    detect such columns by name pattern AND by checking the actual values look
    like 4-digit years between 1800 and one year past the current year.
    """
    name_lc = str(name).lower()
    name_hits_year = (
        name_lc == "year"
        or name_lc.endswith(" year")
        or " year " in name_lc
        or "year of" in name_lc
        or name_lc.endswith(" year)")
    )
    if not name_hits_year:
        return False
    nums = pd.to_numeric(series, errors="coerce").dropna()
    if nums.empty:
        return False
    # All non-null values must look like plausible years
    next_year = datetime.now().year + 1
    return ((nums >= 1800) & (nums <= next_year) & (nums == nums.astype(int))).all()


def is_numeric_column(series):
    """True if at least 80% of non-null values can be parsed as numbers.

    Used to decide whether to offer numeric (range / <= / >= / between) filter
    modes for a column. The 80% threshold lets us still treat a mostly-numeric
    column as numeric even when there's the occasional stray text value.
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    if pd.api.types.is_numeric_dtype(series):
        return True
    coerced = pd.to_numeric(non_null, errors="coerce")
    return coerced.notna().mean() >= 0.8


def is_date_column(series):
    """True if the column is a real datetime dtype (not a year-as-int)."""
    return pd.api.types.is_datetime64_any_dtype(series)


def _parse_to_iso_date(v):
    """Convert one value to a YYYY-MM-DD string, or None if it can't be parsed.

    Works for any year from 0001 to 9999, including dates pandas can't represent
    as Timestamps (pre-1677, post-2262). Tries the fast pandas path first; falls
    back to dateutil.parser for out-of-range or unusual formats.

    Years are zero-padded so ISO strings compare lexicographically the same way
    they compare chronologically: "0570-06-15" < "1066-12-25" < "2024-01-01".
    """
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    # Pandas Timestamp / numpy datetime64 - already in range, fast path
    if isinstance(v, pd.Timestamp):
        if pd.isna(v):
            return None
        return f"{int(v.year):04d}-{int(v.month):02d}-{int(v.day):02d}"
    # Python date / datetime
    if hasattr(v, "year") and hasattr(v, "month") and hasattr(v, "day"):
        try:
            return f"{int(v.year):04d}-{int(v.month):02d}-{int(v.day):02d}"
        except Exception:
            pass
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "nat", "null"):
        return None
    # Fast path: pandas (handles ~95% of normal dates very quickly)
    ts = pd.to_datetime(s, errors="coerce")
    if pd.notna(ts):
        return f"{int(ts.year):04d}-{int(ts.month):02d}-{int(ts.day):02d}"
    # Fallback: dateutil for out-of-range years (570 AD etc.) or unusual formats
    try:
        from dateutil import parser as _dp
        parsed = _dp.parse(s, dayfirst=False)
        return f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"
    except Exception:
        pass
    try:
        from dateutil import parser as _dp
        parsed = _dp.parse(s, dayfirst=True)
        return f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"
    except Exception:
        return None


def _iso_to_date(s):
    """Convert a YYYY-MM-DD string to a Python date object (any year 1..9999)."""
    if s is None:
        return None
    if isinstance(s, date):
        return s
    parts = str(s).split("-")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def to_iso_date_series(series):
    """Convert a Series of date-ish values to a Series of YYYY-MM-DD strings.

    Used in place of pd.to_datetime when the column may contain dates outside
    the 1677-2262 Timestamp range. ISO strings sort chronologically when
    compared lexicographically, so all the >, <, ≥, ≤, between comparisons
    work directly on the string Series.
    """
    return series.apply(_parse_to_iso_date)


def is_date_like(series):
    """True if values are dates or look parseable as dates (>= 80% success).

    Handles both real datetime dtypes and string date formats (YYYY/MM/DD,
    DD/MM/YYYY, ISO, etc.) - including years pandas can't natively represent
    as Timestamps (pre-1677). Years-as-integers are NOT counted as dates
    because they're better handled as integer ranges, not date pickers.
    """
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    non_null = series.dropna()
    if len(non_null) == 0:
        return False
    # Pure-numeric columns aren't dates even if they coerce successfully
    if pd.api.types.is_numeric_dtype(series):
        return False
    sample = non_null.head(200)
    # First try pandas (fast). If too many fail (likely out-of-range years),
    # fall back to the full ISO parser which uses dateutil.
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        try:
            parsed = pd.to_datetime(sample, errors="coerce", dayfirst=False)
            rate = parsed.notna().mean()
        except Exception:
            rate = 0.0
        if rate < 0.8:
            try:
                parsed = pd.to_datetime(sample, errors="coerce", dayfirst=True)
                rate = parsed.notna().mean()
            except Exception:
                pass
    if rate < 0.8:
        # Last resort: per-value parse via dateutil (handles year 570 etc.)
        iso = to_iso_date_series(sample)
        rate = iso.notna().mean()
    return rate >= 0.8


def to_dates(series):
    """Coerce a series to datetime (Timestamps).

    Only works inside pandas' nanosecond range (1677-2262). For columns with
    dates outside that range, use to_iso_date_series instead.
    """
    primary = pd.to_datetime(series, errors="coerce")
    if pd.api.types.is_datetime64_any_dtype(series):
        return primary
    if primary.notna().mean() < 0.8:
        non_null = series.dropna()
        if len(non_null) > 0:
            sample_dayfirst = pd.to_datetime(non_null.head(200), errors="coerce", dayfirst=True)
            if sample_dayfirst.notna().mean() > primary.dropna().notna().mean():
                return pd.to_datetime(series, errors="coerce", dayfirst=True)
    return primary


def display_value(v, is_year=False):
    """Render a single value the way a person would expect to see it.

    Strips the '.0' from float-encoded integers (e.g. years) and presents
    Timestamps as ISO dates. Used both for dropdown options and as the
    canonical key when matching filter selections against row values.
    """
    if v is None:
        return ""
    if isinstance(v, float):
        if np.isnan(v):
            return ""
        if is_year or v.is_integer():
            return str(int(v))
        return str(v)
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    return str(v)


def display_series(series, is_year=False):
    """Apply display_value across a pandas Series, returning string dtype."""
    is_year = bool(is_year)
    if is_year:
        nums = pd.to_numeric(series, errors="coerce")
        out = nums.apply(lambda v: "" if pd.isna(v) else str(int(v)))
        return out
    return series.apply(lambda v: display_value(v))


def safe_filename(s, default="chart"):
    """Sanitise a user-supplied chart title into a safe download filename stem."""
    if not s:
        return default
    s = str(s).strip()
    # Strip path separators and characters problematic on Windows/Mac/Linux
    bad = '<>:"/\\|?*\n\r\t'
    out = "".join("_" if ch in bad else ch for ch in s)
    out = out.strip(" ._")
    return out or default



def count_unknown_rows(df_active, mode, layout=None, target_col=None):
    """Number of rows in df_active that contributed nothing to the ranking.

    - Industry/Buzzword mode (single): rows where every relevant column is blank.
    - Industry/Buzzword mode (wide):   rows where no indicator column is set.
    - Generic mode:                    rows where the target column is blank.
    """
    if mode == "Yes" and layout is not None:
        if layout.get("mode") == "single":
            check_cols = [c for c in (layout.get("ind_col"), layout.get("buzz_col")) if c]
            if not check_cols:
                return 0
            has_any = pd.Series(False, index=df_active.index)
            for c in check_cols:
                has_any = has_any | _cell_has_data(df_active[c])
            return int((~has_any).sum())
        if layout.get("mode") == "wide":
            cols_to_check = layout.get("ind_cols", []) + layout.get("buzz_cols", [])
            cols_to_check = [c for c in cols_to_check if c in df_active.columns]
            if not cols_to_check:
                return 0
            # A row is "unknown" if NONE of its indicator columns are truthy.
            # Uses the same robust truthiness as the ranking logic, so TRUE/FALSE
            # strings work as well as numeric 1/0.
            any_true = pd.Series(False, index=df_active.index)
            for c in cols_to_check:
                any_true = any_true | _to_truthy(df_active[c])
            return int((~any_true).sum())
        return 0
    if target_col is not None and target_col in df_active.columns:
        return int((~_cell_has_data(df_active[target_col])).sum())
    return 0


def build_csv_table(series, unknown_count, item_label, value_label, include_rank=True):
    """Turn a sorted metric Series into the CSV body the user wants.

    Always includes the FULL ranking (not just the top N shown in the chart),
    and appends an 'Unknown' row whenever there are rows with no category.
    """
    df = pd.DataFrame({item_label: series.index.astype(str), value_label: series.values})
    if unknown_count and unknown_count > 0:
        df = pd.concat(
            [df, pd.DataFrame([{item_label: "Unknown", value_label: unknown_count}])],
            ignore_index=True,
        )
    # Coerce value column to int when every value is whole - cleaner CSV output
    try:
        if np.all(np.equal(np.mod(df[value_label].astype(float), 1), 0)):
            df[value_label] = df[value_label].astype(float).astype("Int64")
    except (TypeError, ValueError):
        pass
    if include_rank:
        df.insert(0, "Rank", range(1, len(df) + 1))
        # The Unknown row isn't part of the ranking - clear its rank
        if unknown_count and unknown_count > 0:
            df.loc[df[item_label] == "Unknown", "Rank"] = pd.NA
    return df


def build_combined_csv_table(metric_series, final_series, unknown_count, item_label, value_label):
    """Build a single CSV with two side-by-side rankings.

    Columns:
      Full Rank | Full Industry / Buzzword | Full Number of companies | (blank) |
      Chart Rank | Chart Industry / Buzzword | Chart Number of companies

    The left half is the full ranking (every item from the metric series, plus
    an Unknown row). The right half is the chart-matched ranking: drops items
    excluded via the 'Exclude from chart' multiselect but keeps every other
    item - not truncated to the top N bars.

    A blank spacer column sits between the two halves so it's instantly readable
    in Excel. The two halves can be different lengths; shorter side is padded
    with empty rows so they're aligned at row 1 (the top rank).
    """
    full_df = build_csv_table(metric_series, unknown_count, item_label, value_label)
    chart_df = build_csv_table(final_series, unknown_count, item_label, value_label)

    # Prefix columns so the two halves are unambiguous when scanned
    full_df = full_df.rename(columns={
        "Rank": "Rank (Full)",
        item_label: f"{item_label} (Full)",
        value_label: f"{value_label} (Full)",
    })
    chart_df = chart_df.rename(columns={
        "Rank": "Rank (Chart)",
        item_label: f"{item_label} (Chart)",
        value_label: f"{value_label} (Chart)",
    })

    # Pad the shorter side with empty rows so the two halves stay row-aligned
    max_len = max(len(full_df), len(chart_df))
    if len(full_df) < max_len:
        pad = pd.DataFrame({c: [pd.NA] * (max_len - len(full_df)) for c in full_df.columns})
        full_df = pd.concat([full_df, pad], ignore_index=True)
    if len(chart_df) < max_len:
        pad = pd.DataFrame({c: [pd.NA] * (max_len - len(chart_df)) for c in chart_df.columns})
        chart_df = pd.concat([chart_df, pad], ignore_index=True)

    # Concatenate horizontally with a blank spacer column between
    spacer = pd.DataFrame({"": [""] * max_len})
    combined = pd.concat(
        [full_df.reset_index(drop=True), spacer, chart_df.reset_index(drop=True)],
        axis=1,
    )
    return combined


def _render_filter_editor_body(df, current_source):
    """Render the Raw Data Filters UI.

    Wrapped with @st.fragment below so widget interactions inside don't trigger
    a full app rerun - only this section rerenders. The Apply button lives
    OUTSIDE the fragment, so clicking it triggers a normal full rerun that
    rebuilds df_active and refreshes the chart.

    Side effects:
      st.session_state.rules         - mutated by Add/Remove/per-rule widgets
      st.session_state["_active_only_state"]  - the Active-only checkbox value
      st.session_state["_active_col_state"]   - the chosen status column
    """
    # === Active filter (auto-detect + manual override) ===
    status_cols_auto = find_companies_house_status_columns(df.columns)
    if not status_cols_auto:
        status_cols_auto = [c for c in df.columns if looks_like_status_values(df[c])]

    active_only = st.checkbox(
        "Active companies only",
        value=False,
        key="filter_active_only",
        help="Include only rows where Companies House status is 'Active' or "
             "'Dormant Company'. Auto-detects the status column; pick one "
             "manually if your export uses a non-standard name. Combined "
             "with your other filters using AND."
    )
    chosen_status_col = None
    if active_only:
        other_cols = [c for c in df.columns if c not in status_cols_auto]
        options = ["<None>"] + list(status_cols_auto) + list(other_cols)
        default_idx = 1 if status_cols_auto else 0
        chosen_status_col = st.selectbox(
            "Status column",
            options,
            index=default_idx,
            key="filter_active_status_col",
            help="Auto-detected columns are listed first. Pick a different "
                 "one if your export uses a non-standard name."
        )
        if chosen_status_col == "<None>":
            chosen_status_col = None
        elif chosen_status_col in df.columns:
            vals_lower = df[chosen_status_col].astype(str).str.strip().str.lower()
            n_active = int(vals_lower.isin(_ACTIVE_STATUSES).sum())
            if n_active == 0:
                distinct = df[chosen_status_col].dropna().astype(str).str.strip().unique().tolist()[:5]
                st.warning(
                    f"No rows in `{chosen_status_col}` have a value of "
                    f"'Active' or 'Dormant Company'. Sample values: "
                    f"{', '.join(repr(v) for v in distinct)}."
                )
            else:
                st.caption(
                    f"Of {len(df):,} rows, {n_active:,} have status "
                    f"'Active' or 'Dormant Company'."
                )
    # Stash state so the outer (full-rerun) scope can read it after Apply
    st.session_state["_active_only_state"] = active_only
    st.session_state["_active_col_state"] = chosen_status_col

    # === Add / Remove filter rule buttons ===
    c1, c2 = st.columns(2)
    if c1.button("➕ Add filter"):
        st.session_state.rules.append({
            'col': df.columns[0], 'mode': 'Include', 'kind': 'Values',
            'vals': [], 'op': '≥', 'num1': None, 'num2': None, '_type': 'number',
        })
    if c2.button("➖ Remove last"):
        if st.session_state.rules:
            st.session_state.rules.pop()

    # === Per-rule editor ===
    df_cols = list(df.columns.astype(str))
    for i, rule in enumerate(st.session_state.rules):
        label = f"Filter {i+1}: {rule.get('col', '(pick a column)')}"
        with st.expander(label, expanded=True):
            current_col = rule.get('col')
            if current_col not in df_cols:
                current_col = df_cols[0]
            col_idx = df_cols.index(current_col)

            chosen_col = st.selectbox(
                "Column",
                df_cols,
                index=col_idx,
                key=f"f_col_{i}",
                help="Column to filter on."
            )
            rule['col'] = chosen_col

            series = df[chosen_col]
            # Column-type metadata is cached per (data source, column) so we
            # don't re-detect date/year/numeric on every fragment rerun.
            _meta_key = ("_colmeta", current_source, chosen_col)
            if _meta_key not in st.session_state:
                is_year_v = is_year_column(chosen_col, series)
                is_date_v = is_date_like(series) and not is_year_v
                is_num_v = is_numeric_column(series) and not is_year_v and not is_date_v
                st.session_state[_meta_key] = (is_year_v, is_date_v, is_num_v)
            is_year, is_date, is_num = st.session_state[_meta_key]

            kinds = ["Values"]
            if is_num or is_year or is_date:
                kinds.append("Range / comparison")

            if rule.get('kind', 'Values') not in kinds:
                rule['kind'] = kinds[0]
            if len(kinds) > 1:
                rule['kind'] = st.radio(
                    "Filter type",
                    kinds,
                    index=kinds.index(rule['kind']),
                    key=f"f_kind_{i}",
                    horizontal=True,
                    help="Pick specific values, or apply a range. "
                         "Ranges work for numbers, years, and dates."
                )
            else:
                rule['kind'] = kinds[0]

            rule['mode'] = st.radio(
                "Action",
                ["Include", "Exclude"],
                index=0 if rule.get('mode', 'Include') == 'Include' else 1,
                key=f"f_mode_{i}",
                horizontal=True,
            )

            if rule['kind'] == "Range / comparison":
                if is_date:
                    rule['_type'] = 'date'
                elif is_year:
                    rule['_type'] = 'year'
                else:
                    rule['_type'] = 'number'

                ops = ["=", "≥", "≤", ">", "<", "between"]
                rule['op'] = st.selectbox(
                    "Comparison",
                    ops,
                    index=ops.index(rule.get('op')) if rule.get('op') in ops else (5 if rule['_type'] == 'date' else 1),
                    key=f"f_op_{i}",
                )

                if rule['_type'] == 'date':
                    iso_series = to_iso_date_series(series).dropna()
                    if not len(iso_series):
                        st.caption(f"`{chosen_col}` has no parseable dates.")
                        rule['num1'] = None
                        rule['num2'] = None
                    else:
                        col_min_iso = iso_series.min()
                        col_max_iso = iso_series.max()
                        col_min = _iso_to_date(col_min_iso)
                        col_max = _iso_to_date(col_max_iso)
                        st.caption(
                            f"`{chosen_col}` ranges from {col_min_iso} to "
                            f"{col_max_iso} ({len(iso_series):,} dated values)."
                        )

                        def _coerce_date(v, fallback):
                            if v is None:
                                return fallback
                            if isinstance(v, date) and not isinstance(v, datetime):
                                return v
                            if isinstance(v, datetime):
                                return v.date()
                            if hasattr(v, "date") and callable(v.date):
                                try:
                                    return v.date()
                                except Exception:
                                    pass
                            iso = _parse_to_iso_date(v)
                            parsed = _iso_to_date(iso) if iso else None
                            return parsed if parsed else fallback

                        DATE_PICKER_MIN = date(1, 1, 1)
                        DATE_PICKER_MAX = date(9999, 12, 31)
                        if rule['op'] == "between":
                            lo_default = _coerce_date(rule.get('num1'), col_min)
                            hi_default = _coerce_date(rule.get('num2'), col_max)
                            c_lo, c_hi = st.columns(2)
                            rule['num1'] = c_lo.date_input(
                                "From", value=lo_default,
                                min_value=DATE_PICKER_MIN, max_value=DATE_PICKER_MAX,
                                key=f"f_num1_{i}"
                            ).isoformat()
                            rule['num2'] = c_hi.date_input(
                                "To", value=hi_default,
                                min_value=DATE_PICKER_MIN, max_value=DATE_PICKER_MAX,
                                key=f"f_num2_{i}"
                            ).isoformat()
                        else:
                            default = _coerce_date(rule.get('num1'), col_min)
                            rule['num1'] = st.date_input(
                                "Value", value=default,
                                min_value=DATE_PICKER_MIN, max_value=DATE_PICKER_MAX,
                                key=f"f_num1_{i}"
                            ).isoformat()
                            rule['num2'] = None
                elif rule['_type'] == 'year':
                    coerced = pd.to_numeric(series, errors="coerce").dropna()
                    col_min = int(coerced.min()) if len(coerced) else datetime.now().year
                    col_max = int(coerced.max()) if len(coerced) else datetime.now().year
                    st.caption(
                        f"`{chosen_col}` ranges from {col_min} to {col_max} "
                        f"({len(coerced):,} year values)."
                    )
                    if rule['op'] == "between":
                        lo_default = int(rule.get('num1') if rule.get('num1') is not None else col_min)
                        hi_default = int(rule.get('num2') if rule.get('num2') is not None else col_max)
                        c_lo, c_hi = st.columns(2)
                        rule['num1'] = c_lo.number_input(
                            "From", value=lo_default, step=1, format="%d", key=f"f_num1_{i}"
                        )
                        rule['num2'] = c_hi.number_input(
                            "To", value=hi_default, step=1, format="%d", key=f"f_num2_{i}"
                        )
                    else:
                        default = int(rule.get('num1') if rule.get('num1') is not None else col_min)
                        rule['num1'] = st.number_input(
                            "Value", value=default, step=1, format="%d", key=f"f_num1_{i}"
                        )
                        rule['num2'] = None
                else:
                    coerced = pd.to_numeric(series, errors="coerce").dropna()
                    col_min = float(coerced.min()) if len(coerced) else 0.0
                    col_max = float(coerced.max()) if len(coerced) else 0.0
                    st.caption(
                        f"`{chosen_col}` ranges from "
                        f"{display_value(col_min)} to {display_value(col_max)} "
                        f"({len(coerced):,} numeric values)."
                    )
                    if rule['op'] == "between":
                        lo_default = rule.get('num1') if rule.get('num1') is not None else col_min
                        hi_default = rule.get('num2') if rule.get('num2') is not None else col_max
                        c_lo, c_hi = st.columns(2)
                        rule['num1'] = c_lo.number_input(
                            "From", value=float(lo_default), key=f"f_num1_{i}"
                        )
                        rule['num2'] = c_hi.number_input(
                            "To", value=float(hi_default), key=f"f_num2_{i}"
                        )
                    else:
                        default = rule.get('num1') if rule.get('num1') is not None else col_min
                        rule['num1'] = st.number_input(
                            "Value", value=float(default), key=f"f_num1_{i}"
                        )
                        rule['num2'] = None
            else:
                # Values mode
                non_null = series.dropna()
                if len(non_null) == 0:
                    st.caption(f"`{chosen_col}` has no non-empty values.")
                    rule['vals'] = []
                else:
                    disp = display_series(non_null, is_year=is_year)
                    unique_vals = disp[disp != ""].unique().tolist()
                    if len(unique_vals) > 5000:
                        st.caption(
                            f"`{chosen_col}` has {len(unique_vals):,} unique values — "
                            f"showing the 5,000 most common."
                        )
                        top = disp[disp != ""].value_counts().head(5000).index.tolist()
                        opts = sorted(top)
                    else:
                        try:
                            opts = sorted(unique_vals, key=lambda v: (0, float(v)))
                        except (ValueError, TypeError):
                            opts = sorted(unique_vals)
                    prev = [v for v in rule.get('vals', []) if v in opts]
                    rule['vals'] = st.multiselect(
                        "Values to include / exclude",
                        opts,
                        default=prev,
                        key=f"f_vals_{i}",
                        help=f"{len(opts):,} option{'s' if len(opts) != 1 else ''} available."
                    )
                rule['op'] = None
                rule['num1'] = None
                rule['num2'] = None


# Wrap the filter editor with @st.fragment when available (Streamlit ≥ 1.37).
# This is the meat of the perceived-speed improvement: widget interactions
# inside the filter editor only re-render the filter editor, not the entire
# script. The chart, downloads, and metric computation stay as they were.
# Older Streamlit versions fall through to a normal full rerun.
if hasattr(st, "fragment"):
    render_filter_editor = st.fragment(_render_filter_editor_body)
else:
    render_filter_editor = _render_filter_editor_body




# ========================= APP START =========================
st.markdown(f'<h1 style="color:{APP_TITLE_COLOR};">Ranklin</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.header("1. Data Source")
    uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx", "xls"])
    sheet_name = None
    if uploaded_file and os.path.splitext(uploaded_file.name)[1].lower() in [".xlsx", ".xls"]:
        xls = pd.ExcelFile(uploaded_file)
        sheet_name = st.selectbox("Select sheet:", xls.sheet_names)

if uploaded_file:
    df = load_data(uploaded_file, sheet_name)

    # Fingerprint of the current data source (file + sheet). Used everywhere
    # downstream as a cache key for per-data-source memoisation. Computed
    # here, immediately after load, so it's available to the filter UI and
    # the column-type metadata cache.
    current_source = (getattr(uploaded_file, "name", None), sheet_name)
    source_changed = st.session_state.get("data_source") != current_source
    if source_changed:
        # Drop any filter rules pointing at columns that don't exist on the
        # new sheet, otherwise the next Apply click will crash.
        current_cols = set(df.columns.astype(str))
        st.session_state.rules = [
            r for r in st.session_state.get("rules", [])
            if r.get("col") in current_cols
        ]
        # Drop the column-type metadata cache - stale entries would point at
        # the previous sheet's data and produce wrong filter-type detection.
        for k in [k for k in st.session_state if isinstance(k, tuple) and k and k[0] == "_colmeta"]:
            del st.session_state[k]
        st.session_state.data_source = current_source

    with st.sidebar:
        st.markdown("---")
        chart_title = st.text_input("Chart Title:", "Ranking Chart")
        st.header("2. Analysis Options")
        mode = st.radio("Ranking Industries/Buzzwords?", ["Yes", "No"], horizontal=True)

        if mode == "No":
            analysis_type = st.radio("Analysis Type:", ["Count", "Sum"], horizontal=True)
            target_col = st.selectbox("Select Column to Rank", df.columns)
            explode_enabled = st.checkbox(
                "Explode comma-separated values",
                help="Split values like 'Apple, Orange' into separate counts"
            )
            beauhurst_aware = False
            if explode_enabled:
                beauhurst_aware = st.checkbox(
                    "Use Beauhurst-aware splitting",
                    value=True,
                    help="Treat multi-comma Beauhurst industry names (e.g. 'Repair, maintenance and servicing') as a single item."
                )
            if analysis_type == "Sum":
                # All columns are eligible — pandas may have read a number column
                # as text because of a stray 'N/A'; we coerce to numeric below so
                # the user is never silently locked out of a column they want.
                sum_col = st.selectbox(
                    "Column to Sum",
                    df.columns,
                    help="Any column with numeric values. Non-numeric values are ignored when summing."
                )
                if not pd.api.types.is_numeric_dtype(df[sum_col]):
                    coerced = pd.to_numeric(df[sum_col], errors="coerce")
                    valid = coerced.notna().sum()
                    if valid == 0:
                        st.warning(f"'{sum_col}' has no numeric values — sums will all be zero.")
                    else:
                        st.caption(f"'{sum_col}' isn't a number column; using {valid:,} numeric values from it.")
        else:
            ranking_by = st.radio("Rank by:", ["Count", "Total Amount Raised"], horizontal=True)
            # Show every column, with GBP/money-flavoured columns ranked first.
            ranked_amount_cols = rank_amount_columns(df.columns)
            amt_choice_raw = st.selectbox(
                "Amount column",
                ["<None>"] + ranked_amount_cols,
                help="Any numeric column will work. Best matches (GBP-converted, then other money columns) are listed first."
            )
            amount_choice = None if amt_choice_raw == "<None>" else amt_choice_raw
            if amount_choice and not pd.api.types.is_numeric_dtype(df[amount_choice]):
                coerced = pd.to_numeric(df[amount_choice], errors="coerce")
                valid = coerced.notna().sum()
                if valid == 0:
                    st.warning(f"'{amount_choice}' has no numeric values — totals will all be zero.")
                else:
                    st.caption(f"'{amount_choice}' isn't a number column; using {valid:,} numeric values from it.")

        st.markdown("---")
        st.header("3. Raw Data Filters")
        if 'rules' not in st.session_state:
            st.session_state.rules = []

        # The filter editor is wrapped in @st.fragment so widget interactions
        # inside (column picker, value multiselect, range inputs, Add/Remove
        # rule buttons) only re-render this section - not the chart or the
        # downstream computations. The APPLY CHANGES button below sits OUTSIDE
        # the fragment, so clicking it triggers a normal full rerun that
        # rebuilds df_active from the new rules.
        render_filter_editor(df, current_source)

        st.markdown('<div class="apply-btn">', unsafe_allow_html=True)
        apply_trigger = st.button("🚀 APPLY CHANGES", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Filtering Execution
    # The Active-only checkbox and status-column dropdown live inside the
    # filter editor fragment, which writes its state to session_state. Read
    # the latest values from there before rebuilding df_active.
    active_only = bool(st.session_state.get("_active_only_state", False))
    chosen_status_col = st.session_state.get("_active_col_state", None)

    if apply_trigger or source_changed or 'df_active' not in st.session_state:
        df_active = df.copy()
        # One-click Active filter (applied before the manual rule list so
        # subsequent rules operate on the already-narrowed view).
        if active_only and chosen_status_col and chosen_status_col in df_active.columns:
            status_lower = df_active[chosen_status_col].astype(str).str.strip().str.lower()
            df_active = df_active[status_lower.isin(_ACTIVE_STATUSES)]
        for rule in st.session_state.rules:
            col = rule.get('col')
            if col not in df_active.columns:
                continue
            kind = rule.get('kind', 'Values')
            mask = None

            # Backwards-compat: old rule kind was called "Number rule"
            if kind in ("Range / comparison", "Number rule"):
                op = rule.get('op')
                n1 = rule.get('num1')
                n2 = rule.get('num2')
                if op is None or n1 is None:
                    continue

                rtype = rule.get('_type', 'number')
                if rtype == 'date':
                    # Compare as zero-padded ISO date strings. This handles
                    # dates outside pandas' nanosecond Timestamp range (pre-1677,
                    # post-2262), including historical data back to year 1 AD.
                    # ISO 8601 dates with zero-padded years sort lexicographically
                    # the same way they sort chronologically.
                    col_vals = to_iso_date_series(df_active[col])
                    # n1/n2 are already ISO strings from the date_input.isoformat()
                    # call, but normalise via _parse_to_iso_date in case they came
                    # from older session state in a different form.
                    v1 = _parse_to_iso_date(n1)
                    v2 = _parse_to_iso_date(n2) if n2 is not None else None
                    if v1 is None:
                        continue
                    # Cells we couldn't parse become NaN in col_vals; pandas '<' '>'
                    # comparisons against NaN return False, but we replace NaN
                    # with an unmatchable sentinel string just to be explicit.
                    # We use the empty string which sorts before any real date.
                    col_vals = col_vals.fillna("")
                else:
                    col_vals = pd.to_numeric(df_active[col], errors="coerce")
                    v1, v2 = n1, n2

                if op == "=":
                    mask = col_vals == v1
                elif op == "≥":
                    mask = col_vals >= v1
                elif op == "≤":
                    mask = col_vals <= v1
                elif op == ">":
                    mask = col_vals > v1
                elif op == "<":
                    mask = col_vals < v1
                elif op == "between":
                    if v2 is None:
                        continue
                    lo, hi = (v1, v2) if v1 <= v2 else (v2, v1)
                    mask = (col_vals >= lo) & (col_vals <= hi)
                # For date: cells we couldn't parse have empty-string col_vals,
                # which would falsely match ≥ "" or = "". Re-mask them out.
                if rtype == 'date' and mask is not None:
                    parseable = col_vals != ""
                    mask = mask & parseable
                # NaN/NaT comparisons return False but be explicit for safety
                if mask is not None:
                    mask = mask.fillna(False)
            else:
                # Values mode: match on the year-aware displayed string so a user
                # selecting "2024" matches both the float 2024.0 and the string "2024".
                if not rule.get('vals'):
                    continue
                is_year = is_year_column(col, df_active[col])
                disp = display_series(df_active[col], is_year=is_year)
                mask = disp.isin(rule['vals'])

            if mask is not None:
                df_active = df_active[mask] if rule.get('mode', 'Include') == "Include" else df_active[~mask]
        st.session_state.df_active = df_active
        # Bump a cheap integer cache key. Used downstream to gate metric_series
        # recomputation - avoids the ~30ms DataFrame hash that @st.cache_data
        # would do on every rerun even when df_active hasn't changed.
        st.session_state._df_active_version = st.session_state.get("_df_active_version", 0) + 1
    df_active = st.session_state.df_active
    _df_active_version = st.session_state.get("_df_active_version", 0)

    # --- CALCULATION LOGIC ---
    if mode == "Yes":
        layout_auto = detect_layout(df_active)

        # Auto-detection provides the defaults; user can override either column
        # to point at any column in their file. This makes Ranklin work even
        # when Beauhurst (or the user's own export) names columns unexpectedly.
        with st.sidebar:
            cols_with_none = ["<None>"] + list(df_active.columns.astype(str))

            if layout_auto["mode"] == "wide":
                ind_w = layout_auto.get("ind_cols", [])
                buzz_w = layout_auto.get("buzz_cols", [])
                st.caption(
                    f"Detected wide-format columns "
                    f"({len(ind_w)} industry, {len(buzz_w)} buzzword)."
                )
                use_auto_wide = st.checkbox(
                    "Use detected wide-format columns",
                    value=True,
                    help="Uncheck to instead pick a single Industry/Buzzword column manually."
                )
            else:
                use_auto_wide = False

            if not use_auto_wide:
                auto_ind = layout_auto.get("ind_col") if layout_auto["mode"] == "single" else None
                auto_buzz = layout_auto.get("buzz_col") if layout_auto["mode"] == "single" else None
                ind_idx = cols_with_none.index(auto_ind) if auto_ind in cols_with_none else 0
                buzz_idx = cols_with_none.index(auto_buzz) if auto_buzz in cols_with_none else 0

                ind_col_choice = st.selectbox(
                    "Industry column",
                    cols_with_none,
                    index=ind_idx,
                    help="Pick any column with separator-separated industry tags "
                         "(commas or semicolons both work). Auto-detected default "
                         "shown — change if your column is named differently. If your "
                         "export has industries and buzzwords merged into a single "
                         "column, set both dropdowns to that column (or just pick it "
                         "here and set Buzzword to <None>)."
                )
                buzz_col_choice = st.selectbox(
                    "Buzzword column",
                    cols_with_none,
                    index=buzz_idx,
                    help="Pick any column with separator-separated buzzword tags, "
                         "or <None> to skip. Commas and semicolons both work."
                )
                if (
                    ind_col_choice != "<None>"
                    and buzz_col_choice != "<None>"
                    and ind_col_choice == buzz_col_choice
                ):
                    st.caption(
                        f"Treating `{ind_col_choice}` as a combined Industry + "
                        f"Buzzword column (counted once)."
                    )

            # IS-8 toggle: high-level Industrial Strategy 8 categories aggregate
            # many specific tags and usually dominate the top of the chart.
            # Default on (include them); flip off to compare specific tags.
            include_is8 = st.checkbox(
                "Include IS-8 categories",
                value=True,
                key="include_is8",
                help="The Industrial Strategy 8 (Advanced manufacturing, Clean energy, "
                     "Creative industries, Defence, Digital and technologies, Financial services, "
                     "Life sciences, Professional and business services). They aggregate many "
                     "specific tags, so excluding them surfaces narrower categories."
            )

        if use_auto_wide:
            layout = layout_auto
        else:
            ind_col_final = None if ind_col_choice == "<None>" else ind_col_choice
            buzz_col_final = None if buzz_col_choice == "<None>" else buzz_col_choice
            if not (ind_col_final or buzz_col_final):
                st.error(
                    "Pick at least one column to rank from. Use the Industry column or "
                    "Buzzword column dropdowns in the sidebar — any column with "
                    "comma-separated values will work."
                )
                st.stop()
            layout = {"mode": "single", "ind_col": ind_col_final, "buzz_col": buzz_col_final}

        # Defensive: validate every column the calculation will reference exists
        # on df_active. Prevents KeyError stack traces after sheet switches /
        # re-uploads where Streamlit retains a stale widget value.
        required = []
        if layout.get("mode") == "single":
            for c in (layout.get("ind_col"), layout.get("buzz_col")):
                if c:
                    required.append(c)
        elif layout.get("mode") == "wide":
            required.extend(layout.get("ind_cols", []))
            required.extend(layout.get("buzz_cols", []))
        if ranking_by != "Count" and amount_choice:
            required.append(amount_choice)
        missing = [c for c in required if c not in df_active.columns]
        if missing:
            st.error(
                "Column not found in current data: "
                + ", ".join(repr(c) for c in missing)
                + ". This usually means a previous selection is stale after "
                "switching sheets or re-uploading. Re-select the column from "
                "the dropdown in the sidebar, then click 🚀 APPLY CHANGES."
            )
            st.stop()

        # Cache metric_series in session_state to skip @st.cache_data's
        # DataFrame hashing on reruns where nothing relevant changed. The
        # version counter changes only when df_active is rebuilt; the other
        # cache key fields capture every other input that affects metric_series.
        _metric_key = (
            "yes", _df_active_version, str(layout),
            amount_choice if ranking_by != "Count" else None,
            ranking_by, include_is8,
        )
        if st.session_state.get("_metric_key") == _metric_key and "_metric_series" in st.session_state:
            metric_series = st.session_state["_metric_series"]
            if not include_is8 and "_is8_removed" in st.session_state and st.session_state["_is8_removed"] > 0:
                st.caption(
                    f"IS-8 categories excluded ({st.session_state['_is8_removed']} removed from ranking)."
                )
        else:
            metric_series = process_industry_buzzword(
                df_active, layout, amount_choice if ranking_by != "Count" else None
            )
            if not include_is8 and len(metric_series):
                before = len(metric_series)
                keep = [idx for idx in metric_series.index if str(idx).lower() not in _IS_8_LOWER]
                metric_series = metric_series.loc[keep]
                removed = before - len(metric_series)
                st.session_state["_is8_removed"] = removed
                if removed > 0:
                    st.caption(f"IS-8 categories excluded ({removed} removed from ranking).")
            else:
                st.session_state["_is8_removed"] = 0
            st.session_state["_metric_series"] = metric_series
            st.session_state["_metric_key"] = _metric_key
        agg_label = ranking_by
    else:
        # Defensive: if Streamlit's widget state retains a stale column name
        # (a known foot-gun after switching sheets or re-uploading files), the
        # raw access below would throw a KeyError stack trace. Surface a clean
        # message instead and stop here.
        required = [target_col]
        if analysis_type == "Sum":
            required.append(sum_col)
        missing = [c for c in required if c and c not in df_active.columns]
        if missing:
            st.error(
                "Column not found in current data: "
                + ", ".join(repr(c) for c in missing)
                + ". This usually means a previous selection is stale after "
                "switching sheets or re-uploading. Re-select the column from "
                "the dropdown in the sidebar, then click 🚀 APPLY CHANGES."
            )
            st.stop()

        _metric_key = (
            "no", _df_active_version, target_col, analysis_type,
            sum_col if analysis_type == "Sum" else None,
            explode_enabled, beauhurst_aware,
        )
        if st.session_state.get("_metric_key") == _metric_key and "_metric_series" in st.session_state:
            metric_series = st.session_state["_metric_series"]
            agg_label = "Sum" if analysis_type == "Sum" else "Count"
        else:
            if analysis_type == "Sum":
                # Coerce so a text-typed number column (e.g. one containing stray 'N/A')
                # still sums correctly. Non-numeric values become NaN and are skipped.
                sum_values = pd.to_numeric(df_active[sum_col], errors="coerce")
                metric_series = sum_values.groupby(df_active[target_col]).sum()
                agg_label = "Sum"
            else:
                if explode_enabled:
                    metric_series = process_generic_explode(df_active, target_col, use_smart_split=beauhurst_aware)
                else:
                    metric_series = df_active[target_col].value_counts()
                agg_label = "Count"
            st.session_state["_metric_series"] = metric_series
            st.session_state["_metric_key"] = _metric_key

    # --- CHART OPTIONS ---
    metric_series = metric_series.sort_values(ascending=False)

    with st.sidebar:
        st.markdown("---")
        st.header("4. View Options")
        exclude = st.multiselect(
            "Exclude from chart:",
            metric_series.index.tolist(),
            key="view_exclude",
            help="Items to drop from the chart. The CSV's 'Chart' columns "
                 "respect this list; the 'Full' columns ignore it."
        )
        final_series = metric_series.drop(exclude, errors='ignore')
        top_n = st.number_input(
            "Number of bars", 1, max(1, len(final_series)),
            min(10, max(1, len(final_series))),
            key="view_top_n",
        )
        rank_mode = st.radio(
            "Order:", ["Highest first", "Lowest first"],
            horizontal=True, key="view_rank_mode",
        )

    l_chart = final_series.index.tolist()
    v_chart = final_series.values.tolist()
    if rank_mode == "Lowest first":
        l_chart, v_chart = l_chart[::-1][:top_n], v_chart[::-1][:top_n]
    else:
        l_chart, v_chart = l_chart[:top_n], v_chart[:top_n]

    # --- MAIN DISPLAY ---
    st.subheader(f"Analysis Results ({len(df_active):,} rows)")
    if not l_chart:
        st.warning("No data found.")
    else:
        is_money = (mode == "Yes" and ranking_by != "Count") or (mode == "No" and analysis_type == "Sum")
        # render_chart_bytes is @st.cache_data-decorated, returning the
        # display PNG bytes at 100 DPI (~80-100ms cold, near-instant warm).
        # SVG and 300 DPI PNG are rendered LAZILY via callables passed to the
        # download buttons - only invoked when the user actually clicks the
        # respective button. This keeps the chart-update path very light: just
        # one ~80ms PNG render plus an O(1) byte copy from cache.
        png_display = render_chart_bytes(
            tuple(str(x) for x in l_chart),
            tuple(float(v) for v in v_chart),
            chart_title,
            (rank_mode == "Highest first"),
            "money" if is_money else "count",
        )
        st.image(png_display, use_container_width=True)

        with st.sidebar:
            st.markdown("---")
            st.header("5. Download")

            # Build the full data table (all ranks, plus Unknown row)
            if mode == "Yes":
                item_label = "Industry / Buzzword"
                value_label = (
                    amount_choice if (ranking_by != "Count" and amount_choice) else "Number of companies"
                )
                unknown_count = count_unknown_rows(df_active, mode="Yes", layout=layout)
            else:
                item_label = target_col
                if analysis_type == "Sum":
                    value_label = f"Sum of {sum_col}"
                else:
                    value_label = "Number of companies"
                unknown_count = count_unknown_rows(df_active, mode="No", target_col=target_col)

            combined_df = build_combined_csv_table(
                metric_series, final_series, unknown_count, item_label, value_label
            )
            csv_bytes = combined_df.to_csv(index=False).encode("utf-8")
            chart_exclusion_count = len(metric_series) - len(final_series)

            default_stem = safe_filename(chart_title)
            if st.session_state.get("_filename_last_default") != default_stem:
                st.session_state["_filename_stem"] = default_stem
                st.session_state["_filename_last_default"] = default_stem
            filename_stem = st.text_input(
                "Filename (no extension)",
                value=st.session_state.get("_filename_stem", default_stem),
                key="filename_stem_input",
                help="Used for all downloads below. Defaults to the chart title."
            )
            filename_stem = safe_filename(filename_stem, default=default_stem)
            st.session_state["_filename_stem"] = filename_stem

            # Lazy download callables - matplotlib only runs when the user
            # clicks. Captured into local tuples so the closures have stable
            # values rather than referring to mutating outer-scope variables.
            _chart_args = (
                tuple(str(x) for x in l_chart),
                tuple(float(x) for x in v_chart),
                chart_title,
                (rank_mode == "Highest first"),
                "money" if is_money else "count",
            )

            col_a, col_b, col_c = st.columns(3)
            col_a.download_button(
                "SVG (Adobe)",
                data=lambda a=_chart_args: _render_svg(*a),
                file_name=f"{filename_stem}.svg",
                mime="image/svg+xml",
            )
            col_b.download_button(
                "PNG (High Res)",
                data=lambda a=_chart_args: _render_hires_png(*a),
                file_name=f"{filename_stem}.png",
                mime="image/png",
            )
            col_c.download_button(
                "CSV (Data)",
                csv_bytes,
                f"{filename_stem}.csv",
                "text/csv",
                help="Side-by-side rankings: the left columns are the FULL ranking "
                     "(no chart exclusions); the right columns match the CHART (drops "
                     "anything in 'Exclude from chart', keeps every other item)."
            )

            if unknown_count > 0:
                st.caption(f"CSV includes an 'Unknown' row for {unknown_count:,} row{'s' if unknown_count != 1 else ''} with no value in this column.")
            if chart_exclusion_count > 0:
                st.caption(
                    f"Chart half of CSV omits {chart_exclusion_count} item{'s' if chart_exclusion_count != 1 else ''} "
                    f"from the 'Exclude from chart' list; Full half keeps them."
                )
else:
    st.info("Please upload a file to begin.")
