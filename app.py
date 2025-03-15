import streamlit as st
import pandas as pd
import altair as alt


# Set page config
def make_donut(input_response, input_text, input_color):
    if input_color == "blue":
        chart_color = ["#29b5e8", "#155F7A"]
    if input_color == "green":
        chart_color = ["#27AE60", "#12783D"]
    if input_color == "orange":
        chart_color = ["#F39C12", "#875A12"]
    if input_color == "red":
        chart_color = ["#E74C3C", "#781F16"]

    source = pd.DataFrame(
        {"Topic": ["", input_text], "% value": [100 - input_response, input_response]}
    )
    source_bg = pd.DataFrame({"Topic": ["", input_text], "% value": [100, 0]})

    plot = (
        alt.Chart(source)
        .mark_arc(innerRadius=45, cornerRadius=25)
        .encode(
            theta="% value",
            color=alt.Color(
                "Topic:N",
                scale=alt.Scale(
                    # domain=['A', 'B'],
                    domain=[input_text, ""],
                    # range=['#29b5e8', '#155F7A']),  # 31333F
                    range=chart_color,
                ),
                legend=None,
            ),
        )
        .properties(width=130, height=130)
    )

    text = plot.mark_text(
        align="center",
        color="#29b5e8",
        font="Lato",
        fontSize=32,
        fontWeight=700,
        fontStyle="italic",
    ).encode(text=alt.value(f"{input_response} %"))
    plot_bg = (
        alt.Chart(source_bg)
        .mark_arc(innerRadius=45, cornerRadius=20)
        .encode(
            theta="% value",
            color=alt.Color(
                "Topic:N",
                scale=alt.Scale(
                    # domain=['A', 'B'],
                    domain=[input_text, ""],
                    range=chart_color,
                ),  # 31333F
                legend=None,
            ),
        )
        .properties(width=130, height=130)
    )
    return plot_bg + plot + text


def format_number(num):
    if num > 1000000:
        if not num % 1000000:
            return f"{num // 1000000} M"
        return f"{round(num / 1000000, 1)} M"
    return f"{num // 1000} K"


def make_heatmap(input_df, input_y, input_x, input_color, input_color_theme):
    heatmap = (
        alt.Chart(input_df)
        .mark_rect()
        .encode(
            y=alt.Y(
                f"{input_y}:O",
                axis=alt.Axis(
                    title="Year",
                    titleFontSize=18,
                    titlePadding=15,
                    titleFontWeight=900,
                    labelAngle=0,
                ),
            ),
            x=alt.X(
                f"{input_x}:O",
                axis=alt.Axis(
                    title="", titleFontSize=18, titlePadding=15, titleFontWeight=900
                ),
            ),
            color=alt.Color(
                f"max({input_color}):Q",
                legend=None,
                scale=alt.Scale(scheme=input_color_theme),
            ),
            stroke=alt.value("black"),
            strokeWidth=alt.value(0.25),
        )
        .properties(width=900)
        .configure_axis(labelFontSize=12, titleFontSize=12)
    )
    # height=300
    return heatmap


st.set_page_config(page_title="Streamlit YouTube Channel Dashboard", layout="wide")


@st.cache_data
def load_data():
    data = pd.read_csv("data/youtube_channel_data.csv")
    data["DATE"] = pd.to_datetime(data["DATE"])
    data["NET_SUBSCRIBERS"] = data["SUBSCRIBERS_GAINED"] - data["SUBSCRIBERS_LOST"]
    return data


def format_with_commas(number):
    return f"{number:,}"


def create_metric_chart(df, column, color, height=150):
    chart_df = df[["DATE", column]].set_index("DATE")
    return st.area_chart(chart_df, color=color, height=height)


def display_metric(col, title, value, df, column, color):
    with col:
        with st.container(border=True):
            st.metric(title, format_with_commas(value))
            create_metric_chart(df, column, color)


# Load data
df = load_data()
df_cumulative = df.copy()

alt.themes.enable("dark")

for column in ["NET_SUBSCRIBERS", "VIEWS", "WATCH_HOURS", "LIKES"]:
    df_cumulative[column] = df_cumulative[column].cumsum()

total_subscriber = df_cumulative["TOTAL_SUBSCRIBERS"].values[-1]
total_views = df_cumulative["VIEWS"].values[-1]

ratio_paid = (
    df_cumulative["type"].value_counts(normalize=True).loc["paid"].round(3) * 100
)
ratio_organic = (
    df_cumulative["type"].value_counts(normalize=True).loc["organic"].round(3) * 100
)
# Set up the dashboard
st.title("Streamlit YouTube Channel Dashboard")

logo_icon = "images/streamlit-mark-color.png"
logo_image = "images/streamlit-logo-primary-colormark-lighttext.png"
st.logo(icon_image=logo_icon, image=logo_image)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    start_date = st.date_input("Start date", df["DATE"].min())
    end_date = st.date_input("End date", df["DATE"].max())
    time_frame = st.selectbox("Select time frame", ("Daily", "Cumulative"))

# Key Metrics
st.subheader("Key Metrics")
st.caption("All-Time Statistics")

metrics = [
    ("Total Subscribers", "NET_SUBSCRIBERS", "#29b5e8"),
    ("Total Views", "VIEWS", "#FF9F36"),
    ("Total Watch Hours", "WATCH_HOURS", "#D45B90"),
    ("Total Likes", "LIKES", "#7D44CF"),
]
col = st.columns((2, 6), gap="medium")

with col[0]:
    st.markdown("#### Gains/Losses")
    st.metric(label="Total_views", value=total_subscriber, delta="", border=True)
    st.metric(label="Total Subscribers", value=total_views, delta="", border=True)

    st.markdown("#### Organic vs Paid")

    migrations_col = st.columns((0.2, 1, 0.2))

    donut_chart_greater = make_donut(ratio_paid, "Organic", "green")
    donut_chart_less = make_donut(ratio_organic, "Paid", "blue")
    with migrations_col[1]:
        st.write("Organic")
        st.altair_chart(donut_chart_greater)
        st.write("Paid")
        st.altair_chart(donut_chart_less)

with col[1]:
    cols = st.columns(2)
    # Selected Duration Metrics
    st.caption("Selected Duration")
    df_filtered = df_cumulative if time_frame == "Cumulative" else df
    mask = (df_filtered["DATE"].dt.date >= start_date) & (
        df_filtered["DATE"].dt.date <= end_date
    )
    df_filtered = df_filtered.loc[mask]

    for col, (title, column, color) in zip(cols, metrics[2:]):
        display_metric(
            col,
            title,
            df_filtered[column].sum(),
            df_cumulative if time_frame == "Cumulative" else df,
            column,
            color,
        )

    cols = st.columns(2)
    for col, (title, column, color) in zip(cols, metrics):
        display_metric(
            col,
            title.split()[-1],
            df_filtered[column].sum(),
            df_filtered,
            column,
            color,
        )

    # DataFrame display
    with st.expander("See DataFrame"):
        st.dataframe(df)
