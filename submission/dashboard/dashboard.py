"""Dashboard historis penyewaan Capital Bikeshare."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from bike_metrics import BLOCKS, assign_blocks, rental_segments, weather_comparison


DATA = Path(__file__).resolve().parents[1] / "data"
DAY_TYPES = {0: "Nonkerja", 1: "Kerja"}
WEATHER = {1: "Cerah / sedikit awan", 2: "Kabut / berawan",
           3: "Hujan / salju ringan", 4: "Cuaca berat"}


@st.cache_data(max_entries=1)
def load_data():
    daily = pd.read_csv(DATA / "day.csv", parse_dates=["dteday"])
    hourly = pd.read_csv(DATA / "hour.csv", parse_dates=["dteday"])
    for frame in (daily, hourly):
        frame["Tipe hari"] = frame["workingday"].map(DAY_TYPES)
    daily["Cuaca"] = daily["weathersit"].map(WEATHER)
    hourly["Blok jam"] = assign_blocks(hourly["hr"])
    hourly["Hari lengkap"] = hourly.groupby("dteday")["hr"].transform("size").eq(24)
    return daily, hourly


def summarize(frame, keys):
    return frame.groupby(keys, observed=True, as_index=False).agg(
        rata_rata=("cnt", "mean"), observasi=("cnt", "size")
    )


def id_number(value, decimals=0):
    return f"{value:,.{decimals}f}".translate(str.maketrans(",.", ".,"))


st.set_page_config(page_title="Bike Sharing | Capital Bikeshare", page_icon="🚲", layout="wide")
st.title("Pola penyewaan Capital Bikeshare")
st.caption("Washington, DC · Januari 2011–Desember 2012")
daily, hourly = load_data()
first = daily["dteday"].min().date()
last = daily["dteday"].max().date()

st.sidebar.header("Filter data")
period = st.sidebar.date_input("Rentang tanggal", (first, last), min_value=first,
                               max_value=last, format="DD/MM/YYYY", key="period")
day_type = st.sidebar.selectbox("Tipe hari", ["Semua", "Kerja", "Nonkerja"], key="day_type")
st.sidebar.caption("Nonkerja mencakup akhir pekan dan hari libur.")
if len(period) != 2:
    st.info("Pilih tanggal awal dan akhir untuk melihat hasil.")
    st.stop()

start, end = map(pd.Timestamp, period)
daily = daily[daily["dteday"].between(start, end)]
if day_type != "Semua":
    daily = daily[daily["Tipe hari"].eq(day_type)]
hourly = hourly[hourly["dteday"].isin(daily["dteday"])]
if daily.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini.")
    st.stop()

st.write(f"**{start:%d/%m/%Y} – {end:%d/%m/%Y}** · {day_type}")
metrics = st.columns(4)
metrics[0].metric("Total penyewaan", id_number(daily["cnt"].sum()), border=True)
metrics[1].metric("Rata-rata per hari", id_number(daily["cnt"].mean(), 1), border=True)
metrics[2].metric("Hari terpilih", id_number(len(daily)), border=True)
metrics[3].metric("Porsi pengguna terdaftar",
                  id_number(100 * daily["registered"].sum() / daily["cnt"].sum(), 1) + "%", border=True)

trend_tab, hours_tab, weather_tab, bins_tab = st.tabs(
    ["Tren harian", "Jam puncak", "Cuaca harian", "Segmentasi jam"]
)
with trend_tab:
    st.subheader("Penyewaan harian menurut tipe pengguna")
    trend = daily.melt(id_vars="dteday", value_vars=["casual", "registered"],
                       var_name="Pengguna", value_name="Penyewaan")
    trend["Pengguna"] = trend["Pengguna"].map({"casual": "Kasual", "registered": "Terdaftar"})
    chart = alt.Chart(trend).mark_line(point=len(daily) <= 30).encode(
        x=alt.X("dteday:T", title="Tanggal"),
        y=alt.Y("Penyewaan:Q", title="Penyewaan per hari"),
        color="Pengguna:N",
        tooltip=[alt.Tooltip("dteday:T", title="Tanggal", format="%d/%m/%Y"),
                 "Pengguna:N", "Penyewaan:Q"],
    )
    st.altair_chart(chart, width="stretch")
    st.caption("Grafik menghubungkan tanggal yang termasuk dalam pilihan filter.")

with hours_tab:
    st.subheader("Jam prioritas redistribusi")
    complete_only = st.toggle("Tampilkan hanya hari dengan 24 slot", key="complete_only")
    hour_sample = hourly[hourly["Hari lengkap"]] if complete_only else hourly
    profile = summarize(hour_sample, ["Tipe hari", "hr"])
    if profile.empty:
        st.info("Tidak ada hari dengan 24 slot dalam rentang terpilih.")
    else:
        ranked = profile.sort_values(["rata_rata", "hr"], ascending=[False, True])
        top_hours = ranked.groupby("Tipe hari", sort=False).head(3)
        for label, rows in top_hours.groupby("Tipe hari"):
            times = ", ".join(f"{row.hr:02d}.00 ({id_number(row.rata_rata, 1)})"
                              for row in rows.itertuples())
            st.write(f"**{label}** · {times} sewa per slot tercatat")
        st.altair_chart(alt.Chart(profile).mark_line(point=True).encode(
            x=alt.X("hr:O", title="Jam lokal", sort=list(range(24))),
            y=alt.Y("rata_rata:Q", title="Rata-rata sewa per slot"),
            color="Tipe hari:N",
            tooltip=["Tipe hari:N", alt.Tooltip("hr:O", title="Jam"),
                     alt.Tooltip("rata_rata:Q", title="Rata-rata", format=".1f"),
                     alt.Tooltip("observasi:Q", title="Slot tercatat")],
        ), width="stretch")
    missing = 24 * len(daily) - len(hourly)
    st.caption(f"{id_number(missing)} dari {id_number(24 * len(daily))} slot tidak tercatat "
               "dalam pilihan ini. Rata-rata memakai slot dengan observasi.")

with weather_tab:
    st.subheader("Bagaimana volume berubah menurut kategori cuaca?")
    weather = summarize(daily, ["Cuaca"])
    st.altair_chart(alt.Chart(weather).mark_bar(cornerRadiusEnd=5, color="#008878").encode(
        y=alt.Y("Cuaca:N", title=None, sort=list(WEATHER.values())),
        x=alt.X("rata_rata:Q", title="Rata-rata sewa per hari"),
        tooltip=["Cuaca:N", alt.Tooltip("rata_rata:Q", title="Rata-rata", format=".1f"),
                 alt.Tooltip("observasi:Q", title="Jumlah hari")],
    ), width="stretch")
    st.dataframe(weather.rename(columns={"rata_rata": "Rata-rata sewa", "observasi": "Jumlah hari"}),
                 hide_index=True, column_config={"Rata-rata sewa": st.column_config.NumberColumn(format="%.1f")})
    st.subheader("Bandingkan dengan hari cerah yang sebanding")
    min_days = st.select_slider("Minimum hari per kategori dalam setiap kelompok",
                                options=[1, 3, 5], value=3, key="weather_min")
    comparison = weather_comparison(daily, min_days=min_days)
    st.caption("Kelompok dibentuk dari tahun, musim, dan tipe hari. Rata-rata ditimbang "
               "menurut jumlah hari kategori pembanding.")
    if comparison.empty or not daily["weathersit"].eq(1).any():
        st.info("Pilih rentang yang mencakup hari cerah dan kategori cuaca lain.")
    else:
        comparison["Cuaca"] = comparison["weathersit"].map(WEATHER)
        comparison["Cakupan"] = (comparison["hari_tercakup"].astype(str) + " dari "
                                  + comparison["hari_kategori"].astype(str) + " hari")
        comparison["Ambang tinjau terpenuhi"] = (comparison["selisih_sebanding_pct"].le(-20)
                                                   & comparison["cakupan_pct"].ge(70))
        st.dataframe(comparison[["Cuaca", "selisih_mentah_pct", "selisih_sebanding_pct",
                                 "kelompok", "Cakupan", "Ambang tinjau terpenuhi"]],
                     hide_index=True,
                     column_config={
                         "selisih_mentah_pct": st.column_config.NumberColumn("Mentah (%)", format="%.1f"),
                         "selisih_sebanding_pct": st.column_config.NumberColumn("Sebanding (%)", format="%.1f"),
                         "kelompok": "Kelompok sebanding",
                     })
        st.caption("Selisih sebanding kosong jika tidak ada kelompok yang memenuhi syarat. "
                   "Ambang tinjau ilustratif: penurunan ≥20% dengan cakupan ≥70%.")

with bins_tab:
    st.subheader("Penyewaan dan peluang promosi per blok jam")
    segment_labels = {"Semua penyewaan": "rata_rata", "Penyewaan kasual": "kasual_per_slot"}
    selected_metric = st.radio("Metrik grafik", list(segment_labels), horizontal=True, key="segment_metric")
    segment_metric = segment_labels[selected_metric]
    segments = rental_segments(hourly, ["Blok jam", "Tipe hari"]).reset_index()
    st.altair_chart(alt.Chart(segments).mark_bar().encode(
        x=alt.X("Blok jam:O", sort=BLOCKS, title="Blok jam lokal"),
        xOffset="Tipe hari:N",
        y=alt.Y(segment_metric + ":Q", title="Rata-rata sewa per slot"),
        color="Tipe hari:N",
        tooltip=["Blok jam:O", "Tipe hari:N",
                 alt.Tooltip(segment_metric + ":Q", title="Rata-rata", format=".1f"),
                 alt.Tooltip("porsi_kasual_pct:Q", title="Porsi kasual (%)", format=".1f"),
                 alt.Tooltip("slot:Q", title="Slot tercatat")],
    ), width="stretch")
    st.dataframe(segments[["Blok jam", "Tipe hari", "rata_rata", "kasual_per_slot", "porsi_kasual_pct", "slot"]],
                 hide_index=True, column_config={
                     "rata_rata": st.column_config.NumberColumn("Sewa per slot", format="%.1f"),
                     "kasual_per_slot": st.column_config.NumberColumn("Kasual per slot", format="%.1f"),
                     "porsi_kasual_pct": st.column_config.NumberColumn("Porsi kasual (%)", format="%.1f"),
                     "slot": "Slot tercatat",
                 })
    st.caption("Panjang blok berbeda. Perbandingan memakai rata-rata per slot tercatat.")

st.divider()
st.caption("Sumber · [Bike Sharing Dataset, UCI](https://doi.org/10.24432/C5W894)")
