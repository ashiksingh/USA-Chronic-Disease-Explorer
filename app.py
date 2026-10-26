import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

st.set_page_config(
    page_title="USA Chronic Disease Explorer",
    page_icon="🏥",
    layout="wide"
)

px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = [
    "#1565C0", "#D84315", "#2E7D32", "#6A1B9A", "#00838F"
]

st.markdown("""
<style>
.stApp { background-color: #F5F7FB; color: #111827; }
.block-container { padding-top: 1.5rem; }
h1, h2, h3, p, label { color: #111827 !important; }
div[data-testid="stMetric"] {
    background-color: white; padding: 16px; border-radius: 12px;
    border: 1px solid #D1D5DB;
}
div[data-testid="stMetricLabel"] { color: #374151 !important; font-weight: 700 !important; }
div[data-testid="stMetricValue"] { color: #111827 !important; font-weight: 800 !important; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def connect_db():
    client = MongoClient(
        "mongodb://127.0.0.1:27017",
        serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")
    return client["chronicDiseaseDB"]["disease_records"]


try:
    collection = connect_db()
except Exception:
    st.error("MongoDB connection failed. Please make sure MongoDB Server is running.")
    st.stop()


@st.cache_data(ttl=300)
def get_filter_values(field):
    values = collection.distinct(field)
    return sorted(
        [v for v in values if v is not None and str(v).strip()],
        key=lambda value: str(value)
    )


@st.cache_data(ttl=300)
def get_group_values(category):
    if category == "All categories":
        return []
    values = collection.distinct(
        "Stratification1",
        {"StratificationCategory1": category}
    )
    return sorted(
        [v for v in values if v is not None and str(v).strip()],
        key=lambda value: str(value)
    )


def parse_numeric(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


st.title("USA Chronic Disease Explorer")
st.write(
    "Search and explore U.S. chronic disease indicators by health topic, "
    "location, year, measure, and population group."
)

topics = get_filter_values("Topic")
locations = get_filter_values("LocationDesc")
location_abbrs = get_filter_values("LocationAbbr")
data_sources = get_filter_values("DataSource")
questions = get_filter_values("Question")
value_types = get_filter_values("DataValueType")
value_units = get_filter_values("DataValueUnit")
categories = get_filter_values("StratificationCategory1")
years_raw = get_filter_values("YearStart")
end_years_raw = get_filter_values("YearEnd")

years = sorted(
    {int(float(y)) for y in years_raw if parse_numeric(y) is not None}
)
end_years = sorted(
    {int(float(y)) for y in end_years_raw if parse_numeric(y) is not None}
)

st.sidebar.title("Search & Filters")
st.sidebar.caption("Choose any combination of filters.")

selected_topic = st.sidebar.selectbox("Health Topic", ["All Topics"] + topics)
selected_location = st.sidebar.selectbox("State / Location", ["All Locations"] + locations)
selected_abbr = st.sidebar.selectbox("Location Abbreviation", ["All Abbreviations"] + location_abbrs)
selected_source = st.sidebar.selectbox("Data Source", ["All Sources"] + data_sources)

if years:
    selected_year_range = st.sidebar.slider(
        "YearStart range",
        min_value=min(years),
        max_value=max(years),
        value=(min(years), max(years)),
        step=1
    )
else:
    selected_year_range = None

if end_years:
    selected_end_year_range = st.sidebar.slider(
        "YearEnd range",
        min_value=min(end_years),
        max_value=max(end_years),
        value=(min(end_years), max(end_years)),
        step=1
    )
else:
    selected_end_year_range = None

selected_category = st.sidebar.selectbox(
    "Population Group Category",
    ["All categories"] + categories
)

if selected_category != "All categories":
    group_values = get_group_values(selected_category)
    selected_group = st.sidebar.selectbox(
        "Population Group",
        ["All groups"] + group_values
    )
else:
    selected_group = "All groups"

selected_value_type = st.sidebar.selectbox(
    "Data Value Type",
    ["All types"] + value_types
)
selected_value_unit = st.sidebar.selectbox(
    "Data Value Unit",
    ["All units"] + value_units
)

search_text = st.sidebar.text_input(
    "Search Health Question",
    placeholder="e.g. diabetes, cancer, asthma"
)
search_value = st.sidebar.text_input(
    "Search Data Value (optional)",
    placeholder="e.g. 2.9 or 9537"
)

confidence_min = st.sidebar.number_input(
    "Minimum Low Confidence Limit",
    value=0.0,
    step=0.1,
    help="Applied only to records with a numeric LowConfidenceLimit."
)
confidence_max = st.sidebar.number_input(
    "Maximum High Confidence Limit",
    value=1000000000.0,
    min_value=0.0,
    step=1.0,
    help="Applied only to records with a numeric HighConfidenceLimit."
)
use_confidence_filter = st.sidebar.checkbox(
    "Apply confidence limit filters",
    value=False
)

query = {}

if selected_topic != "All Topics":
    query["Topic"] = selected_topic
if selected_location != "All Locations":
    query["LocationDesc"] = selected_location
if selected_abbr != "All Abbreviations":
    query["LocationAbbr"] = selected_abbr
if selected_source != "All Sources":
    query["DataSource"] = selected_source

if selected_year_range is not None:
    query["YearStart"] = {
        "$gte": int(selected_year_range[0]),
        "$lte": int(selected_year_range[1])
    }
if selected_end_year_range is not None:
    query["YearEnd"] = {
        "$gte": int(selected_end_year_range[0]),
        "$lte": int(selected_end_year_range[1])
    }

if selected_category != "All categories":
    query["StratificationCategory1"] = selected_category
if selected_group != "All groups":
    query["Stratification1"] = selected_group
if selected_value_type != "All types":
    query["DataValueType"] = selected_value_type
if selected_value_unit != "All units":
    query["DataValueUnit"] = selected_value_unit

if search_text.strip():
    query["Question"] = {"$regex": search_text.strip(), "$options": "i"}

if search_value.strip():
    numeric_value = parse_numeric(search_value)
    if numeric_value is not None:
        query["DataValue"] = numeric_value
    else:
        query["DataValue"] = {"$regex": search_value.strip(), "$options": "i"}

if use_confidence_filter:
    query["LowConfidenceLimit"] = {
        "$exists": True,
        "$ne": None,
        "$gte": confidence_min
    }
    query["HighConfidenceLimit"] = {
        "$exists": True,
        "$ne": None,
        "$lte": confidence_max
    }

total_records = collection.count_documents(query)
topic_count = len(collection.distinct("Topic", query))
location_count = len(collection.distinct("LocationDesc", query))

st.subheader("Dataset Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Matching Records", f"{total_records:,}")
col2.metric("Health Topics", f"{topic_count:,}")
col3.metric("Locations", f"{location_count:,}")
st.caption("Filters apply to the charts and records below. Record counts are dataset entries, not people.")
st.divider()

if total_records == 0:
    st.warning("No matching records found. Change or reset the filters in the sidebar.")
    if st.button("Clear cached filter values"):
        st.cache_data.clear()
        st.rerun()
    st.stop()


def style_chart(fig, height=430):
    fig.update_layout(
        template="plotly_white",
        height=height,
        font=dict(family="Arial", size=14, color="#111827"),
        title_font=dict(family="Arial", size=21, color="#111827"),
        legend=dict(font=dict(size=13, color="#111827")),
        margin=dict(l=20, r=20, t=75, b=45),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis=dict(
            title_font=dict(size=14, color="#111827"),
            tickfont=dict(size=12, color="#111827"),
            gridcolor="#D1D5DB",
            linecolor="#6B7280",
            showline=True
        ),
        yaxis=dict(
            title_font=dict(size=14, color="#111827"),
            tickfont=dict(size=12, color="#111827"),
            gridcolor="#D1D5DB",
            linecolor="#6B7280",
            showline=True
        )
    )
    return fig


st.subheader("Records by YearStart")
year_pipeline = [
    {"$match": query},
    {"$group": {"_id": "$YearStart", "Records": {"$sum": 1}}},
    {"$sort": {"_id": 1}}
]
year_results = list(collection.aggregate(year_pipeline))

if year_results:
    year_df = pd.DataFrame([
        {"Year": str(item["_id"]), "Records": item["Records"]}
        for item in year_results
    ])
    fig_year = px.bar(
        year_df, x="Year", y="Records", text="Records",
        title="Dataset Records by Starting Year",
        color_discrete_sequence=["#1565C0"]
    )
    fig_year.update_traces(
        texttemplate="%{text:,}", textposition="outside",
        textfont=dict(size=12, color="#111827")
    )
    st.plotly_chart(style_chart(fig_year, 420), width="stretch")


left, right = st.columns(2)

with left:
    st.subheader("Health Topic Distribution")
    topic_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$Topic", "Records": {"$sum": 1}}},
        {"$sort": {"Records": -1}},
        {"$limit": 10}
    ]
    topic_results = list(collection.aggregate(topic_pipeline))
    if topic_results:
        topic_df = pd.DataFrame([
            {"Topic": item["_id"] or "Not specified", "Records": item["Records"]}
            for item in topic_results
        ])
        fig_topic = px.bar(
            topic_df, x="Records", y="Topic", orientation="h",
            title="Top 10 Topics by Record Count", text="Records",
            color_discrete_sequence=["#00838F"]
        )
        fig_topic.update_traces(textposition="outside")
        fig_topic.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(style_chart(fig_topic, 500), width="stretch")

with right:
    st.subheader("Location Distribution")
    location_pipeline = [
        {"$match": query},
        {"$group": {"_id": "$LocationDesc", "Records": {"$sum": 1}}},
        {"$sort": {"Records": -1}},
        {"$limit": 10}
    ]
    location_results = list(collection.aggregate(location_pipeline))
    if location_results:
        location_df = pd.DataFrame([
            {"Location": item["_id"] or "Not specified", "Records": item["Records"]}
            for item in location_results
        ])
        fig_location = px.bar(
            location_df, x="Records", y="Location", orientation="h",
            title="Top 10 Locations by Record Count", text="Records",
            color_discrete_sequence=["#D84315"]
        )
        fig_location.update_traces(textposition="outside")
        fig_location.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(style_chart(fig_location, 500), width="stretch")


st.divider()
st.subheader("Data Value Types and Units")
value_pipeline = [
    {"$match": query},
    {
        "$group": {
            "_id": {"type": "$DataValueType", "unit": "$DataValueUnit"},
            "Records": {"$sum": 1}
        }
    },
    {"$sort": {"Records": -1}},
    {"$limit": 15}
]
value_results = list(collection.aggregate(value_pipeline))
if value_results:
    value_df = pd.DataFrame([
        {
            "Data Value Type": item["_id"].get("type") or "Not specified",
            "Unit": item["_id"].get("unit") or "Not specified",
            "Records": item["Records"]
        }
        for item in value_results
    ])
    st.dataframe(value_df, width="stretch", hide_index=True)


st.divider()
st.subheader("Explore Individual Health Records")
st.caption(
    "DataValue and confidence limits are shown as stored in the source. "
    "Values with different units or measure types should not be directly compared."
)

page_size = st.selectbox("Records per page", [10, 25, 50, 100], index=0)
total_pages = max(1, (total_records + page_size - 1) // page_size)
page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
skip = (page - 1) * page_size

records = list(
    collection.find(
        query,
        {
            "_id": 0,
            "YearStart": 1,
            "YearEnd": 1,
            "LocationAbbr": 1,
            "LocationDesc": 1,
            "DataSource": 1,
            "Topic": 1,
            "Question": 1,
            "DataValue": 1,
            "DataValueAlt": 1,
            "DataValueType": 1,
            "DataValueUnit": 1,
            "LowConfidenceLimit": 1,
            "HighConfidenceLimit": 1,
            "StratificationCategory1": 1,
            "Stratification1": 1,
            "StratificationCategory2": 1,
            "Stratification2": 1,
            "StratificationCategory3": 1,
            "Stratification3": 1
        }
    )
    .sort([("YearStart", 1), ("LocationDesc", 1)])
    .skip(skip)
    .limit(page_size)
)

if records:
    records_df = pd.DataFrame(records)
    st.dataframe(records_df, width="stretch", hide_index=True)
    csv_data = records_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Download Current Page as CSV",
        data=csv_data,
        file_name="chronic_disease_records.csv",
        mime="text/csv"
    )

st.caption("Source: U.S. Chronic Disease Indicators dataset.")
