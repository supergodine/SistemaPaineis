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

// Função para salvar coluna (adicionar ou editar)
$('#saveColumn').on('click', function () {
    var form = $('#addColumnForm')[0];
    var formData = new FormData(form);
    formData.append('painel_id', painelId); // Adiciona o painel_id ao formData

    // Define a URL com base no modo (adicionar ou editar)
    var url = editando ? '/edit_column/' + $('#coluna_id').val() : '/adicionar_coluna/' + painelId;

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#addColumnModal').modal('hide');
            alert('Coluna salva com sucesso!');
            location.reload(); // Recarrega a página para mostrar a nova coluna
        } else {
            alert('Erro ao salvar a coluna: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro na comunicação com o servidor.');
    });
});

// Função para editar uma coluna
window.editarColuna = function (id, titulo, atributo, classe, escondido, tamanho, numeroApre) {
    editando = true; // Define o modo de edição
    $('#coluna_id').val(id); // Preenche o ID da coluna
    $('#titulo_coluna').val(titulo); // Preenche o título da coluna
    $('#atributo_coluna').val(atributo); // Preenche o atributo
    $('#classe_coluna').val(classe); // Preenche a classe
    $('#escondido_coluna').prop('checked', (escondido === 'H')); // Marca se a coluna está escondida
    $('#tamanho_coluna').val(tamanho); // Preenche o tamanho
    $('#numero_apre_coluna').val(numeroApre); // Preenche o número de aparições

    $('#addColumnModal').modal('show'); // Abre o modal para edição
    $('#duplicateColumn').show(); // Mostra o botão de duplicar quando em modo de edição
};


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




