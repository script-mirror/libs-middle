from typing import List

def gerar_tabela(body: List[List[str]], header: List[str] = [], width_colunas: List[int] = [], nth_color: int = 1) -> str:
    """ Gera uma tabela formatada no formato HTML que possa ser interpretada pelo GMAIL
    :param body: [lst] Uma lista no qual cada item da lista e uma linha. A linha e outra lista no qual cada item e uma celula
    :param header: [lst] Lista com as celulas do header
    :param width_colunas: [lst] Lista especificando os tamanhos das colunas
    :param nth_color: [int] Numero de linhas consecutivas da mesma cor
    :return html: [str] Tabela em forma de string formatada em html pronta a ser inserida no corpo do email 
    """

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
