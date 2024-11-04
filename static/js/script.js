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


    /******************************************Inicio Painel **********************************/
    //Editar painel
    document.addEventListener('DOMContentLoaded', function () {
        const form = document.getElementById('editarPainelForm');
        const tituloPainel = document.getElementById('ds_titulo_painel');

        form.addEventListener('submit', function (event) {
            // Verificar se o título do painel está vazio
            if (!tituloPainel.value.trim()) {
                event.preventDefault();
                alert("O título do painel é obrigatório.");
            }
        });

        // Função para exibir flash messages temporárias
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach((msg) => {
            setTimeout(() => {
                msg.style.display = 'none';
            }, 5000); // Oculta as mensagens após 5 segundos
        });

        // Exemplo de código adicional para preview do SQL
        const sqlInput = document.getElementById('ds_sql');
        const previewButton = document.getElementById('previewSQL');

        previewButton.addEventListener('click', function () {
            alert("SQL Preview:\n" + sqlInput.value);
        });
    });

    
    /******************************************Fim Painel **********************************/


/**********************************inicio colunas***************************************/

    // Função para preencher e exibir o modal de edição de coluna
    function editarColuna(id, titulo, atributo, classe, tamanho, numero_apre) {
        // Preencher os campos do modal com os dados da coluna
        document.getElementById('coluna_id').value = id;
        document.getElementById('titulo_coluna').value = titulo;
        document.getElementById('atributo_coluna').value = atributo;
        document.getElementById('classe_coluna').value = classe;
        document.getElementById('tamanho_coluna').value = tamanho;
        document.getElementById('numero_apre_coluna').value = numero_apre;

        // Abrir o modal
        $('#addColumnModal').modal('show');
    }

    // Envio do formulário via AJAX
    $('#adicionarColunaForm').submit(function (event) {
        event.preventDefault(); // Impede o envio tradicional do formulário

        // Coleta o ID da coluna e os dados do formulário
        const colunaId = $(this).data('coluna-id');
        const formData = {
            nr_sequencia: colunaId,
            titulo_coluna: $('#titulo_coluna').val(),
            atributo_coluna: $('#atributo_coluna').val(),
            classe_coluna: $('#classe_coluna').val(),
            tamanho_coluna: $('#tamanho_coluna').val(),
            numero_apre_coluna: $('#numero_apre_coluna').val(),
            escondido_coluna: $('#escondido_coluna').is(':checked') ? 'H' : ''
        };

        // Envia os dados via AJAX para a rota de edição
        $.ajax({
            url: '/editar_coluna',  // A rota da função de edição no backend
            type: 'POST',
            data: formData,
            success: function (response) {
                if (response.success) {
                    // Fecha o modal e limpa o formulário
                    $('#addColumnModal').modal('hide');
                    $('#adicionarColunaForm')[0].reset();

                    // Mostra mensagem de sucesso
                    alert('Coluna editada com sucesso!');

                    // Atualiza a tabela ou recarrega a página para refletir a mudança
                    location.reload();
                } else {
                    alert('Erro ao editar a coluna.');
                }
            },
            error: function () {
                alert('Erro ao editar a coluna. Verifique a conexão e tente novamente.');
            }
        });
    });
    // Abertura do modal para nova coluna
    $('#novaColunaBtn').on('click', function () {
        editando = false;
        $('#addColumnModal').modal('show');
        $('#addColumnForm')[0].reset(); // Limpa o formulário quando o modal é aberto
        $('#duplicateColumn').hide(); // Esconde o botão de duplicar no modo de adicionar
    });
    // adicionar nova coluna
    document.getElementById("adicionarColunaForm").addEventListener("submit", function (event) {
        event.preventDefault(); // Impede o envio normal do formulário

        const formData = new FormData(this);

        fetch(this.action, {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fecha o modal
                    $('#addColumnModal').modal('hide');

                    // Atualiza a lista de colunas na tela de edição
                    atualizarColunas(data);
                } else {
                    alert("Erro ao adicionar a coluna.");
                }
            })
            .catch(error => console.error("Erro:", error));
    });

    function atualizarColunas(data) {
        // Seleciona o corpo da tabela onde as colunas estão
        const tbody = document.getElementById("colunas");

        // Cria uma nova linha na tabela
        const novaLinha = document.createElement("tr");
        novaLinha.setAttribute("data-coluna-id", data.coluna_id);

        // Adiciona as células com os dados da nova coluna
        /* novaLinha.innerHTML = `
        <td>${data.titulo_coluna}</td>
        <td>${data.atributo_coluna}</td>
        <td>${data.classe_coluna || ''}</td>
        <td>${data.escondido_coluna ? 'Sim' : 'Não'}</td>
        <td>${data.tamanho_coluna}</td>
        <td>${data.numero_apre_coluna}</td>
        <td>
            <button class="btn btn-sm btn-outline-none"
                onclick="editarColuna('${data.coluna_id}', '${data.titulo_coluna}', '${data.atributo_coluna}', '${data.numero_apre_coluna}', '${data.tamanho_coluna}', '${data.classe_coluna}', '${data.escondido_coluna}')">
                <i class="fas fa-pencil-alt" style="color: rgb(1, 145, 212)" title="Editar Coluna"></i>
            </button>
            <button class="btn btn-sm btn-outline-none" title="Excluir" onclick="excluirColuna('${data.coluna_id}');">
                <i class="fas fa-trash-alt" style="color: rgb(187, 1, 1)"></i>
            </button>
            <button class="btn btn-sm btn-outline-none" onclick="duplicarColuna('${data.coluna_id}')">
                <i class="fas fa-copy" style="color: rgb(156, 212, 1)" title="Duplicar Coluna"></i>
            </button>
            
        </td>
    `*/
    ;

        // Adiciona a nova linha ao tbody
        tbody.appendChild(novaLinha);
    }


    // Adicionando o listener ao botão de exclusão
    document.addEventListener('DOMContentLoaded', function () {
        const deleteButtons = document.querySelectorAll('button[title="Excluir"]');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function () {
                const colunaId = this.closest('tr').getAttribute('data-coluna-id');
                console.log("ID da coluna extraído para exclusão:", colunaId);  // Verifique o ID da coluna extraído
                excluirColuna(colunaId);
            });
        });
    });


    // Garanta que o código que chama a função esteja dentro do DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function () {
        // Aqui você pode adicionar outros códigos ou inicializações
    });

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
    $('.celula-cor').each(function () {
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

    dadosColunas.forEach(function (coluna) {
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

    // Duplicar colunas
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

    // Duplicar coluna
    function duplicarColuna(coluna_id) {
        if (confirm('Tem certeza de que deseja duplicar esta coluna?')) {
            // Realiza a requisição POST para duplicar a coluna
            $.post('/duplicar_coluna', { nr_sequencia: coluna_id })
                .done(function (response) {
                    if (response.success) {
                        alert('Coluna duplicada com sucesso!'); // Mensagem de sucesso
                        location.reload(); // Recarrega a página para mostrar a coluna duplicada
                    } else {
                        alert('Erro ao duplicar a coluna: ' + response.message);
                    }
                })
                .fail(function () {
                    alert('Erro ao fazer a requisição. Por favor, tente novamente.');
                });
        }
    }
    

/****************************************Fim Colunas ***************************************/

/****************************************Inicio cards ***************************************/
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

/***********************************Fim Cards**********************************/


/**************************************Inicio Legendas ************************/
    // Função para editar legenda
    window.editarLegenda = function (id, titulo, cor) {
        $('#legenda_id').val(id);
        $('#titulo_legenda').val(titulo);
        $('#cor_legenda').val(cor);
        $('#addLegendModal').modal('show');
    };


// legendas
function duplicarLegenda(titulo, cor, numero_apre) {
    // Adiciona "Cópia de" ao título
    document.getElementById('titulo_legenda').value = "Cópia de " + titulo;
    document.getElementById('cor_legenda').value = cor;
    document.getElementById('numero_apre_legenda').value = numero_apre;

    // Exibe o modal de adição de legenda
    $('#addLegendModal').modal('show');
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

// cadastrar legenda

$(document).ready(function () {
    $('#saveLegendButton').on('click', function (event) {
        event.preventDefault();  // Previne o comportamento padrão de submissão do formulário

        // Captura os dados do formulário
        let titulo_legenda = $('#titulo_legenda').val();
        let cor_legenda = $('#cor_legenda').val();
        let numero_apre_legenda = $('#numero_apre_legenda').val();
        let painel_id = $('input[name="painel_id"]').val();

        // Debug: Verificar os valores capturados
        console.log('Título da Legenda:', titulo_legenda);
        console.log('Cor da Legenda:', cor_legenda);
        console.log('Número de Apresentação:', numero_apre_legenda);
        console.log('ID do Painel:', painel_id);

        // Verificar se os campos estão preenchidos
        if (!titulo_legenda || !cor_legenda || !numero_apre_legenda || !painel_id) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;  // Para se os campos não estiverem preenchidos
        }

        let formData = {
            descricao_legenda: titulo_legenda,  // Use o título como descrição
            cor_legenda: cor_legenda,
            numero_apre_legenda: numero_apre_legenda,
            painel_id: painel_id
        };

        $.ajax({
            url: '/cadastrar_legenda',
            method: 'POST',
            data: formData,
            success: function (response) {
                console.log('Resposta do servidor:', response);
                if (response.success) {
                    alert('Legenda cadastrada com sucesso!');
                    location.reload();  // Recarrega a página para refletir as mudanças
                } else {
                    alert('Erro: ' + response.error);
                }
            },
            error: function (xhr, status, error) {
                console.error('Erro na comunicação com o servidor:', xhr.status, xhr.statusText);
                alert('Erro ao cadastrar a legenda.');
            }
        });
    });
});


/********************************************Fim Legendas************************************** */


/*******************************************Inicio dashboard ************************************/
// Função para editar dashboard
window.editarDashboard = function (id, titulo, sql, cor) {
    $('#dashboard_id').val(id);
    $('#titulo_dashboard').val(titulo);
    $('#sql_dashboard').val(sql);
    $('#cor_dashboard').val(cor);
    $('#addDashboardModal').modal('show');
};

// dashboard
function duplicarDashboard(titulo, sql, cor) {
    // Adiciona "Cópia de" ao título
    document.getElementById('titulo_dashboard').value = "Cópia de " + titulo;
    document.getElementById('sql_dashboard').value = sql;
    document.getElementById('cor_dashboard').value = cor;

    // Exibe o modal de adição de dashboard
    $('#addDashboardModal').modal('show');
}

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

// Função para salvar as alterações de Dashboard

$(document).ready(function () {
    $('#saveDashboardButton').on('click', function (event) {
        console.log('Botão clicado!');  // Para verificar se o evento está sendo acionado
        alert('Botão clicado!');  // Para garantir que o click está funcionando
        event.preventDefault();  // Previne o comportamento padrão de submissão do formulário

        let formData = {
            // Adicione seus campos aqui
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
            success: function (response) {
                if (response.success) {
                    alert('Dashboard salvo com sucesso!');
                    location.reload();  // Recarrega a página para refletir as mudanças
                } else {
                    alert('Erro: ' + response.error);
                }
            },
            error: function (error) {
                console.error('Erro na comunicação com o servidor:', error);
                alert('Erro ao salvar o dashboard.');
            }
        });
    });
});

// Editar dashboard
$('#editDashboardButton').on('click', function (event) {
    event.preventDefault();  // Previne o comportamento padrão de submissão do formulário

    let formData = {
        dashboard_id: $('#dashboard_id').val(),
        titulo_dashboard: $('#titulo_dashboard').val(),
        sql_dashboard: $('#sql_dashboard').val(),
        cor_dashboard: $('#cor_dashboard').val(),
    };

    let url = '/editar_dashboard/' + formData.dashboard_id;

    $.ajax({
        url: url,
        method: 'POST',
        data: formData,
        success: function (response) {
            if (response.success) {
                alert('Dashboard atualizado com sucesso!');
                location.reload();  // Recarrega a página para refletir as mudanças
            } else {
                alert('Erro: ' + response.error);
            }
        },
        error: function (error) {
            console.error('Erro na comunicação com o servidor:', error);
            alert('Erro ao atualizar o dashboard.');
        }
    });
});

/************************************Fim Dashboard *****************************/

/************************************Inicio Regra ******************************/

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

// Função para popular o select de colunas no modal de regras
$(document).ready(function () {
    $('#addRuleModal').on('show.bs.modal', function (event) {
        var painelId = $('input[name="painel_id"]').val(); // Obtém o painel ID do formulário

        $.ajax({
            url: '/listar_colunas_painel',
            method: 'GET',
            data: { painel_id: painelId },
            success: function (response) {
                var colunasSelect = $('#coluna_regra');
                colunasSelect.empty(); // Limpa o select antes de adicionar os novos valores

                // Popula o select com as colunas retornadas do servidor
                $.each(response.colunas, function (index, coluna) {
                    colunasSelect.append(new Option(coluna.ds_atributo, coluna.nr_sequencia));
                });
            },
            error: function (error) {
                console.error('Erro ao buscar colunas:', error);
                alert('Erro ao carregar as colunas.');
            }
        });
    });
});


document.getElementById('addRuleForm').addEventListener('submit', function (event) {
    event.preventDefault(); // Impede o envio padrão do formulário

    const formData = {
        valor_regra: document.getElementById('valor_regra').value,
        icone_regra: document.getElementById('icone_regra').value,
        classe_regra: document.getElementById('classe_regra').value,
        substituicao_regra: document.getElementById('substituicao_regra').checked ? 'S' : 'N',
        cor_regra: document.getElementById('cor_regra').value,
        coluna_regra: document.getElementById('coluna_regra').value,
        celula_linha_regra: document.getElementById('celula_linha_regra').value,
        painel_id: document.getElementById('painel_id').value // Inclua o painel_id
    };

    fetch('/cadastrar_regra_cor', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json' // Cabeçalho correto
        },
        body: JSON.stringify(formData) // Dados enviados como JSON
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log(data); // Manipule a resposta aqui
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
});


function atualizarRegras(data) {
    // Seleciona o corpo da tabela onde as regras estão
    const tbody = document.getElementById("regras");

    // Cria uma nova linha na tabela
    const novaLinha = document.createElement("tr");
    novaLinha.setAttribute("data-regra-id", data.regra_id);

    // Adiciona as células com os dados da nova regra
    novaLinha.innerHTML = `
        <td>${data.valor_regra}</td>
        <td>${data.icone_regra || ''}</td>
        <td>${data.classe_regra || ''}</td>
        <td>${data.substituicao_regra ? 'Sim' : 'Não'}</td>
        <td>${data.cor_regra}</td>
        <td>${data.coluna_regra}</td>
        <td>${data.celula_linha_regra}</td>
        <td>
            <button class="btn btn-sm btn-outline-none"
                onclick="editarRegra('${data.regra_id}', '${data.valor_regra}', '${data.icone_regra}', '${data.classe_regra}', '${data.substituicao_regra}', '${data.cor_regra}', '${data.coluna_regra}', '${data.celula_linha_regra}')">
                <i class="fas fa-pencil-alt" style="color: rgb(1, 145, 212)" title="Editar Regra"></i>
            </button>
            <button class="btn btn-sm btn-outline-none" title="Excluir" onclick="excluirRegra('${data.regra_id}');">
                <i class="fas fa-trash-alt" style="color: rgb(187, 1, 1)"></i>
            </button>
        </td>
    `;

    // Adiciona a nova linha ao tbody
    tbody.appendChild(novaLinha);
}

/*******************************************Fim Regra ******************************************************/
