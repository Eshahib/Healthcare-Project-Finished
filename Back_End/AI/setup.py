import google.generativeai as genai
import os
import pandas as pd
from dotenv import load_dotenv
import kagglehub
from processing import clean_data, format_data, prep_RAG, retrieve_context, generate_answer, process_query
# Load environment variables from .env file
load_dotenv()
# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is not set. Please create a .env file with GEMINI_API_KEY=your-api-key or set it as an environment variable.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

path = kagglehub.dataset_download("dantecady/comprehensive-disease-profiles-dataset")
filepath = os.path.join(path, "disease_dataset.xlsx")

df = pd.read_excel(filepath, header=None)

#clean and format data for disease_dataset
index_name_disease_dataset = "disease_name"
column_mapping_disease_dataset = {
    1: 'alt_name',
    2: 'description',
    3: 'symptom_1',
    4: 'symptom_2',
    5: 'symptom_3',
    6: 'symptom_4',
    7: 'symptom_5',
    8: 'cause_1',
    9: 'cause_2',
    10: 'cause_3',
    11: 'cause_4',
    12: 'cause_5',
    13: 'treatment_1',
    14: 'treatment_2',
    15: 'treatment_3',
    16: 'treatment_4',
    17: 'treatment_5',
    18: 'treatment_6',
    19: 'prognosis',
    20: 'severity',
    21: 'diagnosis_1',
    22: 'diagnosis_2',
    23: 'diagnosis_3',
    24: 'region',
    25: 'complication_1',
    26: 'complication_2',
    27: 'complication_3'
}

clean_df = clean_data(df, index_name_disease_dataset, column_mapping_disease_dataset)
clean_df.reset_index(inplace=True)

#melt the similar columns
melt_groups = {
    'symptom': ['symptom_1', 'symptom_2', 'symptom_3', 'symptom_4', 'symptom_5'],
    'cause': ['cause_1', 'cause_2', 'cause_3', 'cause_4', 'cause_5'],
    'treatment': ['treatment_1', 'treatment_2', 'treatment_3', 'treatment_4', 'treatment_5', 'treatment_6'],
    'diagnosis': ['diagnosis_1', 'diagnosis_2', 'diagnosis_3'],
    'complication': ['complication_1', 'complication_2', 'complication_3']
}
#constant variables
stable_vars = ['disease_name', 'alt_name', 'description', 'prognosis', 'severity', 'region']
#base dataframe is all stable variables
base_df = clean_df[stable_vars].set_index('disease_name')
#use dictionary to hold the new, stable + melted dataframes
tidy_dataframes = {}
for new_name, col_list in melt_groups.items():
    # print(f"Processing: {new_name}s")
    # Always melt from the original clean_df
    tidy_dataframes[new_name] = format_data(
        clean_df, 
        id_vars=stable_vars,
        value_vars=col_list,
        new_value_name=new_name
    )

new_df = prep_RAG(tidy_dataframes, base_df)
print("READY")

#main chat loop
while True:
    user_q = input("Ask a question about a disease (or 'quit'): ")
    if user_q.lower() == 'quit':
        break
        
    # For this simple model, we assume the user's question IS the disease name
    # A more advanced model would extract the disease name from the question
    disease_query = user_q.strip().lower() 

    # 1. RETRIEVE
    context = retrieve_context(new_df, disease_query)
    new_query = process_query(disease_query)
    print(new_query)
    # if context is None:
    #     print(f"Sorry, I have no information on '{disease_query}'.")
    # else:
    #     # We can ask a more general question now
    #     full_question = f"Tell me about {context.name}. What are its symptoms, causes, and treatments?"
        
    #     # 2. AUGMENT & 3. GENERATE
    #     print("Generating answer...")
    #     answer = generate_answer(context, full_question, model)
    #     print("\n--- ANSWER ---")
    #     print(answer)
    #     print("---------------\n")