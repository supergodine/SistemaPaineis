from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import cx_Oracle
from datetime import datetime
import logging
import re


# Configure o logger
logging.basicConfig(level=logging.INFO)


app = Flask(__name__)
# Definir o filtro regex_search
@app.template_filter('regex_search')
def regex_search(s, pattern):
    # Converte 's' em string para evitar TypeError
    s = str(s)
    return re.search(pattern, s)

app.secret_key = 'chave_secreta'

DB_HOST = '172.16.0.100'
DB_PORT = '1521'
DB_SERVICE_NAME = 'prd'
DB_USER = 'painel'
DB_PASSWORD = 'P0T4syti'

def get_db_connection():
    dsn = cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE_NAME)
    return cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)

# Função de autenticação
def autenticar_usuario(username, password):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()

        # Consulta ao banco de dados usando a função PL/SQL hp_permite_login_admin
        cursor.execute("""
            SELECT tasy.hp_permite_login_admin(:username, :password) 
            FROM dual
        """, username=username, password=password)

        # Obter o resultado da função
        resultado = cursor.fetchone()

        # Verificar se a função retornou 'S'
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
        # Captura os valores do formulário
        username = request.form['username']
        password = request.form['password']

        # Tenta autenticar o usuário
        if autenticar_usuario(username, password):
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for('lista_paineis'))
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger")
            return redirect(url_for('login'))
    
    return render_template('login.html')

# Rota listar paineis
@app.route('/paineis')
def lista_paineis():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT nr_sequencia, ds_titulo_painel, ds_observacao, qt_segundos_rolagem, qt_segundos_atualizacao, ds_sql FROM hp_painel ORDER BY nr_sequencia')
        paineis = cursor.fetchall()
        return render_template('lista_paineis.html', paineis=paineis)
    
    
    
# Rota visualizar painel
@app.route('/visualizar_painel/<int:painel_id>', methods=['GET'])
def visualizar_painel(painel_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    # Consulta para obter o SQL, título do painel, tempo de rolagem e tempo de atualização
    sql_query = """
        SELECT ds_titulo_painel, ds_sql, qt_segundos_rolagem, qt_segundos_atualizacao 
        FROM hp_painel 
        WHERE nr_sequencia = :painel_id
    """
    
    cursor.execute(sql_query, {'painel_id': painel_id})
    painel = cursor.fetchone()

    if painel:
        ds_titulo_painel = painel[0]  # Título do painel
        sql_body_query = painel[1]    # SQL para obter os dados do painel
        segundos_rolagem = painel[2] or 10  # Se o campo estiver nulo, usa 10 segundos como padrão
        segundos_atualizacao = painel[3] or 30  # Se o campo estiver nulo, usa 30 segundos como padrão

        try:
            # Obter títulos e atributos das colunas cadastradas
            colunas_query = """
            SELECT
                ds_titulo_coluna, ds_atributo, nm_class, ie_hidden, qt_tamanho, nr_seq_apresentacao, nr_sequencia,  dt_atualizacao, dt_criacao, nm_usuario_atualizacao, nm_usuario_criacao,  ie_situacao, fk_nr_seq_painel
                FROM
                     hp_painel_coluna
                        WHERE
                        fk_nr_seq_painel = :painel_id
                        ORDER BY
                            nr_seq_apresentacao
            """
            cursor.execute(colunas_query, {'painel_id': painel_id})
            colunas = cursor.fetchall()

            # Verifica se existem colunas cadastradas
            if not colunas:
                flash("Nenhuma coluna cadastrada para este painel.", "danger")
                return redirect(url_for('lista_paineis'))

            # Separa os títulos e atributos
            titulos = [coluna[0] for coluna in colunas]  # Títulos das colunas
            atributos = [coluna[1] for coluna in colunas]  # Atributos

            # Ajusta a consulta SQL para selecionar apenas os atributos cadastrados
            if atributos:
                sql_body_query = f"SELECT {', '.join(atributos)} FROM ({sql_body_query})"

            # Executa o SQL modificado para obter os dados do painel
            cursor.execute(sql_body_query)
            resultados = cursor.fetchall()

            # Não realizar paginação manual aqui, enviar todos os resultados para o template
            per_page = 12  # Define quantos resultados por página no carrossel
            total = len(resultados)
            
            # Consulta para obter as regras de cor
            regras_query = """
                SELECT ds_valor, ds_cor, ie_icon_replace, nm_icon, ie_celula_linha, nm_class, nm_usuario_atualizacao, nm_usuario_criacao, dt_criacao, dt_atualizacao
                FROM hp_painel_regra_cor
                WHERE fk_nr_seq_painel_coluna IN (
                    SELECT nr_sequencia FROM hp_painel_coluna WHERE fk_nr_seq_painel = :painel_id)
            """
            cursor.execute(regras_query, {'painel_id': painel_id})
            regras = cursor.fetchall()

            # Coleta das regras em uma lista
            regras_resultados = []
            for regra in regras:
                ds_valor, ds_cor, ie_icon_replace, nm_icon, ie_celula_linha, nm_class, nm_usuario_atualizacao, nm_usuario_criacao, dt_criacao, dt_atualizacao = regra

                regras_resultados.append({
                    'ds_valor': ds_valor if ds_valor is not None else '',
                    'ds_cor': ds_cor if ds_cor is not None else '',
                    'ie_icon_replace': ie_icon_replace if ie_icon_replace is not None else '',
                    'nm_icon': nm_icon if nm_icon is not None else '',
                    'ie_celula_linha': ie_celula_linha if ie_celula_linha is not None else '',
                    'nm_class': nm_class if nm_class is not None else '',
                    'nm_usuario_atualizacao': nm_usuario_atualizacao if nm_usuario_atualizacao is not None else '',
                    'nm_usuario_criacao': nm_usuario_criacao if nm_usuario_criacao is not None else '',
                    'dt_criacao': dt_criacao if dt_criacao is not None else '',
                    'dt_atualizacao': dt_atualizacao if dt_atualizacao is not None else ''
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

                # Adiciona os resultados e os dados do dashboard a uma lista
                dashboards_resultados.append({
                    'titulo': ds_titulo_dashboard,
                    'cor': ds_cor_dashboard,
                    'dados': resultado_dashboard
                })

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

            # Aplicação das regras às linhas e células
            # Cria um dicionário para mapear ds_valor para ds_cor para 'C' e 'L' regras
            regras_por_valor = {}
            for regra in regras_resultados:
                ds_valor = regra['ds_valor']
                ds_cor = regra['ds_cor']
                ie_celula_linha = regra['ie_celula_linha']
                ie_icon_replace = regra['ie_icon_replace']
                nm_icon = regra['nm_icon']

                if ie_celula_linha == 'C':
                    if ds_valor not in regras_por_valor:
                        regras_por_valor[ds_valor] = {}
                    regras_por_valor[ds_valor]['C'] = {
                        'ds_cor': ds_cor,
                        'ie_icon_replace': ie_icon_replace,
                        'nm_icon': nm_icon
                    }
                elif ie_celula_linha == 'L':
                    if ds_valor not in regras_por_valor:
                        regras_por_valor[ds_valor] = {}
                    regras_por_valor[ds_valor]['L'] = {
                        'ds_cor': ds_cor,
                        'ie_icon_replace': ie_icon_replace,
                        'nm_icon': nm_icon
                    }

            # Processa cada resultado aplicando as regras
            for index in range(len(resultados)):
                linha_atual = list(resultados[index])

                # Supõe que a primeira coluna contém o ds_valor para correspondência
                ds_valor_linha = linha_atual[0] if len(linha_atual) > 0 else ''

                if ds_valor_linha in regras_por_valor:
                    regra_linha = regras_por_valor[ds_valor_linha].get('L', None)
                    if regra_linha:
                        ds_cor = regra_linha['ds_cor']
                        ie_icon_replace = regra_linha['ie_icon_replace']
                        nm_icon = regra_linha['nm_icon']

                        if ie_icon_replace == 'S':
                            # Substitui toda a linha com o ícone
                            resultados[index] = [f'<i class="{nm_icon}"></i>'] * len(linha_atual)
                            
                        else:
                            # Aplica a cor em toda a linha
                            resultados[index] = [f'<span class="linha-cor-{ds_cor}">{valor}</span>' for valor in linha_atual]

                # Aplica as regras 'C' para células específicas
                for col_index, valor in enumerate(linha_atual):
                    if valor in regras_por_valor:
                        regra_celula = regras_por_valor[valor].get('C', None)
                        if regra_celula:
                            ds_cor = regra_celula['ds_cor']
                            ie_icon_replace = regra_celula['ie_icon_replace']
                            nm_icon = regra_celula['nm_icon']
                            

                            if ie_icon_replace == 'S':
                                
                                if nm_icon != '' or nm_icon == None:
                                    # Substitui o valor da célula pelo ícone e aplica a cor
                                    linha_atual[col_index] = f'<i class="{nm_icon}" style="color:{ds_cor}"></i>'
                                    print("teste", ds_cor)  
                                else:
                                    # Aplica apenas a cor, sem ícone e sem valor
                                    linha_atual[col_index] = f'<span class="celula-cor" data-color="{ds_cor}"></span>'
                            else:
                                # Aplica a cor ao valor original da célula
                                linha_atual[col_index] = f'<span class="celula-cor" style="background-color:{ds_cor}" data-color="{ds_cor}">{valor}</span>'



                resultados[index] = tuple(linha_atual)
                
                
                # Aplica a regra para a linha inteira 'L'
                if ds_valor_linha in regras_por_valor:
                    regra_linha = regras_por_valor[ds_valor_linha].get('L', None)
                    if regra_linha:
                        ds_cor = regra_linha['ds_cor']
                        ie_icon_replace = regra_linha['ie_icon_replace']
                        nm_icon = regra_linha['nm_icon']

                        if ie_icon_replace == 'S':
                            if nm_icon:  # Verifica se o ícone existe
                                # Substitui toda a linha com o ícone e aplica a cor
                                resultados[index] = [f'<i class="{nm_icon}" style="color:{ds_cor}"></i>'] * len(linha_atual)
                            else:
                                # Se não houver ícone, aplica apenas a cor, sem valor
                                resultados[index] = [f'<span class="linha-cor" style="background-color:{ds_cor}"></span>'] * len(linha_atual)
                        else:
                            # Aplica a cor para cada valor da linha
                            resultados[index] = [f'<span class="linha-cor" style="background-color:{ds_cor}; width: 100%; height: 100%; display: block; padding: 5px;">{valor}</span>' for valor in linha_atual]
                
        

            # Debugging: printar os dashboards e seus resultados
            print("Dashboards:", dashboards_resultados)
            print("Legendas:", legendas_resultados)
            print("Regras:", regras_resultados)

        except cx_Oracle.DatabaseError as e:
            flash(f"Erro ao executar o SQL do painel: {str(e)}", "danger")
            return redirect(url_for('lista_paineis'))

        finally:
            cursor.close()
            connection.close()

        return render_template('visualizar_painel.html',
                            resultados=resultados,  # Enviar todos os resultados
                            titulo_painel=ds_titulo_painel,
                            titulos=titulos,
                            painel_id=painel_id,
                            total=total,
                            per_page=per_page,
                            segundos_rolagem=segundos_rolagem,
                            segundos_atualizacao=segundos_atualizacao,
                            dashboards=dashboards_resultados,  # Passar dashboards e resultados para o template
                            legendas=legendas_resultados,
                            regras=regras_resultados)  # Passar as regras para o template
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

        with get_db_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT PAINEL_SEQ.NEXTVAL FROM dual")
                painel_id = cursor.fetchone()[0]

                # Inserir o painel
                cursor.execute(""" 
                    INSERT INTO hp_painel (nr_sequencia, ds_titulo_painel, ds_observacao, qt_segundos_rolagem, 
                                        qt_segundos_atualizacao, ds_sql, dt_atualizacao, dt_criacao, 
                                        nm_usuario_criacao, ie_situacao)
                    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
                """, (painel_id, titulo, descricao, segundos_rolagem, segundos_atualizacao, 
                    sql_query, dt_atualizacao, dt_criacao, nm_usuario_criacao, ie_situacao))

                connection.commit()
                flash("Painel cadastrado com sucesso!")
                
                # Redirecionar para a rota editar_painel com o painel_id
                return redirect(url_for('editar_painel', painel_id=painel_id))
                
            except cx_Oracle.IntegrityError as e:
                error, = e.args
                if error.code == 1:  # Para ORA-00001 (violação de chave primária)
                    flash("Erro: já existe um painel com este ID.", "danger")
                else:
                    flash(f"Erro ao cadastrar painel: {str(e)}", "danger")

    return render_template('cadastrar_painel.html')









# Rota editar painel
@app.route('/editar_painel/<int:painel_id>', methods=['GET', 'POST'])
def editar_painel(painel_id):
    # Se o método for POST, o painel está sendo salvo
    if request.method == 'POST':
        # Lógica de atualização do painel, se necessário
        # Mas não deve redirecionar para 'edit_column' automaticamente
        # Caso contrário, deve-se remover essa parte.
        pass

    # Buscar as informações do painel
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT ds_titulo_painel, ds_observacao, qt_segundos_rolagem, qt_segundos_atualizacao, ds_sql 
            FROM hp_painel 
            WHERE nr_sequencia = :1
        """, (painel_id,))
        painel = cursor.fetchone()

        if not painel:
            flash("Painel não encontrado.", "danger")
            return redirect(url_for('cadastrar_painel'))

        # Buscar colunas associadas ao painel
        cursor.execute("""
            SELECT ds_titulo_coluna,  ds_atributo, nvl(nm_class,' ') as nm_class, nvl(ie_hidden,' ') as ie_hidden, qt_tamanho, nr_seq_apresentacao 
            FROM hp_painel_coluna 
            WHERE fk_nr_seq_painel = :1 
            ORDER BY nr_seq_apresentacao
        """, (painel_id,))
        colunas = cursor.fetchall()

        # Buscar dashboards associados ao painel
        cursor.execute("""
            SELECT ds_titulo, ds_cor, ds_sql 
            FROM hp_painel_dashboard 
            WHERE fk_nr_seq_painel = :1
        """, (painel_id,))
        dashboards = cursor.fetchall()

        # Buscar legendas associadas ao painel
        cursor.execute("""
            SELECT ds_legenda, ds_cor 
            FROM hp_painel_legenda 
            WHERE fk_nr_seq_painel = :1
        """, (painel_id,))
        legendas = cursor.fetchall()

        # Buscar regras de cores associadas ao painel
        cursor.execute("""
            SELECT ds_valor, ds_cor, nvl(ie_icon_replace,' ') as ie_icon_replace, nm_icon 
            FROM hp_painel_regra_cor 
            WHERE fk_nr_seq_painel_coluna IN (
                SELECT nr_sequencia FROM hp_painel_coluna WHERE fk_nr_seq_painel = :1
            )
        """, (painel_id,))
        regras = cursor.fetchall()

    return render_template(
        'editar_painel.html', 
        painel=painel, 
        colunas=colunas, 
        dashboards=dashboards, 
        legendas=legendas, 
        regras=regras, 
        painel_id=painel_id
    )


    
# Rota para excluir painel
@app.route('/excluir_painel/<int:painel_id>', methods=['POST'])
def excluir_painel(painel_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hp_painel WHERE nr_sequencia = :1", (painel_id,))
        connection.commit()
        flash("Painel excluído com sucesso!")
        return redirect(url_for('lista_paineis'))
    
    
    
# Rota para duplicar painel
@app.route('/duplicar_painel/<int:painel_id>', methods=['POST'])
def duplicar_painel(painel_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        # Buscar o painel original
        cursor.execute('SELECT * FROM hp_painel WHERE nr_sequencia = :1', (painel_id,))
        painel = cursor.fetchone()
        
        if painel is None:
            flash('Painel não encontrado.')
            return redirect(url_for('lista_paineis'))

        # Obter o próximo valor da sequência para o novo painel
        cursor.execute("SELECT PAINEL_SEQ.NEXTVAL FROM dual")
        new_painel_id = cursor.fetchone()[0]

        # Inserir um novo painel com os mesmos dados, mas com a nova sequência (novo ID)
        cursor.execute("""
            INSERT INTO hp_painel (nr_sequencia, ds_titulo_painel, ds_observacao, qt_segundos_rolagem, qt_segundos_atualizacao, ds_sql)
            VALUES (:1, :2, :3, :4, :5, :6)
        """, (new_painel_id, painel[1], painel[2], painel[4], painel[3], painel[5]))

        # Adicionar colunas do painel original ao novo painel
        cursor.execute('SELECT * FROM hp_painel_coluna WHERE FK_NR_SEQ_PAINEL = :1', (painel_id,))
        colunas = cursor.fetchall()

        
        
        for coluna in colunas:
            # Obter o próximo valor da sequência para cada nova coluna
            cursor.execute("SELECT PAINEL_COLUNA_SEQ.NEXTVAL FROM dual")
            new_coluna_id = cursor.fetchone()[0]

            # Inserir as colunas do painel original, associando-as ao novo painel
        cursor.execute("""
    INSERT INTO hp_painel_coluna 
    (NR_SEQUENCIA, DT_ATUALIZACAO, DS_TITULO_COLUNA, DS_ATRIBUTO, NM_CLASS, QT_TAMANHO, NR_SEQ_APRESENTACAO, IE_HIDDEN, dt_criacao, nm_usuario_atualizacao, nm_usuario_criacao, FK_NR_SEQ_PAINEL)
    VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)
""", (new_coluna_id, coluna[1], coluna[2], coluna[3], coluna[4], coluna[5], coluna[6], coluna[7], coluna[8], coluna[9], coluna[10], new_painel_id))


        connection.commit()
        flash('Painel duplicado com sucesso!')
        return redirect(url_for('lista_paineis'))
    except Exception as e:
        flash(f"Erro ao duplicar painel: {str(e)}")
        return redirect(url_for('lista_paineis'))
    finally:
        cursor.close()
        connection.close()
# Adiciona coluna
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
        classe_coluna = request.form.get('classe_coluna') or None  # Define como None se não estiver preenchido
        tamanho_coluna = request.form.get('tamanho_coluna')
        numero_apre_coluna = request.form.get('numero_apre_coluna')
        escondido_coluna = 'H' if request.form.get('escondido_coluna') else None  # Define como None se não estiver marcado

        # Verificar se os campos obrigatórios estão preenchidos
        if not titulo_coluna or not atributo_coluna or not tamanho_coluna or not numero_apre_coluna:
            return jsonify({'success': False, 'error': 'Preencha todos os campos obrigatórios'}), 400

        try:
            # Gerar um novo ID para a coluna
            cursor.execute("SELECT COLUNA_SEQ.NEXTVAL FROM dual")
            coluna_id = cursor.fetchone()[0]
            print("Nova ID da coluna:", coluna_id) 
            # Debug: imprimir o ID gerado
            print(f"ID gerado para a nova coluna: {coluna_id}")

            # Inserir nova coluna no banco de dados
            cursor.execute(""" 
                INSERT INTO HP_PAINEL_COLUNA 
                (NR_SEQUENCIA, DS_TITULO_COLUNA, DS_ATRIBUTO, FK_NR_SEQ_PAINEL, 
                DT_CRIACAO, DT_ATUALIZACAO, NM_USUARIO_CRIACAO, NM_USUARIO_ATUALIZACAO, 
                QT_TAMANHO, NR_SEQ_APRESENTACAO, IE_HIDDEN, IE_SITUACAO, NM_CLASS)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13)
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
                escondido_coluna,  # IE_HIDDEN
                'A',               # IE_SITUACAO
                classe_coluna      # NM_CLASS
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
            print(f"Erro ao inserir a coluna: {str(e)}")  # Debug: imprimir erro
            return jsonify({'success': False, 'error': str(e)}), 500



#Rota editar coluna
    
@app.route('/edit_column', methods=['POST'])
def edit_column():
    coluna_id = request.form.get('nr_sequencia')
    titulo_coluna = request.form.get('titulo_coluna')
    atributo_coluna = request.form.get('atributo_coluna')
    classe_coluna = request.form.get('classe_coluna')
    tamanho_coluna = request.form.get('tamanho_coluna')
    numero_apre_coluna = request.form.get('numero_apre_coluna')
    escondido_coluna = request.form.get('escondido_coluna')
    dt_atualizacao = datetime.now()
    usuario_atualizacao = 'DMMSANTOS'
    
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""UPDATE HP_PAINEL_COLUNA
                          SET DS_TITULO_COLUNA = :1, DS_ATRIBUTO = :2, NM_CLASS = :3, QT_TAMANHO = :4, 
                              NR_SEQ_APRESENTACAO = :5, IE_HIDDEN = :6, DT_ATUALIZACAO = :7, 
                              nm_usuario_atualizacao = :8
                          WHERE NR_SEQUENCIA = :9""",
                          (titulo_coluna, atributo_coluna, classe_coluna, tamanho_coluna, numero_apre_coluna, 
                           'H' if escondido_coluna else None, dt_atualizacao, usuario_atualizacao, coluna_id))

        connection.commit()
        return jsonify(success=True)

# Rota deletar coluna
@app.route('/delete_column', methods=['POST'])
def delete_column():
    coluna_id = request.form.get('coluna_id')
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM HP_PAINEL_COLUNA WHERE NR_SEQUENCIA = :1", (coluna_id,))
        connection.commit()
        return jsonify(success=True)
    
from flask import Flask, request, render_template, flash, redirect, url_for
from datetime import datetime

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
                (nr_sequencia, ds_titulo, ds_sql, ds_cor, fk_nr_seq_painel, dt_criacao, dt_atualizacao, nm_usuario_criacao, nm_usuario_atualizacao)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
            """, (
                dashboard_id, 
                titulo_dashboard, 
                sql_dashboard, 
                cor_dashboard, 
                painel_id, 
                datetime.now(), 
                datetime.now(), 
                "DMMSANTOS",  # Substitua pelo usuário atual se necessário
                "DMMSANTOS"   # Substitua pelo usuário atual se necessário
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




@app.route('/editar_dashboard/<int:dashboard_id>', methods=['POST'])
def editar_dashboard(dashboard_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()

        # Captura os dados do formulário enviados via modal
        titulo_dashboard = request.form.get('titulo_dashboard')
        sql_dashboard = request.form.get('sql_dashboard')
        cor_dashboard = request.form.get('cor_dashboard')

        # Verificar se os campos obrigatórios estão preenchidos
        if not titulo_dashboard or not sql_dashboard:
            return jsonify({'success': False, 'error': 'Preencha todos os campos obrigatórios'}), 400

        try:
            # Atualizar o dashboard no banco de dados
            cursor.execute("""
                UPDATE hp_painel_dashboard
                SET ds_titulo = :1, ds_sql = :2, ds_cor = :3, dt_atualizacao = :4
                WHERE nr_sequencia = :5
            """, (
                titulo_dashboard, 
                sql_dashboard, 
                cor_dashboard, 
                datetime.now(), 
                dashboard_id
            ))
            connection.commit()

            # Retornar sucesso e os dados do dashboard atualizado para serem refletidos no frontend
            return jsonify({
                'success': True,
                'dashboard_id': dashboard_id,
                'titulo_dashboard': titulo_dashboard,
                'sql_dashboard': sql_dashboard,
                'cor_dashboard': cor_dashboard
            }), 200

        except Exception as e:
            connection.rollback()
            print(f"Erro ao atualizar o dashboard: {str(e)}")  # Debug: imprimir erro
            return jsonify({'success': False, 'error': str(e)}), 500



# Excluir Dashboard
@app.route('/excluir_dashboard/<int:dashboard_id>', methods=['POST'])
def excluir_dashboard(dashboard_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hp_painel_dashboard WHERE nr_sequencia = :1", (dashboard_id,))
        connection.commit()
        flash('Dashboard excluído com sucesso!')
        return redirect(url_for('listar_dashboards'))

# Listar Legendas
@app.route('/legendas')
def listar_legendas():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM hp_painel_legenda')
        legendas = cursor.fetchall()
        return render_template('listar_legendas.html', legendas=legendas)
    
 #cadastrar legendas

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


# Editar Legenda
@app.route('/editar_legenda/<int:legenda_id>', methods=['GET', 'POST'])
def editar_legenda(legenda_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            descricao_legenda = request.form['descricao_legenda']
            
            cursor.execute("""
                UPDATE hp_painel_legenda
                SET ds_legenda = :1
                WHERE nr_sequencia = :2
            """, (descricao_legenda, legenda_id))
            connection.commit()
            flash('Legenda atualizada com sucesso!')
            return redirect(url_for('listar_legendas'))
        
        cursor.execute('SELECT * FROM hp_painel_legenda WHERE nr_sequencia = :1', (legenda_id,))
        legenda = cursor.fetchone()
        return render_template('editar_legenda.html', legenda=legenda)

# Excluir Legenda
@app.route('/excluir_legenda/<int:legenda_id>', methods=['POST'])
def excluir_legenda(legenda_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hp_painel_legenda WHERE nr_sequencia = :1", (legenda_id,))
        connection.commit()
        flash('Legenda excluída com sucesso!')
        return redirect(url_for('listar_legendas'))

# Listar Regras de Cor
@app.route('/regras_cor')
def listar_regras_cor():
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM hp_painel_regra_cor')
        regras = cursor.fetchall()
        return render_template('listar_regras_cor.html', regras=regras)

# Cadastrar Regra de Cor
@app.route('/cadastrar_regra_cor', methods=['POST'])
def cadastrar_regra_cor():
    if request.method == 'POST':
        descricao_regra = request.form['valor_regra']
        cor_regra = request.form['cor_regra']
        icone_regra = request.form['icone_regra']
        classe_regra = request.form['classe_regra']
        substituicao_regra = request.form.get('substituicao_regra', 'N')  # Pega 'N' se não estiver marcado
        coluna_id = request.form['coluna_regra']
        celula_linha_regra = request.form['celula_linha_regra']
        usuario_logado = session.get('username')  # Nome do usuário logado

        with get_db_connection() as connection:
            cursor = connection.cursor()
            # Gerar novo ID da regra de cor
            cursor.execute("SELECT REGRA_SEQ.NEXTVAL FROM dual")
            regra_id = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO hp_painel_regra_cor (NR_SEQUENCIA,
                                                  DS_COR,
                                                  DT_ATUALIZACAO,
                                                  DT_CRIACAO,
                                                  NM_ICON,
                                                  IE_CELULA_LINHA,
                                                  NM_USUARIO_ATUALIZACAO,
                                                  NM_USUARIO_CRIACAO,
                                                  IE_ICON_REPLACE,
                                                  IE_SITUACAO,
                                                  DS_VALOR,
                                                  FK_NR_SEQ_PAINEL_COLUNA,
                                                  NM_CLASS)
                VALUES (:1, :2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :3, :4, :5, :5, :6, 'A', :7, :8, :9)
            """, (regra_id, cor_regra, icone_regra, celula_linha_regra, usuario_logado, substituicao_regra, descricao_regra, coluna_id, classe_regra))
            connection.commit()
            return jsonify({'success': True, 'message': 'Regra de cor cadastrada com sucesso!'})
    
    return jsonify({'success': False, 'message': 'Erro ao cadastrar regra de cor.'})

# Rota para listar as colunas no modal da regra
@app.route('/listar_colunas_painel', methods=['GET'])
def listar_colunas_painel():
    painel_id = request.args.get('painel_id')
    
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT nr_sequencia, ds_coluna FROM hp_painel_coluna WHERE fk_nr_seq_painel = :1', (painel_id,))
        colunas = cursor.fetchall()

        colunas_list = [{'nr_sequencia': coluna[0], 'ds_coluna': coluna[1]} for coluna in colunas]
        return jsonify({'colunas': colunas_list})
    

# Editar Regra de Cor
@app.route('/editar_regra_cor/<int:regra_id>', methods=['GET', 'POST'])
def editar_regra_cor(regra_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        
        if request.method == 'POST':
            descricao_regra = request.form['descricao_regra']
            cor_regra = request.form['cor_regra']
            
            cursor.execute("""
                UPDATE hp_painel_regra_cor
                SET ds_regra = :1, ds_cor = :2
                WHERE nr_sequencia = :3
            """, (descricao_regra, cor_regra, regra_id))
            connection.commit()
            flash('Regra de cor atualizada com sucesso!')
            return redirect(url_for('listar_regras_cor'))
        
        cursor.execute('SELECT * FROM hp_painel_regra_cor WHERE nr_sequencia = :1', (regra_id,))
        regra = cursor.fetchone()
        return render_template('editar_regra_cor.html', regra=regra)

# Excluir Regra de Cor
@app.route('/excluir_regra_cor/<int:regra_id>', methods=['POST'])
def excluir_regra_cor(regra_id):
    with get_db_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM hp_painel_regra_cor WHERE nr_sequencia = :1", (regra_id,))
        connection.commit()
        flash('Regra de cor excluída com sucesso!')
        return redirect(url_for('listar_regras_cor'))
    

if __name__ == '__main__':
    app.run(debug=True)
