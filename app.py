import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px 

st.set_page_config(page_title="StatLab | Dashboard Statistik", page_icon="📊", layout="wide")

# ---------- Style ----------
st.markdown("""
<style>
    .stApp { background: #0b1120; color: #e5e7eb; }
    [data-testid="stSidebar"] { background: #111827; }
    .block-container { padding-top: 1.7rem; padding-bottom: 2rem; }
    .hero { padding: 1.25rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#172554,#111827 65%,#164e63); border: 1px solid #263449; margin-bottom: 1rem; }
    .hero h1 { margin: 0; color: #f8fafc; }
    .hero p { color: #bfdbfe; margin: .35rem 0 0 0; }
    div[data-testid="stMetric"] { background: #111827; border: 1px solid #273449; padding: 14px; border-radius: 14px; }
    .note { color: #94a3b8; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>📊 StatLab — Dashboard Statistik Deskriptif</h1>
  <p>Jelajahi data, atur tampilan grafik dengan slider, dan pahami pola data secara interaktif.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Sample data ----------
def sample_data():
    rng = np.random.default_rng(42)
    rows = []
    for g in range(1, 11):
        values = rng.normal(loc=70 + (g-5)*1.5, scale=4 + (g % 4), size=10)
        for i, value in enumerate(values, start=1):
            rows.append({"Kelompok": f"Kelompok {g}", "Orang": f"Orang {i}", "Nilai": round(float(value), 2)})
    return pd.DataFrame(rows)

with st.sidebar:
    st.header("⚙️ Pengaturan")
    uploaded = st.file_uploader("Unggah data CSV (opsional)", type=["csv"])
    st.caption("CSV sebaiknya memiliki kolom kategori/kelompok dan satu kolom angka.")
    st.divider()
    st.subheader("Tampilan grafik")
   
chart_type = st.selectbox(
    "Jenis grafik",
    [
        "Batang",
        "Garis",
        "Area",
        "Lingkaran",
        "Box Plot",
        "Histogram",
        "Heatmap"
    ]
)

    position = st.slider("Posisi vertikal grafik", min_value=-30, max_value=30, value=0, step=1,
                         help="Menggeser tampilan grafik secara visual; tidak mengubah nilai data asli.")
    scale_pct = st.slider("Skala vertikal (%)", min_value=50, max_value=200, value=100, step=10,
                          help="Mengatur rentang sumbu Y untuk melihat perbedaan data lebih jelas.")
    st.divider()
    st.caption("StatLab • Dashboard pembelajaran")

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded, sep=None, engine="python")
        if df.empty:
            st.error("File CSV kosong. Silakan unggah file yang berisi data.")
            st.stop()
    except Exception as e:
        st.error(f"CSV belum bisa dibaca: {e}")
        st.info("Coba simpan file sebagai CSV UTF-8, lalu unggah kembali.")
        st.stop()
else:
    df = sample_data()
    st.info("Kamu sedang melihat **data contoh** (100 nilai dari 10 kelompok). Unggah CSV milikmu melalui sidebar untuk menggantinya.")

# Identify numeric and category columns
numeric_cols = df.select_dtypes(include="number").columns.tolist()
if not numeric_cols:
    # Try converting columns to numbers (useful for CSV numbers stored as text)
    for col in df.columns:
        converted = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=False), errors="coerce")
        if converted.notna().sum() > 0:
            df[col] = converted
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

if not numeric_cols:
    st.error("Tidak ditemukan kolom angka. Pastikan CSV memiliki setidaknya satu kolom numerik.")
    st.stop()

with st.sidebar:
    value_col = st.selectbox("Kolom nilai angka", numeric_cols, index=0)
    other_cols = [c for c in df.columns if c != value_col]
    
# Pilih kolom kelompok secara otomatis jika tersedia
category_options = ["(nomor baris)"] + other_cols

default_category = "(nomor baris)"
for col in other_cols:
    nama = str(col).strip().lower()
    if nama in ["kelompok", "kategori", "group", "grup"]:
        default_category = col
        break

default_index = category_options.index(default_category)
category_col = st.selectbox(
    "Kolom kelompok/kategori",
    category_options,
    index=default_index
)

work = df.copy()
work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
work = work.dropna(subset=[value_col])
if work.empty:
    st.error("Kolom angka tidak memiliki nilai valid setelah dibersihkan.")
    st.stop()

if category_col == "(nomor baris)":
    work["_Kategori"] = [f"Data {i+1}" for i in range(len(work))]
    cat = "_Kategori"
else:
    work[category_col] = work[category_col].fillna("Tidak diketahui").astype(str)
    cat = category_col

# Summary metrics
values = work[value_col]
mean = values.mean()
median = values.median()
std = values.std(ddof=1) if len(values) > 1 else 0
minimum = values.min()
maximum = values.max()

st.subheader("Ringkasan data")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Jumlah data", f"{len(values):,}")
m2.metric("Rata-rata", f"{mean:.2f}")
m3.metric("Median", f"{median:.2f}")
m4.metric("Standar deviasi", f"{std:.2f}")
m5.metric("Rentang nilai", f"{maximum-minimum:.2f}")

st.divider()

# Group aggregation for charts

grouped = work.groupby(cat, dropna=False)[value_col].agg(
    ["mean", "sum", "count", "std"]
).reset_index()

grouped["std"] = grouped["std"].fillna(0)
grouped = grouped.rename(columns={
    "mean": "Rata-rata",
    "sum": "Total",
    "count": "Jumlah",
    "std": "Standar deviasi"
})

# Urutkan Kelompok 1, Kelompok 2, ..., Kelompok 10
import re

def urutan_kelompok(nilai):
    teks = str(nilai)
    angka = re.search(r"\d+", teks)
    if angka:
        return (0, int(angka.group()))
    return (1, teks.lower())

grouped["_urutan"] = grouped[cat].map(urutan_kelompok)
grouped = grouped.sort_values("_urutan", kind="stable").drop(
    columns="_urutan"
).reset_index(drop=True)

grouped["Tampilan"] = grouped["Rata-rata"] + position


# slider scale around current visible data range
visible_min = float(grouped["Tampilan"].min())
visible_max = float(grouped["Tampilan"].max())
center = (visible_min + visible_max) / 2
half_range = max((visible_max - visible_min) / 2, 1.0) * (scale_pct / 100)
y_min, y_max = center - half_range, center + half_range
if y_min == y_max:
    y_min -= 1
    y_max += 1

left, right = st.columns([1.65, 1])
with left:
    st.subheader("Visualisasi interaktif")
   
    if chart_type == "Batang":
        fig = px.bar(
            grouped, x=cat, y="Tampilan",
            hover_data=["Rata-rata", "Jumlah", "Standar deviasi"],
            labels={"Tampilan": f"Rata-rata {value_col} (tampilan)", cat: "Kelompok"},
            color="Rata-rata", color_continuous_scale="blues"
        )
        fig.update_yaxes(range=[y_min, y_max])

    elif chart_type == "Garis":
        fig = px.line(
            grouped, x=cat, y="Tampilan", markers=True,
            hover_data=["Rata-rata", "Jumlah", "Standar deviasi"],
            labels={"Tampilan": f"Rata-rata {value_col} (tampilan)", cat: "Kelompok"}
        )
        fig.update_yaxes(range=[y_min, y_max])

    elif chart_type == "Area":
        fig = px.area(
            grouped, x=cat, y="Tampilan", markers=True,
            hover_data=["Rata-rata", "Jumlah", "Standar deviasi"],
            labels={"Tampilan": f"Rata-rata {value_col} (tampilan)", cat: "Kelompok"}
        )
        fig.update_yaxes(range=[y_min, y_max])

    elif chart_type == "Lingkaran":
        pie_df = grouped.copy()
        pie_df["Bagian"] = pie_df["Rata-rata"].clip(lower=0)
        if pie_df["Bagian"].sum() <= 0:
            pie_df["Bagian"] = pie_df["Jumlah"]

        fig = px.pie(
            pie_df, names=cat, values="Bagian", hole=0.45,
            hover_data=["Rata-rata", "Jumlah"],
            title="Proporsi rata-rata tiap kelompok"
        )

    elif chart_type == "Box Plot":
        fig = px.box(
            work, x=cat, y=value_col, points="all",
            color=cat,
            labels={cat: "Kelompok", value_col: "Nilai"},
            title="Sebaran Nilai Setiap Kelompok"
        )

    elif chart_type == "Histogram":
        fig = px.histogram(
            work, x=value_col, color=cat,
            barmode="overlay", opacity=0.75,
            labels={value_col: "Nilai"},
            title="Distribusi Nilai"
        )

    elif chart_type == "Heatmap":
        heat_df = grouped.set_index(cat)[
            ["Rata-rata", "Standar deviasi", "Jumlah"]
        ].copy()

        # Normalisasi setiap kolom agar skala berbeda
        # tidak mendominasi warna heatmap.
        heat_norm = heat_df.copy()
        for col in heat_norm.columns:
            min_val = heat_norm[col].min()
            max_val = heat_norm[col].max()
            if max_val != min_val:
                heat_norm[col] = (
                    (heat_norm[col] - min_val) / (max_val - min_val)
                )
            else:
                heat_norm[col] = 0.5

        fig = px.imshow(
            heat_norm.T,
            x=heat_norm.index.astype(str),
            y=heat_norm.columns,
            color_continuous_scale="Blues",
            aspect="auto",
            labels={
                "x": "Kelompok",
                "y": "Statistik",
                "color": "Skor relatif"
            },
            title="Heatmap Perbandingan Statistik"
        )
        fig.update_xaxes(side="bottom")

    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=45, b=10), height=420,
        font=dict(color="#e5e7eb"), coloraxis_colorbar_title="Rata-rata"
    )
    st.plotly_chart(fig, use_container_width=True)
    if chart_type != "Lingkaran":
        st.caption(f"Posisi visual: {position:+d} • Skala sumbu Y: {scale_pct}% — data asli tidak diubah.")

with right:
    st.subheader("Statistik per kelompok")
    display = grouped[[cat, "Jumlah", "Rata-rata", "Standar deviasi"]].copy()
    display["Rata-rata"] = display["Rata-rata"].round(2)
    display["Standar deviasi"] = display["Standar deviasi"].round(2)
    st.dataframe(display, use_container_width=True, hide_index=True, height=420)

st.divider()
st.subheader("Tabel data")
st.dataframe(work.drop(columns=["_Kategori"], errors="ignore"), use_container_width=True, hide_index=True)
csv_out = work.drop(columns=["_Kategori"], errors="ignore").to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Unduh data yang digunakan (CSV)", data=csv_out, file_name="data_dashboard.csv", mime="text/csv")


st.divider()
st.subheader("Analisis Variasi Antar Kelompok")

# Cari kelompok dengan variasi terkecil dan terbesar
most_consistent = grouped.loc[grouped["Standar deviasi"].idxmin()]
most_variable = grouped.loc[grouped["Standar deviasi"].idxmax()]
highest = grouped.loc[grouped["Rata-rata"].idxmax()]
lowest = grouped.loc[grouped["Rata-rata"].idxmin()]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Paling konsisten",
        str(most_consistent[cat]),
        f"SD: {most_consistent['Standar deviasi']:.2f}"
    )

with col2:
    st.metric(
        "Paling bervariasi",
        str(most_variable[cat]),
        f"SD: {most_variable['Standar deviasi']:.2f}"
    )

with col3:
    st.metric(
        "Rata-rata tertinggi",
        str(highest[cat]),
        f"{highest['Rata-rata']:.2f}"
    )

st.subheader("Grafik Standar Deviasi")

fig_sd = px.bar(
    grouped,
    x=cat,
    y="Standar deviasi",
    color="Standar deviasi",
    color_continuous_scale="blues",
    text="Standar deviasi",
    labels={
        cat: "Kelompok",
        "Standar deviasi": "Standar deviasi"
    }
)

fig_sd.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig_sd.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e5e7eb"),
    height=420,
    coloraxis_showscale=False
)

st.plotly_chart(fig_sd, use_container_width=True)

st.subheader("Kesimpulan Otomatis")

st.write(
    f"Rata-rata keseluruhan nilai adalah **{mean:.2f}**, "
    f"dengan median **{median:.2f}** dan standar deviasi keseluruhan "
    f"**{std:.2f}**."
)

st.write(
    f"Kelompok dengan rata-rata tertinggi adalah **{highest[cat]}** "
    f"({highest['Rata-rata']:.2f}), sedangkan rata-rata terendah "
    f"adalah **{lowest[cat]}** ({lowest['Rata-rata']:.2f})."
)

st.write(
    f"Kelompok paling konsisten adalah **{most_consistent[cat]}**, "
    f"dengan standar deviasi **{most_consistent['Standar deviasi']:.2f}**."
)

st.write(
    f"Kelompok dengan variasi nilai terbesar adalah **{most_variable[cat]}**, "
    f"dengan standar deviasi **{most_variable['Standar deviasi']:.2f}**."
)

st.caption(
    "Interpretasi: standar deviasi yang kecil menunjukkan nilai lebih "
    "berdekatan dengan rata-rata kelompok. Standar deviasi yang besar "
    "menunjukkan penyebaran nilai yang lebih lebar."
)
