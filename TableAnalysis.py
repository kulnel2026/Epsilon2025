import pandas as pd
import anthropic

csv_file = "journal_entries.csv"


#Market environment - date, currency, (name), 
#Forward dates is anchor dates and Libor fwd is the forward rate
#SLMA-REG for june 30 2020

df = pd.read_csv(csv_file)

print(df.head())


NLPPrompt = input("Enter your query: ")

with open('tableAnalysisPrompt.txt', 'r', encoding='utf-8') as f:
    anthropicPrompt = f.read()
    prompt = anthropicPrompt + NLPPrompt


client = anthropic.Anthropic(api_key = "")


response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens = 1024,
        messages = [ {"role": "user", "content": prompt} ]
)

anthropicResult = response.content[0].text


print("---------------------------------------")
print(anthropicResult)
print("---------------------------------------")

local_vars = {"df": df, "pd": pd}




if "import os" in anthropicResult or "open(" in anthropicResult:
    print("⚠️ Potentially unsafe code detected.")
    exit(1)


try:
    exec(anthropicResult, {}, local_vars)
except Exception as e:
    print("Error while executing generated code:", e)
