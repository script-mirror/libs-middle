import pandas as pd
import numpy as np


def gera_tabela_html(
    df:pd.DataFrame,
    titulo:str,
    colunas_index: list,
    colunas_comparar: list = None,
    comparar: bool = True,
):
    style = '''
        <style> 
            body { font-family: Arial, sans-serif; } 
            table { border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 4px 6px; text-align: center; }
            thead { background-color:  #2a4e6c; color: white; font-weight: bold } 
            tbody tr:nth-child(even) { background-color: #f9f9f9; }
            .none{ background-color: inherit; } 
            .index-color{ background-color: #E7E6E6; font-weight: bold; }
            .negative-color{ background-color: #C6EFCE; color: #006100; font-weight: bold; }
            .positive-color{ background-color: #FFC7CE; color: #9C0006; font-weight: bold; }
        </style>
    '''
    html = f'''
        <table>
            <thead><tr><th colspan="{len(df.columns)}">{titulo}</th> </tr></thead>
            <thead>
        <tr>
    '''
    
    df[colunas_index] = df[colunas_index].replace({np.nan: "-"})
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += ' </tr></thead><tbody>'
    for i, row in df.iterrows():
        html += '<tr>'
        for j, col in enumerate(row):
            if df.columns[j] in colunas_index:
                css_class = "index-color"
                content = col
            elif type(col) not in[int, float, np.int64, np.float64]:
                css_class = "none"
                content = col
            elif np.isnan(col):
                css_class = "none"
                content = ""
            elif colunas_comparar and df.columns[j] not in colunas_comparar:
                css_class = "none"
                content = col
            elif comparar and col < 0:
                css_class = "positive-color"
                content = col
            elif comparar and col > 0:
                css_class = "negative-color"
                content = col
            else:
                css_class = "none"
                content = col
            html += f'<td class="{css_class}">{content}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    
    return f'{style} {html}'


