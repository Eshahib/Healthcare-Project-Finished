from collections import Counter

STOP_WORDS = set([
    'a', 'an', 'the', 'i', 'me', 'my', 'is', 'am', 'are', 'have', 'had',
    'and', 'or', 'but', 'with', 'of', 'in', 'on', 'at', 'to', 'for', 
    'feeling', 'symptoms', 'pains', 'feels', 'like'
])

def clean_data(df, index_name, column_mapping):
    """
    Cleans a DataFrame by setting the index, renaming columns, and filling empty values.
    
    Args:
        df (pd.DataFrame): The DataFrame to clean.
        index_name (str): The name for the index column.
        column_mapping (dict): A dictionary mapping the column names to the new names.
    """
    df.set_index(0, inplace=True)
    df.index.name = index_name
    df.rename(columns=column_mapping, inplace=True)

    # print(df.head())
    # print(df.columns)
    #clean the data
    df.fillna('', inplace=True)
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip().str.lower()
    df.index = df.index.str.strip().str.lower()
    
    if df.index.duplicated().sum() > 0:
        print("removing: ", df.index.duplicated().sum())
        df = df[~df.index.duplicated(keep='first')]
    if df.duplicated().sum() > 0:
        print("removing: ", df.duplicated().sum())
        df = df[~df.duplicated(keep='first')]

    return df

def format_data(df, id_vars, value_vars, new_value_name):
    """
    Melts a DataFrame from wide to long format.
    
    Args:
        df (pd.DataFrame): The DataFrame to melt.
        id_vars (list): List of columns to keep as identifiers.
        value_vars (list): List of columns to unpivot.
        new_value_name (str): The name for the new column holding the values.
    """
    # print(df.info())
    df_unpivot = df.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='source',  # Temporary column
        value_name=new_value_name
    )
    
    # Drop the temporary 'source' column
    df_unpivot.drop(columns=['source'], inplace=True)
    
    # Drop rows that were originally empty strings
    df_unpivot = df_unpivot[df_unpivot[new_value_name] != '']
    
    return df_unpivot

def prep_RAG(dfs, base_df):
    """
    Prepares a dictionary of DataFrames for RAG.
    
    Args:
        dfs (dict): A dictionary of DataFrames to prepare.
    """

    aggregated_dfs = [base_df]

    for key, df in dfs.items():
        # print("--------------------------------")
        # print(f"Aggregating: {key}s")       
        agg_series = df.groupby('disease_name')[key].apply(', '.join)
        # print(agg_series.head(10))
        agg_series.name = f"{key}"
        
        aggregated_dfs.append(agg_series)
    
    rag_df = base_df.join(aggregated_dfs[1:])
    rag_df.fillna('N/A', inplace=True)

    return rag_df

def process_query(query):
    """
    Splits a query into a list of words.
    
    Args:
        query (str): The query to split.
    """
    query = set(query.strip().lower().split(" "))
    # print("after split: ", query)
    query = query - STOP_WORDS
    # print("after stop words: ", query)
    if not query:
        return "no keywords found"
    return query

def count_keywords(processed_query, rag_df, tiny_df, key, top_n=3):
    """
    Counts the keywords in the processed query, and returns the top N matching diseases.
    
    Args:
        processed_query (set): The processed query.
        rag_df (pd.DataFrame): The RAG DataFrame.
        tiny_df (pd.DataFrame): The melted DataFrame containing disease_name and key columns.
        key (str): The column name to search in (e.g., 'symptom').
        top_n (int): Number of top matching diseases to return.
    """
    matching_disease_names = []
    # print(tiny_df)
    # print(tiny_df[key].head(10))
    for keyword in processed_query:
        matches = tiny_df[tiny_df[key].str.contains(keyword, na=False)]
        # Extract disease names from the matches
        if not matches.empty:
            disease_names = matches['disease_name'].tolist()
            matching_disease_names.extend(disease_names)
    
    if not matching_disease_names:
        return None
    
    # Count occurrences of each disease
    d_score = Counter(matching_disease_names)
    top_diseases = [disease for disease, score in d_score.most_common(top_n)]

    # print(top_diseases)
    # print("________________________________")
    try:
        context = rag_df.loc[top_diseases]
        return context
    except KeyError:
        found_diseases = [d for d in top_diseases if d in rag_df.index]
        if not found_diseases:
            return None
        context = rag_df.loc[found_diseases]
        return context

def retrieve_context(rag_df, disease_query):
    """
    Retrieves the context document for a given disease query.
    
    Args:
        rag_df (pd.DataFrame): Your aggregated RAG DataFrame.
        disease_query (str): The name of the disease to search for.
    """
    # Clean the query just like your index
    query = disease_query.strip().lower()
    
    # 1. Try to find a match in the main 'disease_name' index
    if query in rag_df.index:
        # .loc[query] pulls the entire row as a Series
        context_series = rag_df.loc[query]
        return context_series
        
    # 2. If not found, try to find a match in the 'alt_name' column
    # This is why adding 'alt_name' was so important!
    alt_match = rag_df[rag_df['alt_name'] == query]
    
    if not alt_match.empty:
        # .iloc[0] gets the first (and likely only) matching row
        return alt_match.iloc[0]

    # 3. If no match, return None
    return None

def generate_answer(context, user_question, model):
    """
    Augments a prompt with context and generates an answer.
    
    Args:
        context (pd.Series): The row of data for the disease.
        user_question (str): The original question from the user.
        model (genai.GenerativeModel): The model to use for generation.
    """
    
    # --- This is the "Augment" part ---
    # Convert the pandas Series (our context) into a formatted string
    context_str = f"""--- CONTEXT ---
        Disease: {context.name}
        Description: {context.description}
        Alternative Name: {context.alt_name}
        Symptoms: {context.symptom}
        Causes: {context.cause}
        Treatments: {context.treatment}
        Diagnosis: {context.diagnosis}
        Complications: {context.complication}
        Prognosis: {context.prognosis}
        Severity: {context.severity}
        Region: {context.region}
    --- END CONTEXT ---"""
    
    # Create the final prompt
    prompt = f"""
    You are a helpful medical assistant. Based *only* on the context provided,
    answer the user's question. Do not use any outside knowledge.
    If the context does not contain the answer, say so.

    {context_str}

    User Question: {user_question}
    
    Answer:
    """
    
    # --- This is the "Generate" part ---
    # (Assuming 'model' is your genai.GenerativeModel("gemini-2.5-flash"))
    response = model.generate_content(prompt)
    return response.text

def generate_differential_answer(context_df, user_query, model):
    """
    Generates a differential diagnosis-style answer.
    
    Args:
        context_df (pd.DataFrame): The DataFrame of top N matching diseases.
        user_query (str): The original user query.
        model (genai.GenerativeModel): The model to use.
    """
    context_str = ""
    context_str += f"""--- CONTEXT ---
    Here is a list of potential diseases that match the user's symptoms,
    along with their causes and treatments:\n"""
    # Loop through each matching disease (each row in the context_df)
    for disease_name, data in context_df.iterrows():
        context_str += f"""
        Disease: {disease_name}
        Symptoms: {data['symptom']}
        Causes: {data['cause']}
        Treatments: {data['treatment']}
        Complications: {data['complication']}
        Prognosis: {data['prognosis']}
        Severity: {data['severity']}
        Region: {data['region']}
        ---
        """
    context_str += """--- END CONTEXT ---"""

    # Create the final prompt
    prompt = f"""
    You are a helpful medical assistant. Based *only* on the context provided,
    analyze the potential diseases and present them to the user.
    Do not use any outside knowledge.
    
    Start by listing the diseases that match the user's query,
    then provide common symptoms as well as their potential causes, treatments, complications, prognosis, severity, and region as listed.
    
    {context_str}

    User Question: {user_query}
    
    Answer:
    """
    
    # --- This is the "Generate" part ---
    response = model.generate_content(prompt)
    return response.text