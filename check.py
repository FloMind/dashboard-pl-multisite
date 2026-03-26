import pandas as pd 
df = pd.read_excel('data/sample_balance.xlsx') 
print(df.dtypes) 
print(df.head(3).to_string()) 
