import streamlit as st
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from pathlib import Path
import time
import pandas as pd
# from st_pages import Page, add_page_title, show_pages
from PIL import Image
from io import BytesIO
import requests 


st.set_page_config(
  page_title="INDIAN-FEMALE-EDUCATION-INSIGHTS",
  page_icon="🏠",
  layout="wide",
  initial_sidebar_state="expanded",
) 

# show_pages(
#           [
#               Page("0_Home.py", "START FORM HERE", "🏠"),
#               Page("pages/1_📈_FEMALE_DROP_OUT_ANALYSIS.py", "FEMALE DROP OUT ANALYSIS", "📈"),
#               Page("pages/2_🌍_CLASS_&_AGEWISE_ENROLLMENT_TO_SCHOOLS.py", "CLASSWISE & AGEWISE ENROLLMENT TO SCHOOLS", "🌍"),
#               Page("pages/3_📊_SCHOOLS_INFRA_STATISTICS.py", "SCHOOL'S INFRA STATISTICS", "📈"),
# 			  Page("pages/4_📊_ALL_INDIA_SURVEY_ON_HIGHER_EDUCATION.py", "ALL INDIA SURVEY ON HIGHER EDUCATION", "📈"),
#               Page("pages/5_📊_CLASSWISE_GIRLS_PER_HUNDRED_BOYS.py", "CLASS-WISE GIRLS PER HUNDRED BOYS", "📈"),
# 			  Page("pages/6_📊_INDIAN_EDUCATION_FORECASTS.py", "INDIAN EDUCATION FORECASTS", "📈"),
#           ]
#       )  
# add_page_title()
# Function to store Snowflake credentials in session state

def display_image_from_github(url,caption):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    st.image(img, caption=caption)


def store_credentials(account, role, warehouse, database, schema, user, password):
    st.session_state.account = account
    st.session_state.role = role
    st.session_state.warehouse = warehouse
    st.session_state.database = database
    st.session_state.schema = schema
    st.session_state.user = user
    st.session_state.password = password

# Function to connect to Snowflake
# @st.cache    
# Create a Snowflake connection function
def create_snowflake_connection(account, role, warehouse, database, schema, user, password):
    try:
        conn = snowflake.connector.connect(
            account=account,
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema,
            user=user,
            password=password,
            client_session_keep_alive=True
        )
        st.toast("Connection to Snowflake successfully!", icon='🎉')
        time.sleep(.5)
        st.balloons()
    except Exception as e:
        st.error(f"Error connecting to Snowflake: {str(e)}")    
    return conn

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

with st.sidebar:
    st.markdown("[![Foo](https://cdn2.iconfinder.com/data/icons/social-media-2285/512/1_Linkedin_unofficial_colored_svg-48.png)](https://www.linkedin.com/in/danammahiremath/) Connect me.")
    # st.sidebar.header("Snowflake Credentials")
    # expander = st.expander("Set Up SF Connection")
    account = st.secrets.db_credentials.account # expander.text_input('Acount','qa07240.ap-southeast-1')
    role = st.secrets.db_credentials.role #expander.text_input('Role','ACCOUNTADMIN')
    warehouse = st.secrets.db_credentials.warehouse # expander.text_input('Warehouse','COMPUTE_WH')
    database = st.secrets.db_credentials.database # expander.text_input('Database','IND_DATA')
    schema = st.secrets.db_credentials.schema # expander.text_input('Schema','IND_SCHEMA')
    user = st.secrets.db_credentials.user #expander.text_input('User','Hackathon')
    password = st.secrets.db_credentials.password #expander.text_input("Password", type="password")
    client_session_keep_alive = st.secrets.db_credentials.client_session_keep_alive
    # if expander.button("Connect"):
    store_credentials(account, role, warehouse, database, schema, user, password)
    # connection = create_snowflake_connection(account, role, warehouse, database, schema, user, password)


st.title('❄️ WELCOME TO INDIAN-FEMALE-EDUCATION-INSIGHTS APP ❄️')
image_url = "https://github.com/97Danu/streamlit_hackathon/raw/main/src/Application_Flow.jpg"
caption='APP FLOW'
display_image_from_github(image_url,caption)


def main(): 
                st.title('Detail steps how analysis done')

                st.markdown('STEP 1:DATA DOWNLOADED FROM data.gov.in IN CSV FORMAT')

                st.markdown('STEP 2:DATASET DOWNLOADED AND LOADED TO SNOWFLAKE USING MY OWN CREATED UTILITY')
                st.markdown('130+ data set loaded and analysed')
                tbl_url = "https://github.com/97Danu/streamlit_hackathon/raw/main/src/TBLS_CNT.jpg"
                tbl_caption='Datasets loaded and analysed'
                display_image_from_github(tbl_url,tbl_caption)

                Q1='''SELECT distinct table_name,COMMENTS
                            FROM T01_METADAT_IND_SCHEMA C
                           
                            WHERE  COMMENTS is not null
                            ORDER BY table_name'''
                R1 = execute_query(Q1)
                r1_expander = st.expander("Main Tables used in this entire analysis.")
                R1_DF = pd.DataFrame(R1)
                R1_DF.index = R1_DF.index + 1
                r1_expander.write(R1_DF)

                
                st.markdown('Upload file to Snowflake')
                file = st.file_uploader('Upload file', type=['xls', 'xlsx', 'csv', 'txt'])

                if file is not None:
                    # Read the file
                    file_extension = file.name.split('.')[-1]
                    if file_extension.lower() in ['xls', 'xlsx', 'csv', 'txt']:
                        data = pd.read_excel(file) if file_extension.lower() in ['xls', 'xlsx'] else pd.read_csv(file, encoding='latin-1')

                        st.subheader('Preview of Uploaded Data')
                        st.write(data.head())

                        # Save data to Snowflake
                        conn = create_snowflake_connection(account, role, warehouse, database, schema, user, password)
                        if conn:
                            st.info('Connected to Snowflake!')

                            table_name = st.text_input('Enter table name in Snowflake')

                            if st.button('Save to Snowflake'):
                                try:
                                    data_f=pd.DataFrame(data)
                                    success, nchunks, nrows, _ = write_pandas(conn=conn,df=data_f,table_name=table_name,database=database,schema=schema,auto_create_table=True)
                                    LOAD_Q=f'''call system$send_email(
                                            'SF_Email_Notifications',
                                            'danuhiremath123@gmail.com',
                                            '[SF_Email_Notifications]:Email Alert: file loading finished.',
                                            'File has successfully loaded to table {table_name}   .\n   ON:' || TO_VARCHAR(CURRENT_TIMESTAMP()) || 
                                            'Total Records loaded: {nrows} '
                                             )'''
                                    execute_query(LOAD_Q)
                                    st.success(f'Dataloaded to snowflake table: {table_name}  rows : {nrows} also email sent')
                                except Exception as e:
                                    st.error(f'Error: {str(e)}')
                        else:
                            st.error('Unable to connect to Snowflake. Please check your credentials.')
                st.markdown('STEP 3:COMPLEX  VIEWS CREATED AND SQLS USED TO DO ANALYSIS ')
                st.markdown('STEP 4:All PAGES DEVELOPED ')

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
