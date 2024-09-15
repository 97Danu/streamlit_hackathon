import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import altair as alt
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns

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

# Streamlit app layout
def main():

    st.title("📊FUTURE PREDICTION of DROP OUT RATES IN INDIA USING SNOWFLAKE.ML.FORECAST")
    col1,col2=st.columns(2)
    with col1:
        yr_options = [10,15,20,25,30]  
        yr = st.selectbox('Select predicts years:', options=yr_options, index=1)
    with col2:
        s_col_options = ["I_V_BOYS",
                        "I_V_GIRLS",
                        "I_V_TOTAL",
                        "I_VIII_BOYS",
                        "I_VIII_GIRLS",
                        "I_VIII_TOTAL",
                        "I_X_BOYS",
                        "I_X_GIRLS",
                        "I_X_TOTAL",
                        "SC_I_V_BOYS",
                        "SC_I_V_GIRLS",
                        "SC_I_V_TOTAL",
                        "SC_I_VIII_BOYS",
                        "SC_I_VIII_GIRLS",
                        "SC_I_VIII_TOTAL",
                        "SC_I_X_BOYS",
                        "SC_I_X_GIRLS",
                        "SC_I_X_TOTAL",
                        "ST_I_V_BOYS",
                        "ST_I_V_GIRLS",
                        "ST_I_V_TOTAL",
                        "ST_I_VIII_BOYS",
                        "ST_I_VIII_GIRLS",
                        "ST_I_VIII_TOTAL",
                        "ST_I_X_BOYS",
                        "ST_I_X_GIRLS",
                        "ST_I_X_TOTAL"] 
        s_col_index = s_col_options.index("SC_I_X_TOTAL")  # Find the index of the default value
        s_col = st.selectbox('Select class (catergory):', options=s_col_options, index=s_col_index)

    Q1=f'''
        BEGIN

        CREATE OR REPLACE VIEW V01_USE_DATA_DROPDATE_FORECAST_{s_col}
            AS
        SELECT TS_FOR_FORECAST,{s_col} FROM V01_DATA_FOR_DRR_FORECAST
        WHERE YEAR(TS_FOR_FORECAST) IN (2008,2009,2010);

        DROP SNOWFLAKE.ML.FORECAST IF EXISTS  DROPDATE_FORECAST_{s_col};
        
        CREATE SNOWFLAKE.ML.FORECAST DROPDATE_FORECAST_{s_col}(
        INPUT_DATA => SYSTEM$REFERENCE('VIEW', 'V01_USE_DATA_DROPDATE_FORECAST_{s_col}'),
        TIMESTAMP_COLNAME => 'TS_FOR_FORECAST',
        TARGET_COLNAME => '{s_col}');

        
        CALL DROPDATE_FORECAST_{s_col}!FORECAST(FORECASTING_PERIODS => 365 * {yr} );
        
        LET x := SQLID;
        CREATE OR REPLACE TABLE SF_FORECAST_{s_col} AS 
        SELECT YEAR(TS) YEAR,(CASE WHEN avg(ROUND(FORECAST,2))<0 THEN 0
                                  ELSE  avg(ROUND(FORECAST,2)) END ) FORECAST,
        (CASE WHEN avg(ROUND(LOWER_BOUND,2))<0 THEN 0
                                        ELSE  avg(ROUND(LOWER_BOUND,2)) END ) AS LOWER_BOUND,
                                        
        (CASE WHEN avg(ROUND(UPPER_BOUND,2))<0 THEN 0
                                        ELSE  avg(ROUND(UPPER_BOUND,2)) END ) AS UPPER_BOUND
        FROM TABLE(RESULT_SCAN(:x))
        GROUP BY YEAR;

        CREATE OR REPLACE VIEW SF_ACTUAL_FORECAST_{s_col}
            AS 
        SELECT YEAR,ROUND(FORECAST,2) ACTUAL_FORECAST,ROUND(LOWER_BOUND,2) LOWER_BOUND,
        ROUND(UPPER_BOUND,2) UPPER_BOUND   FROM SF_FORECAST_{s_col}
        
        UNION ALL
        
        SELECT DISTINCT CAST(YEAR AS INTEGER) YEAR,{s_col},NULL,NULL FROM V01_DATA_FOR_DRR_FORECAST; 
        RETURN 'SF_ACTUAL_FORECAST_{s_col} will have Actual and forecast data';
        END;
        '''
    # Once Generate Forecast clicked Q1, Q2 will be executed 
    if st.button('Generate Forecast'):
            try:
                R1 = execute_query(Q1)
                r1_expander = st.expander(f'Query generated for for executed for class  {s_col} ')
                r1_expander.write(Q1)
                r1_expander.write(R1)

                LOAD_Q=f'''call system$send_email(
                                            'SF_Email_Notifications',
                                            'danuhiremath123@gmail.com',
                                            '[SF_Email_Notifications]:Email Alert: Forecast for dropout rate  class: {s_col}  generated for  {yr} years.',
                                            'Forecast for dropout rate  class: {s_col}  generated for  {yr}   .\n   ON:' || TO_VARCHAR(CURRENT_TIMESTAMP()) || 
                                            'Hurryyyy!! :) '
                                             )'''
                execute_query(LOAD_Q)
                st.success(f'Forecast for dropout rate  class: {s_col}  generated for  {yr} Years also email sent')
                Q2=f''' SELECT * FROM SF_ACTUAL_FORECAST_{s_col} '''
                R2 = execute_query(Q2)
                R2_DF = pd.DataFrame(R2)
                R2_DF.index = R2_DF.index + 1
                r2_expander = st.expander(f'Atual and forcast drop out rate generated for {s_col} Years ')
                r2_expander.write(R2_DF)
            except Exception as e:
                    st.error(f'Error: {str(e)}')

            title=f'''Actual and Forecast dropout rate for  class: {s_col}  for  {yr} Years. After 2010 all are predicted'''
            def plot_chart(data, x_axis, y_axes):
                selected_columns = [x_axis] + y_axes
                melted_data = data.melt('YEAR', value_vars=y_axes, var_name='CATEGORY')
                
                chart = alt.Chart(melted_data).mark_line(point=True).encode(
                    x=alt.X('YEAR:N', title=title),
                    y=alt.Y('value:Q', title='DROPOUT_RATE'),
                    color='CATEGORY:N',
                    tooltip=['YEAR:N', alt.Tooltip('value:Q', title='DROPOUT_RATE', format='.2f'), 'CATEGORY:N']
                ).properties(
                    width=600,
                    height=400
                ).configure_legend(
                orient='left',
                title=None,
                labelFontSize=10
                ).configure_axis(grid=False).interactive()
                return chart

            x_axis_column ='YEAR'
            y_axis_columns =st.multiselect('Select Y-axis', options=list(R2_DF.columns)[1:], default=list(R2_DF.columns)[1:])#[list(R2_DF.columns)[1]])

            # Plotting the chart with multiple Y-axis columns
            st.altair_chart(plot_chart(R2_DF, x_axis_column, y_axis_columns), use_container_width=True)

    st.divider()
    st.title("Future Drop out rates in India from 2011 to 2040")
    Q2_F='''SELECT * FROM DRR_FORECAST_FROM_2011_2040'''
    R2_F = execute_query(Q2_F)
    r2_f_expander = st.expander("Data set used in this  analysis")
    R2_F_DF = pd.DataFrame(R2_F)
    R2_F_DF.index = R2_F_DF.index + 1
    r2_f_expander.write(R2_F_DF)
    st.write('Year-wise drop out rate for all categories')

    # Creating the chart with multiple Y-axis columns
    def plot_chart(data, x_axis, y_axes):
        selected_columns = [x_axis] + y_axes
        melted_data = data.melt('YEAR', value_vars=y_axes, var_name='CATEGORY')
        
        chart = alt.Chart(melted_data).mark_line(point=True).encode(
            x=alt.X('YEAR:N', title='YEAR'),
            y=alt.Y('value:Q', title='DROPOUT_RATE'),
            color='CATEGORY:N',
            tooltip=['YEAR:N', alt.Tooltip('value:Q', title='DROPOUT_RATE', format='.2f'), 'CATEGORY:N']
        ).properties(
            width=600,
            height=400
        ).configure_legend(
        orient='left',
        title=None,
        labelFontSize=9
        ).configure_axis(grid=False).interactive()
        return chart
    # Selecting X-axis (Year) and multiple Y-axis columns with 'GIRL' keyword
    girl_columns = [col for col in R2_F_DF.columns if 'GIRLS' in col]
    default_selection = girl_columns if girl_columns else [list(R2_F_DF.columns)[1]]  # If 'GIRL' columns exist, use them as default, else use the first column
    # Selecting X-axis (Year) and multiple Y-axis columns
    x_axis_column ='YEAR'
    y_axis_columns = st.multiselect('Select Y-axis (Categories)', options=list(R2_F_DF.columns)[1:], default=default_selection)#[list(R2_DF.columns)[1]])

    # Plotting the chart with multiple Y-axis columns
    st.altair_chart(plot_chart(R2_F_DF, x_axis_column, y_axis_columns), use_container_width=True)
    f_expander= st.expander("Complete Insights/Recommendations for  classwise girls per hundred boys")
    f_expander.markdown('''
        **Data Insights:**

        1. **Decreasing Dropout Rates:** There has been a consistent decline in dropout rates across all categories from 2012 to 2040, indicating an improvement in educational opportunities and access to quality education.

        2. **Gender Disparity:** While both boys and girls have experienced a decrease in dropout rates, girls consistently have lower dropout rates compared to boys. This suggests progress towards gender equality in education.

        3. **Socio-Economic Status Impact:** Students from socio-economically disadvantaged backgrounds, including Scheduled Castes (SC), Scheduled Tribes (ST), and economically weaker sections, have higher dropout rates compared to their more affluent peers. Addressing socio-economic disparities is crucial for reducing dropout rates further.

        4. **Class-Wise Trends:** Dropout rates seem to be higher in the earlier grades (I-V) compared to later grades (I-X), indicating a need for focused interventions to support students during their initial years of schooling.

        5. **Need for Continued Improvement:** While dropout rates are decreasing, there is still room for further improvement. By addressing factors such as access to quality education, socio-economic disparities, and student support systems, dropout rates can be reduced even further.

        **Recommendations:**

        1. **Targeted Interventions:** Implement targeted interventions to address the needs of students from socio-economically disadvantaged backgrounds, including SC, ST, and economically weaker sections, to help them stay in school and succeed.

        2. **Early Childhood Education:** Focus on early childhood education programs to provide a strong foundation and reduce the risk of students dropping out later in their schooling.

        3. **Quality Education:** Invest in improving the quality of education, including teacher training, curriculum development, and infrastructure upgrades, to make schools more attractive and engaging for students.

        4. **Counseling and Support Services:** Provide counseling and support services to students facing challenges, such as poverty, family issues, or learning difficulties, to help them overcome these obstacles and stay in school.

        5. **Community Involvement:** Engage parents, communities, and local organizations in efforts to reduce dropout rates by promoting the importance of education and providing support to students and their families.

        6. **Policy Reviews:** Conduct regular reviews of education policies and programs to identify areas where improvements can be made to further reduce dropout rates and ensure equitable access to quality education for all students. 
    ''')

if __name__ == '__main__':
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
