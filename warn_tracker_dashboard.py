import streamlit as st
import pandas as pd
import numpy as np
# import datetime
import plotly.express as px
import us

# --- Page Configuration ---
# Set page config
st.set_page_config(page_title='WARN Act Tracker', layout='wide', page_icon='favicon.ico')
st.logo('https://wwwrise.org/images/branding/WWW-logo-horizontal.svg', link='https://wwwrise.org')
# st.image('https://wwwrise.org/favicon.ico')

st.title('WARN Act Layoff Tracker')
st.markdown('This is a project of [What We Will](https://wwwrise.org) to track [WARN Act](https://www.ecfr.gov/current/title-20/chapter-V/part-639) filings across the US. \
            Data is sourced from the [WARN Scraper](https://github.com/biglocalnews/warn-scraper), which collects data from state labor department websites. \
            The dashboard allows users to explore WARN Act filings, filter by various criteria, and visualize trends over time. \
            *Note that not all states make WARN Act filings public, and not all state scrapers are fully implemented.*')

# @st.cache_data # Cache the data loading for performance
def load_data():
    # df = pd.read_csv("/Users/joshuadsr/.warn-scraper/cache/az_raw.csv") # Example of loading real data
    # df = pd.read_csv("/Users/joshuadsr/.warn-scraper/exports/wi.csv", sep=',')
    column_order = ['company', 'jobs', 'notice_date', 'effective_date', 'postal_code', 'location']
    # df = pd.read_csv("integrated.csv", usecols=column_order)[column_order] # .head(5000) # dtype=str,
    df = pd.read_parquet('data/integrated.parquet').head(7500) # , usecols=column_order)[column_order]
    df['notice_date'] = pd.to_datetime(df['notice_date'], errors='coerce')
    df['effective_date'] = pd.to_datetime(df['effective_date'], errors='coerce')
    df['date'] = df[['notice_date', 'effective_date']].min(axis=1)
    return df

df = load_data()

# 2. Add an interactive widget (slider) for filtering
st.sidebar.header('Filter data')

# 1. State Filter
selected_states = st.sidebar.multiselect(
    "States",
    options=sorted(df["postal_code"].unique()),
    default=sorted(df["postal_code"].unique())
)

# 2. Company Filter
selected_companies = st.sidebar.multiselect(
    "Companies",
    options=df["company"].unique(),
    default=df["company"].unique()
)

# 3. Date Range Filter
min_date = df["date"].min().date()
max_date = df["date"].max().date()
selected_dates = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date), # (datetime.date.today() - datetime.timedelta(days=90), max_date), # (max_date - datetime.timedelta(days=365), datetime.date.today()), # default
    min_value=min_date,
    max_value=max_date
)

# 4. Jobs Filter
min_jobs = df["jobs"].min().astype(int)
max_jobs = df["jobs"].max().astype(int)
selected_jobs = st.sidebar.slider(
    "# layoffs per WARN filing",
    min_value=min_jobs,
    max_value=max_jobs,
    value=(min_jobs, max_jobs)
)

# --- Applying Filters ---
if len(selected_dates) == 2: # make sure both start and end dates are selected
    filtered_df = df[
            (df["postal_code"].isin(selected_states)) &
            (df["company"].isin(selected_companies)) &
            (df["jobs"] >= selected_jobs[0]) &
            (df["jobs"] <= selected_jobs[1]) &
            (df["date"].dt.date >= selected_dates[0]) &
            (df["date"].dt.date <= selected_dates[1])
        ]
else:
    filtered_df = df[
            (df["postal_code"].isin(selected_states)) &
            (df["company"].isin(selected_companies)) &
            (df["jobs"] >= selected_jobs[0]) &
            (df["jobs"] <= selected_jobs[1])
        ]
filtered_df = filtered_df.sort_values(by=['date'], ascending=False)

# --- Main Dashboard Area ---
# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total layoffs", int(filtered_df["jobs"].sum()))
col2.metric("Unique companies", filtered_df["company"].nunique())
col3.metric("States affected", filtered_df["postal_code"].nunique())
st.markdown(f'{df['postal_code'].nunique()} states (+DC) in dataset: {', '.join(sorted(df['postal_code'].unique()))}.')
state_abbrs = [s.abbr for s in us.STATES]
territory_abbrs = [s.abbr for s in us.TERRITORIES]
absent_states = set(state_abbrs) - set(df['postal_code'].unique())
absent_territories = set(territory_abbrs) - set(df['postal_code'].unique())
st.markdown(f'{len(absent_states)} states with no WARN filings in dataset: {', '.join(sorted(absent_states))}.')
st.markdown(f'{len(absent_territories)} territories with no WARN filings in dataset: {', '.join(sorted(absent_territories))}.')
st.markdown(f'{len(df)} most recent WARN records loaded from dataset of 84,000+.')

st.write("---")
st.subheader("Most recent WARN records - current & upcoming layoffs")
st.markdown('Since this data is sourced from state labor department websites that each have different formats this information is reported in, \
            not all records have the same fields filled out. Not all records have both a notice date and effective date, so we use the earliest of the dates available to sort the data.')
st.markdown(f'Columns in integrated.csv: {list(df.columns)}')
st.dataframe(filtered_df, width='stretch')

# --- Visualizations ---
st.subheader("Layoffs by state")

# Plotly Choropleth Map
df_jobs_state = filtered_df.groupby('postal_code')['jobs'].sum().reset_index()
fig = px.choropleth(
    df_jobs_state,
    locations='postal_code',
    locationmode='USA-states',
    color='jobs',
    scope='usa',
    color_continuous_scale='Oranges',
    hover_data={"jobs": ":.0f"}
)
st.plotly_chart(fig, width='stretch')

# Bar chart
st.bar_chart(filtered_df.groupby('postal_code')['jobs'].sum())

st.subheader("Layoffs by company")
st.markdown('*You can expand this!* Use the tools on the upper right of this chart, \
            or double click on a state to show only companies in that state. \
            You can also use the filters on the left to filter by state, company, date range, and number of jobs affected.')
fig_comp = px.bar(filtered_df, x='company', y='jobs', color='postal_code', # color='jobs'
                  height=750, # log_y=True, # color_continuous_scale='oranges',
                  category_orders={'postal_code': sorted(filtered_df['postal_code'].unique())}) # title="Company Layoffs")
fig_comp.update_layout(xaxis={'categoryorder':'total descending', 'tickangle': 45})
st.plotly_chart(fig_comp, width='stretch')

df_jobs_company = filtered_df.groupby('company')[['company', 'jobs', 'postal_code']].agg({
    'jobs': 'sum',
    'postal_code': lambda x: sorted(x.unique()),
}).sort_values(by='jobs', ascending=False).reset_index()
st.dataframe(df_jobs_company, width='stretch')

st.subheader("Layoffs over time")
# st.bar_chart(filtered_df.groupby('date')['jobs'].sum()) # line_chart

fig_time = px.bar(filtered_df.groupby('date')['jobs'].sum().reset_index(), x='date', y='jobs', title='daily') # line
st.plotly_chart(fig_time, width='stretch')

df_monthly = filtered_df.groupby(pd.Grouper(key='date', freq='ME'))['jobs'].sum().reset_index()
fig_time = px.bar(df_monthly, x='date', y='jobs', title='monthly',
                  hover_data={"jobs": ":.0f"}) # line
st.plotly_chart(fig_time, width='stretch')