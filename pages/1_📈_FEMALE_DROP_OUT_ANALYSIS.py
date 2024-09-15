import streamlit as st
import snowflake.connector
import pandas as pd
import plotly.express as px
import altair as alt






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

st.title('DROP OUT ANALYSIS ')


def main():

    Q1='''SELECT table_name, ALL_COLUMNS, COMMENTS
         FROM T01_METADAT_IND_SCHEMA WHERE table_name LIKE 'DRR_%'
        ORDER BY table_name'''
    R1 = execute_query(Q1)
    r1_expander = st.expander("Data sets used in this entire analysis.")
    R1_DF = pd.DataFrame(R1)
    R1_DF.index = R1_DF.index + 1
    r1_expander.write(R1_DF)
    st.divider()
    st.title("1.Drop out rates in India from 1960-61 to 2010-11")
    Q2='''SELECT * FROM V01_DRR_1960_TO_2011'''
    R2 = execute_query(Q2)
    r2_expander = st.expander("Data set used in this  analysis")
    R2_DF = pd.DataFrame(R2)
    R2_DF.index = R2_DF.index + 1
    r2_expander.write(R2_DF)
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
    girl_columns = [col for col in R2_DF.columns if 'GIRLS' in col]
    default_selection = girl_columns if girl_columns else [list(R2_DF.columns)[1]]  # If 'GIRL' columns exist, use them as default, else use the first column
    # Selecting X-axis (Year) and multiple Y-axis columns
    x_axis_column ='YEAR'
    y_axis_columns = st.multiselect('Select Y-axis (Categories)', options=list(R2_DF.columns)[1:], default=default_selection)#[list(R2_DF.columns)[1]])

    # Plotting the chart with multiple Y-axis columns
    st.altair_chart(plot_chart(R2_DF, x_axis_column, y_axis_columns), use_container_width=True)
    r2_expander_1 = st.expander("Insights from School Dropouts (1960-2011)")

    r2_expander_1.markdown("""
    ### Insights:

    1. **Declining Dropout Rates Over Time:**
    - The dropout rates for primary education (I-V) have gradually decreased from approximately 64.9% in 1960-61 to around 27.4% in 2010-11.
    - Similar declining trends are observed across other educational levels (I-VIII, I-X), indicating an overall improvement in student retention over the years.

    2. **Gender Disparities in Dropout Rates:**
    - Historically, dropout rates for girls across all educational levels were slightly higher compared to boys.
    - However, over time, this gap has narrowed significantly, showcasing a positive trend towards gender parity in educational retention.

    3. **Socioeconomic Impact on Dropout Rates:**
    - Students from Scheduled Castes (SC) and Scheduled Tribes (ST) communities experienced higher dropout rates compared to the general population.
    - The dropout rates for SC/ST students were consistently higher across all educational levels compared to non-SC/ST students, indicating an existing educational disparity.

    4. **Impact of Education Level on Dropout Rates:**
    - The dropout rates notably increase as the education level progresses. For instance, dropout rates for I-X are significantly higher than those for I-V.
    - This trend suggests that students tend to be more susceptible to dropping out as they advance to higher classes.

    5. **Fluctuations in Dropout Rates:**
    - Throughout the years, certain periods exhibit fluctuations in dropout rates, indicating potential external factors influencing student retention, such as economic conditions, policies, or social changes.

    6. **Regional Disparities:**
    - Regional disparities in dropout rates are noticeable, with certain states or regions consistently showing higher or lower dropout rates compared to the national average.
    - Variances among states may signify differences in educational infrastructure, socio-economic factors, or cultural influences impacting dropout rates.

    ### Summary:
    The analysis of the dataset on school dropouts from 1960 to 2011 indicates an overall positive trend in reducing dropout rates across various educational levels. However, persistent disparities related to gender, socioeconomic backgrounds, educational levels, and regional influences emphasize the need for targeted interventions and policies to ensure equitable access to education and reduce dropout rates further.

    """)
    st.divider()
    st.title("2.Drop-out Rate from 2009 TO 2012 state wise class wise for different category")

    col1, col2, col3 = st.columns(3)
    with col1:
        top_options = list(range(1, 31))  # Generates a list from 1 to 30
        top = st.selectbox('Select top dropout:', options=top_options, index=9)
    with col2:
        s_year_options = [2009, 2010, 2011, 2012]
        s_year = st.selectbox('Select which year:', options=s_year_options, index=0)
    with col3:
        s_col_options = [
        "I-V BOYS", "I-V GIRLS", "I-V TOTAL", "I-VIII BOYS", "I-VIII GIRLS", "I-VIII TOTAL",
        "I-X BOYS", "I-X GIRLS", "I-X TOTAL", "SC I-V BOYS", "SC I-V GIRLS", "SC I-V TOTAL",
        "SC I-VIII BOYS", "SC I-VIII GIRLS", "SC I-VIII TOTAL", "SC I-X BOYS", "SC I-X GIRLS",
        "SC I-X TOTAL", "ST I-V BOYS", "ST I-V GIRLS", "ST I-V TOTAL", "ST I-VIII BOYS",
        "ST I-VIII GIRLS", "ST I-VIII TOTAL", "ST I-X BOYS", "ST I-X GIRLS", "ST I-X TOTAL"
        ] 
        s_col_index = s_col_options.index("SC I-X GIRLS")  # Find the index of the default value
        s_col = st.selectbox('Select class:', options=s_col_options, index=s_col_index)
  
    Q3 = f'''WITH CTE AS 
        (SELECT STATES, YEAR, ROUND(IFNULL(TRY_TO_DOUBLE("{s_col}"), 0), 2) AS DROP_OUT_RATE, 
            DENSE_RANK() OVER (PARTITION BY YEAR ORDER BY DROP_OUT_RATE DESC) DNK 
            FROM V01_DRR_STATEWISE_CLASSWISE_2009_2012)
            SELECT CTE.STATES,CTE.YEAR,CTE.DROP_OUT_RATE , CTE.DNK RANK FROM CTE WHERE YEAR = {s_year} AND DNK <= {top}'''
    R3 = execute_query(Q3)
    #AS "{s_col}"
    r3_expander = st.expander("Data sets used in this analysis")
    R3_DF = pd.DataFrame(R3)
    R3_DF.index = R3_DF.index + 1
    r3_expander.write(R3_DF)
    R3_DF = R3_DF.sort_values(by="DROP_OUT_RATE", ascending=False)
    selected_items = f"Top  {top} dropout states of the Year: {s_year} for Class: {s_col}"
    # Creating the Altair chart
    chart = (
        alt.Chart(R3_DF)
        .mark_bar()
        .encode(
            x=alt.X("DROP_OUT_RATE:Q", title="  Dropout Rate"),
            y=alt.Y("STATES:N", title="States", sort="-x"),
            tooltip=[
            alt.Tooltip("STATES", title="State"),
            alt.Tooltip("DROP_OUT_RATE", title="Dropout Rate"),
            ]
        )
        .properties(width=900,  title=f"{selected_items}")
        .interactive()
    )

    # Displaying the chart using Streamlit
    st.altair_chart(chart, use_container_width=True)
    st.markdown("""---------------------------------""")
    st.title("3. Drop-out Rate for selected state and classes across 2009 TO 2012")

    # Select state and display dataset used in the analysis
    s_states_options = pd.DataFrame(execute_query('SELECT DISTINCT STATES FROM V01_DRR_STATEWISE_CLASSWISE_2009_2012'))
    s_states_col = st.selectbox('Select state:', options=s_states_options['STATES'].tolist())
    Q4 = f"SELECT * FROM V01_DRR_STATEWISE_CLASSWISE_2009_2012 WHERE STATES = '{s_states_col}'"
    R4 = execute_query(Q4)
    r4_expander = st.expander("Data sets used in this analysis")
    R4_DF = pd.DataFrame(R4)
    R4_DF.index = R4_DF.index + 1
    r4_expander.write(R4_DF)

    # Select categories
    selected_categories = st.multiselect('Select categories:', options=(R4_DF.columns)[2:],default=["I-V BOYS","I-V GIRLS"])

    # Filter data based on selected state and categories
    filtered_data = R4_DF[['YEAR', 'STATES'] + selected_categories]
    filtered_data = filtered_data[filtered_data['STATES'] == s_states_col]

    # Melt the DataFrame for visualization
    melted_df = filtered_data.melt(id_vars=['YEAR', 'STATES'], var_name='Category', value_name='Dropout Rate')
    r4_title = f"Dropout Rates for {', '.join(selected_categories)} in {s_states_col}"

    # Line chart using Altair
    line_chart = (
        alt.Chart(melted_df)
        .mark_line(point=True)
        .encode(
            x='YEAR:N',
            y=alt.Y('Dropout Rate:Q', title='Dropout Rate'),
            color='Category:N',
            tooltip=['YEAR:N', 'STATES:N', 'Category:N', 'Dropout Rate:Q']
        )
        .properties( title=r4_title)
        .configure_legend(
        orient='left',
        title=None,
        labelFontSize=9)
        .interactive()
    )

    # Display the chart using Streamlit
    st.altair_chart(line_chart, use_container_width=True)
    st.markdown("""---------------------------------""")

    dropout_expander= st.expander("Complete insights for School Dropouts")
    dropout_expander.markdown('''
    # Insights on Girls' Dropout Rates

    ## Gender Disparity:

    - **Higher Education Levels:** In several states, particularly in higher education levels (I-VIII, I-X), girls tend to exhibit higher dropout rates compared to boys during the specified period.

    ## State-wise Disparities:

    - **Bihar, Rajasthan, and Uttar Pradesh:** These states consistently demonstrate higher dropout rates among girls across various education levels, highlighting persistent challenges in retaining girls in schools.

    ## Regional Variances:

    - **Southern States:** States like Kerala and Tamil Nadu generally exhibit lower dropout rates among girls, especially in higher education levels, indicating better educational retention for girls in these regions.

    ## Year-wise Changes:

    - **2012 Increase:** Some states witness a slight increase in girls' dropout rates in 2012, especially noticeable in higher education levels, suggesting a potential challenge or trend that needs attention.

    ## Scheduled Castes and Tribes:

    - **Disparity Within Groups:** Within Scheduled Castes (SC) and Scheduled Tribes (ST), there are variations in dropout rates among girls across different states, emphasizing the need for targeted interventions within these communities.

    ## Efforts and Implications:

    - **Policy Impact:** States with lower dropout rates among girls might have implemented successful policies or programs promoting girls' education and retention.

    These insights underscore the importance of addressing the specific challenges faced by girls in continuing their education across different states and education levels. Policy measures focusing on girls' education, socio-economic support, and community engagement could help mitigate the disparities and improve retention rates among girls, thereby fostering a more inclusive and equitable educational landscape.
    ''')

    Recommendation_expander= st.expander("Recommendations to decrese School Dropouts")
    Recommendation_expander.markdown('''
        # Global Level:
        ## Advocacy and Support:

        - **Campaigns and Advocacy:** Collaborate with international organizations and NGOs to launch global campaigns advocating for girls' education, emphasizing its crucial role in societal development.
        - **Financial Support:** Allocate funding and resources to support educational programs targeting girls in developing countries.

        ## Knowledge Sharing and Collaboration:

        - **Data Sharing:** Encourage countries to share their dropout rate data to identify global trends and best practices.
        - **Collaborative Research:** Foster collaborations among research institutions globally to understand the underlying causes and solutions for girls' dropout rates.

        # National Level:

        ## Policy Implementation and Reform:

        - **Policy Review:** Conduct regular reviews of education policies to ensure they address the specific challenges faced by girls in education.
        - **Incentives and Scholarships:** Offer scholarships and incentives specifically targeting girls to encourage their continuous education.

        ## Community Engagement:

        - **Awareness Programs:** Launch nationwide awareness campaigns to emphasize the importance of girls' education and combat societal norms that discourage girls from pursuing education.
        - **Parental Involvement:** Engage parents and local communities to highlight the benefits of educating girls and involve them in promoting girls' education.

        # State Level:

        ## Targeted Interventions:

        - **State-specific Programs:** Develop state-specific programs addressing the unique challenges faced by girls in each region.
        - **Resource Allocation:** Allocate resources towards improving infrastructure, teacher training, and educational materials targeting girls' education.

        ## Data-Driven Strategies:

        - **Data Monitoring:** Implement systems to continuously monitor dropout rates among girls, enabling timely intervention and adjustment of strategies.
        - **Local Partnerships:** Collaborate with local NGOs and community leaders to implement grassroots initiatives addressing girls' dropout issues.

        ## Gender-Sensitive Curriculum:

        - **Curriculum Revision:** Develop a gender-sensitive curriculum that fosters inclusivity and encourages girls' participation in various subjects and extracurricular activities.

        By implementing these recommendations at different levels—global, national, and state—agencies can work towards reducing girls' dropout rates, promoting gender equality in education, and creating an environment where girls feel empowered to pursue their education to higher levels. ''')

            

 

                    
if __name__ == "__main__":
    main()


st.markdown(
    '''
    <style>
    .streamlit-expanderHeader {
        background-color: blue;
        color: white; # Adjust this for expander header color
    }
    .streamlit-expanderContent {
        background-color: blue;
        color: white; # Expander content color
    }
    </style>
    ''',
    unsafe_allow_html=True
)

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
