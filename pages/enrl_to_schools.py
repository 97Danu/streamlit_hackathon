import streamlit as st
import snowflake.connector
from main import *
from st_pages import Page, add_page_title, show_pages
# import matplotlib.pyplot as plt
import plotly.express as px
import altair as alt
import io
import geopandas as gpd
from vega_datasets import data
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import shapefile as shp
from shapely.geometry import Point
import numpy as np
sns.set_style('whitegrid')




def execute_query(query):
    try:
        conn = snowflake.connector.connect(
            account=st.session_state.account,
            role=st.session_state.role,
            warehouse=st.session_state.warehouse,
            database=st.session_state.database,
            schema=st.session_state.schema,
            user=st.session_state.user,
            password=st.session_state.password,
            client_session_keep_alive=True
        )
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = [col[0] for col in cursor.description]  # Extract column names from cursor
        conn.close()
        result_df = pd.DataFrame(result, columns=columns)  # Create DataFrame with column names
        return result_df
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        return None

st.title('CLASSWISE & AGEWISE ENROLLMENT TO SCHOOLS')

def main():

    Q1='''SELECT C.table_name, LISTAGG(C.column_name, ',') AS ALL_COLUMNS,T.COMMENT AS COMMENTS
            FROM information_schema.columns C
            inner join information_schema.tables T ON (T.table_name=C.table_name)
            WHERE C.table_schema = 'IND_SCHEMA' AND (C.table_name LIKE 'CLSWISE_ENR_%' or C.table_name LIKE 'ENRL_BY_AGE_%')
            GROUP BY C.table_name,COMMENTS
            ORDER BY C.table_name'''
    R1 = execute_query(Q1)
    r1_expander = st.expander("Data sets used in this entire analysis")
    R1_DF = pd.DataFrame(R1)
    R1_DF.index = R1_DF.index + 1
    r1_expander.write(R1_DF)


    st.divider()
    st.title("1.Gross Enrolment Ratio from 2013-14 to 2015-16")

    col1,col2=st.columns(2)

    with col1:
            enr_s_year_options = ["2013-14", "2015-16", "2014-15"]
            enr_s_year_index = enr_s_year_options.index("2013-14")
            enr_s_year = st.selectbox('Select which year:', options=enr_s_year_options, index=enr_s_year_index)
    with col2:
            enr_s_col_options = ["PRIMARY_BOYS", "PRIMARY_GIRLS", "PRIMARY_TOTAL", "UPPER_PRIMARY_BOYS", "UPPER_PRIMARY_GIRLS",
                                "UPPER_PRIMARY_TOTAL", "SECONDARY_BOYS", "SECONDARY_GIRLS", "SECONDARY_TOTAL",
                                "HIGHER_SECONDARY_BOYS", "HIGHER_SECONDARY_GIRLS", "HIGHER_SECONDARY_TOTAL"]
            enr_s_col_index = enr_s_col_options.index("PRIMARY_BOYS")
            enr_s_col = st.selectbox('Select class:', options=enr_s_col_options, index=enr_s_col_index)
        
    Q2 = f''' WITH CTE AS 
        (SELECT STATES, YEAR, ROUND(IFNULL(TRY_TO_DOUBLE("{enr_s_col}"), 0), 2) AS GROSS_ENRL_RATIO
            FROM V01_ENRL_BY_GROSS_RATIO_2013_2015 WHERE YEAR ='{enr_s_year}'
            )           
        SELECT INDIA_STATES.STATES,CTE.GROSS_ENRL_RATIO GROSS_ENRL_RATIO FROM INDIA_STATES 
            LEFT JOIN CTE ON (CTE.STATES=INDIA_STATES.STATES) '''
    R2 = execute_query(Q2)

    r2_expander = st.expander("Data sets used in this analysis")
    R2_DF = pd.DataFrame(R2)
    R2_DF.index = R2_DF.index + 1
    r2_expander.write(R2_DF)
    selected_items = f"Gross Enrolment Ratio for Year: {enr_s_year}  Class: {enr_s_col}"
    st.title(selected_items)

    india_states_shp = 'https://github.com/97Danu/Maps_with_python/raw/master/india-polygon.shp'
    india_states = gpd.read_file(india_states_shp)
    # st.write(india_states)
    india_states.rename(columns={'st_nm': 'STATES'}, inplace=True)

    # Merge dropout rates with GeoDataFrame
    merged_data = india_states.merge(R2_DF, how='left', on='STATES')

    # Define bins and labels
    bins = [float('-inf'), 95, 105, float('inf')]
    labels = ['Below 95', '95 - 105', 'Above 105']

    # Assigning values to bins and handling 'NA' values
    conditions = [
        merged_data['GROSS_ENRL_RATIO'] < 95,
        (merged_data['GROSS_ENRL_RATIO'] >= 95) & (merged_data['GROSS_ENRL_RATIO'] <= 105),
        merged_data['GROSS_ENRL_RATIO'] > 105
    ]

    # Assigning labels
    merged_data['color'] = np.select(conditions, labels, default='NA')

    # Create a plotly figure with categorical colors
    fig = px.choropleth_mapbox(merged_data, geojson=merged_data.geometry, locations=merged_data.index,
                            color='color',
                            color_discrete_map={'Below 95': 'Green', '95 - 105': 'Blue', 'Above 105': 'Red', 'NA': 'Yellow'},
                            mapbox_style="carto-positron",
                            hover_data={'STATES': True, 'GROSS_ENRL_RATIO': True},
                            center={"lat": 20.5937, "lon": 78.9629},
                            zoom=3,
                            opacity=0.5)
    

# Update layout for better visualization
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, mapbox={'center': {'lat': 20, 'lon': 78}})

# Display the map in Streamlit
    st.plotly_chart(fig)

    st.markdown("""---------------------------------""")
    st.title("2.Top Gross Enrolment Ratio from 2013-14 to 2015-16")

    # col1 = st.columns(1)
    # with col1:
    top_options = list(range(1, 31))  # Generates a list from 1 to 30
    top = st.selectbox('Select top GROSS_ENRL_RATIO:', options=top_options, index=9)
    
    Q3 = f'''WITH CTE AS 
            (SELECT STATES, YEAR, ROUND(IFNULL(TRY_TO_DOUBLE("{enr_s_col}"), 0), 2) AS GROSS_ENRL_RATIO, 
                DENSE_RANK() OVER (PARTITION BY YEAR ORDER BY GROSS_ENRL_RATIO DESC) DNK 
                FROM V01_ENRL_BY_GROSS_RATIO_2013_2015)
                SELECT CTE.STATES,CTE.YEAR,CTE.GROSS_ENRL_RATIO , CTE.DNK RANK FROM CTE WHERE YEAR = '{enr_s_year}' AND DNK <= {top}'''
    R3 = execute_query(Q3)
        #AS "{s_col}"
    r3_expander = st.expander("Data sets used in this analysis")
    R3_DF = pd.DataFrame(R3)
    R3_DF.index = R3_DF.index + 1
    r3_expander.write(R3_DF)
    R3_DF = R3_DF.sort_values(by="GROSS_ENRL_RATIO", ascending=False)
    selected_items = f"Top  {top} dropout states of the Year: {enr_s_year} for Class: {enr_s_col}"
    # Creating the Altair chart
    chart = (
        alt.Chart(R3_DF)
        .mark_bar()
        .encode(
            x=alt.X("GROSS_ENRL_RATIO:Q", title="  Dropout Rate"),
            y=alt.Y("STATES:N", title="States", sort="-x"),
            tooltip=[
            alt.Tooltip("STATES", title="State"),
            alt.Tooltip("GROSS_ENRL_RATIO", title="Dropout Rate"),
            ]
        )
        .properties(width=800,  title=f"{selected_items}")
        .interactive()
    )

        # Displaying the chart using Streamlit
    st.altair_chart(chart, use_container_width=True)
    r4_expander = st.expander("****Insights from 2013 to 2016*****")
    r4_expander.markdown("1. **During 2015-16:**")
    r4_expander.markdown("- **GER in Higher Secondary Schools:** Boys - 55.95, Girls - 56.41, Total - 56.16")
    r4_expander.markdown("- **States/UTs below Nation value (56.16):**")
    r4_expander.markdown("  - Daman & Diu (21.54), Bihar (35.62), Nagaland (36.43), Odisha (36.54), Assam (38.81), Karnataka (39.86), Meghalaya (43.35), Gujarat (43.43), Tripura (43.46), Madhya Pradesh (45.25), Jharkhand (48.32), Dadra & Nagar Haveli (48.49), West Bengal (51.54), Chhattisgarh (54), Mizoram (55.68)")
    r4_expander.markdown("- **States/UTs above Nation value (56.16):**")
    r4_expander.markdown("  - Lakshadweep (98.16), Himachal Pradesh (95.53), Chandigarh (83.28), Tamil Nadu (82.03), Delhi (77.9), Kerala (77.56), Goa (75.84), Uttarakhand (75.83), Puducherry (74.8), Andaman & Nicobar Islands (74.62), Punjab (70.19), Sikkim (68.23), Manipur (67.95), Maharashtra (67.81), Arunachal Pradesh (61.81), Telangana (61.32), Uttar Pradesh (60.78), Andhra Pradesh (60.16), Haryana (59.59), Rajasthan (59.31), Jammu & Kashmir (58.6)")

    r4_expander.markdown("2. **During 2014-15:**")
    r4_expander.markdown("- **GER in Higher Secondary Schools:** Boys - 54.57, Girls - 53.81, Total - 54.21")
    r4_expander.markdown("- **States/UTs below Nation value (54.21):**")
    r4_expander.markdown("  - Bihar, Karnataka, Nagaland, Assam, Meghalaya, Daman & Diu, Dadra & Nagar Haveli, Tripura, Gujarat, Madhya Pradesh, Jharkhand, West Bengal, Andhra Pradesh")

    r4_expander.markdown("3. **During 2013-14:**")
    r4_expander.markdown("- **GER in Higher Secondary Schools:** Boys - 52.77, Girls - 51.58, Total - 52.21")
    r4_expander.markdown("- **States/UTs below Nation value (52.21):**")
    r4_expander.markdown("  - Karnataka, Meghalaya, Bihar, Assam, Nagaland, Dadra & Nagar Haveli, Tripura, Jharkhand, Daman & Diu, Madhya Pradesh, West Bengal, Gujarat, Jammu & Kashmir")
	
    st.markdown("""---------------------------------""")

    

 

                    
if __name__ == "__main__":
    main()
footer="""<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed with ❤️ by <a style='display: inline; text-align: center;' href="https://www.linkedin.com/in/danammahiremath/" target="_blank">DANAMMA HIREMATH</a></p>
</div>
"""
st.markdown(footer,unsafe_allow_html=True)  