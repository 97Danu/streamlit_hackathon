import streamlit as st
import snowflake.connector
import pandas as pd
# import matplotlib.pyplot as plt
import plotly.express as px
import altair as alt
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

st.title('📊 CLASSWISE GIRLS PER HUNDRED BOYS ')


def main():

    Q1='''SELECT table_name, ALL_COLUMNS, COMMENTS
         FROM T01_METADAT_IND_SCHEMA WHERE table_name LIKE  'GIRLS_PER_%'
         ORDER BY table_name
        '''
    R1 = execute_query(Q1)
    r1_expander = st.expander("Data sets used in this entire analysis")
    R1_DF = pd.DataFrame(R1)
    R1_DF.index = R1_DF.index + 1
    r1_expander.write(R1_DF)
    st.divider()
    st.title("1.Classwise girls per hundred boys in entire india from 2008 to 2012")
    Q2='''    SELECT * exclude STATES  FROM V01_GIRLS_PER_100_2008_2012
            where STATES='INDIA'
            ORDER BY 1'''
    R2 = execute_query(Q2)
    r2_expander = st.expander("Data set used in this  analysis")
    R2_DF = pd.DataFrame(R2)
    R2_DF.index = R2_DF.index + 1
    r2_expander.write(R2_DF)

    # Multi-select for selecting Categories with default all selected
    selected_categories = st.multiselect('Select Categories', R2_DF['CATEGORY'].unique(), default=list(R2_DF['CATEGORY'].unique()))

    # Select for choosing a single class
    selected_class = st.selectbox('Select Class', R2_DF.columns[2:], index=0)

    # Filter data based on selected categories
    filtered_data = R2_DF[R2_DF['CATEGORY'].isin(selected_categories)]

    # Filter data based on selected class
    filtered_data = filtered_data[['YEAR', 'CATEGORY', selected_class]]

    # Melt the DataFrame for visualization
    filtered_data_melted = pd.melt(filtered_data, id_vars=['YEAR', 'CATEGORY'], value_vars=[selected_class], var_name='Class', value_name='Girls per Hundred Boys')

    # Line Chart Visualization with points
    st.subheader(f'Girls per Hundred Boys in {selected_class}')

    line_chart = alt.Chart(filtered_data_melted).mark_line(point=True).encode(
        x=alt.X('YEAR:O', axis=alt.Axis(format='d'), title='Year'),
        y='Girls per Hundred Boys',
        color='CATEGORY',
        tooltip=['YEAR', 'Girls per Hundred Boys']
    ).properties(
        width=900
    ).interactive()

    st.altair_chart(line_chart)

    # Insights in Markdown
    st.markdown('## Insights')
    st.markdown('- **Disparity Among Categories**: Selecting multiple categories shows varying trends in gender disparity across different educational categories.')
    st.markdown('- **Temporal Variations**: Over the years, fluctuations in the ratio of girls per hundred boys are observed among the selected categories.')
    st.markdown(f'- **Classwise Trends in {selected_class}**: Displays the gender ratio in the chosen class across different categories.')

    st.divider()
    st.title("2.Classwise girls per hundred boys in states from 2008 to 2012 across different catergory")
    
    col5,col6=st.columns(2)
    with col5:
        q3_states_options = pd.DataFrame(execute_query('SELECT DISTINCT STATES FROM V01_GIRLS_PER_100_2008_2012'))
        q3_selected_state = st.selectbox('Select State', q3_states_options, index=5)
    with col6:
        q3_category_options=["SC","ST","ALL_CAT"]
        q3_category_index = q3_category_options.index("ALL_CAT")
        q3_selected_category = st.selectbox('Select Category', q3_category_options, q3_category_index)
    q3_title=f' Classwise girls per hundred boys in State: {q3_selected_state} and category: {q3_selected_category} '
    
    Q3=f'''WITH CTE
            AS
            (
            SELECT * FROM V01_GIRLS_PER_100_2008_2012
            where STATES= '{q3_selected_state}' and CATEGORY= '{q3_selected_category}' )
            SELECT *  FROM CTE'''
    R3 = execute_query(Q3)
    r3_expander = st.expander("Data set used in this  analysis")
    R3_DF = pd.DataFrame(R3)
    R3_DF.index = R3_DF.index + 1
    r3_expander.write(R3_DF)

    def plot_chart(data, x_axis, y_axes):
        selected_columns = [x_axis] + y_axes
        melted_data = data.melt('YEAR', value_vars=y_axes, var_name='CATEGORY')
        
        chart = alt.Chart(melted_data).mark_line(point=True).encode(
            x=alt.X('YEAR:N', title='YEAR',axis=alt.Axis(grid=True)),
            y=alt.Y('value:Q', title=f'State {q3_selected_state} category: {q3_selected_category} ', axis=alt.Axis(grid=True)),
            color='CATEGORY:N',
            tooltip=['YEAR:N', alt.Tooltip('value:Q', title='girls per hundred', format='d'), 'CATEGORY:N']
        ).properties(
            width=600,
            height=400
        ).configure_legend(
        orient='left',
        title=None,
        labelFontSize=9
        ).configure_axis(grid=False).interactive()
        return chart

    class_columns = [col for col in R3_DF.columns if 'CLASSES' in col]
    default_selection = class_columns if class_columns else [list(R3_DF.columns)[1]]  
    # Selecting X-axis (Year) and multiple Y-axis columns
    x_axis_column ='YEAR'
    y_axis_columns = st.multiselect('Select Y-axis (Categories)', options=list(R3_DF.columns)[1:], default=default_selection)

    # Plotting the chart with multiple Y-axis columns
    st.altair_chart(plot_chart(R3_DF, x_axis_column, y_axis_columns), use_container_width=True)   


    g_per_expander= st.expander("Complete Insights/Recommendations for  classwise girls per hundred boys")
    g_per_expander.markdown('''  
    1. **Significant Variations in Gender Ratio Across States:**
        - Some states like Kerala, Himachal Pradesh, and Tamil Nadu have consistently shown high gender ratios in favor of females across all years and categories, while others like Rajasthan, Bihar, and Jharkhand have consistently low ratios.

    2. **Urban-Rural Divide:**
        - In most states, urban areas tend to have lower gender ratios compared to rural areas. This is evident in states like Andhra Pradesh, Gujarat, and Maharashtra, where the gender ratio in urban areas is lower than in rural areas for all years and categories.

    3. **Increasing Trend of Gender Ratios Over Time:**
        - In many states, the gender ratio has shown a gradual increase over the years, indicating a positive trend towards bridging the gender gap. This is particularly noticeable in states like Andhra Pradesh, Assam, and Odisha.

    4. **Wide Disparities in Gender Ratios Among Different Categories:**
        - Scheduled Tribes (ST) consistently have the lowest gender ratios compared to other categories (ALL_CAT, SC, and General) in almost all states and years. This disparity highlights the need for targeted interventions to address the specific challenges faced by tribal communities.

    5. **Fluctuations in Gender Ratios:**
        - While some states show a consistent pattern, others exhibit fluctuations in gender ratios over the years. These fluctuations may be influenced by various factors such as changes in policies, socio-economic conditions, and cultural norms.

    6. **Need for Continued Efforts:**
        - Despite the progress made in improving gender ratios, there is still a significant gap between the number of girls and boys in many states, particularly in certain categories and regions. This underscores the need for continued efforts and targeted interventions to achieve gender equality and bridge the gender divide.

    Somemore insights
     1. **Overall Increase in Girls per Hundred Boys:** From 2008 to 2012, there was a general upward trend in the number of girls per hundred boys in the entire nation, indicating a positive shift in the gender ratio.


    2. **Regional Variations:** Different States in India exhibited varying trends in the girl-boy ratio. Some States showed a consistent increase, while others displayed fluctuations over the years.


    3. **Southern and North-eastern Dominance:** Southern States like Kerala and Tamil Nadu and several North-eastern States like Meghalaya and Nagaland consistently maintained a high girl-boy ratio throughout the period, indicating better gender equality in these regions.


    4. **Low Ratios in Northern States:** Some States in the northern region, such as Bihar and Rajasthan, experienced persistently low girl-boy ratios, highlighting the need for focused efforts to address gender disparity.


    5. **Urban-Rural Divide:** The data indicated that urban areas generally had higher girl-boy ratios compared to rural areas, suggesting a possible correlation between access to education, healthcare, and overall development.


    6. **Steady Improvement in Class IX-X:** The ratio of girls to boys in classes IX-X showed a steady increase from 2008 to 2012, implying an encouraging trend towards higher secondary education for girls.


    7. **Socio-economic Factors:** States with better socio-economic conditions and higher literacy rates often exhibited higher girl-boy ratios, suggesting a link between socio-economic factors and gender equality.


    8. **Government Interventions:** The analysis suggests that government initiatives and policies aimed at promoting gender equality, such as the Beti Bachao Beti Padhao program, may have contributed to the gradual improvement in the girl-boy ratio.


    9. **Inter-state Variations in SC, ST, and General Categories:** The data revealed considerable variations in the girl-boy ratio among different social categories (SC, ST, and General) across States, indicating the need for targeted interventions to address specific challenges faced by these groups.


    10. **Shifts in Class-wise Ratios:** Over the years, there were noticeable shifts in the girl-boy ratio across different classes, indicating changes in enrolment and retention patterns at various stages of schooling.
    
    ### RECOMMENDATIONS TO IMPROVE THE GENDER RATIO

    
     1. **Encouraging Girls to Pursue Education:**
   - Implement targeted programs and initiatives to promote the importance of education among girls, highlighting the benefits and opportunities it offers for their future.
   - Provide accessible and affordable education for girls by addressing financial barriers through scholarships, stipends, and fee waivers.
   - Support and empower parents and communities to recognize the value of education for girls and break down cultural stereotypes that may discourage their enrollment and retention.
   - Train teachers and educators to create inclusive and gender-sensitive learning environments that encourage girls' participation and address their specific needs.


    2. **Addressing Infrastructure and Safety Issues:**
    - Improve the infrastructure of schools and educational institutions, ensuring safe, clean, and well-maintained facilities that provide a conducive learning environment for girls.
    - Enhance security measures and implement measures to prevent gender-based violence, harassment, and discrimination within educational settings.
    - Ensure adequate sanitation facilities and menstrual hygiene management infrastructure to address the unique needs of girls and reduce absenteeism.


    3. **Strengthening the Quality of Education:**
    - Develop and implement gender-responsive curricula that challenge gender stereotypes, promote gender equality, and encourage girls' participation in all subjects, including STEM (Science, Technology, Engineering, and Mathematics) fields.
    - Provide quality teacher training programs that equip educators with the skills and knowledge necessary to effectively teach and support girls, addressing their specific needs and learning styles.
    - Promote inclusive teaching methodologies and assessment practices that encourage active participation, critical thinking, and collaboration among students, creating a positive learning environment for girls.


    4. **Enhancing Career Guidance and Opportunities:**
    - Provide career counseling and guidance services to girls at all levels of education, helping them explore different career options, understand their interests and strengths, and develop the skills necessary for success.
    - Collaborate with industries and businesses to create internship and apprenticeship opportunities specifically designed for girls, exposing them to various fields and potential career paths.
    - Encourage girls to pursue higher education and postgraduate studies by providing financial assistance, mentorship programs, and support networks.


    5. **Engaging Communities and Stakeholders:**
    - Involve parents, community leaders, and civil society organizations in the effort to improve girls' education, fostering a supportive environment and promoting collective action.
    - Conduct awareness campaigns and community dialogue to challenge gender stereotypes, address social norms, and encourage families to prioritize the education of their daughters.
    - Collaborate with local governments and policymakers to advocate for policies and initiatives that promote gender equality in education, ensuring equitable access and opportunities for girls.


    6. **Monitoring and Evaluation:**
    - Establish a robust monitoring and evaluation framework to track progress, identify challenges, and measure the impact of interventions aimed at improving girls' education.
    - Collect and analyze data on enrollment, retention, completion rates, and learning outcomes for girls, disaggregated by gender, to inform policy decisions and targeted interventions.
    - Regularly review and update policies, programs, and strategies based on evidence and emerging trends, ensuring they remain responsive to the evolving needs and challenges of girls' education.
    
    ''' )

    
    st.divider()
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
