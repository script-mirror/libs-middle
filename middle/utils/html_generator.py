import pandas as pd
import numpy as np
from datetime import datetime

def gera_tabela_html(
    df: pd.DataFrame,
    titulo: str,
    colunas_index: list,
    colunas_comparar: list = None,
    comparar: bool = True,
    analise_media: bool = False,
    medias_historicas: dict = None,
):
    style = '''
        <style> 
            body { font-family: Arial, sans-serif; } 
            table { border-collapse: collapse; }
            th, td { border: 1px solid #d0d0d0; padding: 4px 6px; text-align: center; }
            thead { background-color:  #2a4e6c; color: white; font-weight: bold } 
            tbody tr:nth-child(even) { background-color: #f0f0f7; }
            .none{ background-color: inherit; } 
            .index-color{ background-color: #E6E6EF; font-weight: bold; }
            .negative-color{ background-color: #C6EFCE; color: #006100; font-weight: bold; }
            .positive-color{ background-color: #FFC7CE; color: #9C0006; font-weight: bold; }
            .media-historica{ font-size: 0.8em; color: #666; display:block; }
        </style>
    '''

    html = f'''
        <table>
            <thead><tr><th colspan="{len(df.columns)}">{titulo}</th></tr></thead>
            <thead><tr>
    '''

    df[colunas_index] = df[colunas_index].replace({np.nan: "-"})

    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'

    for _, row in df.iterrows():
        html += '<tr>'
        bacia = row[colunas_index[0]] if colunas_index else None

        for j, valor in enumerate(row):
            coluna = df.columns[j]
            css_class = "none"
            conteudo = valor

            if coluna in colunas_index:
                css_class = "index-color"

            elif isinstance(valor, (int, float, np.int64, np.float64)):
                if np.isnan(valor):
                    conteudo = ""
                else:
                    if colunas_comparar and coluna not in colunas_comparar:
                        css_class = "none"
                    elif comparar:
                        if valor < 0:
                            css_class = "positive-color"
                        elif valor > 0:
                            css_class = "negative-color"

                    if analise_media and medias_historicas and bacia in medias_historicas:
                        try:
                            mes = datetime.strptime(coluna, "%d/%m/%y").strftime("%m")
                            media_mes = medias_historicas[bacia].get(mes)
                            if media_mes is not None:
                                conteudo = f"{valor}<span class='media-historica'>({media_mes})</span>"
                        except Exception:
                            pass

            html += f'<td class="{css_class}">{conteudo}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return f'{style} {html}'