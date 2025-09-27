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


class HtmlBuilder:
    def __init__(self):
        self.table_generators = {
            'resultados_prospec': self._gerar_tabela_resultados_prospec,
        }

    def _gerar_tabela_resultados_prospec(self, dados) -> str:
        """
        Gera um documento HTML completo contendo todas as tabelas de resultados de prospecção

        Args:
            dados: [dict] Um dicionário contendo os dados necessários para gerar as tabelas. Deve conter as chaves:
                - 'body': Lista de listas com os dados das células do corpo da tabela
                - 'header': Lista com os cabeçalhos das colunas
                - 'width_colunas': Lista com as larguras das colunas (em pontos)
                - 'nth_color': Número de linhas para alternar a cor 

        Returns:
            str: HTML completo com todas as tabelas
        """
        
        body = dados.get('body', [])
        header = dados.get('header', [])
        width_colunas = dados.get('width_colunas', [])
        nth_color = 1

        tamanho_default_colunas = 61 #pt
        if width_colunas == [] and header != []:
            for i in range(len(header)+1):
                width_colunas.append(tamanho_default_colunas)

        tamanho_tabela = 0
        for tam in width_colunas:
            tamanho_tabela += tam

        html = '<table style="width:{}pt;border-collapse:collapse" width="{}" cellspacing="0" cellpadding="0" border="0"><tbody>\n'.format(int(tamanho_tabela*1.12), int(tamanho_tabela*1.12*1.33))
        if header != []:
            html += '\t<tr style="height: 15pt;">\n'
            for i, cell in enumerate(header):
                html += '\t\t<td style="width: {}pt; border: 1pt solid windowtext; background: rgb(100,100,100) none repeat scroll 0% 0%; padding: 0cm 3.5pt; height: 15pt;" width="{}" valign="bottom" nowrap="nowrap">\n'.format(width_colunas[i], int(width_colunas[i]*1.33))
                html += '\t\t<p class="MsoNormal" style="margin: 0cm 0cm 0.0001pt; text-align: center; line-height: normal; font-size: 11pt; font-family: &quot;Calibri&quot;, sans-serif;" align="center"><span style="color: white;">{}<span></span></span></p>\n'.format(cell)
                html += '\t\t</td>\n'
            html += '\t\t</tr>\n'

        cor_verde = False
        if body != []:
            for index_linha, linha in enumerate(body):

                # a cada n iteracoes, a cor e alternada entre branco e verde
                if index_linha % nth_color == 0:
                    cor_verde = not cor_verde

                html += '\t<tr style="height: 15pt;">\n'
                for cell in linha:
                    # if index_linha%2 == 0:
                    if cor_verde:
                        html += '\t\t<td style="width:49pt;border-color:currentcolor windowtext windowtext;border-style:none solid solid;border-width:medium 1pt 1pt;background:white none repeat scroll 0% 0%;padding:0cm 3.5pt;height:15pt" width="65" valign="bottom" nowrap="">\n'
                        html += '\t\t<p class="MsoNormal" style="margin:0cm 0cm 0.0001pt;text-align:center;line-height:normal;font-size:11pt;font-family:&quot;Calibri&quot;,sans-serif" align="center"><span style="color:black"><span>&nbsp;</span>{}<span></span></span></p>\n'.format(cell)
                        html += '\t\t</td>\n'

                    else:
                        html += '\t\t<td style="width:49pt;border-color:currentcolor windowtext windowtext;border-style:none solid solid;border-width:medium 1pt 1pt;background:rgb(200,200,200) none repeat scroll 0% 0%;padding:0cm 3.5pt;height:15pt" width="65" valign="bottom" nowrap="">\n'
                        html += '\t\t<p class="MsoNormal" style="margin:0cm 0cm 0.0001pt;text-align:center;line-height:normal;font-size:11pt;font-family:&quot;Calibri&quot;,sans-serif" align="center"><span style="color:black"><span>&nbsp;</span>{}<span></span></span></p>\n'.format(cell)
                        html += '\t\t</td>\n'

                html += '\t</tr>\n'
        html += '</tbody></table>\n'
        return html
