$(document).ready(function () {
    var editando = false;
    var painelId = $("#painel_id").val(); // Atribuindo o ID do painel associado

    // Tema no painel
    const currentTheme = localStorage.getItem('theme') || 'light';
    $('body').addClass(currentTheme + '-theme');

    // Alterna o tema ao clicar no botão
    $('#themeToggle').click(function () {
        $('body').toggleClass('light-theme dark-theme');
        // Salva a preferência do tema no localStorage
        localStorage.setItem('theme', $('body').hasClass('dark-theme') ? 'dark' : 'light');
    });




   // Abertura do modal para nova coluna
$('#novaColunaBtn').on('click', function () {
    editando = false;
    $('#addColumnModal').modal('show');
    $('#addColumnForm')[0].reset(); // Limpa o formulário quando o modal é aberto
    $('#duplicateColumn').hide(); // Esconde o botão de duplicar no modo de adicionar
});

// Adicionar coluna
$('#addColumnForm').on('submit', function (e) {
    e.preventDefault();  // Evita que o formulário seja submetido da maneira tradicional

    var form = $('#addColumnForm')[0];
    var formData = new FormData(form);

    // Não precisa adicionar painel_id via JavaScript se ele já está no formulário como campo hidden
    // formData.append('painel_id', painelId); 

    // Definindo a URL correta para adicionar ou editar
    var url = editando ? '/edit_column/' + $('#coluna_id').val() : '/adicionar_coluna/' + $('input[name="painel_id"]').val();

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#addColumnModal').modal('hide');
            alert('Coluna salva com sucesso!');
            location.reload();  // Recarrega a página para refletir a nova coluna
        } else {
            alert('Erro ao salvar a coluna: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro na comunicação com o servidor.');
    });
});
/// Função para editar uma coluna
window.editarColuna = function (id, titulo, atributo, classe, escondido, tamanho, numeroApre) {
    console.log("Editando coluna com ID:", id); // Debug para ver o ID da coluna sendo editada
    editando = true; // Define o modo de edição

    $('#coluna_id').val(id); // Preenche o ID da coluna
    console.log("ID da coluna preenchido:", id); // Debug para ver o ID preenchido

    $('#titulo_coluna').val(titulo); // Preenche o título da coluna
    console.log("Título da coluna preenchido:", titulo); // Debug para ver o título preenchido

    $('#atributo_coluna').val(atributo); // Preenche o atributo
    console.log("Atributo da coluna preenchido:", atributo); // Debug para ver o atributo preenchido

    $('#classe_coluna').val(classe); // Preenche a classe
    console.log("Classe da coluna preenchida:", classe); // Debug para ver a classe preenchida

    $('#escondido_coluna').prop('checked', (escondido === 'H')); // Marca se a coluna está escondida
    console.log("Coluna escondida marcada:", escondido === 'H'); // Debug para ver se está escondida

    $('#tamanho_coluna').val(tamanho); // Preenche o tamanho
    console.log("Tamanho da coluna preenchido:", tamanho); // Debug para ver o tamanho preenchido

    $('#numero_apre_coluna').val(numeroApre); // Preenche o número de aparições
    console.log("Número de aparições preenchido:", numeroApre); // Debug para ver o número de aparições preenchido

    $('#addColumnModal').modal('show'); // Abre o modal para edição
    $('#duplicateColumn').show(); // Mostra o botão de duplicar quando em modo de edição
    console.log("Modal de edição aberto."); // Debug para confirmar que o modal foi aberto
};

// Função para salvar as alterações ao clicar no botão de salvar
$('#saveChangesButton').on('click', function() {
    // Coleta os dados do modal para envio
    let formData = {
        nr_sequencia: $('#coluna_id').val(),
        titulo_coluna: $('#titulo_coluna').val(),
        atributo_coluna: $('#atributo_coluna').val(),
        classe_coluna: $('#classe_coluna').val(),
        escondido_coluna: $('#escondido_coluna').is(':checked') ? 'H' : null,
        tamanho_coluna: $('#tamanho_coluna').val(),
        numero_apre_coluna: $('#numero_apre_coluna').val(),
    };

    // Envia os dados via AJAX para a rota edit_column
    $.ajax({
        url: '/edit_column',
        method: 'POST',
        data: formData,
        success: function(response) {
            if (response.success) {
                alert('Coluna editada com sucesso');
                // Aqui você pode atualizar a interface ou recarregar a página para refletir as mudanças
            } else {
                alert('Erro ao editar coluna: ' + response.error);
            }
        },
        error: function(error) {
            console.error('Erro na comunicação com o servidor', error);
        }
    });
});

    // Função para excluir uma coluna
    window.excluirColuna = function (id) {
        if (confirm('Tem certeza que deseja excluir esta coluna?')) {
            fetch('/delete_column', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ coluna_id: id })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Coluna excluída com sucesso!');
                    location.reload();
                } else {
                    alert('Erro ao excluir a coluna: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Erro:', error);
                alert('Erro na comunicação com o servidor.');
            });
        }
    };

    // Filtro da tabela
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('painelTableBody');

    if (searchInput && tableBody) {
        searchInput.addEventListener('input', function () {
            const filter = searchInput.value.toLowerCase();
            const rows = tableBody.getElementsByTagName('tr');

            for (let i = 0; i < rows.length; i++) {
                let row = rows[i];
                let cells = row.getElementsByTagName('td');
                let found = false;

                for (let j = 0; j < cells.length; j++) {
                    const cell = cells[j];
                    if (cell.textContent.toLowerCase().includes(filter)) {
                        found = true;
                        break;
                    }
                }

                row.style.display = found ? '' : 'none';
            }
        });
    } else {
        console.error("Elementos 'searchInput' ou 'painelTableBody' não encontrados.");
    }
    // Função para tornar os cards arrastáveis e salvar posições
    function tornarCardsArrastaveis(selector) {
        $(selector).draggable({
            containment: "body",
            stop: function (event, ui) {
                const cardId = $(this).attr('id');
                const position = ui.position;
                localStorage.setItem(cardId, JSON.stringify(position));
            }
        }).resizable({
            containment: "body"
        });

        // Restaura a posição dos cards ao carregar a página
        $(selector).each(function () {
            const cardId = $(this).attr('id');
            const position = JSON.parse(localStorage.getItem(cardId));
            if (position) {
                console.log(`Restaurando card ${cardId} para posição:`, position); // Debug
                $(this).css({
                    top: position.top + "px",
                    left: position.left + "px",
                    position: 'absolute'
                });
            } else {
                console.log(`Nenhuma posição encontrada para o card ${cardId}`); // Debug
            }
        });
    }

    // Torna todos os cards da dashboard e das legendas arrastáveis
    tornarCardsArrastaveis(".dashboard-card");
    tornarCardsArrastaveis(".legenda-card");

    // Altera a cor de fundo dos cards do dashboard
    $('.dashboard-card').each(function () {
        let titulo = $(this).find('.card-title').text();
        var cor = $(this).data('cor');
        if (titulo) {
            $(this).css('background-color', cor);
        }
    });

    // Altera a cor de fundo dos cards das legendagens
    $('.legenda-card').each(function () {
        var cor = $(this).data('cor'); // Captura o valor do data-cor
        let titulo = $(this).find('.card-title').text();
        if (titulo) {
            $(this).css('background-color', cor);
        }
    });

    // Função para editar legenda
    window.editarLegenda = function (id, titulo, cor) {
    $('#legenda_id').val(id);
    $('#titulo_legenda').val(titulo);
    $('#cor_legenda').val(cor);
    $('#addLegendModal').modal('show');
};

    // Função para editar dashboard
    window.editarDashboard = function (id, titulo, sql, cor) {
    $('#dashboard_id').val(id);
    $('#titulo_dashboard').val(titulo);
    $('#sql_dashboard').val(sql);
    $('#cor_dashboard').val(cor);
    $('#addDashboardModal').modal('show');
};

    var regras = []; // Inicializa a variável regras no escopo global ou do módulo

    // Função para buscar regras do servidor
    function buscarRegras() {
        $.ajax({
            url: '/sua-url-para-buscar-regras',
            method: 'GET',
            success: function (data) {
                regras = data.regras; // Assume que a resposta contém uma propriedade 'regras'
                aplicarCores(); // Chama a função para aplicar cores após carregar as regras
            },
            error: function (xhr, status, error) {
                console.error("Erro ao buscar regras:", error);
            }
        });
    }

    // Chame essa função para inicializar as regras
    buscarRegras();

    // Função para aplicar cores
    function aplicarCores() {
        $('#painelTableBody tr').each(function () {
            var rowIndex = $(this).index(); // Índice da linha atual
            $(this).find('td').each(function (index) {
                var cellContent = $(this).text().trim(); // Obtém o conteúdo de texto da célula

                // Procura a regra correspondente para a célula
                var regra = regras.find(function (reg) {
                    return reg.ds_valor.trim().toLowerCase() === cellContent.toLowerCase();
                });

                // Se encontrar a regra, aplica a cor ou o ícone conforme as condições
                if (regra) {
                    console.log(regra);
                    if (regra.ie_celula_linha === 'L' && regra.ds_cor) {
                        $(this).closest('tr').css('background-color', regra.ds_cor); // Aplica a cor ao fundo da linha
                    } else if (regra.ie_celula_linha === 'C' && regra.ds_cor) {
                        $(this).css('background-color', regra.ds_cor); // Aplica a cor ao fundo da célula
                    }
                    if (regra.ie_icon_replace === 'S' && regra.nm_icon) {
                        var iconHtml = `<img src="${regra.nm_icon}" alt="${cellContent} icon" />`;
                        $(this).html(iconHtml); // Substitui o conteúdo da célula pelo ícone
                    }
                }
            });
        });
    }

    // Função para editar regra
    window.editarRegra = function (id, valor, icone, classe, substituicao, cor, coluna, celulaLinha) {
    $('#regra_id').val(id);
    $('#valor_regra').val(valor);
    $('#icone_regra').val(icone);
    $('#classe_regra').val(classe);
    $('#substituicao_regra').val(substituicao);
    $('#cor_regra').val(cor);
    $('#coluna_regra').val(coluna);
    $('#celula_linha_regra').val(celulaLinha);
    $('#addRuleModal').modal('show');
    };

    // Duplicando coluna
    $('#duplicateColumn').on('click', function () {
        if (editando) {
            var colunaId = $('#coluna_id').val();
            var titulo = $('#titulo_coluna').val();
            var atributo = $('#atributo_coluna').val();
            var classe = $('#classe_coluna').val();
            var escondido = $('#escondido_coluna').is(':checked') ? 'H' : null;
            var tamanho = $('#tamanho_coluna').val();
            var numeroApre = $('#numero_apre_coluna').val();

            fetch('/duplicate_column', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    titulo_coluna: titulo,
                    atributo_coluna: atributo,
                    classe_coluna: classe,
                    escondido_coluna: escondido,
                    tamanho_coluna: tamanho,
                    numero_apre_coluna: numeroApre,
                    painel_id: painelId // Passa o ID do painel
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Coluna duplicada com sucesso!');
                        $('#addColumnModal').modal('hide');
                        location.reload(); // Recarrega a página para mostrar as mudanças
                    } else {
                        alert('Erro ao duplicar a coluna: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Erro:', error);
                });
        }
    });


    console.log("CELULAS");
    $('.celula-cor').each(function(){
        $(this).parent('td').css('background-color', $(this).data('color'));
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    const tableBody = document.getElementById('painelTableBody');

    searchInput.addEventListener('input', function () {
        const filter = searchInput.value.toLowerCase();
        const rows = tableBody.getElementsByTagName('tr');

        for (let i = 0; i < rows.length; i++) {
            let row = rows[i];
            let cells = row.getElementsByTagName('td');
            let found = false;

            // Verifica cada célula da linha
            for (let j = 0; j < cells.length; j++) {
                const cell = cells[j];
                if (cell.textContent.toLowerCase().includes(filter)) {
                    found = true; // Se encontrar, marca como encontrado
                    break; // Não precisa verificar mais células
                }
            }

            // Exibe ou oculta a linha com base na pesquisa
            if (found) {
                row.style.display = ''; // Exibe a linha
            } else {
                row.style.display = 'none'; // Oculta a linha
            }
        }
    });
});

function renderizarTabela(dadosColunas) {
    var tabelaBody = $('#painelTableBody');
    tabelaBody.empty(); // Limpa a tabela existente

    dadosColunas.forEach(function(coluna) {
        console.log(`Coluna: ${coluna.titulo}, Escondido: ${coluna.escondido}`); // Verifica o valor de escondido
        if (coluna.escondido !== 'H') { // Verifica se a coluna não está escondida
            var novaLinha = `<tr>
                <td>${coluna.titulo}</td>
                <td>${coluna.atributo}</td>
                <td>${coluna.classe}</td>
                <td>${coluna.tamanho}</td>
                <td>${coluna.numeroApre}</td>
                <td>
                    <button onclick="editarColuna('${coluna.id}', '${coluna.titulo}', '${coluna.atributo}', '${coluna.classe}', '${coluna.escondido}', '${coluna.tamanho}', '${coluna.numeroApre}')">Editar</button>
                    <button onclick="excluirColuna('${coluna.id}')">Excluir</button>
                </td>
            </tr>`;
            tabelaBody.append(novaLinha);
        } else {
            console.log(`Coluna ${coluna.titulo} está escondida.`);
        }
    });
}

// Funções para duplicar cadastros adicionais
// colunas
function duplicarColuna(titulo, atributo, classe, escondido, tamanho, numero_apre) {
    // Adiciona "Cópia de" ao título
    document.getElementById('titulo_coluna').value = "Cópia de " + titulo;
    document.getElementById('atributo_coluna').value = atributo;
    document.getElementById('classe_coluna').value = classe;
    document.getElementById('tamanho_coluna').value = tamanho;
    document.getElementById('numero_apre_coluna').value = numero_apre;

    // Define o checkbox de 'escondido' com base no valor booleano recebido
    document.getElementById('escondido_coluna').checked = escondido === 'H';

    // Exibe o modal de adição de coluna
    $('#addColumnModal').modal('show');
}

// dashboard
function duplicarDashboard(titulo, sql, cor) {
    // Adiciona "Cópia de" ao título
    document.getElementById('titulo_dashboard').value = "Cópia de " + titulo;
    document.getElementById('sql_dashboard').value = sql;
    document.getElementById('cor_dashboard').value = cor;

    // Exibe o modal de adição de dashboard
    $('#addDashboardModal').modal('show');
}

// legendas
function duplicarLegenda(titulo, cor, numero_apre) {
    // Adiciona "Cópia de" ao título
    document.getElementById('titulo_legenda').value = "Cópia de " + titulo;
    document.getElementById('cor_legenda').value = cor;
    document.getElementById('numero_apre_legenda').value = numero_apre;

    // Exibe o modal de adição de legenda
    $('#addLegendModal').modal('show');
}

// regras
function duplicarRegra(valor, icone, classe, substituicao, cor, coluna, celula_linha) {
    // Adiciona "Cópia de" ao valor
    document.getElementById('valor_regra').value = "Cópia de " + valor;
    document.getElementById('icone_regra').value = icone;
    document.getElementById('classe_regra').value = classe;
    document.getElementById('substituicao_regra').value = substituicao;
    document.getElementById('cor_regra').value = cor;
    document.getElementById('coluna_regra').value = coluna;
    document.getElementById('celula_linha_regra').value = celula_linha;

    // Exibe o modal de adição de regra
    $('#addRuleModal').modal('show');
}

let editandoDashboard = false;
let editandoLegenda = false;
let editandoRegra = false;

// Função para abrir o modal para adicionar um novo dashboard
function abrirModalAdicionarDashboard() {
    editandoDashboard = false; // Define que estamos adicionando
    $('#dashboard_id').val(''); // Limpa o campo de ID
    $('#titulo_dashboard').val(''); // Limpa o campo de título
    $('#sql_dashboard').val(''); // Limpa o campo SQL
    $('#cor_dashboard').val('#000000'); // Reseta a cor
    $('#addDashboardModal').modal('show'); // Mostra o modal
}

// Função para abrir o modal para editar um dashboard existente
function editarDashboard(id, titulo, sql, cor) {
    editandoDashboard = true; // Define que estamos editando
    $('#dashboard_id').val(id); // Preenche o ID
    $('#titulo_dashboard').val(titulo); // Preenche o título
    $('#sql_dashboard').val(sql); // Preenche o SQL
    $('#cor_dashboard').val(cor); // Preenche a cor
    $('#addDashboardModal').modal('show'); // Mostra o modal
}

// Função para abrir o modal para adicionar uma nova legenda
function abrirModalAdicionarLegenda() {
    editandoLegenda = false; // Define que estamos adicionando
    $('#legenda_id').val(''); // Limpa o campo de ID
    $('#titulo_legenda').val(''); // Limpa o campo de título
    $('#cor_legenda').val('#000000'); // Reseta a cor
    $('#numero_apre_legenda').val(''); // Limpa o campo de número de aparições
    $('#addLegendModal').modal('show'); // Mostra o modal
}

// Função para abrir o modal para editar uma legenda existente
function editarLegenda(id, titulo, cor, numeroApre) {
    editandoLegenda = true; // Define que estamos editando
    $('#legenda_id').val(id); // Preenche o ID
    $('#titulo_legenda').val(titulo); // Preenche o título
    $('#cor_legenda').val(cor); // Preenche a cor
    $('#numero_apre_legenda').val(numeroApre); // Preenche o número de aparições
    $('#addLegendModal').modal('show'); // Mostra o modal
}

// Função para abrir o modal para adicionar uma nova regra
function abrirModalAdicionarRegra() {
    editandoRegra = false; // Define que estamos adicionando
    $('#regra_id').val(''); // Limpa o campo de ID
    $('#valor_regra').val(''); // Limpa o campo de valor
    $('#icone_regra').val(''); // Limpa o campo de ícone
    $('#classe_regra').val(''); // Limpa o campo de classe
    $('#substituicao_regra').val(''); // Limpa o campo de substituição
    $('#cor_regra').val('#000000'); // Reseta a cor
    $('#coluna_regra').val(''); // Limpa o campo de coluna
    $('#celula_linha_regra').val(''); // Limpa o campo de célula/linha
    $('#addRuleModal').modal('show'); // Mostra o modal
}

// Função para abrir o modal para editar uma regra existente
function editarRegra(id, valor, icone, classe, substituicao, cor, coluna, celula) {
    editandoRegra = true; // Define que estamos editando
    $('#regra_id').val(id); // Preenche o ID
    $('#valor_regra').val(valor); // Preenche o valor
    $('#icone_regra').val(icone); // Preenche o ícone
    $('#classe_regra').val(classe); // Preenche a classe
    $('#substituicao_regra').val(substituicao); // Preenche a substituição
    $('#cor_regra').val(cor); // Preenche a cor
    $('#coluna_regra').val(coluna); // Preenche a coluna
    $('#celula_linha_regra').val(celula); // Preenche a célula/linha
    $('#addRuleModal').modal('show'); // Mostra o modal
}




// Função para salvar as alterações de Dashboard

// Função para salvar o dashboard ao clicar no botão "Salvar"
$('#saveDashboardButton').on('click', function(event) {
    event.preventDefault();  // Previne o comportamento padrão de submissão do formulário
    
    let formData = {
        dashboard_id: $('#dashboard_id').val(),
        titulo_dashboard: $('#titulo_dashboard').val(),
        sql_dashboard: $('#sql_dashboard').val(),
        cor_dashboard: $('#cor_dashboard').val(),
        painel_id: $('input[name="painel_id"]').val()
    };

    // Defina a URL de acordo com o modo de edição ou adição
    let url = formData.dashboard_id ? '/edit_dashboard' : '/cadastrar_dashboard'; 

    $.ajax({
        url: url,
        method: 'POST',
        data: formData,
        success: function(response) {
            if (response.success) {
                alert('Dashboard salvo com sucesso!');
                location.reload();  // Recarrega a página para refletir as mudanças
            } else {
                alert('Erro: ' + response.error);
            }
        },
        error: function(error) {
            console.error('Erro na comunicação com o servidor:', error);
            alert('Erro ao salvar o dashboard.');
        }
    });
});





// Função para salvar as alterações de Legenda
$('#saveLegendButton').on('click', function() {
    let formData = {
        legenda_id: $('#legenda_id').val(),
        titulo_legenda: $('#titulo_legenda').val(),
        cor_legenda: $('#cor_legenda').val(),
        numero_apre_legenda: $('#numero_apre_legenda').val(),
    };

    let url = editandoLegenda ? '/edit_legenda' : '/add_legenda'; // Ajuste as rotas conforme necessário

    $.ajax({
        url: url,
        method: 'POST',
        data: formData,
        success: function(response) {
            if (response.success) {
                alert('Operação realizada com sucesso');
                // Atualize a interface ou recarregue os dados conforme necessário
            } else {
                alert('Erro: ' + response.error);
            }
        },
        error: function(error) {
            console.error('Erro na comunicação com o servidor', error);
        }
    });
});

// Função para salvar as alterações de Regra
$('#saveRuleButton').on('click', function() {
    let formData = {
        regra_id: $('#regra_id').val(),
        valor_regra: $('#valor_regra').val(),
        icone_regra: $('#icone_regra').val(),
        classe_regra: $('#classe_regra').val(),
        substituicao_regra: $('#substituicao_regra').val(),
        cor_regra: $('#cor_regra').val(),
        coluna_regra: $('#coluna_regra').val(),
        celula_linha_regra: $('#celula_linha_regra').val(),
    };

    let url = editandoRegra ? '/edit_regra' : '/add_regra'; // Ajuste as rotas conforme necessário

    $.ajax({
        url: url,
        method: 'POST',
        data: formData,
        success: function(response) {
            if (response.success) {
                alert('Operação realizada com sucesso');
                // Atualize a interface ou recarregue os dados conforme necessário
            } else {
                alert('Erro: ' + response.error);
            }
        },
        error: function(error) {
            console.error('Erro na comunicação com o servidor', error);
        }
    });
});
