import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import altair as alt
import io
import geopandas as gpd
from vega_datasets import data
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

st.title('📊 ALL INDIA SURVEY ON HIGHER EDUCATION')

def main():

    Q1='''SELECT table_name, ALL_COLUMNS, COMMENTS
         FROM T01_METADAT_IND_SCHEMA WHERE table_name LIKE  'AISHE_%'
         ORDER BY table_name'''
    R1 = execute_query(Q1)
    r1_expander = st.expander("Data sets used in this entire analysis")
    R1_DF = pd.DataFrame(R1)
    R1_DF.index = R1_DF.index + 1
    r1_expander.write(R1_DF)


    st.divider()
    st.title("1.Number of colleges,Institutes and Universities across India in 2015-16")

    ais_edu_options = ["Colleges",  "Standalone Institutes" ,"Universities" ]
    ais_edu_index = ais_edu_options.index("Colleges")
    ais_edu= st.selectbox('Select Education type:', options=ais_edu_options, index=ais_edu_index)
    selected_items = f"Education type: {ais_edu} "
    st.title(selected_items)
    Q2 = f''' WITH CTE AS 
                (SELECT STATES, YEAR,COUNT 
                    FROM V01_AISHE_EDUCATION_TYPE WHERE  EDUCATION_TYPE= '{ais_edu}' 
                    )           
                SELECT INDIA_STATES.STATES,CTE.COUNT  FROM INDIA_STATES 
                    LEFT JOIN CTE ON (CTE.STATES=INDIA_STATES.STATES) '''
    R2 = execute_query(Q2)

    r2_expander = st.expander("Data sets used in this analysis")
    R2_DF = pd.DataFrame(R2)
    R2_DF.index = R2_DF.index + 1
    r2_expander.write(R2_DF)

    india_states_shp = 'https://github.com/97Danu/Maps_with_python/raw/master/india-polygon.shp'
    india_states = gpd.read_file(india_states_shp)
    india_states.rename(columns={'st_nm': 'STATES'}, inplace=True)

    # Merge dropout rates with GeoDataFrame
    merged_data = india_states.merge(R2_DF, how='left', on='STATES')

    # Define bins and labels
    bins = [float('-inf'), 100, 1000, float('inf')]
    labels = ['Below 100', '100 - 1000', 'Above 1000']

    # Assigning values to bins and handling 'NA' values
    conditions = [
        merged_data['COUNT'] < 100,
        (merged_data['COUNT'] >= 100) & (merged_data['COUNT'] <= 1000),
        merged_data['COUNT'] > 1000
    ]

    # Assigning labels
    merged_data['color'] = np.select(conditions, labels, default='NA')

    # Create a plotly figure with categorical colors
    fig = px.choropleth_mapbox(merged_data, geojson=merged_data.geometry, locations=merged_data.index,
                            color='color',
                            color_discrete_map={'Below 100': 'Green', '100 - 1000': 'Blue', 'Above 1000': 'Red', 'NA': 'Yellow'},
                            mapbox_style="carto-positron",
                            hover_data={'STATES': True, 'COUNT': True},
                            center={"lat": 20.5937, "lon": 78.9629},
                            zoom=3,
                            opacity=0.5)
    

# Update layout for better visualization
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, mapbox={'center': {'lat': 20, 'lon': 78}})

# Display the map in Streamlit
    st.plotly_chart(fig)

    st.markdown("""---------------------------------""")
    st.title("2.Top count of colleges,Institutes and Universities across India in 2015-16")

    top_options = list(range(1, 31))  # Generates a list from 1 to 30
    top = st.selectbox('Select top COUNT:', options=top_options, index=15)
    
    Q3 = f'''  WITH CTE AS 
            (SELECT STATES, YEAR,COUNT, 
                DENSE_RANK() OVER (PARTITION BY YEAR ORDER BY COUNT DESC) DNK 
                FROM V01_AISHE_EDUCATION_TYPE WHERE  EDUCATION_TYPE = '{ais_edu}' )
                SELECT CTE.STATES,CTE.YEAR,CTE.COUNT , CTE.DNK RANK FROM CTE where DNK <= {top}  '''
    R3 = execute_query(Q3)
    r3_expander = st.expander("Data sets used in this analysis")
    R3_DF = pd.DataFrame(R3)
    R3_DF.index = R3_DF.index + 1
    r3_expander.write(R3_DF)
    R3_DF = R3_DF.sort_values(by="COUNT", ascending=False)
    selected_items = f"Top  {top}  Education type : {ais_edu} in India  Year: 2015-16"
    # Creating the Altair chart
    chart = (
        alt.Chart(R3_DF)
        .mark_bar()
        .encode(
            x=alt.X("COUNT:Q", title="COUNT"),
            y=alt.Y("STATES:N", title="States", sort="-x"),
            tooltip=[
            alt.Tooltip("STATES", title="State"),
            alt.Tooltip("COUNT", title="COUNT"),
            ]
        )
        .properties(width=800,  title=f"{selected_items}")
        .interactive()
    )

        # Displaying the chart using Streamlit
    st.altair_chart(chart, use_container_width=True)
 
    st.markdown("""---------------------------------""")
    st.title("3.Education loan distribution stats across India in 2015-16")

    col5,col6=st.columns(2)
    with col5:
        ais_loan_options = ["Standalone Institutes" ,"Universities" ]
        ais_loan_index = ais_loan_options.index("Universities")
        ais_loan_edu= st.selectbox('Select Education type:', options=ais_loan_options, index=ais_loan_index)

    with col6:
        ais_loan_col_options = ["TOTAL_GENERAL_TOTAL", "TOTAL_GENERAL_FEMALES",
                                "TOTAL_SC_TOTAL", "TOTAL_SC_FEMALES",
                                "TOTAL_ST_TOTAL", "TOTAL_ST_FEMALES",
                                "TOTAL_OBC_TOTAL", "TOTAL_OBC_FEMALES",
                                "TOTAL_TOTAL_PERSONS", "TOTAL_TOTAL_FEMALES",
                                "PWD_GENERAL_TOTAL", "PWD_GENERAL_FEMALES",
                                "PWD_SC_TOTAL", "PWD_SC_FEMALES",
                                "PWD_ST_TOTAL", "PWD_ST_FEMALES",
                                "PWD_OBC_TOTAL", "PWD_OBC_FEMALES",
                                "PWD_TOTAL_PERSONS", "PWD_TOTAL_FEMALES",
                                "MUSLIM_MINORITY_GENERAL_TOTAL", "MUSLIM_MINORITY_GENERAL_FEMALES",
                                "MUSLIM_MINORITY_SC_TOTAL", "MUSLIM_MINORITY_SC_FEMALES",
                                "MUSLIM_MINORITY_ST_TOTAL", "MUSLIM_MINORITY_ST_FEMALES",
                                "MUSLIM_MINORITY_OBC_TOTAL", "MUSLIM_MINORITY_OBC_FEMALES",
                                "MUSLIM_MINORITY_TOTAL_PERSONS", "MUSLIM_MINORITY_TOTAL_FEMALES",
                                "OTHER_MINORITY_GENERAL_TOTAL", "OTHER_MINORITY_GENERAL_FEMALES",
                                "OTHER_MINORITY_SC_TOTAL", "OTHER_MINORITY_SC_FEMALES",
                                "OTHER_MINORITY_ST_TOTAL", "OTHER_MINORITY_ST_FEMALES",
                                "OTHER_MINORITY_OBC_TOTAL", "OTHER_MINORITY_OBC_FEMALES",
                                "OTHER_MINORITY_TOTAL_PERSONS", "OTHER_MINORITY_TOTAL_FEMALES"]
        ais_loan_col_index = ais_loan_col_options.index("TOTAL_SC_FEMALES")
        ais_loan_col = st.selectbox('Select cast of category :', options=ais_loan_col_options, index=ais_loan_col_index)
    selected_items = f"Education loan distribution for Education type: {ais_loan_edu}  category: {ais_loan_col}  in India  Year: 2015-16"
    st.title(selected_items)
    Q3 = f''' WITH CTE AS 
                (SELECT STATES,"{ais_loan_col}" LOAN_COUNT 
                    FROM V01_AISHE_EDUCATION_TYPE_LOANS_2015_2016 WHERE  EDUCATION_TYPE= '{ais_loan_edu}' 
                    )           
                SELECT INDIA_STATES.STATES,CTE.LOAN_COUNT  FROM INDIA_STATES 
                    LEFT JOIN CTE ON (CTE.STATES=INDIA_STATES.STATES)'''
    R3 = execute_query(Q3)

    r3_expander = st.expander("Data sets used in this analysis")
    R3_DF = pd.DataFrame(R3)
    R3_DF.index = R3_DF.index + 1
    r3_expander.write(R3_DF)

    india_states_shp = 'https://github.com/97Danu/Maps_with_python/raw/master/india-polygon.shp'
    india_states = gpd.read_file(india_states_shp)
    india_states.rename(columns={'st_nm': 'STATES'}, inplace=True)

    # Merge dropout rates with GeoDataFrame
    merged_data = india_states.merge(R3_DF, how='left', on='STATES')

    # Define bins and labels
    bins = [float('-inf'), 100, 1000, float('inf')]
    labels = ['Below 100', '100 - 1000', 'Above 1000']

    # Assigning values to bins and handling 'NA' values
    conditions = [
        merged_data['LOAN_COUNT'] < 100,
        (merged_data['LOAN_COUNT'] >= 100) & (merged_data['LOAN_COUNT'] <= 1000),
        merged_data['LOAN_COUNT'] > 1000
    ]

    # Assigning labels
    merged_data['color'] = np.select(conditions, labels, default='NA')

    # Create a plotly figure with categorical colors
    fig = px.choropleth_mapbox(merged_data, geojson=merged_data.geometry, locations=merged_data.index,
                            color='color',
                            color_discrete_map={'Below 100': 'Red', '100 - 1000': 'Blue', 'Above 1000': 'Green', 'NA': 'Yellow'},
                            mapbox_style="carto-positron",
                            hover_data={'STATES': True, 'LOAN_COUNT': True},
                            center={"lat": 20.5937, "lon": 78.9629},
                            zoom=3,
                            opacity=0.5)
    

# Update layout for better visualization
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, mapbox={'center': {'lat': 20, 'lon': 78}})

# Display the map in Streamlit
    st.plotly_chart(fig)

    st.markdown("""---------------------------------""")
    
    st.title("4.Top states based on education loan distribution across India in 2015-16")

    top_loan_options = list(range(1, 10))  # Generates a list from 1 to 10
    top_loan = st.selectbox('Select top LOAN_COUNT:', options=top_loan_options, index=8)
    
    Q4 = f'''   WITH CTE AS 
            (SELECT STATES,"{ais_loan_col}" LOAN_COUNT, 
                DENSE_RANK() OVER ( ORDER BY LOAN_COUNT DESC) DNK 
                FROM  V01_AISHE_EDUCATION_TYPE_LOANS_2015_2016 WHERE  EDUCATION_TYPE= '{ais_loan_edu}' )
                SELECT CTE.STATES,CTE.LOAN_COUNT, CTE.DNK RANK FROM CTE where DNK <= {top_loan}  '''
    R4 = execute_query(Q4)
    r4_expander = st.expander("Data sets used in this analysis")
    R4_DF = pd.DataFrame(R4)
    R4_DF.index = R4_DF.index + 1
    r4_expander.write(R4_DF)
    R4_DF = R4_DF.sort_values(by="LOAN_COUNT", ascending=False)
    selected_items = f"Top  {top_loan}  states for edu loan Education type : {ais_loan_edu} category: {ais_loan_col}  in India  Year: 2015-16"
    # Creating the Altair chart
    chart = (
        alt.Chart(R4_DF)
        .mark_bar()
        .encode(
            x=alt.X("LOAN_COUNT:Q", title="LOAN_COUNT"),
            y=alt.Y("STATES:N", title="States", sort="-x"),
            tooltip=[
            alt.Tooltip("STATES", title="State"),
            alt.Tooltip("LOAN_COUNT", title="LOAN_COUNT"),
            ]
        )
        .properties(width=800,  title=f"{selected_items}")
        .interactive()
    )

        # Displaying the chart using Streamlit
    st.altair_chart(chart, use_container_width=True)
    st.markdown("""---------------------------------""")

    st.title("5.Education scholarship distribution stats across India in 2015-16")

    col8,col9=st.columns(2)
    with col8:
        scholarship_options = ["Standalone Institutes" ,"Universities","Colleges" ]
        scholarship_index = scholarship_options.index("Universities")
        scholarship_edu= st.selectbox('Select Education type:', options=scholarship_options, index=scholarship_index)

    with col9:
        scholarship_col_options = ["TOTAL_GENERAL_TOTAL", "TOTAL_GENERAL_FEMALES",
                                "TOTAL_SC_TOTAL", "TOTAL_SC_FEMALES",
                                "TOTAL_ST_TOTAL", "TOTAL_ST_FEMALES",
                                "TOTAL_OBC_TOTAL", "TOTAL_OBC_FEMALES",
                                "TOTAL_TOTAL_PERSONS", "TOTAL_TOTAL_FEMALES",
                                "PWD_GENERAL_TOTAL", "PWD_GENERAL_FEMALES",
                                "PWD_SC_TOTAL", "PWD_SC_FEMALES",
                                "PWD_ST_TOTAL", "PWD_ST_FEMALES",
                                "PWD_OBC_TOTAL", "PWD_OBC_FEMALES",
                                "PWD_TOTAL_PERSONS", "PWD_TOTAL_FEMALES",
                                "MUSLIM_MINORITY_GENERAL_TOTAL", "MUSLIM_MINORITY_GENERAL_FEMALES",
                                "MUSLIM_MINORITY_SC_TOTAL", "MUSLIM_MINORITY_SC_FEMALES",
                                "MUSLIM_MINORITY_ST_TOTAL", "MUSLIM_MINORITY_ST_FEMALES",
                                "MUSLIM_MINORITY_OBC_TOTAL", "MUSLIM_MINORITY_OBC_FEMALES",
                                "MUSLIM_MINORITY_TOTAL_PERSONS", "MUSLIM_MINORITY_TOTAL_FEMALES",
                                "OTHER_MINORITY_GENERAL_TOTAL", "OTHER_MINORITY_GENERAL_FEMALES",
                                "OTHER_MINORITY_SC_TOTAL", "OTHER_MINORITY_SC_FEMALES",
                                "OTHER_MINORITY_ST_TOTAL", "OTHER_MINORITY_ST_FEMALES",
                                "OTHER_MINORITY_OBC_TOTAL", "OTHER_MINORITY_OBC_FEMALES",
                                "OTHER_MINORITY_TOTAL_PERSONS", "OTHER_MINORITY_TOTAL_FEMALES"]
        scholarship_col_index = scholarship_col_options.index("TOTAL_SC_FEMALES")
        scholarship_col_category = st.selectbox('Select scholarship cast of category :', options=scholarship_col_options, index=scholarship_col_index)
    scholarship_selected_items = f"Education scholarship distribution for Education type: {scholarship_edu}  category: {scholarship_col_category}  in India  Year: 2015-16"
    st.title(scholarship_selected_items)
    Q5 = f''' WITH CTE AS 
                (SELECT STATES,"{scholarship_col_category}" SCHOLARSHIP_COUNT 
                    FROM V01_AISHE_EDUCATION_TYPE_SCHOLARSHIP_2015_2016 WHERE  EDUCATION_TYPE= '{scholarship_edu}' 
                    )           
                SELECT INDIA_STATES.STATES,CTE.SCHOLARSHIP_COUNT  FROM INDIA_STATES 
                    LEFT JOIN CTE ON (CTE.STATES=INDIA_STATES.STATES)'''
    R5 = execute_query(Q5)

    r5_expander = st.expander("Data sets used in this analysis")
    R5_DF = pd.DataFrame(R5)
    R5_DF.index = R5_DF.index + 1
    r5_expander.write(R5_DF)

    india_states_shp = 'https://github.com/97Danu/Maps_with_python/raw/master/india-polygon.shp'
    india_states = gpd.read_file(india_states_shp)
    india_states.rename(columns={'st_nm': 'STATES'}, inplace=True)

    # Merge dropout rates with GeoDataFrame
    merged_data = india_states.merge(R5_DF, how='left', on='STATES')

    # Define bins and labels
    bins = [float('-inf'), 1000, 10000, float('inf')]
    labels = ['Below 100', '1000 - 10000', 'Above 10000']

    # Assigning values to bins and handling 'NA' values
    conditions = [
        merged_data['SCHOLARSHIP_COUNT'] < 100,
        (merged_data['SCHOLARSHIP_COUNT'] >= 1000) & (merged_data['SCHOLARSHIP_COUNT'] <= 10000),
        merged_data['SCHOLARSHIP_COUNT'] > 10000
    ]

    # Assigning labels
    merged_data['color'] = np.select(conditions, labels, default='NA')

    # Create a plotly figure with categorical colors
    fig = px.choropleth_mapbox(merged_data, geojson=merged_data.geometry, locations=merged_data.index,
                            color='color',
                            color_discrete_map={'Below 1000': 'Red', '1000 - 10000': 'Blue', 'Above 10000': 'Green', 'NA': 'Yellow'},
                            mapbox_style="carto-positron",
                            hover_data={'STATES': True, 'SCHOLARSHIP_COUNT': True},
                            center={"lat": 20.5937, "lon": 78.9629},
                            zoom=3,
                            opacity=0.5)
    

    # Update layout for better visualization
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, mapbox={'center': {'lat': 20, 'lon': 78}})

    # Display the map in Streamlit
    st.plotly_chart(fig)
    st.markdown("""---------------------------------""")

    st.title("6.Top states based on scholarship  distribution across India in 2015-16")

    top_scholarship_options = list(range(1, 10))  # Generates a list from 1 to 10
    top_scholarship = st.selectbox('Select top SCHOLARSHIP_COUNT:', options=top_scholarship_options, index=8)
    
    Q6 = f'''   WITH CTE AS 
            (SELECT STATES,"{scholarship_col_category}" SCHOLARSHIP_COUNT, 
                DENSE_RANK() OVER ( ORDER BY SCHOLARSHIP_COUNT DESC) DNK 
                FROM  V01_AISHE_EDUCATION_TYPE_SCHOLARSHIP_2015_2016 WHERE  EDUCATION_TYPE= '{scholarship_edu}' )
                SELECT CTE.STATES,CTE.SCHOLARSHIP_COUNT, CTE.DNK RANK FROM CTE where DNK <= {top_scholarship} '''
    R6 = execute_query(Q6)
    r6_expander = st.expander("Data sets used in this analysis")
    R6_DF = pd.DataFrame(R6)
    R6_DF.index = R6_DF.index + 1
    r6_expander.write(R6_DF)
    R6_DF = R6_DF.sort_values(by="SCHOLARSHIP_COUNT", ascending=False)
    selected_items = f"Top  {top_loan} scholarships given states for edu loan Education type : {scholarship_edu} category: {scholarship_col_category}  in India  Year: 2015-16"
    # Creating the Altair chart
    chart = (
        alt.Chart(R6_DF)
        .mark_bar()
        .encode(
            x=alt.X("SCHOLARSHIP_COUNT:Q", title="SCHOLARSHIP_COUNT"),
            y=alt.Y("STATES:N", title="States", sort="-x"),
            tooltip=[
            alt.Tooltip("STATES", title="State"),
            alt.Tooltip("SCHOLARSHIP_COUNT", title="SCHOLARSHIP_COUNT"),
            ]
        )
        .properties(width=800,  title=f"{selected_items}")
        .interactive()
    )

        # Displaying the chart using Streamlit
    st.altair_chart(chart, use_container_width=True)


    st.markdown("""---------------------------------""")
    aishe_expander= st.expander("Complete Insights/Recommendations for  all India survey on education")
    aishe_expander.markdown(''' 
    1. **Colleges Dominate Educational Landscape**: Colleges account for the majority of educational institutions across all states, with a total count of 37,038 in 2015-16. This highlights the significant role colleges play in providing higher education opportunities to students.

    2. **Maharashtra Leads in All Categories**: Maharashtra has the highest number of Colleges (3931), Standalone Institutes (1402), and Universities (45) among all states in India. This indicates Maharashtra's commitment to providing diverse educational options to its students.

    3. **Uttar Pradesh Has Most Colleges**: Uttar Pradesh boasts the highest number of Colleges (5573) among all states in India. This suggests that the state has a strong focus on expanding access to higher education through colleges.

    4. **Tamil Nadu and Karnataka Excel in Standalone Institutes and Universities**: Tamil Nadu and Karnataka have the highest number of Standalone Institutes (991 and 889, respectively) and Universities (57 and 50, respectively) among all states. This indicates their efforts in establishing specialized educational institutions and promoting research and higher learning.

    5. **North-Eastern States Have Lower Numbers of Institutions**: North-Eastern states like Arunachal Pradesh, Mizoram, and Nagaland have lower numbers of Colleges, Standalone Institutes, and Universities compared to other states. This suggests the need for increased investment and focus on educational infrastructure in these regions.

    6. **Delhi and Chandigarh Have Strong University Presence**: Delhi and Chandigarh, despite being relatively smaller regions, have a significant presence of Universities. This highlights their role as centers of higher learning and academic excellence in India.

                            
    Somemore insights EDUCATION LOANS in 2015-2016 
    1. **Maharashtra has the highest number of EDUCATION LOANS in both Universities and Standalone Institutes**: 
    - Maharashtra leads in both universities and standalone institutes in terms of the total number of education loans. 
    - This suggests that the state has a high demand for higher education, and students are willing to take on debt to finance their studies.


    2. **Tamil Nadu has the second-highest number of EDUCATION LOANS in Universities**: 
    - Tamil Nadu has the second-highest number of education loans in universities, highlighting the state's focus on higher education. 
    - The large number of loans disbursed in Tamil Nadu indicates a strong demand for higher education, especially among students from marginalized communities.


    3. **Karnataka has the second-highest number of EDUCATION LOANS in Standalone Institutes**: 
    - Karnataka emerges as the second-highest state in terms of education loans in standalone institutes. 
    - The high number of loans in Karnataka indicates a vibrant private higher education sector in the state, providing diverse educational opportunities to students.


    4. **PWD, Muslim Minority, and Other Minority categories have a low representation across states**: 
    - The data shows that categories such as PWD, Muslim Minority, and Other Minority have a low representation across states in both universities and standalone institutes. 
    - This suggests that there is a need for more inclusive policies and outreach efforts to ensure equal access to education for these marginalized groups.


    5. **Punjab and Delhi have the highest percentage of General category loans in Universities**: 
    - Punjab and Delhi have the highest percentage of General category loans in universities, indicating a concentration of education loans among non-reserved categories. 
    - This suggests areas where targeted interventions may be needed to increase access to education loans for marginalized groups.


    6. **Kerala has a high percentage of Muslim Minority loans in Universities**: 
    - Kerala stands out with a notably high percentage of Muslim Minority loans in universities, demonstrating the state's efforts to promote education among minority communities. 
    - This is a positive trend that can serve as a model for other states in ensuring equitable access to higher education.                        
    
    Somemore insights SCHOLARSHIPS in 2015-2016 

    **1.** Out of the named states in the dataset, Tamil Nadu had the highest number of granted scholarships, with 29049 scholars. On the other hand, Mizoram, Nagaland, and Arunachal Pradesh had the lowest with only 0 scholars granted. 

    **2.** The most number of scholarships were granted to the ST category, with a total of 7389. This was followed by the OBC category with 3184 scholars. The least number of scholarships were granted to the PWD category with 36.

    **3.** In the Universities category, Gujarat had the highest number of scholarships granted to the Muslim minority with a total of 98. In the Standalone Institutes category, Maharashtra had the highest number of scholarships granted to the Muslim minority with a total of 5132.

    **4.** In the Universities category, Karnataka had the highest number of scholarships granted to the Other Minority with a total of 6434. In the Standalone Institutes category, Tamil Nadu had the highest number of scholarships granted to the Other Minority with a total of 1901.

    **5.** The total number of scholarships granted in the Universities was 45438, and the total number of scholarships granted in the Standalone Institutes was 62038. 

    **6.** The total number of scholarships granted across all the states was 107476.                                                                       
                            
    ### Strategies to Increase the Quality of Educational Institutions:

    1. **Faculty Development and Training:**
        - Conduct professional development programs for faculty.
        - Encourage and support faculty research activities.

    2. **Curriculum Enhancement:**
        - Regularly review and update curricula to align with industry standards.
        - Integrate practical learning experiences into the curriculum.

    3. **Infrastructure Development:**
        - Invest in state-of-the-art facilities and technology-enabled classrooms.
        - Provide access to digital resources and modern libraries.

    4. **Quality Assurance and Accreditation:**
        - Encourage institutions to pursue accreditation from recognized bodies.
        - Implement quality monitoring mechanisms and assessments.

    5. **Student Support and Services:**
        - Offer career counseling and guidance services.
        - Establish student support programs and mentorship initiatives.

    6. **Research and Innovation:**
        - Promote a culture of research and innovation.
        - Facilitate collaborations with industries for research projects.

    7. **Governance and Leadership:**
        - Ensure transparent and efficient administrative processes.
        - Foster visionary leadership for academic excellence.

    8. **Inclusivity and Diversity:**
        - Promote diversity and inclusivity in the student population.
        - Create a culturally rich learning environment.

    Implementing these strategies can significantly enhance the quality of education and academic standards in colleges, standalone institutes, and universities across all states.
                        

    ''')
 

                    
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
