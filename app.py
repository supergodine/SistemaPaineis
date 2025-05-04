from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import oracledb
from datetime import datetime
from flask import session
from sqlalchemy import create_engine
from sqlalchemy.sql import text
import logging
import concurrent.futures
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from io import BytesIO
import base64


app = Flask(__name__)
app.secret_key = 'chave_secreta'

# Habilitar o modo "thick"
oracledb.init_oracle_client(lib_dir=r"C:\Users\Diego\Desktop\oracle client\instantclient_23_7")

# Configurações de banco de dados
DB_HOST = '172.16.0.227'
DB_PORT = '1521'
DB_SERVICE_NAME = 'prd'
DB_USER = 'painel'
DB_PASSWORD = 'P0T4syti'

# Criar engine do SQLAlchemy (depois das configurações)
engine = create_engine(f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?service_name={DB_SERVICE_NAME}")

# Configuração do logger
logging.basicConfig(level=logging.INFO)

# Função para conexão com o banco de dados
def get_db_connection():
    dsn = oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE_NAME)
    return oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)

# ------------------------------------- Função gerar grafico ------------------------------
def gerar_grafico(df, titulo, tipo, exibir_legenda=False, legendas=[], ax=None):
    print("Função gerar_grafico() chamada")
    print(f"Dados: Titulo: {titulo}, Tipo: {tipo}")
    print(f"Dataframe: \n{df}")

    try:
        tipo = tipo.lower()
        fig = None

        if len(df.columns) == 1:
            valores = df.iloc[:, 0].astype(float)
            valores = valores[valores > 0]  # Remove valores zerados ou negativos

            if tipo in ['pizza', 'rosca']:
                if valores.empty:
                    print("Erro: Não há valores válidos para o gráfico.")
                    return None

                if not ax:
                    fig, ax = plt.subplots()

                labels = df.index.astype(str) if not legendas else [legenda['ds_legenda'] for legenda in legendas]

                # Criando gráfico de pizza
                wedges, texts, autotexts = ax.pie(valores, labels=labels[:len(valores)], autopct='%1.1f%%', startangle=90)
                ax.axis('equal')

                # Adicionando o círculo ao centro do gráfico de rosca
                if tipo == 'rosca':
                    centro = plt.Circle((0, 0), 0.6, fc='white')
                    ax.add_artist(centro)

                elif tipo == 'card':
                    fig, ax = plt.subplots(figsize=(2, 1))
                    if df.empty:
                        valor = "Sem valor"
                    elif len(df) == 1:
                        valor = df.iloc[0, 0]
                    else:
                        valor = df.iloc[:, 0].sum()
                    ax.text(0.5, 0.5, str(valor), ha='center', va='center', fontsize=24, weight='bold')
                    ax.set_xticks([])
                    ax.set_yticks([])
                    ax.set_frame_on(False)
                else:
                    print(f"Tipo de gráfico {tipo} não suportado com uma única coluna.")
                    return None

        elif len(df.columns) >= 2:
            valores = df.iloc[:, 1].astype(float)
            valores = valores[valores > 0]

            if tipo in ['pizza', 'rosca'] :
                if valores.empty:
                    print("Erro: Não há valores válidos para o gráfico.")
                    return None

                if not ax:
                    fig, ax = plt.subplots()

                labels = df.iloc[:, 0].astype(str) if not legendas else [legenda['ds_legenda'] for legenda in legendas]

                wedges, texts, autotexts = ax.pie(valores, labels=labels[:len(valores)], autopct='%1.1f%%', startangle=90)
                ax.axis('equal')

                if tipo == 'rosca':
                    centro = plt.Circle((0, 0), 0.6, fc='white')
                    ax.add_artist(centro)

            elif tipo in ['barra', 'barras']:
                if not ax:
                    fig, ax = plt.subplots()
                ax.bar(df.iloc[:, 0], valores) #alterado para receber os valores do eixo x

            elif tipo == 'linha' or tipo == 'linhas':
                if not ax:
                    fig, ax = plt.subplots()
                ax.plot(df.iloc[:, 0], valores, marker='o', linestyle='-')
                ax.set_ylabel('Valores')
                ax.set_xlabel('Categorias')
                ax.tick_params(axis='x', rotation=45)
                ax.grid(True)  # Adiciona grade para melhor visualização
            elif tipo == 'barras_horizontais':
                if not ax:
                    fig, ax = plt.subplots()
                ax.barh(df.iloc[:, 0], valores) #alterado para barras horizontais
                ax.set_ylabel('Categorias')
                ax.set_xlabel('Valores')
            elif tipo == 'dispersao':
                if not ax:
                    fig, ax = plt.subplots()
                ax.scatter(df.iloc[:, 0], valores) #alterado para dispersão
                ax.set_ylabel('Valores')
                ax.set_xlabel('Categorias')
            elif tipo == 'area':
                if not ax:
                    fig, ax = plt.subplots()
                ax.fill_between(df.iloc[:, 0], valores) #alterado para area
                ax.set_ylabel('Valores')
                ax.set_xlabel('Categorias')
            elif tipo == 'card':
                fig, ax = plt.subplots(figsize=(2, 1))
                if df.empty:
                    valor = "Sem valor"
                else:
                    valor = df.iloc[:, 1].sum()
                ax.text(0.5, 0.5, str(valor), ha='center', va='center', fontsize=24, weight='bold')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_frame_on(False)    

        if fig and exibir_legenda:
            ax.legend(loc='best')

        if fig:
            plt.title(titulo)
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            print("Imagem gerada com sucesso!")
            return image_base64
        else:
            print("Erro: Nenhuma figura gerada.")
            return None

    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        import traceback
        traceback.print_exc()
        return None


# ------------------------------------- fim Função gerar grafico ------------------------------
# Função auxiliar para gerar os graficos em threads
@app.route('/obter_dados_graficos/<int:painel_id>', methods=['GET'])
def obter_dados_graficos(painel_id):
    try:
        engine = create_engine(
            f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?service_name={DB_SERVICE_NAME}"
        )

        with engine.connect() as conn:
            # Obter título do painel
            painel_query = text(""" 
                SELECT ds_titulo_painel FROM hp_painel WHERE nr_sequencia = :painel_id
            """)
            painel = conn.execute(painel_query, {'painel_id': painel_id}).fetchone()

            if not painel:
                return jsonify({"error": "Painel não encontrado"}), 404

            ds_titulo_painel = painel[0] or " "

            # Obter dados dos gráficos
            graficos_query = text(""" 
                SELECT nr_sequencia, ds_titulo, ds_sql, nr_seq_apresentacao, ds_tipo_grafico
                FROM hp_painel_grafico
                WHERE fk_nr_seq_painel = :painel_id
                ORDER BY nr_seq_apresentacao
            """)
            graficos = conn.execute(graficos_query, {'painel_id': painel_id}).fetchall()

            if not graficos:
                return jsonify({"error": "Nenhum gráfico encontrado para o painel"}), 404

            # Log dos dados retornados
            print(f"Dados dos gráficos retornados: {graficos}")

            graficos_data = {}
            for nr_sequencia, titulo, sql, num_apres, tipo in graficos:
                print(f"Processando gráfico: {nr_sequencia}, Tipo: {tipo}, SQL: {sql}")

                if not sql or not sql.strip():
                    graficos_data[f'grafico_{nr_sequencia}'] = {
                        'image': None,
                        'titulo': titulo,
                        'tipo': tipo,
                        'error': 'SQL vazio para este gráfico.'
                    }
                    continue

                # Obtenha as legendas associadas ao gráfico
                legendas_query = text("""
                SELECT l.ds_legenda, l.ds_cor
                FROM hp_painel_legenda l
                JOIN hp_painel_grafico_legenda gl ON l.nr_sequencia = gl.fk_nr_seq_legenda
                WHERE gl.fk_nr_seq_grafico = :nr_sequencia
                """)

                legendas_result = conn.execute(legendas_query, {'nr_sequencia': nr_sequencia}).fetchall()
                legendas = [{'ds_legenda': legenda[0], 'ds_cor': legenda[1]} for legenda in legendas_result]

                try:
                    df = pd.read_sql_query(text(sql), con=engine)

                    # Verificação do DataFrame
                    print(f"DataFrame carregado: \n{df}")

                    if df.empty:
                        graficos_data[f'grafico_{nr_sequencia}'] = {
                            'image': None,
                            'titulo': titulo,
                            'tipo': tipo,
                            'error': 'Sem dados para gerar o gráfico.'
                        }
                        continue

                    # Garantir que temos pelo menos 2 colunas
                    if len(df.columns) < 2:
                        print(f"DataFrame com menos de 2 colunas. Colunas: {df.columns}")
                        graficos_data[f'grafico_{nr_sequencia}'] = {
                            'image': None,
                            'titulo': titulo,
                            'tipo': tipo,
                            'error': 'O DataFrame não possui colunas suficientes para gerar o gráfico.'
                        }
                        continue

                    # Gerar o gráfico
                    image_base64 = gerar_grafico(df, titulo, tipo, len(legendas) > 0, legendas)

                    graficos_data[f'grafico_{nr_sequencia}'] = {
                        'image': image_base64,
                        'titulo': titulo,
                        'tipo': tipo,
                        'legendas' : legendas
                    }

                except Exception as e:
                    print(f"Erro ao processar gráfico {nr_sequencia}: {e}")
                    graficos_data[f'grafico_{nr_sequencia}'] = {
                        'image': None,
                        'titulo': titulo,
                        'tipo': tipo,
                        'error': f"Erro ao executar SQL: {str(e)}"
                    }
            print(f"graficos_data: {graficos_data}")
            return jsonify(graficos_data)

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": "Erro inesperado"}), 500

# ---------------- INÍCIO Funções de Autenticação ----------------
def autenticar_usuario(username, password):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""SELECT tasy.hp_permite_login_admin(:username, :password) FROM dual""", 
                    username=username, password=password)
        resultado = cursor.fetchone()
        return resultado and resultado[0] == 'S'
    except Exception as e:
        print(f"Erro ao autenticar: {e}")
        return False
    finally:
        connection.close()

# Rota de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if autenticar_usuario(username, password):
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('lista_paineis'))
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')
# ---------------- FIM Funções de Autenticação ----------------

# ---------------- INÍCIO Rotas de Painel ----------------
# Rota listar paineis
@app.route('/paineis')
def lista_paineis():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT nr_sequencia, ds_titulo_painel, ds_observacao, qt_segundos_rolagem, qt_segundos_atualizacao, ds_sql FROM hp_painel ORDER BY nr_sequencia asc')
        paineis = cursor.fetchall()
        return render_template('lista_paineis.html', paineis=paineis)

# Rota para atualizar o per_page dinamicamente
@app.route('/atualizar_per_page', methods=['POST'])
def atualizar_per_page():
    print(request.form)
    try:
        per_page = int(request.form['per_page'])
    except ValueError:
        per_page = 12
    session['per_page'] = per_page
    return jsonify({'success': True})

# Rota visualizar painel
# Rota visualizar painel
@app.route('/visualizar_painel/<int:painel_id>', methods=['GET'])
def visualizar_painel(painel_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Consulta para obter o SQL, título do painel, tempo de rolagem e tempo de atualização
    sql_query = """
        SELECT ds_titulo_painel, ds_sql, qt_segundos_rolagem, qt_segundos_atualizacao, ds_sql_filtro, ie_tipo_filtro 
        FROM hp_painel
        WHERE nr_sequencia = :painel_id
    """
    
    cursor.execute(sql_query, {'painel_id': painel_id})
    painel = cursor.fetchone()

    if painel:
        ds_titulo_painel = painel[0] or " "  # Título do painel
        sql_body_query = painel[1] or " "  # SQL para obter os dados do painel
        segundos_rolagem = painel[2] or 10  # Se o campo estiver nulo, usa 10 segundos como padrão
        segundos_atualizacao = painel[3] or 30  # Se o campo estiver nulo, usa 30 segundos como padrão
        sql_filtro = painel[4] or "" # SQL do filtro
        tipo_filtro = painel[5] or "" # Tipo do filtro (unico ou multiselecao)
        # Obtém per_page da sessão ou usa o valor padrão
        
        per_page = session.get('per_page', 12)
        total = 0 # Define total aqui, antes do try
        try:
            # Obter títulos e atributos das colunas cadastradas
            colunas_query = """
            SELECT
                ds_titulo_coluna, ds_atributo, nm_class,  qt_tamanho, nr_seq_apresentacao, ie_hidden, nr_sequencia,  dt_atualizacao, dt_criacao, nm_usuario_atualizacao, nm_usuario_criacao,  ie_situacao, fk_nr_seq_painel, nvl(DS_COR_TEXTO,'#000000' ) AS DS_COR_TEXTO, nvl(QT_TAMANHO_FONTE,14) AS QT_TAMANHO_FONTE, nvl(DS_ALINHAMENTO,'center') AS DS_ALINHAMENTO, nvl(IE_FONT_BOLD,'N') AS IE_FONT_BOLD, nvl(IE_FONT_ITALIC,'N') AS IE_FONT_ITALIC
            FROM
                hp_painel_coluna
            WHERE
                fk_nr_seq_painel = :painel_id
            ORDER BY
                nr_seq_apresentacao
            """
            cursor.execute(colunas_query, {'painel_id': painel_id})
            colunas = cursor.fetchall()
            
            #tratamento das colunas
            colunas_tratadas = []
            for coluna in colunas:
                coluna_tratada = []
                for valor in coluna:
                    coluna_tratada.append(valor if valor is not None else "")
                colunas_tratadas.append(coluna_tratada)
            
            if not colunas:
                flash("Nenhuma coluna cadastrada para este painel.", "danger")
                return redirect(url_for('lista_paineis'))
            
            # Separar colunas visíveis e ocultas
            colunas_visiveis = [coluna for coluna in colunas if coluna[5] != 'H']  # Colunas onde ie_hidden != 'H'

            # Obter títulos e atributos
            titulos_visiveis = [{'titulo': coluna[0], 'tamanho': coluna[3]} for coluna in colunas_visiveis]
            
            # Obter todos os atributos (visíveis + ocultos)
            todos_atributos = [coluna[1] for coluna in colunas]
            atributos_tratados = [f"nvl({atributo}, '') AS {atributo}" for atributo in todos_atributos]

            # Montar o SQL ajustado
            sql_body_query = f"SELECT {', '.join(atributos_tratados)} FROM ({sql_body_query})"

            # Executa o SQL modificado para obter os dados do painel
            # Obter os valores do filtro
            valores_filtro = []
            if sql_filtro:
                cursor.execute(sql_filtro)
                valores_filtro = cursor.fetchall()

            # Obter os valores selecionados do filtro (se houver)
            filtro_selecionado = request.args.getlist('filtro')

            # Construir a cláusula WHERE com base no tipo de filtro e nos valores selecionados
            where_clause = ""
            if filtro_selecionado:
                if tipo_filtro == "unico":
                    where_clause = f" WHERE cd_convenio = '{filtro_selecionado[0]}'"
                elif tipo_filtro == "multiselecao":
                    where_clause = f" WHERE cd_convenio IN ({','.join([f"'{v}'" for v in filtro_selecionado])})"

            # Adicionar a cláusula WHERE à consulta principal
            sql_body_query = sql_body_query.replace("@sql_where", where_clause)

            cursor.execute(sql_body_query)
            resultados = cursor.fetchall()

            total = len(resultados) # Define o total aqui, dentro do try

            # Transformar resultados para substituir None por strings vazias
            def substituir_none_por_vazio(resultados, cursor):
                return [
                    {desc[0]: (valor if valor is not None else '') for desc, valor in zip(cursor.description, linha)}
                    for linha in resultados
                ]

            # Aplicar a transformação
            resultados_tratados = substituir_none_por_vazio(resultados, cursor)
            print("Resultados após transformação:", resultados_tratados)
            
        
            # Consulta para obter as regras de cor
            regras_query = """
                SELECT nr_sequencia, ds_valor, ds_cor, ie_icon_replace, nm_icon, ie_celula_linha, nm_class, nm_usuario_atualizacao, nm_usuario_criacao, dt_criacao, dt_atualizacao, (SELECT DS_TITULO_COLUNA FROM painel.hp_painel_coluna WHERE nr_sequencia = fk_nr_seq_painel_coluna ) as coluna
                FROM hp_painel_regra_cor
                WHERE fk_nr_seq_painel_coluna IN (
                    SELECT nr_sequencia FROM hp_painel_coluna WHERE fk_nr_seq_painel = :painel_id)
            """
            cursor.execute(regras_query, {'painel_id': painel_id})
            regras = cursor.fetchall()

            # Coleta das regras em uma lista
            regras_resultados = []
            for idx, regra in enumerate(regras):
                print(f"Posição {idx}: {regra}")  # Exibe a posição e os valores da tupla
                nr_sequencia, ds_valor, ds_cor, ie_icon_replace, nm_icon, ie_celula_linha, nm_class, nm_usuario_atualizacao, nm_usuario_criacao, dt_criacao, dt_atualizacao, coluna = regra

                regras_resultados.append({
                    'nr_sequencia': nr_sequencia,
                    'ds_valor': ds_valor if ds_valor is not None else '',
                    'ds_cor': ds_cor if ds_cor is not None else '',
                    'ie_icon_replace': ie_icon_replace if ie_icon_replace is not None else '',
                    'nm_icon': nm_icon if nm_icon is not None else '',
                    'ie_celula_linha': ie_celula_linha if ie_celula_linha is not None else '',
                    'nm_class': nm_class if nm_class is not None else '',
                    'nm_usuario_atualizacao': nm_usuario_atualizacao if nm_usuario_atualizacao is not None else '',
                    'nm_usuario_criacao': nm_usuario_criacao if nm_usuario_criacao is not None else '',
                    'dt_criacao': dt_criacao if dt_criacao is not None else '',
                    'dt_atualizacao': dt_atualizacao if dt_atualizacao is not None else '',
                    'coluna': coluna if coluna is not None else ''
                })
            
            # Adicionar a consulta para os dashboards
            dashboards_query = """
                SELECT ds_titulo, ds_cor, ds_sql
                FROM hp_painel_dashboard
                WHERE fk_nr_seq_painel = :painel_id
            """
            cursor.execute(dashboards_query, {'painel_id': painel_id})
            dashboards = cursor.fetchall()

            # Para cada dashboard, executa o SQL armazenado e coleta os resultados
            dashboards_resultados = []
            for dashboard in dashboards:
                ds_titulo_dashboard = dashboard[0]
                ds_cor_dashboard = dashboard[1]
                ds_sql_dashboard = dashboard[2]

                # Executa o SQL do dashboard
                cursor.execute(ds_sql_dashboard)
                resultado_dashboard = cursor.fetchall()
                
                # Tratamento para remover caracteres indesejados
                dados_tratados = [item[0] for item in resultado_dashboard]

                # Adiciona os resultados e os dados do dashboard a uma lista
                dashboards_resultados.append({
                    'titulo': ds_titulo_dashboard,
                    'cor': ds_cor_dashboard,
                    'dados': dados_tratados
                })
                print('teste: ', dashboards_resultados)
            # Consulta para obter as legendas
            legendas_query = """
                SELECT ds_legenda, ds_cor
                FROM hp_painel_legenda
                WHERE fk_nr_seq_painel = :painel_id
            """
            cursor.execute(legendas_query, {'painel_id': painel_id})
            legendas = cursor.fetchall()

            # Coleta as legendas em uma lista
            legendas_resultados = []
            for legenda in legendas:
                ds_legendas = legenda[0]
                ds_cor_legendas = legenda[1]

                # Adiciona os resultados e os dados da legenda à lista
                legendas_resultados.append({
                    'titulo': ds_legendas,
                    'cor': ds_cor_legendas
                })
            
            
        # Monta o dicionário com as regras, separando 'C' (célula) e 'L' (linha)
            regras_por_valor = {}
            for regra in regras_resultados:
                ds_valor = regra['ds_valor']
                ds_cor = regra['ds_cor']
                ie_celula_linha = regra['ie_celula_linha']  # 'C' ou 'L'
                ie_icon_replace = regra['ie_icon_replace']
                nm_icon = regra['nm_icon']
                coluna = regra['coluna']  # Coluna de gatilho

                print(f"Processando regra - Valor: {ds_valor}, Cor: {ds_cor}, Tipo: {ie_celula_linha}, Ícone: {nm_icon}, Coluna: {coluna}")

                if ds_valor not in regras_por_valor:
                    regras_por_valor[ds_valor] = {}
                regras_por_valor[ds_valor][ie_celula_linha] = {
                    'ds_cor': ds_cor,
                    'ie_icon_replace': ie_icon_replace,
                    'nm_icon': nm_icon,
                    'coluna': coluna  # Guardar o nome da coluna de gatilho
                }

            # Obter os nomes das colunas para encontrar o índice da coluna de gatilho
            nomes_colunas = [coluna[0] for coluna in colunas]
            print(f"Nomes das colunas disponíveis: {nomes_colunas}")

            # Agora, calculando o índice da coluna de gatilho dinamicamente
            try:
                gatilho_linha_index = nomes_colunas.index(coluna)  # Encontrar o índice da coluna de gatilho
                print(f"A coluna '{coluna}' está na posição {gatilho_linha_index}")
            except ValueError:
                print(f"ERRO: A coluna '{coluna}' não foi encontrada!")
                gatilho_linha_index = -1  # Define um valor de fallback caso não encontre a coluna

            # Faz apenas UM loop, aplicando as regras de célula ou linha
            for idx, row in enumerate(resultados):
                row_list = list(row)
                print(f"Processando linha {idx}: {row_list}")

                # 1) Verifica se há regra de linha para o valor na coluna de gatilho
                valor_gatilho_linha = row_list[gatilho_linha_index] if gatilho_linha_index >= 0 else None
                print(f"Valor de gatilho na linha {idx}: {valor_gatilho_linha}")
                
                line_rule = None
                if valor_gatilho_linha in regras_por_valor and 'L' in regras_por_valor[valor_gatilho_linha]:
                    line_rule = regras_por_valor[valor_gatilho_linha]['L']
                    print(f"Regra de linha encontrada para {valor_gatilho_linha}: {line_rule}")

                # 2) Percorre cada coluna para decidir se aplica regra de célula ou de linha
                for col_index, valor_celula in enumerate(row_list):
                    cell_rule = None
                    if valor_celula in regras_por_valor and 'C' in regras_por_valor[valor_celula]:
                        cell_rule = regras_por_valor[valor_celula]['C']
                        print(f"Regra de célula encontrada na coluna {col_index} para valor {valor_celula}: {cell_rule}")

                    if cell_rule:
                        ds_cor = cell_rule['ds_cor']
                        ie_icon_replace = cell_rule['ie_icon_replace']
                        nm_icon = cell_rule['nm_icon']

                        if ie_icon_replace == 'S':
                            if nm_icon and nm_icon.strip() not in [None, '', ' ', 'null']:
                                row_list[col_index] = f'<i class="formatado-celula {nm_icon}" style="color:{ds_cor}"></i>'
                            else:
                                row_list[col_index] = f'<span class="formatado-celula celula-cor" style="background-color:{ds_cor}; display:block; padding:5px; width:100%; height:100%">&nbsp;</span>'
                        else:
                            row_list[col_index] = f'<span class="formatado-celula celula-cor" style="background-color:{ds_cor}; display:block; padding:5px; width:100%; height:100%">{valor_celula}</span>'
                    elif line_rule:
                        ds_cor = line_rule['ds_cor']
                        ie_icon_replace = line_rule['ie_icon_replace']
                        nm_icon = line_rule['nm_icon']

                        if ie_icon_replace == 'S':
                            if nm_icon and nm_icon.strip() not in [None, '', ' ', 'null']:
                                row_list[col_index] = f'<i class="formatado-linha {nm_icon}" style="color:{ds_cor}"></i>'
                            else:
                                row_list[col_index] = f'<span class="formatado-linha linha-cor" style="background-color:{ds_cor}; display:block; padding:5px;">&nbsp;</span>'
                        else:
                            row_list[col_index] = f'<span class="formatado-linha linha-cor" style="background-color:{ds_cor}; display:block; padding:5px;">{valor_celula if valor_celula not in [None, '', ' '] else "&nbsp;"}</span>'
                    else:
                        row_list[col_index] = valor_celula
                
                print(f"Linha {idx} após aplicação das regras: {row_list}")
                resultados[idx] = tuple(row_list)

                    


        except oracledb.DatabaseError as e:
            flash(f"Erro ao executar o SQL do painel: {str(e)}", "danger")
            return redirect(url_for('lista_paineis'))

        finally:
            cursor.close()
            connection.close()
        
        indices_visiveis = [i for i, coluna in enumerate(colunas) if coluna[5] != 'H']  # Índices das colunas visíveis
        return render_template('visualizar_painel.html',
                            resultados=resultados,  # Enviar todos os resultados
                            titulo_painel=ds_titulo_painel,
                            titulos=titulos_visiveis,
                            painel_id=painel_id,
                            total=total,
                            per_page=per_page,
                            indices_visiveis=indices_visiveis,  # Índices para filtrar os valores no template
                            segundos_rolagem=segundos_rolagem,
                            segundos_atualizacao=segundos_atualizacao,
                            dashboards=dashboards_resultados,  # Passar dashboards e resultados para o template
                            legendas=legendas_resultados,
                            regras=regras_resultados,  # Passar as regras para o template
                            colunas=colunas_tratadas)
    else:
        return "Painel não encontrado", 404
    


# Rota cadastrar painel
@app.route('/cadastrar_painel', methods=['GET', 'POST'])
def cadastrar_painel():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        sql_query = request.form['sql_query']
        segundos_atualizacao = request.form['segundos_atualizacao']
        segundos_rolagem = request.form['segundos_rolagem']
        dt_atualizacao = datetime.now()
        dt_criacao = datetime.now()
        nm_usuario_criacao = "DMMSANTOS"
        ie_situacao = 'A'
        sql_filtro = request.form.get('sql_filtro')
        tipo_filtro = request.form.get('tipo_filtro')

        with get_db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT PAINEL_SEQ.NEXTVAL FROM dual")
                painel_id = cursor.fetchone()[0]

                # Inserir o painel
                cursor.execute(""" 
                    INSERT INTO hp_painel (nr_sequencia, ds_titulo_painel, ds_observacao, qt_segundos_rolagem, 
                                        qt_segundos_atualizacao, ds_sql, dt_atualizacao, dt_criacao, 
                                        nm_usuario_criacao, ie_situacao, ds_sql_filtro, ie_tipo_filtro)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)
                """, (painel_id, titulo, descricao, segundos_rolagem, segundos_atualizacao, 
                    sql_query, dt_atualizacao, dt_criacao, nm_usuario_criacao, ie_situacao, sql_filtro, tipo_filtro))

                connection.commit()
                flash("Painel cadastrado com sucesso!")
                
                # Redirecionar para a rota editar_painel com o painel_id
                return redirect(url_for('editar_painel', painel_id=painel_id))
                
            except oracledb.IntegrityError as e:
                error, = e.args
                if error.code == 1:  # Para ORA-00001 (violação de chave primária)
                    flash("Erro: já existe um painel com este ID.", "danger")
                else:
                    flash(f"Erro ao cadastrar painel: {str(e)}", "danger")

    return render_template('cadastrar_painel.html')
#rota editar painel
@app.route('/editar_painel/<int:painel_id>', methods=['GET', 'POST'])
def editar_painel(painel_id):
    # Se o método for POST, o painel está sendo salvo
    if request.method == 'POST':
        # Capturar dados do formulário
        ds_titulo_painel = request.form.get('ds_titulo_painel')
        ds_observacao = request.form.get('ds_observacao')
        qt_segundos_rolagem = request.form.get('qt_segundos_rolagem')
        qt_segundos_atualizacao = request.form.get('qt_segundos_atualizacao')
        ds_sql = request.form.get('ds_sql')
        sql_filtro = request.form.get('sql_filtro')
        tipo_filtro = request.form.get('tipo_filtro')

         # Validar se ds_titulo_painel não está vazio
        if not ds_titulo_painel:
            flash("O título do painel é obrigatório.", "danger")
            return redirect(url_for('editar_painel', painel_id=painel_id))

        # Rota editar painel/ atualizar
        with get_db_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE hp_painel
                SET ds_titulo_painel = :1,
                    ds_observacao = :2,
                    qt_segundos_rolagem = :3,
                    qt_segundos_atualizacao = :4,
                    ds_sql = :5,
                    dt_atualizacao = SYSDATE,
                    nm_usuario_atualizacao = :6,
                    ds_sql_filtro = :7,
                    ie_tipo_filtro = :8
                WHERE nr_sequencia = :9
            """, (
                ds_titulo_painel,
                ds_observacao,
                qt_segundos_rolagem,
                qt_segundos_atualizacao,
                ds_sql,
                "DMMSANTOS",  # Substitua pelo nome de usuário adequado
                sql_filtro,
                tipo_filtro,
                painel_id
            ))
            connection.commit()

        flash("Painel atualizado com sucesso.", "success")
        return redirect(url_for('editar_painel', painel_id=painel_id))

    # Buscar as informações do painel
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT ds_titulo_painel, ds_observacao, qt_segundos_rolagem, qt_segundos_atualizacao, ds_sql,ds_sql_filtro, ie_tipo_filtro 
            FROM hp_painel 
            WHERE nr_sequencia = :1
        """, (painel_id,))
        painel = cursor.fetchone()

        if not painel:
            flash("Painel não encontrado.", "danger")
            return redirect(url_for('cadastrar_painel'))

        # Buscar colunas associadas ao painel
        cursor.execute("""
            SELECT nr_sequencia, ds_titulo_coluna, ds_atributo, nvl(nm_class,' ') as nm_class, qt_tamanho, nr_seq_apresentacao, nvl(ie_hidden,' ') as ie_hidden, nvl(QT_TAMANHO_FONTE, 14) as QT_TAMANHO_FONTE, nvl(DS_COR_TEXTO, '#000000') as DS_COR_TEXTO, nvl(DS_ALINHAMENTO, 'left') as DS_ALINHAMENTO, nvl(IE_FONT_BOLD,' ') as IE_FONT_BOLD, nvl(IE_FONT_ITALIC,' ') as IE_FONT_ITALIC
            FROM hp_painel_coluna
            WHERE fk_nr_seq_painel = :1
            ORDER BY nr_seq_apresentacao
        """, (painel_id,))
        colunas = cursor.fetchall()
        
        colunas_tratadas = []
        for coluna in colunas:
            coluna_tratada = []
            for valor in coluna:
                coluna_tratada.append(valor if valor is not None else "")
            colunas_tratadas.append(coluna_tratada)

        # Buscar dashboards associados ao painel
        cursor.execute("""
            SELECT nr_sequencia, ds_titulo, ds_sql, ds_cor, nvl(QT_TAMANHO_FONTE, 14) as QT_TAMANHO_FONTE, nvl(DS_COR_TEXTO, '#000000') as DS_COR_TEXTO, nvl(DS_ALINHAMENTO, 'center') as DS_ALINHAMENTO, nvl(IE_FONT_BOLD,' ') as IE_FONT_BOLD, nvl(IE_FONT_ITALIC,' ') as IE_FONT_ITALIC
            FROM hp_painel_dashboard 
            WHERE fk_nr_seq_painel = :1
        """, (painel_id,))
        dashboards = cursor.fetchall()

        # Buscar legendas associadas ao painel
        cursor.execute("""
            SELECT nr_sequencia, ds_legenda, ds_cor, nr_seq_apresentacao
            FROM hp_painel_legenda 
            WHERE fk_nr_seq_painel = :1
        """, (painel_id,))
        legendas = cursor.fetchall()

        # Buscar regras de cores associadas ao painel
        cursor.execute("""
            SELECT nr_sequencia, ds_valor, ds_cor, nvl(ie_icon_replace,' ') as ie_icon_replace, nm_icon, ie_celula_linha, nvl(nm_class,' ') as nm_class, nm_usuario_atualizacao, nm_usuario_criacao, dt_criacao, dt_atualizacao, (SELECT DS_TITULO_COLUNA FROM painel.hp_painel_coluna WHERE nr_sequencia = fk_nr_seq_painel_coluna ) as coluna
            FROM hp_painel_regra_cor 
            WHERE fk_nr_seq_painel_coluna IN (
                SELECT nr_sequencia FROM hp_painel_coluna WHERE fk_nr_seq_painel = :1
            )
        """, (painel_id,))
        regras = cursor.fetchall()
        
        # Buscar graficos associados ao painel
        cursor.execute("""
            SELECT nr_sequencia, ds_titulo, ds_sql, nr_seq_apresentacao, ds_tipo_grafico
            FROM hp_painel_grafico
            WHERE fk_nr_seq_painel = :1
        """,(painel_id,))
        graficos = cursor.fetchall()


    return render_template(
        'editar_painel.html',
        painel=painel,
        colunas=colunas,
        dashboards=dashboards,
        legendas=legendas,
        regras=regras,
        graficos=graficos,
        painel_id=painel_id
        
    )


@app.route('/excluir_painel', methods=['POST'])
def excluir_painel():
    painel_id = request.form.get('nr_sequencia')
    try:
        painel_id = int(painel_id)  # Tente converter para inteiro
    except ValueError:
        return jsonify(success=False, message='ID do painel é inválido.')

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM HP_PAINEL WHERE NR_SEQUENCIA = :1", (painel_id,))
        connection.commit()
    
    return jsonify(success=True, message='Painel excluído com sucesso!')

# Rota para duplicar painel
@app.route('/duplicar_painel/<int:painel_id>', methods=['POST'])
def duplicar_painel(painel_id):
    print(f"Duplicando painel com ID: {painel_id}")
    with get_db_connection() as connection:
        cursor = connection.cursor()
        try:
            # Passo 1: Buscar o painel original
            print("Buscando o painel original...")
            cursor.execute('SELECT * FROM hp_painel WHERE nr_sequencia = :1', (painel_id,))
            painel = cursor.fetchone()
            print(f"Painel original: {painel}")
            
            if painel is None:
                flash('Painel não encontrado.')
                return redirect(url_for('lista_paineis'))

            # Passo 2: Obter novo ID para o painel duplicado
            print("Gerando novo ID para o painel duplicado...")
            cursor.execute("SELECT PAINEL_SEQ.NEXTVAL FROM dual")
            novo_painel_id = cursor.fetchone()[0]
            print(f"Novo painel ID: {novo_painel_id}")
            
            # Inserir novo painel com as informações duplicadas do painel original
            print("Inserindo o novo painel duplicado...")
            
            # Supondo que a lista painel deveria ter 12 itens
            expected_length = 12
            painel = list(painel)  # Garante que painel é uma lista e não uma tupla

            # Preenche valores ausentes com None ou um valor padrão, se necessário
            if len(painel) < expected_length:
                painel.extend([None] * (expected_length - len(painel)))
                print(f"novo_painel_id: {novo_painel_id} (tipo: {type(novo_painel_id)})")
            print(f"qt_segundos_atualizacao: {painel[8]} (tipo: {type(painel[8])})")
            print(f"qt_segundos_rolagem: {painel[9]} (tipo: {type(painel[9])})")
            print(f"ie_situacao: {painel[10]} (tipo: {type(painel[10])})") if painel is None else f""

            # Executa a inserção
            cursor.execute("""
            INSERT INTO hp_painel (
                nr_sequencia, dt_criacao, dt_atualizacao, nm_usuario_criacao, nm_usuario_atualizacao,
                ds_titulo_painel, ds_observacao, qt_segundos_atualizacao, qt_segundos_rolagem, ie_situacao, ds_sql
            ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)
        """, (
            novo_painel_id,
            datetime.now(),
            datetime.now(),
            "DMMSANTOS",
            "DMMSANTOS",
            "Cópia " + painel[5] if painel[5] else "Cópia Sem Nome",
            painel[6],
            painel[7],  # qt_segundos_atualizacao
            painel[8],  # qt_segundos_rolagem
            painel[9], # ie_situacao
            painel[10]  # ds_sql
        ))


            # Passo 3: Duplicar as colunas associadas ao painel
            print("Buscando e duplicando colunas associadas...")
            cursor.execute('SELECT * FROM hp_painel_coluna WHERE fk_nr_seq_painel = :1', (painel_id,))
            colunas = cursor.fetchall()
            print(f"Colunas encontradas: {colunas}")

            for coluna in colunas:
                cursor.execute("SELECT COLUNA_SEQ.NEXTVAL FROM dual")
                nova_coluna_id = cursor.fetchone()[0]
                
                print(f"Inserindo nova coluna com ID: {nova_coluna_id}")

                # Impressão dos valores a serem inseridos
                print(f"Valores a serem inseridos: ID: {nova_coluna_id}, "
                        f"Título: {coluna[9]}, "
                        f"Atributo: {coluna[1]}, "
                        f"Novo Painel ID: {novo_painel_id}, "
                        f"Data de Criação: {datetime.now()}, "
                        f"Data de Atualização: {datetime.now()}, "
                        f"Criador: DMMSANTOS, "
                        f"Atualizador: DMMSANTOS, "
                        f"Tamanho: {coluna[8]}, "            
                        f"Seq Apresentação: {coluna[6]}, "   
                        f"Situação: {coluna[7]}")           
                try:
                    # Validação dos dados
                    qt_tamanho = coluna[8]             # qt_tamanho
                    nr_seq_apresentacao = coluna[6]    # nr_seq_apresentacao
                    ie_situacao = coluna[7]            # ie_situacao

                    cursor.execute("""
                        INSERT INTO hp_painel_coluna (
                            nr_sequencia, ds_titulo_coluna, ds_atributo, fk_nr_seq_painel,
                            dt_criacao, dt_atualizacao, nm_usuario_criacao, nm_usuario_atualizacao,
                            qt_tamanho, nr_seq_apresentacao, ie_situacao, ie_hidden, nm_class
                        ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
                    """, (
                        nova_coluna_id,                 # nr_sequencia
                        coluna[9],                      # ds_titulo_coluna
                        coluna[1],                      # ds_atributo
                        novo_painel_id,                 # fk_nr_seq_painel
                        datetime.now(),                 # dt_criacao
                        datetime.now(),                 # dt_atualizacao
                        "DMMSANTOS",                    # nm_usuario_criacao
                        "DMMSANTOS",                    # nm_usuario_atualizacao
                        qt_tamanho,                     # qt_tamanho
                        nr_seq_apresentacao,            # nr_seq_apresentacao
                        ie_situacao,                    # ie_situacao
                        coluna[11],                     # ie_hidden
                        coluna[12]                      # nm_class
                    ))
                except ValueError as e:
                    print(f"Erro ao converter valores: {e}")
                    continue  # Pula para a próxima coluna se houver erro
                except Exception as e:
                    print(f"Erro ao inserir nova coluna: {e}")
                    
            # Passo 4: Duplicar dashboards associados ao painel
           
            cursor.execute('SELECT * FROM hp_painel_dashboard WHERE fk_nr_seq_painel = :1', (painel_id,))
            dashboards = cursor.fetchall()

            for dashboard in dashboards:
                cursor.execute("SELECT DASHBOARD_SEQ.NEXTVAL FROM dual")
                novo_dashboard_id = cursor.fetchone()[0]
               # print(f"Inserindo dashboard: nr_sequencia={novo_dashboard_id}, ds_cor={dashboard[1]}, dt_criacao={datetime.now()}, dt_atualizacao={datetime.now()}, nm_usuario_criacao='DMMSANTOS', nm_usuario_atualizacao='DMMSANTOS', ds_sql={dashboard[6]}, ds_titulo={dashboard[7]}, fk_nr_seq_painel={novo_painel_id}")

                cursor.execute("""
                INSERT INTO hp_painel_dashboard (
                    nr_sequencia, ds_cor, dt_criacao, dt_atualizacao, nm_usuario_criacao, nm_usuario_atualizacao, ds_sql, ds_titulo, fk_nr_seq_painel, QT_TAMANHO_FONTE, DS_COR_TEXTO, DS_ALINHAMENTO, IE_FONT_BOLD, IE_FONT_ITALIC
                ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14)
            """, (
                novo_dashboard_id,         # nr_sequencia
                dashboard[1],              # ds_cor
                datetime.now(),            # dt_criacao
                datetime.now(),            # dt_atualizacao
                "DMMSANTOS",               # nm_usuario_criacao
                "DMMSANTOS",               # nm_usuario_atualizacao
                dashboard[6],              # ds_sql
                dashboard[7],              # ds_titulo
                novo_painel_id,             # fk_nr_seq_painel
                dashboard[8],
                dashboard[9],
                dashboard[10],
                dashboard[11],
                dashboard[12]
            ))
                            

            # Passo 5: Duplicar legendas associadas ao painel
            print("Buscando e duplicando legendas associadas...")
            cursor.execute('SELECT * FROM hp_painel_legenda WHERE fk_nr_seq_painel = :1', (painel_id,))
            legendas = cursor.fetchall()

            for legenda in legendas:
                cursor.execute("SELECT LEGENDA_SEQ.NEXTVAL FROM dual")
                nova_legenda_id = cursor.fetchone()[0]
                
                cursor.execute("""
        INSERT INTO hp_painel_legenda (
            NR_SEQUENCIA, DS_COR, DS_LEGENDA, DT_ATUALIZACAO, DT_CRIACAO,
            NM_USUARIO_ATUALIZACAO, NM_USUARIO_CRIACAO, NR_SEQ_APRESENTACAO,
            IE_SITUACAO, FK_NR_SEQ_PAINEL
        ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
    """, (
        nova_legenda_id,           # NR_SEQUENCIA
        legenda[1],                # DS_COR
        legenda[2],                # DS_LEGENDA
        datetime.now(),            # DT_ATUALIZACAO
        datetime.now(),            # DT_CRIACAO
        "DMMSANTOS",               # NM_USUARIO_ATUALIZACAO
        "DMMSANTOS",               # NM_USUARIO_CRIACAO
        legenda[7],                # NR_SEQ_APRESENTACAO
        legenda[8],                # IE_SITUACAO
        novo_painel_id             # FK_NR_SEQ_PAINEL
    ))
            # Passo 6: Duplicar regras de cor associadas ao painel
            print("Buscando e duplicando regras de cor associadas...")
            cursor.execute('SELECT * FROM hp_painel_regra_cor WHERE fk_nr_seq_painel_coluna IN (SELECT nr_sequencia FROM hp_painel_coluna WHERE fk_nr_seq_painel = :1)', (painel_id,))
            regras_cor = cursor.fetchall()

            for regra in regras_cor:
                cursor.execute("SELECT REGRA_SEQ.NEXTVAL FROM dual")
                nova_regra_id = cursor.fetchone()[0]
                
                cursor.execute("""
        INSERT INTO hp_painel_regra_cor (
            NR_SEQUENCIA, DS_COR, DT_ATUALIZACAO, DT_CRIACAO, NM_ICON,
            IE_CELULA_LINHA, NM_USUARIO_ATUALIZACAO, NM_USUARIO_CRIACAO,
            IE_ICON_REPLACE, IE_SITUACAO, DS_VALOR, FK_NR_SEQ_PAINEL_COLUNA, NM_CLASS
        ) VALUES (:1, :2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :3, :4, :5, :6, :7, :8, :9, :10, :11)
    """, (
        nova_regra_id,      # NR_SEQUENCIA
        regra[1],           # DS_COR
        regra[4],           # NM_ICON
        regra[5],           # IE_CELULA_LINHA
        "DMMSANTOS",        # NM_USUARIO_ATUALIZACAO
        "DMMSANTOS",        # NM_USUARIO_CRIACAO
        regra[8],           # IE_ICON_REPLACE (ajustado para índice correto)
        regra[9],           # IE_SITUACAO
        regra[10],          # DS_VALOR
        nova_coluna_id,     # FK_NR_SEQ_PAINEL_COLUNA
        regra[12]           # NM_CLASS
    ))

                    
                    

            # Confirmar as transações de duplicação
            connection.commit()
            flash('Painel duplicado com sucesso!')
            return redirect(url_for('visualizar_painel', painel_id=novo_painel_id))

        except Exception as e:
            connection.rollback()
            flash(f"Erro ao duplicar painel: {str(e)}")
            print(f"Erro ao duplicar painel: {str(e)}")
            return redirect(url_for('lista_paineis'))
        finally:
            cursor.close()
# Rota para cadastrar um novo gráfico
@app.route('/cadastrar_grafico', methods=['POST'])
def cadastrar_grafico():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        titulo_grafico = request.form.get('titulo_grafico')
        sql_grafico = request.form.get('sql_grafico')
        numero_apre_grafico = request.form.get('numero_apre_grafico')
        tipo_grafico = request.form.get('tipo_grafico')
        painel_id = request.form.get('painel_id')

        # Obter o próximo valor da sequência
        cursor.execute("SELECT PAINEL.GRAFICO_SEQ.NEXTVAL FROM dual")
        next_grafico_id = cursor.fetchone()[0]

        # Inserir o novo gráfico na tabela HP_PAINEL_GRAFICO
        cursor.execute("""
            INSERT INTO HP_PAINEL_GRAFICO (nr_sequencia, ds_titulo, ds_sql, nr_seq_apresentacao, ds_tipo_grafico, fk_nr_seq_painel, dt_atualizacao, dt_criacao, nm_usuario_criacao)
            VALUES (:nr_sequencia, :titulo_grafico, :sql_grafico, :numero_apre_grafico, :tipo_grafico, :painel_id, SYSDATE, SYSDATE, 'ADMIN')
        """, nr_sequencia = next_grafico_id, titulo_grafico=titulo_grafico, sql_grafico=sql_grafico, numero_apre_grafico=numero_apre_grafico, tipo_grafico=tipo_grafico, painel_id=painel_id)

        connection.commit()
        return jsonify({'success': True, 'message': 'Gráfico cadastrado com sucesso!'})
    except oracledb.DatabaseError as e:
        connection.rollback()
        print(f"Erro oracledb.DatabaseError ao cadastrar gráfico: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Rota para editar um gráfico existente
@app.route('/editar_grafico', methods=['POST'])
def editar_grafico():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        nr_sequencia = request.form.get('nr_sequencia')
        titulo_grafico = request.form.get('titulo_grafico')
        sql_grafico = request.form.get('sql_grafico')
        numero_apre_grafico = request.form.get('numero_apre_grafico')
        tipo_grafico = request.form.get('tipo_grafico')
        
        # Atualiza o gráfico na tabela HP_PAINEL_GRAFICO
        cursor.execute("""
            UPDATE HP_PAINEL_GRAFICO
            SET ds_titulo = :titulo_grafico, ds_sql = :sql_grafico, nr_seq_apresentacao = :numero_apre_grafico, ds_tipo_grafico = :tipo_grafico , dt_atualizacao = SYSDATE, nm_usuario_atualizacao = 'ADMIN'
            WHERE nr_sequencia = :nr_sequencia
        """, titulo_grafico=titulo_grafico, sql_grafico=sql_grafico, numero_apre_grafico=numero_apre_grafico, tipo_grafico=tipo_grafico, nr_sequencia=nr_sequencia)
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Gráfico editado com sucesso!'})
    except oracledb.DatabaseError as e:
        connection.rollback()
        print(f"Erro ao editar gráfico: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        connection.close()

# Rota para excluir um gráfico
@app.route('/excluir_grafico/<int:graficoId>', methods=['POST'])
def excluir_grafico(graficoId):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Excluir o gráfico da tabela HP_PAINEL_GRAFICO
        cursor.execute("DELETE FROM HP_PAINEL_GRAFICO WHERE nr_sequencia = :graficoId", graficoId=graficoId)
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Gráfico excluído com sucesso!'})
    except oracledb.DatabaseError as e:
        connection.rollback()
        print(f"Erro ao excluir Gráfico: {e}")
        return jsonify({'success': False, 'message': 'Erro ao excluir Gráfico: ' + str(e)})
    finally:
        cursor.close()
        connection.close()

# Rota para duplicar um Gráfico existente
@app.route('/duplicar_grafico', methods=['POST'])
def duplicar_grafico():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        grafico_id = request.form.get('grafico_id')
        
        # Consulta o Gráfico que será duplicado
        cursor.execute("SELECT ds_titulo, ds_sql, nr_seq_apresentacao, ds_tipo_grafico, fk_nr_seq_painel FROM HP_PAINEL_GRAFICO WHERE nr_sequencia = :grafico_id", grafico_id=grafico_id)
        grafico = cursor.fetchone()

        if not grafico:
            return jsonify({'success': False, 'message': 'Gráfico não encontrado.'})
        
        titulo, sql, nr_apresentacao, tipo, fk_painel_id = grafico
        
        # Obter o próximo valor da sequência
        cursor.execute("SELECT PAINEL.GRAFICO_SEQ.NEXTVAL FROM dual")
        next_grafico_id = cursor.fetchone()[0]

        # Inserir o Gráfico duplicado
        cursor.execute("""
            INSERT INTO HP_PAINEL_GRAFICO (nr_sequencia, ds_titulo, ds_sql, nr_seq_apresentacao, ds_tipo_grafico, fk_nr_seq_painel, dt_atualizacao, dt_criacao, nm_usuario_criacao)
            VALUES (:nr_sequencia, :titulo, :sql, :nr_apresentacao, :tipo, :fk_painel_id, SYSDATE, SYSDATE, 'ADMIN')
        """, nr_sequencia=next_grafico_id, titulo=titulo, sql=sql, nr_apresentacao=nr_apresentacao, tipo=tipo, fk_painel_id=fk_painel_id)

        connection.commit()
        return jsonify({'success': True, 'message': 'Gráfico duplicado com sucesso!'})
    except oracledb.DatabaseError as e:
        connection.rollback()
        print(f"Erro ao duplicar gráfico: {e}")
        return jsonify({'success': False, 'message': 'Erro ao duplicar gráfico: ' + str(e)})
    finally:
        cursor.close()
        connection.close()


#rota para visualizar grafico
@app.route('/visualizar_painel_grafico/<int:painel_id>', methods=['GET'])
def visualizar_painel_grafico(painel_id):
    try:
        engine = create_engine(
            f"oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?service_name={DB_SERVICE_NAME}"
        )

        with engine.connect() as conn:
            # Obter título do painel
            painel_query = text("""
                SELECT ds_titulo_painel FROM hp_painel WHERE nr_sequencia = :painel_id
            """)
            painel = conn.execute(painel_query, {'painel_id': painel_id}).fetchone()

            if not painel:
                return jsonify({"error": "Painel não encontrado"}), 404

            ds_titulo_painel = painel[0] or " "

            # Obter dados dos gráficos
            graficos_query = text(""" 
                SELECT nr_sequencia, ds_titulo, ds_sql, nr_seq_apresentacao, ds_tipo_grafico
                FROM hp_painel_grafico
                WHERE fk_nr_seq_painel = :painel_id
                ORDER BY nr_seq_apresentacao
            """)
            graficos = conn.execute(graficos_query, {'painel_id': painel_id}).fetchall()

            if not graficos:
                return jsonify({"error": "Nenhum gráfico encontrado para o painel"}), 404

            # Log dos dados retornados
            print(f"Dados dos gráficos retornados: {graficos}")

            graficos_data = {}
            for nr_sequencia, titulo, sql, num_apres, tipo in graficos:
                print(f"Processando gráfico: {nr_sequencia}, Tipo: {tipo}, SQL: {sql}")
                
                if not sql or not sql.strip():
                    graficos_data[f'grafico_{nr_sequencia}'] = {
                        'image': None,
                        'titulo': titulo,
                        'tipo': tipo,
                        'error': 'SQL vazio para este gráfico.'
                    }
                    continue
                # Obtenha as legendas associadas ao gráfico
                legendas_query = text("""
                SELECT l.ds_legenda, l.ds_cor
                FROM hp_painel_legenda l
                JOIN hp_painel_grafico_legenda gl ON l.nr_sequencia = gl.fk_nr_seq_legenda
                WHERE gl.fk_nr_seq_grafico = :nr_sequencia
                """)

                legendas_result = conn.execute(legendas_query, {'nr_sequencia': nr_sequencia}).fetchall()
                legendas = [{'ds_legenda': legenda[0], 'ds_cor': legenda[1]} for legenda in legendas_result]

                try:
                    df = pd.read_sql_query(text(sql), con=engine)
                    
                    # Verificação do DataFrame
                    print(f"DataFrame carregado: \n{df}")
                    
                    if df.empty:
                        graficos_data[f'grafico_{nr_sequencia}'] = {
                            'image': None,
                            'titulo': titulo,
                            'tipo': tipo,
                            'error': 'Sem dados para gerar o gráfico.'
                        }
                        continue
                    
                    # Garantir que temos pelo menos 2 colunas
                    if len(df.columns) < 2:
                        print(f"DataFrame com menos de 2 colunas. Colunas: {df.columns}")
                        graficos_data[f'grafico_{nr_sequencia}'] = {
                            'image': None,
                            'titulo': titulo,
                            'tipo': tipo,
                            'error': 'O DataFrame não possui colunas suficientes para gerar o gráfico.'
                        }
                        continue

                    # Gerar o gráfico
                    image_base64 = gerar_grafico(df, titulo, tipo, len(legendas) > 0, legendas)

                    graficos_data[f'grafico_{nr_sequencia}'] = {
                        'image': image_base64,
                        'titulo': titulo,
                        'tipo': tipo,
                        'legendas': legendas
                    }

                except Exception as e:
                    print(f"Erro ao processar gráfico {nr_sequencia}: {e}")
                    graficos_data[f'grafico_{nr_sequencia}'] = {
                        'image': None,
                        'titulo': titulo,
                        'tipo': tipo,
                        'error': f"Erro ao executar SQL: {str(e)}"
                    }
        print(f"graficos_data: {graficos_data}")
        return render_template('visualizar_painel_grafico.html',graficos_data=graficos_data, painel_id = painel_id)

    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"error": "Erro inesperado"}), 500



# ---------------- FIM Rotas de Painel ----------------

# ---------------- INÍCIO Rotas de Colunas ----------------

# Rota cadastrar coluna
@app.route('/adicionar_coluna/<int:painel_id>', methods=['POST'])
def configurar_colunas(painel_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        
        # Buscar o SQL do painel criado
        cursor.execute("SELECT ds_sql FROM hp_painel WHERE nr_sequencia = :painel_id", {'painel_id': painel_id})
        painel = cursor.fetchone()
        
        if not painel:
            return jsonify({'success': False, 'error': 'Painel não encontrado'}), 404

        # Captura dos dados do formulário (enviados via modal)
        titulo_coluna = request.form.get('titulo_coluna')
        atributo_coluna = request.form.get('atributo_coluna')
        classe_coluna = request.form.get('classe_coluna') or ''  # Define como None se não estiver preenchido
        tamanho_coluna = request.form.get('tamanho_coluna')
        numero_apre_coluna = request.form.get('numero_apre_coluna')
        escondido_coluna = 'H' if request.form.get('escondido_coluna') else None  # Define como None se não estiver marcado
        fonte_coluna = request.form.get('fonte_coluna')
        cor_texto_coluna = request.form.get('cor_texto_coluna')
        alinhamento_coluna = request.form.get('alinhamento_coluna')
        font_bold = 'Y' if request.form.get('font_bold') else None
        font_italic = 'Y' if request.form.get('font_italic') else None
        # Verificar se os campos obrigatórios estão preenchidos
        if not titulo_coluna or not atributo_coluna or not tamanho_coluna or not numero_apre_coluna:
            return jsonify({'success': False, 'error': 'Preencha todos os campos obrigatórios'}), 400

        try:
            # Gerar um novo ID para a coluna
            cursor.execute("SELECT COLUNA_SEQ.NEXTVAL FROM dual")
            coluna_id = cursor.fetchone()[0]
            

            # Inserir nova coluna no banco de dados
            cursor.execute(""" 
            INSERT INTO HP_PAINEL_COLUNA 
            (NR_SEQUENCIA, DS_TITULO_COLUNA, DS_ATRIBUTO, FK_NR_SEQ_PAINEL, 
            DT_CRIACAO, DT_ATUALIZACAO, NM_USUARIO_CRIACAO, NM_USUARIO_ATUALIZACAO, 
            QT_TAMANHO, NR_SEQ_APRESENTACAO, IE_HIDDEN, IE_SITUACAO, NM_CLASS, DS_COR_TEXTO, QT_TAMANHO_FONTE, DS_ALINHAMENTO, IE_FONT_BOLD, IE_FONT_ITALIC)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14, :15, :16, :17, :18)
        """, (
            coluna_id,
            titulo_coluna,
            atributo_coluna,
            painel_id,
            datetime.now(),
            datetime.now(),
            "DMMSANTOS",
            "DMMSANTOS",
            int(tamanho_coluna),
            int(numero_apre_coluna),
            escondido_coluna,
            'A',
            classe_coluna,
            cor_texto_coluna,
            int(fonte_coluna),
            alinhamento_coluna,
            font_bold,
            font_italic
        ))

            connection.commit()

            # Retornar sucesso e os dados da nova coluna para serem atualizados no frontend
            return jsonify({
                'success': True,
                'coluna_id': coluna_id,
                'titulo_coluna': titulo_coluna,
                'atributo_coluna': atributo_coluna,
                'classe_coluna': classe_coluna,
                'tamanho_coluna': tamanho_coluna,
                'numero_apre_coluna': numero_apre_coluna,
                'escondido_coluna': escondido_coluna
            }), 200

        except Exception as e:
            connection.rollback()
            
            return jsonify({'success': False, 'error': str(e)}), 500
        

#Rota editar coluna
@app.route('/edit_column', methods=['POST'])
def edit_column():
    data = request.get_json()  # Recebe os dados JSON
    print("Dados recebidos:", data)
    try:
        # Obtendo os valores enviados pelo JSON
        data = request.json
        coluna_id = data.get('nr_sequencia')
        titulo_coluna = data.get('titulo_coluna')
        atributo_coluna = data.get('atributo_coluna')
        classe_coluna = data.get('classe_coluna')
        tamanho_coluna = data.get('tamanho_coluna')
        numero_apre_coluna = data.get('numero_apre_coluna')
        escondido_coluna = data.get('escondido_coluna')
        fonte_coluna = data.get('fonte_coluna')
        cor_texto_coluna = data.get('cor_texto_coluna')
        alinhamento_coluna = data.get('alinhamento_coluna')
        font_bold = data.get('font_bold')
        font_italic = data.get('font_italic')
        
        # Verificando se `coluna_id` existe antes de prosseguir
        if not coluna_id:
            return jsonify(success=False, message="ID da coluna não encontrado"), 400
        
        # Definindo dados adicionais
        dt_atualizacao = datetime.now()
        usuario_atualizacao = 'DMMSANTOS'
        
        with get_db_connection() as connection:
            cursor = connection.cursor()
            # Execução do comando SQL
            cursor.execute("""UPDATE HP_PAINEL_COLUNA
                SET DS_TITULO_COLUNA = :1, DS_ATRIBUTO = :2, NM_CLASS = :3, QT_TAMANHO = :4,
                    NR_SEQ_APRESENTACAO = :5, IE_HIDDEN = :6, DT_ATUALIZACAO = :7,
                    nm_usuario_atualizacao = :8, DS_COR_TEXTO = :9, QT_TAMANHO_FONTE = :10, DS_ALINHAMENTO = :11, IE_FONT_BOLD = :12, IE_FONT_ITALIC = :13
                WHERE NR_SEQUENCIA = :14""",
            (titulo_coluna, atributo_coluna, classe_coluna, tamanho_coluna, numero_apre_coluna,
                'H' if escondido_coluna else None, dt_atualizacao, usuario_atualizacao, cor_texto_coluna, int(fonte_coluna), alinhamento_coluna, font_bold, font_italic, coluna_id))
            
            # Commit da transação
            connection.commit()

            # Retorno de sucesso
            return jsonify(success=True, message="Coluna editada com sucesso")

    except Exception as e:
        print("Erro ao editar coluna:", str(e))
        return jsonify(success=False, message="Erro ao editar a coluna"), 500
    
# Rota para duplicar coluna
@app.route('/duplicar_coluna', methods=['POST'])
def duplicar_coluna():
    coluna_id = request.form.get('nr_sequencia')
    print(f"ID da coluna a ser duplicada: {coluna_id}")

    try:
        coluna_id = int(coluna_id)  # Tente converter para inteiro
    except ValueError:
        return jsonify(success=False, message='ID da coluna é inválido.')

    with get_db_connection() as connection:
        if connection is None:
            return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

        cursor = connection.cursor()
        # Obter dados da coluna original
        cursor.execute("""
            SELECT DS_ATRIBUTO, DT_ATUALIZACAO, DT_CRIACAO, NM_USUARIO_ATUALIZACAO, NM_USUARIO_CRIACAO,
                NR_SEQ_APRESENTACAO, IE_SITUACAO, QT_TAMANHO, DS_TITULO_COLUNA, FK_NR_SEQ_PAINEL,
                IE_HIDDEN, NM_CLASS
            FROM HP_PAINEL_COLUNA
            WHERE NR_SEQUENCIA = :1
        """, (coluna_id,))
        coluna_original = cursor.fetchone()

        if coluna_original:
            novo_titulo = "Cópia " + coluna_original[8]  # Ajuste o índice conforme necessário para pegar o título

            # Inserir a nova coluna duplicada, incluindo a sequência
            cursor.execute("""
                INSERT INTO HP_PAINEL_COLUNA (
                    NR_SEQUENCIA, DS_ATRIBUTO, DT_ATUALIZACAO, DT_CRIACAO, NM_USUARIO_ATUALIZACAO,
                    NM_USUARIO_CRIACAO, NR_SEQ_APRESENTACAO, IE_SITUACAO, QT_TAMANHO, DS_TITULO_COLUNA,
                    FK_NR_SEQ_PAINEL, IE_HIDDEN, NM_CLASS
                ) VALUES (
                    PAINEL_SEQ.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12
                )
            """, (
                coluna_original[0], coluna_original[1], coluna_original[2], coluna_original[3],
                coluna_original[4], coluna_original[5], coluna_original[6], coluna_original[7],
                novo_titulo, coluna_original[9], coluna_original[10], coluna_original[11]
            ))
            connection.commit()
            return jsonify(success=True, message='Coluna duplicada com sucesso!')
        else:
            return jsonify(success=False, message='Coluna original não encontrada.')

    
#Rota excluir coluna
@app.route('/excluir_coluna', methods=['POST'])
def excluir_coluna():
    coluna_id = request.form.get('nr_sequencia')


    try:
        coluna_id = int(coluna_id)  # Tente converter para inteiro
    except ValueError:
        return jsonify(success=False, message='ID da coluna é inválido.')

    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM HP_PAINEL_COLUNA WHERE NR_SEQUENCIA = :1", (coluna_id,))
        connection.commit()
    
    return jsonify(success=True, message='Coluna excluída com sucesso!')



# ---------------- FIM Rotas de Colunas ----------------

# ---------------- INÍCIO Rotas de Dashboard ----------------

# Rota para cadastrar dashboard
@app.route('/cadastrar_dashboard', methods=['POST'])
def cadastrar_dashboard():
    painel_id = request.form.get('painel_id')  # Obtenha o ID do painel do formulário

    # Verificar se o painel existe
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT ds_sql FROM hp_painel WHERE nr_sequencia = :painel_id", {'painel_id': painel_id})
        painel = cursor.fetchone()

        if not painel:
            return jsonify({'success': False, 'error': 'Painel não encontrado'}), 404

        # Captura os dados do formulário
        titulo_dashboard = request.form.get('titulo_dashboard')
        sql_dashboard = request.form.get('sql_dashboard')
        cor_dashboard = request.form.get('cor_dashboard')
        cor_texto_dashboard = request.form.get("ds_cor_texto")
        alinhamento_dashboard = request.form.get("ds_alinhamento") or "center"
        font_bold_dashboard = request.form.get("font_bold")
        font_italic_dashboard = request.form.get("font_italic")
        fonte_dashboard = request.form.get("fonte_dashboard")



        # Verificar se os campos obrigatórios estão preenchidos
        if not titulo_dashboard or not sql_dashboard:
            return jsonify({'success': False, 'error': 'Preencha todos os campos obrigatórios'}), 400

        try:
            # Gerar um novo ID para o dashboard
            cursor.execute("SELECT DASHBOARD_SEQ.NEXTVAL FROM dual")
            dashboard_id = cursor.fetchone()[0]
            print("Nova ID do dashboard:", dashboard_id)  # Debug: imprimir o ID gerado

            # Inserir novo dashboard no banco de dados
            cursor.execute("""
            INSERT INTO hp_painel_dashboard 
            (nr_sequencia, ds_titulo, ds_sql, ds_cor, fk_nr_seq_painel, dt_criacao, dt_atualizacao, nm_usuario_criacao, nm_usuario_atualizacao, QT_TAMANHO_FONTE, DS_COR_TEXTO, DS_ALINHAMENTO, IE_FONT_BOLD, IE_FONT_ITALIC)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14)
        """, (
                dashboard_id, 
                titulo_dashboard, 
                sql_dashboard, 
                cor_dashboard, 
                painel_id, 
                datetime.now(), 
                datetime.now(), 
                "DMMSANTOS",  
                "DMMSANTOS",
                int(fonte_dashboard),
                cor_texto_dashboard,
                alinhamento_dashboard,
                font_bold_dashboard,
                font_italic_dashboard
            ))
            connection.commit()

            # Retornar sucesso e os dados do novo dashboard para serem atualizados no frontend
            return jsonify({
                'success': True,
                'dashboard_id': dashboard_id,
                'titulo_dashboard': titulo_dashboard,
                'sql_dashboard': sql_dashboard,
                'cor_dashboard': cor_dashboard
            }), 200

        except Exception as e:
            connection.rollback()
            print(f"Erro ao inserir o dashboard: {str(e)}")  # Debug: imprimir erro
            return jsonify({'success': False, 'error': str(e)}), 500


# Rota editar dashboard
@app.route('/editar_dashboard', methods=['POST'])
def editar_dashboard():
    data = request.get_json(force=True)  # Captura os dados no formato JSON
    try:
        # Extrai os dados do JSON recebido
        dashboard_id = data.get('nr_sequencia')
        titulo_dashboard = data.get('titulo_dashboard')
        sql_dashboard = data.get('sql_dashboard')
        cor_dashboard = data.get('cor_dashboard')
        fonte_dashboard = data.get("fonte_dashboard")
        cor_texto_dashboard = data.get("ds_cor_texto")
        alinhamento_dashboard = data.get("ds_alinhamento") or "center"
        font_bold_dashboard = data.get("font_bold")
        font_italic_dashboard = data.get("font_italic")

        print({
            'dashboard_id': dashboard_id,
            'titulo_dashboard': titulo_dashboard,
            'sql_dashboard': sql_dashboard,
            'cor_dashboard': cor_dashboard
        })

        # Verifica se os dados obrigatórios estão presentes
        if not dashboard_id:
            return jsonify(success=False, message="ID do Dashboard não encontrado."), 400

        # Variáveis de atualização
        dt_atualizacao = datetime.now()
        usuario_atualizacao = 'DMMSANTOS'

        # Realiza a atualização no banco de dados
        with get_db_connection() as connection:
            cursor = connection.cursor()
            # Execução do comando SQL
        cursor.execute("""
            UPDATE HP_PAINEL_DASHBOARD
            SET DS_TITULO = :1, DS_SQL = :2, DS_COR = :3, DT_ATUALIZACAO = :4, NM_USUARIO_ATUALIZACAO = :5, QT_TAMANHO_FONTE = :6, DS_COR_TEXTO = :7, DS_ALINHAMENTO = :8, IE_FONT_BOLD = :9, IE_FONT_ITALIC = :10
            WHERE NR_SEQUENCIA = :11
        """, (titulo_dashboard, sql_dashboard, cor_dashboard, dt_atualizacao, usuario_atualizacao, int(fonte_dashboard), cor_texto_dashboard, alinhamento_dashboard, font_bold_dashboard, font_italic_dashboard, dashboard_id))
                    # Confirma a transação
        connection.commit()

        return jsonify(success=True, message="Dashboard editado com sucesso")

    except Exception as e:
        # Tratamento de erro com detalhes
        print("Erro ao editar dashboard:", str(e))
        return jsonify(success=False, message=f"Erro ao editar o dashboard: {str(e)}"), 500

# Excluir Dashboard
@app.route('/excluir_dashboard/<int:dashboard_id>', methods=['POST'])
def excluir_dashboard(dashboard_id):
    print("Id do dashboard para exclusão ", dashboard_id)
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hp_painel_dashboard WHERE nr_sequencia = :1", (dashboard_id,))
        connection.commit()
        
    return jsonify(success=True, message='Coluna excluída com sucesso!')

# Duplicar Dashboard
@app.route('/duplicar_dashboard', methods=['POST'])
def duplicar_dashboard():
    dashboard_id = request.form.get('nr_sequencia')
    print(f"ID do painel a ser duplicado: {dashboard_id}")

    try:
        dashboard_id = int(dashboard_id)  # Tente converter para inteiro
    except ValueError:
        return jsonify(success=False, message='ID do painel é inválido.')

    with get_db_connection() as connection:
        if connection is None:
            return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

        cursor = connection.cursor()
        # Obter dados do painel original
        cursor.execute("""
            SELECT DS_COR, DT_ATUALIZACAO, DT_CRIACAO, NM_USUARIO_ATUALIZACAO, NM_USUARIO_CRIACAO,
                   DS_SQL, DS_TITULO, FK_NR_SEQ_PAINEL
            FROM HP_PAINEL_DASHBOARD
            WHERE NR_SEQUENCIA = :1
        """, (dashboard_id,))
        dashboard_original = cursor.fetchone()

        if dashboard_original:
            novo_titulo = "Cópia " + dashboard_original[6]  # Ajuste o índice conforme necessário para pegar o título

            # Inserir o novo painel duplicado, incluindo a sequência
            cursor.execute("""
                INSERT INTO HP_PAINEL_DASHBOARD (
                    NR_SEQUENCIA, DS_COR, DT_ATUALIZACAO, DT_CRIACAO, NM_USUARIO_ATUALIZACAO,
                    NM_USUARIO_CRIACAO, DS_SQL, DS_TITULO, FK_NR_SEQ_PAINEL
                ) VALUES (
                    PAINEL_SEQ.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8
                )
            """, (
                dashboard_original[0], dashboard_original[1], dashboard_original[2], 
                dashboard_original[3], dashboard_original[4], dashboard_original[5],
                novo_titulo, dashboard_original[7]
            ))
            connection.commit()
            return jsonify(success=True, message='Painel duplicado com sucesso!')
        else:
            return jsonify(success=False, message='Painel original não encontrado.')

# ---------------- FIM Rotas de Dashboard ----------------

# ---------------- INÍCIO Rotas de Legendas ----------------
# Listar Legendas
@app.route('/legendas')
def listar_legendas():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM hp_painel_legenda')
        legendas = cursor.fetchall()
        return render_template('listar_legendas.html', legendas=legendas)

# Cadastrar legenda
@app.route('/cadastrar_legenda', methods=['POST'])
def cadastrar_legenda():
    descricao_legenda = request.form.get('descricao_legenda')
    cor_legenda = request.form.get('cor_legenda')  # Supondo que você tenha um campo para a cor da legenda
    painel_id = request.form.get('painel_id')  # Supondo que você tenha um campo oculto para o ID do painel

    # Verificar se os campos obrigatórios estão preenchidos
    if not descricao_legenda or not cor_legenda or not painel_id:
        return jsonify({'success': False, 'error': 'Preencha todos os campos obrigatórios'}), 400

    with get_db_connection() as connection:
        cursor = connection.cursor()

        try:
            # Gerar um novo ID para a legenda
            cursor.execute("SELECT LEGENDA_SEQ.NEXTVAL FROM dual")
            legenda_id = cursor.fetchone()[0]

            # Inserir nova legenda no banco de dados
            cursor.execute("""
                INSERT INTO hp_painel_legenda (
                    NR_SEQUENCIA,
                    DS_COR,
                    DS_LEGENDA,
                    DT_CRIACAO,
                    DT_ATUALIZACAO,
                    NM_USUARIO_CRIACAO,
                    NM_USUARIO_ATUALIZACAO,
                    NR_SEQ_APRESENTACAO,
                    IE_SITUACAO,
                    FK_NR_SEQ_PAINEL
                )
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
            """, (
                legenda_id,
                cor_legenda,
                descricao_legenda,
                datetime.now(),
                datetime.now(),
                "DMMSANTOS",  # Nome do usuário que está criando
                "DMMSANTOS",  # Nome do usuário que está atualizando
                1,            # Exemplo de NR_SEQ_APRESENTACAO
                'A',          # Estado inicial da legenda
                painel_id
            ))

            connection.commit()

            return jsonify({
                'success': True,
                'legenda_id': legenda_id,
                'descricao_legenda': descricao_legenda,
                'cor_legenda': cor_legenda
            }), 200

        except Exception as e:
            connection.rollback()
            print(f"Erro ao inserir a legenda: {str(e)}")  # Debug: imprimir erro
            return jsonify({'success': False, 'error': str(e)}), 500

# Editar legenda
@app.route('/editar_legenda', methods=['POST'])
def editar_legenda():
    legenda_id = request.form.get('legenda_id')
    painel_id = request.form.get('painel_id')
    titulo_legenda = request.form.get('titulo_legenda')
    cor_legenda = request.form.get('cor_legenda')
    numero_apre_legenda = request.form.get('numero_apre_legenda')

    if not legenda_id or not titulo_legenda or not numero_apre_legenda:
        return jsonify(success=False, message="Dados insuficientes para atualização.")

    try:
        legenda_id = int(legenda_id)
        numero_apre_legenda = int(numero_apre_legenda)
    except ValueError:
        return jsonify(success=False, message="ID ou número de apresentação inválido.")

    with get_db_connection() as connection:
        if connection is None:
            return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

        cursor = connection.cursor()
        # Atualizar a legenda no banco de dados
        cursor.execute("""
            UPDATE HP_PAINEL_LEGENDA
            SET DS_LEGENDA = :1, DS_COR = :2, NR_SEQ_APRESENTACAO = :3
            WHERE NR_SEQUENCIA = :4 AND FK_NR_SEQ_PAINEL = :5
        """, (titulo_legenda, cor_legenda, numero_apre_legenda, legenda_id, painel_id))
        connection.commit()

    return jsonify(success=True, message="Legenda atualizada com sucesso.")


# Excluir Legenda
@app.route('/excluir_legenda/<int:legenda_id>', methods=['POST'])
def excluir_legenda(legenda_id):
    print("ID da legenda para exclusão:", legenda_id)
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hp_painel_legenda WHERE nr_sequencia = :1", (legenda_id,))
        connection.commit()
        
    return jsonify(success=True, message='Legenda excluída com sucesso!')

#Duplicar Legenda

@app.route('/duplicar_legenda', methods=['POST'])
def duplicar_legenda():
    legenda_id = request.form.get('legenda_id')  # Recebe o ID da legenda a ser duplicada
    print(f"ID da legenda a ser duplicada: {legenda_id}")

    # Verifica se o ID fornecido é válido
    if not legenda_id:
        return jsonify(success=False, message="ID da legenda não informado.")

    try:
        legenda_id = int(legenda_id)  # Tenta converter para inteiro
    except ValueError:
        return jsonify(success=False, message="ID da legenda inválido.")

    with get_db_connection() as connection:
        if connection is None:
            return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

        cursor = connection.cursor()

        try:
            # Obter os dados da legenda original
            cursor.execute("""
                SELECT DS_COR, DS_LEGENDA, DT_CRIACAO, DT_ATUALIZACAO,
                       NM_USUARIO_CRIACAO, NM_USUARIO_ATUALIZACAO, 
                       NR_SEQ_APRESENTACAO, IE_SITUACAO, FK_NR_SEQ_PAINEL
                FROM hp_painel_legenda
                WHERE NR_SEQUENCIA = :1
            """, (legenda_id,))
            legenda_original = cursor.fetchone()

            if not legenda_original:
                return jsonify(success=False, message="Legenda original não encontrada.")

            # Gerar novo ID para a legenda duplicada
            cursor.execute("SELECT LEGENDA_SEQ.NEXTVAL FROM dual")
            nova_legenda_id = cursor.fetchone()[0]

            # Adicionar "Cópia de" à descrição da legenda
            nova_descricao = f"Cópia de {legenda_original[1]}"

            # Inserir a legenda duplicada
            cursor.execute("""
                INSERT INTO hp_painel_legenda (
                    NR_SEQUENCIA, DS_COR, DS_LEGENDA, DT_CRIACAO, DT_ATUALIZACAO,
                    NM_USUARIO_CRIACAO, NM_USUARIO_ATUALIZACAO, NR_SEQ_APRESENTACAO,
                    IE_SITUACAO, FK_NR_SEQ_PAINEL
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, :9, :10
                )
            """, (
                nova_legenda_id,
                legenda_original[0],  # DS_COR
                nova_descricao,       # DS_LEGENDA
                datetime.now(),       # DT_CRIACAO
                datetime.now(),       # DT_ATUALIZACAO
                "DMMSANTOS",          # NM_USUARIO_CRIACAO
                "DMMSANTOS",          # NM_USUARIO_ATUALIZACAO
                legenda_original[6],  # NR_SEQ_APRESENTACAO
                legenda_original[7],  # IE_SITUACAO
                legenda_original[8],  # FK_NR_SEQ_PAINEL
            ))

            connection.commit()

            return jsonify(success=True, message="Legenda duplicada com sucesso!", nova_legenda_id=nova_legenda_id)
        
        except Exception as e:
            connection.rollback()
            print(f"Erro ao duplicar a legenda: {str(e)}")  # Debug para identificar o erro
            return jsonify(success=False, message=f"Erro ao duplicar a legenda: {str(e)}")




# ---------------- FIM Rotas de Legendas ----------------

# ---------------- INÍCIO Rotas de Regras de Cor ----------------
# Listar Regras de Cor
@app.route('/regras_cor')
def listar_regras_cor():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM hp_painel_regra_cor')
        regras = cursor.fetchall()
        return render_template('listar_regras_cor.html', regras=regras)
    
# Rota para listar as colunas no modal da regra
@app.route('/listar_colunas_painel', methods=['GET'])
def listar_colunas_painel():
    painel_id = request.args.get('painel_id')
    print("ID atribuida: ", painel_id)
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT nr_sequencia, DS_TITULO_COLUNA FROM hp_painel_coluna WHERE fk_nr_seq_painel = :1', (painel_id,))
        colunas = cursor.fetchall()
        colunas_list = [{'nr_sequencia': coluna[0], 'DS_TITULO_COLUNA': coluna[1]} for coluna in colunas]
        return jsonify({'colunas': colunas_list})
    
    
#Rota cadastrar regra
@app.route('/cadastrar_regra_cor', methods=['POST'])
def cadastrar_regra_cor():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'Nenhum dado recebido.'}), 400
    # Atribuição dos dados
    descricao_regra = data.get('valor_regra')
    cor_regra = data.get('cor_regra')
    icone_regra = data.get('icone_regra') or ''
    classe_regra = data.get('classe_regra') or ''  # Valor padrão caso esteja ausente
    substituicao_regra = data.get('substituicao_regra', 'N')
    coluna_id = data.get('coluna_regra')
    celula_linha_regra = data.get('celula_linha_regra')
    usuario_logado = "DMMSANTOS"  # Ou session.get('username') para capturar o usuário da sessão

    # Conexão com o banco
    with get_db_connection() as connection:
        cursor = connection.cursor()
        
        # Obtenção do próximo valor da sequência
        cursor.execute("SELECT REGRA_SEQ.NEXTVAL FROM dual")
        regra_id = cursor.fetchone()[0]
        print(f"ID da regra gerado: {regra_id}")

        try:
            # Inserção da nova regra
            cursor.execute(""" 
                INSERT INTO hp_painel_regra_cor (
                    NR_SEQUENCIA, DS_COR, DT_ATUALIZACAO, DT_CRIACAO,
                    NM_ICON, IE_CELULA_LINHA, NM_USUARIO_ATUALIZACAO,
                    NM_USUARIO_CRIACAO, IE_ICON_REPLACE, IE_SITUACAO,
                    DS_VALOR, FK_NR_SEQ_PAINEL_COLUNA, NM_CLASS
                ) VALUES (:1, :2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :3, :4, :5, :6, :7, :8, :9, :10, :11)
            """, (
                regra_id, cor_regra, icone_regra, celula_linha_regra,
                usuario_logado, usuario_logado, substituicao_regra, 'A', descricao_regra,
                coluna_id, classe_regra
            ))

            connection.commit()
        
            return jsonify({'success': True, 'message': 'Regra de cor cadastrada com sucesso!'})

        except Exception as e:
            print(f"Erro ao inserir regra: {e}")
            connection.rollback()
            return jsonify({'success': False, 'message': f'Erro ao cadastrar regra de cor: {str(e)}'})

    return jsonify({'success': False, 'message': 'Erro ao cadastrar regra de cor.'})


# Editar Regra de Cor
@app.route('/editar_regra_cor', methods=['POST'])
def editar_regra_cor():
    # Obtendo dados do formulário
    regra_id = request.form.get('regra_id')
    valor_regra = request.form.get('valor_regra')
    icone_regra = request.form.get('icone_regra') or ''
    classe_regra = request.form.get('classe_regra') or ''
    substituicao_regra = request.form.get('substituicao_regra', 'N')  # Padrão 'N' se não for selecionado
    cor_regra = request.form.get('cor_regra')
    coluna_regra = request.form.get('coluna_regra')
    celula_linha_regra = request.form.get('celula_linha_regra')

    # Validações básicas
    if not regra_id or not valor_regra or not cor_regra:
        return jsonify(success=False, message="Dados insuficientes para atualização.")

    try:
        regra_id = int(regra_id)
    except ValueError:
        return jsonify(success=False, message="ID da regra inválido.")

    try:
        # Conectando ao banco de dados e atualizando a regra
        with get_db_connection() as connection:
            if connection is None:
                return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

            cursor = connection.cursor()
            dt_atualizacao = datetime.now()
            usuario_atualizacao = 'DMMSANTOS'  # Substitua pelo usuário atual logado, se aplicável

            # Executa a atualização no banco de dados
            cursor.execute("""
                UPDATE HP_PAINEL_REGRA_COR
                SET DS_VALOR = :1, NM_ICON = :2, NM_CLASS = :3, IE_ICON_REPLACE = :4,
                    DS_COR = :5, DS_COLUNA = :6, IE_CELULA_LINHA = :7, DT_ATUALIZACAO = :8,
                    nm_usuario_atualizacao = :9
                WHERE NR_SEQUENCIA = :10
            """, (
                valor_regra, icone_regra, classe_regra, substituicao_regra,
                cor_regra, coluna_regra, celula_linha_regra, dt_atualizacao,
                usuario_atualizacao, regra_id
            ))
            connection.commit()

        return jsonify(success=True, message="Regra de cor atualizada com sucesso.")

    except Exception as e:
        print("Erro ao editar regra de cor:", str(e))
        return jsonify(success=False, message="Erro ao atualizar a regra de cor.")


# Excluir Regra de Cor
@app.route('/excluir_regra', methods=['POST'])
def excluir_regra():
    regra_id = request.form.get('regra_id')  # Recebe o ID da regra do corpo da requisição
    print(f"ID da regra a ser excluída: {regra_id}")

    try:
        regra_id = int(regra_id)  # Converte para inteiro, caso necessário
    except ValueError:
        return jsonify(success=False, message='ID da regra é inválido.')

    with get_db_connection() as connection:
        if connection is None:
            return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

        cursor = connection.cursor()

        try:
            # Executa a exclusão
            cursor.execute("""
                DELETE FROM HP_PAINEL_REGRA_COR
                WHERE NR_SEQUENCIA = :1
            """, (regra_id,))
            
            # Verifica se alguma linha foi afetada
            if cursor.rowcount > 0:
                connection.commit()
                return jsonify(success=True, message='Regra excluída com sucesso!')
            else:
                return jsonify(success=False, message='Regra não encontrada.')
        
        except Exception as e:
            print(f"Erro ao excluir a regra: {e}")
            return jsonify(success=False, message=f'Erro ao excluir a regra: {str(e)}')

#Rota duplicar regra
@app.route('/duplicar_regra_cor', methods=['POST'])
def duplicar_regra_cor():
    regra_id = request.form.get('regra_id')
    print(f"ID da regra de cor a ser duplicada: {regra_id}")

    try:
        regra_id = int(regra_id)  # Tente converter para inteiro
    except ValueError:
        return jsonify(success=False, message='ID da regra de cor é inválido.')

    with get_db_connection() as connection:
        if connection is None:
            return jsonify(success=False, message="Erro ao conectar ao banco de dados.")

        cursor = connection.cursor()

        # Obter dados da regra de cor original
        cursor.execute("""
            SELECT DS_COR, NM_ICON, IE_CELULA_LINHA, NM_CLASS, IE_ICON_REPLACE, IE_SITUACAO, 
                   DS_VALOR, FK_NR_SEQ_PAINEL_COLUNA, NM_USUARIO_CRIACAO
            FROM HP_PAINEL_REGRA_COR
            WHERE NR_SEQUENCIA = :1
        """, (regra_id,))
        regra_original = cursor.fetchone()

        if regra_original:
            novo_valor = "Cópia de " + regra_original[6]  # Adiciona "Cópia de" ao valor da regra

            # Inserir a nova regra duplicada
            cursor.execute("""
                INSERT INTO HP_PAINEL_REGRA_COR (
                    NR_SEQUENCIA, DS_COR, DT_ATUALIZACAO, DT_CRIACAO, NM_ICON, IE_CELULA_LINHA,
                    NM_CLASS, IE_ICON_REPLACE, IE_SITUACAO, DS_VALOR, FK_NR_SEQ_PAINEL_COLUNA,
                    NM_USUARIO_CRIACAO, NM_USUARIO_ATUALIZACAO
                ) VALUES (
                    REGRA_SEQ.NEXTVAL, :1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :2, :3, :4, :5,
                    :6, :7, :8, :9, :10
                )
            """, (
                regra_original[0],  # DS_COR
                regra_original[1],  # NM_ICON
                regra_original[2],  # IE_CELULA_LINHA
                regra_original[3],  # NM_CLASS
                regra_original[4],  # IE_ICON_REPLACE
                regra_original[5],  # IE_SITUACAO
                novo_valor,         # DS_VALOR (com "Cópia de")
                regra_original[7],  # FK_NR_SEQ_PAINEL_COLUNA
                regra_original[8],  # NM_USUARIO_CRIACAO (mantém o criador original)
                "DMMSANTOS"         # NM_USUARIO_ATUALIZACAO (usuário atual)
            ))

            connection.commit()
            return jsonify(success=True, message='Regra de cor duplicada com sucesso!')
        else:
            return jsonify(success=False, message='Regra de cor original não encontrada.')



# ---------------- FIM Rotas de Regras de Cor ----------------


if __name__ == '__main__':
    app.run(debug=True)