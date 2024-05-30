from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import csv

load_dotenv()

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = "gpt-4"


def carrega(nome_do_arquivo):
    try:
        with open(nome_do_arquivo, "r") as arquivo:
            dados = arquivo.read()
            return dados
    except IOError as e:
        print(f"Erro no carregamento de arquivo: {e}")


def salva(nome_do_arquivo, conteudo):
    try:
        # Assuming conteudo is the dict with a 'transactions' key
        transactions = conteudo.get("transactions", [])
        
        if transactions:  # Check if there are transactions to write
            with open(nome_do_arquivo, mode='w', newline='', encoding='ISO-8859-1') as arquivo:
                fieldnames = transactions[0].keys()  # Get field names from the first transaction
                writer = csv.DictWriter(arquivo, fieldnames=fieldnames)
                writer.writeheader()
                for transaction in transactions:
                    writer.writerow(transaction)
        else:
            # Fallback to save as JSON if no transactions are found
            conteudo_str = json.dumps(conteudo, ensure_ascii=False)
            with open(nome_do_arquivo, "w", encoding="ISO-8859-1") as arquivo:
                arquivo.write(conteudo_str)
    except IOError as e:
        print(f"Erro ao salvar arquivo: {e}")


def analisar_transacao(lista_transacoes):
    print("1. Performing transaction analysis")

    prompt_sistema = """

    # Analyze

    Analyse the expense report of employees (corporate credit card expense report) below and identify whether each one of them "Needs analysis" or "Is OK". Add an attribute "Status" with one of the values: "Review Required" or "Approved".
        
    The data is structured into 6 columns:

    1. Expense Report ID
    2. Account Code
    3. Account Description
    4. Card Transaction Vendor
    5. Expense Report Currency
    6. Amount

    Identify inconsistencies between the "Account Description" and the "Card Transaction Vendor" by inferring the main economic activity of the vendor and comparing it with the account description.

    For instance, if the "Account Description" is "Fuel" and the "Card Transaction Vendor" is "AUTO POSTO LUZ DA LUA", the output should be "Approved" because the vendor's name infers a fuel station activity that matches the account description.

    # Recapitulating:

    Please follow these guidelines for the analysis:
    - Infer the main economic activity of the vendor from the "Card Transaction Vendor" column.
    - Compare this inferred activity with the "Account Description".

    Example:
    - Expense Report ID: "11e9ec-18a42fb12f6-c814"
    - Account Description: "Fuel"
    - Card Transaction Vendor: "AUTO POSTO LUZ DA LUA"
    - 
    - Output: "11e9ec-18a42fb12f6-c814": Approved

    # Output Format

    Each new transaction should be inserted into the JSON list. Adopt the following response format to compose your answer:

    {
        "transactions": [
            {
            "id": "Expense Report ID",
            "gl_account": "Account Code",
            "gl_account_description": "Account Description",
            "vendor": "Card Transaction Vendor",
            "currency": "Expense Report Currency",
            "amount": "Amount",
            "status": ""
            },
        ]
    }   
    """

    lista_mensagens = [
        {
            "role": "system",
            "content": prompt_sistema
        },
        {
            "role": "user",
            "content": f"Consider the CSV below, where each row is a different transaction: {lista_transacoes}. Your answer should follow the # Output Format (just one json without other comments)"
        }
    ]

    resposta = cliente.chat.completions.create(
        messages = lista_mensagens,
        model=modelo,
        temperature=0
    )

    # conteudo = resposta.choices[0].message.content.replace("'", '"')
    conteudo = resposta.choices[0].message.content.replace("\'", '\"')
    print("Debug - Raw JSON content:", conteudo)  # Debugging line to see the raw JSON content
    try:
        json_resultado = json.loads(conteudo)
    except json.JSONDecodeError as e:
        print("JSON decoding failed:", e)
        # Optionally, print more of the string to diagnose further
        print("Starting content:", conteudo[:500])  # Print first 500 characters of the content
        print("Ending content:", conteudo[-500:])   # Print last 500 characters of the content
    return json_resultado


lista_de_transacoes = carrega("filtered_expenses_2.csv")
transacoes_analisadas = analisar_transacao(lista_de_transacoes)
salva("output.csv", transacoes_analisadas)