from typing import List

class HtmlBuilder:
    def __init__(self):
        self.table_generators = {
            'unsi': self._gerar_tabela_unsi,
            'mmgd': self._gerar_tabela_mmgd,
            'mmgd_total': self._gerar_tabela_mmgd_total,
            'cargaglobal': self._gerar_tabela_carga_global,
            'cargaliquida': self._gerar_tabela_carga_liquida,
            'ande': self._gerar_tabela_ande,
            'diferenca_cargas': self._gerar_tabela_diferenca,
            'resultados_prospec': self._gerar_tabela_resultados_prospec,
        }
        
    def gerar_html(self, tabela, dados):
        """
        Gera HTML para o tipo de tabela especificado
        
        Args:
            tabela (str): O tipo de tabela a ser gerada
            dados (dict): Dados necessários para gerar a tabela
            
        Returns:
            str: HTML da tabela gerada
        
        Raises:
            ValueError: Se o tipo de tabela não for suportado
        """
        # Verifica se o tipo de tabela é suportado
        if tabela not in self.table_generators:
            raise ValueError(f"Geração de tabela não mapeado!: {tabela}. Opções disponíveis: {list(self.table_generators.keys())}")
        
        # Chama o gerador de tabela apropriado
        return self.table_generators[tabela](dados)
    
    def _gerar_tabela_unsi(self, dados):
        """
        Gera tabela HTML para dados de geração de usinas não simuladas
        
        Args:
            dados (dict): Dados contendo informações de decks antigo e novo
            
        Returns:
            str: HTML da tabela de diferença de geração UNSI
        """
        if not dados or len(dados) < 2:
            return "<p>Dados insuficientes para gerar a tabela de diferença.</p>"
        
        # Ordenar os dados pelo dt_deck (mais antigo primeiro)
        dados_ordenados = sorted(dados, key=lambda x: x['dt_deck'])
        
        # Extrair dados do deck antigo e novo
        deck_antigo = dados_ordenados[0]
        deck_novo = dados_ordenados[-1]
        
        # Converter os dados para um formato mais fácil de manipular
        dados_antigo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_unsi'] for item in deck_antigo['data']}
        dados_novo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_unsi'] for item in deck_novo['data']}
        
        # Encontrar todos os anos e meses únicos
        anos = sorted(set([item['vl_ano'] for item in deck_antigo['data'] + deck_novo['data']]))
        meses = list(range(1, 13))  # 1 a 12
        
        # Construir a tabela HTML
        html = f"""
        <style>
            table.deck-diff {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            
            table.deck-diff th, table.deck-diff td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }}
            
            table.deck-diff th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            table.deck-diff tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .positive {{
                color: green;
            }}
            
            .negative {{
                color: red;
            }}
            
            .caption {{
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        
        <table class="deck-diff">
            <thead>
                <tr>
                    <th>Ano</th>
                    <th>Jan</th>
                    <th>Fev</th>
                    <th>Mar</th>
                    <th>Abr</th>
                    <th>Mai</th>
                    <th>Jun</th>
                    <th>Jul</th>
                    <th>Ago</th>
                    <th>Set</th>
                    <th>Out</th>
                    <th>Nov</th>
                    <th>Dez</th>
                    <th>Média</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Preencher os dados na tabela
        for ano in anos:
            html += f"<tr><td>{ano}</td>"
            valores_ano = []
            
            for mes in meses:
                valor_antigo = dados_antigo.get((ano, mes), None)
                valor_novo = dados_novo.get((ano, mes), None)
                
                if valor_antigo is not None and valor_novo is not None:
                    # Regra: se o valor do deck novo for zero ou menor, a diferença também será zero
                    if valor_novo <= 0:
                        diferenca = 0
                    else:
                        diferenca = valor_novo - valor_antigo
                    
                    classe_css = "positive" if diferenca >= 0 else "negative"
                    html += f'<td class="{classe_css}">{diferenca:.0f}</td>'
                    valores_ano.append(diferenca)
                else:
                    html += "<td>-</td>"
            
            # Calcular e adicionar a média
            if valores_ano:
                media = sum(valores_ano) / 12
                classe_css_media = "positive" if media >= 0 else "negative"
                html += f'<td class="{classe_css_media}"><strong>{media:.0f}</strong></td>'
            else:
                html += "<td>-</td>"
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _gerar_tabela_mmgd(self, dados):
        """
        Gera tabela HTML para dados de geração MMGD
        
        Args:
            dados (dict): Dados contendo informações de decks antigo e novo
            
        Returns:
            str: HTML da tabela de diferença de geração MMGD
        """
        if not dados or len(dados) < 2:
            return "<p>Dados insuficientes para gerar a tabela de diferença MMGD.</p>"
        
        # Ordenar os dados pelo dt_deck (mais antigo primeiro)
        dados_ordenados = sorted(dados, key=lambda x: x['dt_deck'])
        
        # Extrair dados do deck antigo e novo
        deck_antigo = dados_ordenados[0]
        deck_novo = dados_ordenados[-1]
        
        # Converter os dados para um formato mais fácil de manipular
        dados_antigo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_mmgd'] for item in deck_antigo['data']}
        dados_novo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_mmgd'] for item in deck_novo['data']}
        
        # Encontrar todos os anos e meses únicos
        anos = sorted(set([item['vl_ano'] for item in deck_antigo['data'] + deck_novo['data']]))
        meses = list(range(1, 13))  # 1 a 12
        
        # Construir a tabela HTML
        html = f"""
        <style>
            table.deck-diff {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            
            table.deck-diff th, table.deck-diff td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }}
            
            table.deck-diff th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            table.deck-diff tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .positive {{
                color: green;
            }}
            
            .negative {{
                color: red;
            }}
            
            .caption {{
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        
        <table class="deck-diff">
            <thead>
                <tr>
                    <th>Ano</th>
                    <th>Jan</th>
                    <th>Fev</th>
                    <th>Mar</th>
                    <th>Abr</th>
                    <th>Mai</th>
                    <th>Jun</th>
                    <th>Jul</th>
                    <th>Ago</th>
                    <th>Set</th>
                    <th>Out</th>
                    <th>Nov</th>
                    <th>Dez</th>
                    <th>Média</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Preencher os dados na tabela
        for ano in anos:
            html += f"<tr><td>{ano}</td>"
            valores_ano = []
            
            for mes in meses:
                valor_antigo = dados_antigo.get((ano, mes), None)
                valor_novo = dados_novo.get((ano, mes), None)
                
                if valor_antigo is not None and valor_novo is not None:
                    # Regra: se o valor do deck novo for zero ou menor, a diferença também será zero
                    if valor_novo <= 0:
                        diferenca = 0
                    else:
                        diferenca = valor_novo - valor_antigo
                    
                    classe_css = "positive" if diferenca >= 0 else "negative"
                    html += f'<td class="{classe_css}">{diferenca:.0f}</td>'
                    valores_ano.append(diferenca)
                else:
                    html += "<td>-</td>"
            
            # Calcular e adicionar a média
            if valores_ano:
                media = sum(valores_ano) / 12
                classe_css_media = "positive" if media >= 0 else "negative"
                html += f'<td class="{classe_css_media}"><strong>{media:.0f}</strong></td>'
            else:
                html += "<td>-</td>"
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _gerar_tabela_mmgd_total(self, dados):
        """
        Gera tabela HTML para dados de geração MMGD Total (Base + Expansão)
        
        Args:
            dados (dict): Dados contendo informações de decks antigo e novo
            
        Returns:
            str: HTML da tabela de diferença de geração MMGD Total
        """
        if not dados or len(dados) < 2:
            return "<p>Dados insuficientes para gerar a tabela de diferença MMGD Total.</p>"
        
        # Ordenar os dados pelo dt_deck (mais antigo primeiro)
        dados_ordenados = sorted(dados, key=lambda x: x['dt_deck'])
        
        # Extrair dados do deck antigo e novo
        deck_antigo = dados_ordenados[0]
        deck_novo = dados_ordenados[-1]
        
        # Converter os dados para um formato mais fácil de manipular
        dados_antigo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_mmgd_total'] for item in deck_antigo['data']}
        dados_novo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_mmgd_total'] for item in deck_novo['data']}
        
        # Encontrar todos os anos e meses únicos
        anos = sorted(set([item['vl_ano'] for item in deck_antigo['data'] + deck_novo['data']]))
        meses = list(range(1, 13))  # 1 a 12
        
        # Construir a tabela HTML
        html = f"""
        <style>
            table.deck-diff {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            
            table.deck-diff th, table.deck-diff td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }}
            
            table.deck-diff th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            table.deck-diff tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .positive {{
                color: green;
            }}
            
            .negative {{
                color: red;
            }}
            
            .caption {{
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        
        <table class="deck-diff">
            <thead>
                <tr>
                    <th>Ano</th>
                    <th>Jan</th>
                    <th>Fev</th>
                    <th>Mar</th>
                    <th>Abr</th>
                    <th>Mai</th>
                    <th>Jun</th>
                    <th>Jul</th>
                    <th>Ago</th>
                    <th>Set</th>
                    <th>Out</th>
                    <th>Nov</th>
                    <th>Dez</th>
                    <th>Média</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Preencher os dados na tabela
        for ano in anos:
            html += f"<tr><td>{ano}</td>"
            valores_ano = []
            
            for mes in meses:
                valor_antigo = dados_antigo.get((ano, mes), None)
                valor_novo = dados_novo.get((ano, mes), None)
                
                if valor_antigo is not None and valor_novo is not None:
                    # Regra: se o valor do deck novo for zero ou menor, a diferença também será zero
                    if valor_novo <= 0:
                        diferenca = 0
                    else:
                        diferenca = valor_novo - valor_antigo
                    
                    classe_css = "positive" if diferenca >= 0 else "negative"
                    html += f'<td class="{classe_css}">{diferenca:.0f}</td>'
                    valores_ano.append(diferenca)
                else:
                    html += "<td>-</td>"
            
            # Calcular e adicionar a média
            if valores_ano:
                media = sum(valores_ano) / 12
                classe_css_media = "positive" if media >= 0 else "negative"
                html += f'<td class="{classe_css_media}"><strong>{media:.0f}</strong></td>'
            else:
                html += "<td>-</td>"
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _gerar_tabela_carga_global(self, dados):
        """
        Gera tabela HTML para dados de carga global
        
        Args:
            dados (dict): Dados contendo informações de decks antigo e novo
            
        Returns:
            str: HTML da tabela de diferença de carga global
        """
        if not dados or len(dados) < 2:
            return "<p>Dados insuficientes para gerar a tabela de diferença de carga global.</p>"
        
        # Ordenar os dados pelo dt_deck (mais antigo primeiro)
        dados_ordenados = sorted(dados, key=lambda x: x['dt_deck'])
        
        # Extrair dados do deck antigo e novo
        deck_antigo = dados_ordenados[0]
        deck_novo = dados_ordenados[-1]
        
        # Converter os dados para um formato mais fácil de manipular
        dados_antigo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_carga_global'] for item in deck_antigo['data']}
        dados_novo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_carga_global'] for item in deck_novo['data']}
        
        # Encontrar todos os anos e meses únicos
        anos = sorted(set([item['vl_ano'] for item in deck_antigo['data'] + deck_novo['data']]))
        meses = list(range(1, 13))  # 1 a 12
        
        # Construir a tabela HTML
        html = f"""
        <style>
            table.deck-diff {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            
            table.deck-diff th, table.deck-diff td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }}
            
            table.deck-diff th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            table.deck-diff tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .positive {{
                color: green;
            }}
            
            .negative {{
                color: red;
            }}
            
            .caption {{
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        
        <table class="deck-diff">
            <thead>
                <tr>
                    <th>Ano</th>
                    <th>Jan</th>
                    <th>Fev</th>
                    <th>Mar</th>
                    <th>Abr</th>
                    <th>Mai</th>
                    <th>Jun</th>
                    <th>Jul</th>
                    <th>Ago</th>
                    <th>Set</th>
                    <th>Out</th>
                    <th>Nov</th>
                    <th>Dez</th>
                    <th>Média</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Preencher os dados na tabela
        for ano in anos:
            html += f"<tr><td>{ano}</td>"
            valores_ano = []
            
            for mes in meses:
                valor_antigo = dados_antigo.get((ano, mes), None)
                valor_novo = dados_novo.get((ano, mes), None)
                
                if valor_antigo is not None and valor_novo is not None:
                    # Regra: se o valor do deck novo for zero ou menor, a diferença também será zero
                    if valor_novo <= 0:
                        diferenca = 0
                    else:
                        diferenca = valor_novo - valor_antigo
                    
                    classe_css = "positive" if diferenca >= 0 else "negative"
                    html += f'<td class="{classe_css}">{diferenca:.0f}</td>'
                    valores_ano.append(diferenca)
                else:
                    html += "<td>-</td>"
            
            # Calcular e adicionar a média
            if valores_ano:
                media = sum(valores_ano) / 12
                classe_css_media = "positive" if media >= 0 else "negative"
                html += f'<td class="{classe_css_media}"><strong>{media:.0f}</strong></td>'
            else:
                html += "<td>-</td>"
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _gerar_tabela_carga_liquida(self, dados):
        """
        Gera tabela HTML para dados de carga líquida
        
        Args:
            dados (dict): Dados contendo informações de decks antigo e novo
            
        Returns:
            str: HTML da tabela de diferença de carga líquida
        """
        if not dados or len(dados) < 2:
            return "<p>Dados insuficientes para gerar a tabela de diferença de carga líquida.</p>"
        
        # Ordenar os dados pelo dt_deck (mais antigo primeiro)
        dados_ordenados = sorted(dados, key=lambda x: x['dt_deck'])
        
        # Extrair dados do deck antigo e novo
        deck_antigo = dados_ordenados[0]
        deck_novo = dados_ordenados[-1]
        
        # Converter os dados para um formato mais fácil de manipular
        dados_antigo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_carga_liquida'] for item in deck_antigo['data']}
        dados_novo = {(item['vl_ano'], item['vl_mes']): item['vl_deck_carga_liquida'] for item in deck_novo['data']}
        
        # Encontrar todos os anos e meses únicos
        anos = sorted(set([item['vl_ano'] for item in deck_antigo['data'] + deck_novo['data']]))
        meses = list(range(1, 13))  # 1 a 12
        
        # Construir a tabela HTML
        html = f"""
        <style>
            table.deck-diff {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            
            table.deck-diff th, table.deck-diff td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }}
            
            table.deck-diff th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            table.deck-diff tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .positive {{
                color: green;
            }}
            
            .negative {{
                color: red;
            }}
            
            .caption {{
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        
        <table class="deck-diff">
            <thead>
                <tr>
                    <th>Ano</th>
                    <th>Jan</th>
                    <th>Fev</th>
                    <th>Mar</th>
                    <th>Abr</th>
                    <th>Mai</th>
                    <th>Jun</th>
                    <th>Jul</th>
                    <th>Ago</th>
                    <th>Set</th>
                    <th>Out</th>
                    <th>Nov</th>
                    <th>Dez</th>
                    <th>Média</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Preencher os dados na tabela
        for ano in anos:
            html += f"<tr><td>{ano}</td>"
            valores_ano = []
            
            for mes in meses:
                valor_antigo = dados_antigo.get((ano, mes), None)
                valor_novo = dados_novo.get((ano, mes), None)
                
                if valor_antigo is not None and valor_novo is not None:
                    # Regra: se o valor do deck novo for zero ou menor, a diferença também será zero
                    if valor_novo <= 0:
                        diferenca = 0
                    else:
                        diferenca = valor_novo - valor_antigo
                    
                    classe_css = "positive" if diferenca >= 0 else "negative"
                    html += f'<td class="{classe_css}">{diferenca:.0f}</td>'
                    valores_ano.append(diferenca)
                else:
                    html += "<td>-</td>"
            
            # Calcular e adicionar a média
            if valores_ano:
                media = sum(valores_ano) / 12
                classe_css_media = "positive" if media >= 0 else "negative"
                html += f'<td class="{classe_css_media}"><strong>{media:.0f}</strong></td>'
            else:
                html += "<td>-</td>"
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _gerar_tabela_ande(self, dados):
        """
        Gera tabela HTML para dados de carga do ANDE
        
        Args:
            dados (dict): Dados contendo informações de decks antigo e novo
            
        Returns:
            str: HTML da tabela de diferença de carga ANDE
        """
        if not dados or len(dados) < 2:
            return "<p>Dados insuficientes para gerar a tabela de diferença de carga ANDE.</p>"
        
        # Ordenar os dados pelo dt_deck (mais antigo primeiro)
        dados_ordenados = sorted(dados, key=lambda x: x['dt_deck'])
        
        # Extrair dados do deck antigo e novo
        deck_antigo = dados_ordenados[0]
        deck_novo = dados_ordenados[-1]
        
        # Verificar se os dados contêm a chave necessária
        if not deck_antigo.get('data') or not deck_novo.get('data'):
            return "<p>Estrutura de dados inválida para carga ANDE.</p>"
        
        # Verificar se pelo menos um item tem a chave vl_ande_total
        sample_item_antigo = deck_antigo['data'][0] if deck_antigo['data'] else {}
        sample_item_novo = deck_novo['data'][0] if deck_novo['data'] else {}
        
        if 'vl_ande_total' not in sample_item_antigo and 'vl_ande_total' not in sample_item_novo:
            return "<p>Dados de carga ANDE não encontrados (campo 'vl_ande_total' ausente).</p>"
        
        # Converter os dados para um formato mais fácil de manipular
        dados_antigo = {(item['vl_ano'], item['vl_mes']): item.get('vl_ande_total', 0) for item in deck_antigo['data']}
        dados_novo = {(item['vl_ano'], item['vl_mes']): item.get('vl_ande_total', 0) for item in deck_novo['data']}
        
        # Encontrar todos os anos e meses únicos
        anos = sorted(set([item['vl_ano'] for item in deck_antigo['data'] + deck_novo['data']]))
        meses = list(range(1, 13))  # 1 a 12
        
        # Construir a tabela HTML
        html = f"""
        <style>
            table.deck-diff {{
                border-collapse: collapse;
                width: 100%;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }}
            
            table.deck-diff th, table.deck-diff td {{
                border: 1px solid #ddd;
                padding: 6px;
                text-align: center;
            }}
            
            table.deck-diff th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            table.deck-diff tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .positive {{
                color: green;
            }}
            
            .negative {{
                color: red;
            }}
            
            .caption {{
                font-weight: bold;
                margin-bottom: 8px;
                font-size: 14px;
            }}
        </style>
        
        <table class="deck-diff">
            <thead>
                <tr>
                    <th>Ano</th>
                    <th>Jan</th>
                    <th>Fev</th>
                    <th>Mar</th>
                    <th>Abr</th>
                    <th>Mai</th>
                    <th>Jun</th>
                    <th>Jul</th>
                    <th>Ago</th>
                    <th>Set</th>
                    <th>Out</th>
                    <th>Nov</th>
                    <th>Dez</th>
                    <th>Média</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Preencher os dados na tabela
        for ano in anos:
            html += f"<tr><td>{ano}</td>"
            valores_ano = []
            
            for mes in meses:
                valor_antigo = dados_antigo.get((ano, mes), None)
                valor_novo = dados_novo.get((ano, mes), None)
                
                if valor_antigo is not None and valor_novo is not None:
                    # Regra: se o valor do deck novo for zero ou menor, a diferença também será zero
                    if valor_novo <= 0:
                        diferenca = 0
                    else:
                        diferenca = valor_novo - valor_antigo
                    
                    classe_css = "positive" if diferenca >= 0 else "negative"
                    html += f'<td class="{classe_css}">{diferenca:.0f}</td>'
                    valores_ano.append(diferenca)
                else:
                    html += "<td>-</td>"
            
            # Calcular e adicionar a média
            if valores_ano:
                media = sum(valores_ano) / 12
                classe_css_media = "positive" if media >= 0 else "negative"
                html += f'<td class="{classe_css_media}"><strong>{media:.0f}</strong></td>'
            else:
                html += "<td>-</td>"
            
            html += "</tr>"
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def _gerar_tabela_diferenca(self, dados):
        """
        Gera um documento HTML completo contendo todas as tabelas de diferenças disponíveis

        Args:
            dados: [dict] Um dicionário contendo os dados necessários para gerar as tabelas. Deve conter as chaves:
                - 'dados_unsi': Dados para usinas não simuladas
                - 'dados_ande': Dados para carga ANDE
                - 'dados_mmgd_total': Dados para MMGD Total (Base + Expansão)
                - 'dados_carga_global': Dados para carga global
                - 'dados_carga_liquida': Dados para carga líquida

        Returns:
            str: HTML completo com todas as tabelas
        """
        
        # Extrai os dados necessários dos parâmetros
        dados_unsi = dados.get('dados_unsi', [])
        dados_ande = dados.get('dados_ande', [])
        dados_mmgd_total = dados.get('dados_mmgd_total', [])    
        dados_carga_global = dados.get('dados_carga_global', [])
        dados_carga_liquida = dados.get('dados_carga_liquida', [])
        
        # Gera as tabelas individuais
        html_tabela_diff_unsi = self._gerar_tabela_unsi(dados_unsi) if dados_unsi else "<p>Dados não disponíveis para usinas não simuladas.</p>"
        html_tabela_diff_ande = self._gerar_tabela_ande(dados_ande) if dados_ande else "<p>Dados não disponíveis para carga ANDE.</p>"
        html_tabela_diff_mmgd_total = self._gerar_tabela_mmgd_total(dados_mmgd_total) if dados_mmgd_total else "<p>Dados não disponíveis para MMGD Total.</p>"
        html_tabela_diff_carga_global = self._gerar_tabela_carga_global(dados_carga_global) if dados_carga_global else "<p>Dados não disponíveis para carga global.</p>"
        html_tabela_diff_carga_liquida = self._gerar_tabela_carga_liquida(dados_carga_liquida) if dados_carga_liquida else "<p>Dados não disponíveis para carga líquida.</p>"

        # Combinar todas as tabelas em um documento HTML único
        html_completo = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Relatório de Diferenças - Deck Preliminar Newave</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                }}

                .header h1 {{
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 24px;
                }}

                .header p {{
                    color: #666;
                    font-size: 14px;
                    margin: 5px 0;
                }}

                .table-section {{
                    margin-bottom: 40px;
                }}

                .table-section h2 {{
                    color: #2c3e50;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                    margin-bottom: 15px;
                    font-size: 18px;
                }}

                .no-data {{
                    text-align: center;
                    color: #888;
                    font-style: italic;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="table-section">
                    <h2>Diferença de Usinas Não Simuladas (UNSI)</h2>
                    {html_tabela_diff_unsi}
                </div>
                
                <div class="table-section">
                    <h2>ANDE</h2>
                    {html_tabela_diff_ande}
                </div>

                <div class="table-section">
                    <h2>Diferença de MMGD Total (Base + Expansão)</h2>
                    {html_tabela_diff_mmgd_total}
                </div>

                <div class="table-section">
                    <h2>Diferença de Carga Global</h2>
                    {html_tabela_diff_carga_global}
                </div>

                <div class="table-section">
                    <h2>Diferença de Carga Líquida</h2>
                    {html_tabela_diff_carga_liquida}
                </div>
            </div>
        </body>
        </html>
        """

        return html_completo

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
