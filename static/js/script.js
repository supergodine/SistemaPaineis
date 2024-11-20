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

    // adicionar nova coluna
    document.getElementById("adicionarColunaForm").addEventListener("submit", function (event) {
        event.preventDefault();

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

                    // Recarrega a página de edição
                    location.reload();
                } else {
                    alert("Erro ao adicionar a coluna.");
                }
            })
            .catch(error => console.error("Erro:", error));
    });


    // editar coluna
    document.getElementById("editarColunaForm").addEventListener("submit", function (event) {
        event.preventDefault();

        // Criação de um objeto para os dados do formulário
        const formData = new FormData(this);
        const formObject = {};
        formData.forEach((value, key) => {
            formObject[key] = value;
        });

        // Envio dos dados como JSON
        fetch(this.action, {
            method: "POST",
            headers: {
                "Content-Type": "application/json" // Indica que estamos enviando JSON
            },
            body: JSON.stringify(formObject) // Converte os dados para JSON
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Fecha o modal
                    $('#editColumnModal').modal('hide');

                    // Recarrega a página de edição
                    location.reload();
                } else {
                    alert("Erro ao editar a coluna.");
                }
            })
            .catch(error => console.error("Erro:", error));
    });

    // Duplicando coluna  obs:  precisa ter
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


/****************************************Fim Colunas ***************************************/

/****************************************Inicio cards ***************************************/
// Função para tornar os cards arrastáveis e salvar posições
/*function tornarCardsArrastaveis(selector) {
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
tornarCardsArrastaveis(".legenda-card");*/

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

// Enviar dados para atualizar a legenda
$('#editLegendForm').on('submit', function (event) {
    event.preventDefault(); // Prevenir o envio padrão do formulário
    $.ajax({
        url: '/editar_legenda',
        method: 'POST',
        data: $(this).serialize(),
        success: function (response) {
            if (response.success) {
                alert(response.message);
                // Fechar o modal e atualizar a página ou tabela
                $('#editLegendModal').modal('hide');
                location.reload(); // Recarrega a página para ver as alterações
            } else {
                alert(response.message);
            }
        },
        error: function () {
            alert('Erro ao atualizar a legenda.');
        }
    });
});

/********************************************Fim Legendas************************************** */


/*******************************************Inicio dashboard ************************************/
/*let editandoDashboard = false;
let editandoLegenda = false;
let editandoRegra = false;*/
document.getElementById("editDashboardForm").addEventListener("submit", function (event) {
    event.preventDefault();
    // Criação de um objeto para os dados do formulário
    const formData = new FormData(this);
    const formObject = {};
    formData.forEach((value, key) => {
        formObject[key] = value;
    });

    // Envio dos dados como JSON
    fetch(this.action, {
        method: "POST",
        headers: {
            "Content-Type": "application/json" // Indica que estamos enviando JSON
        },
        body: JSON.stringify(formObject) // Converte os dados para JSON
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Fecha o modal
                $('#editDashboardModal').modal('hide');

                // Recarrega a página de edição
                location.reload();
            } else {
                alert("Erro ao editar a dashboard.");
            }
        })
        .catch(error => console.error("Erro:", error));
});

function duplicarDashboard(dashboard_id) {
    if (confirm('Tem certeza de que deseja duplicar este dashboard?')) {
        // Realiza a requisição POST para duplicar o dashboard
        $.post('/duplicar_dashboard', { nr_sequencia: dashboard_id })
            .done(function (response) {
                if (response.success) {
                    alert('Dashboard duplicado com sucesso!'); // Mensagem de sucesso
                    location.reload(); // Recarrega a página para mostrar o dashboard duplicado
                } else {
                    alert('Erro ao duplicar o dashboard: ' + response.message);
                }
            })
            .fail(function () {
                alert('Erro ao fazer a requisição. Por favor, tente novamente.');
            });
    }
}


/*****************************************Fim Dashboard ******************************************/

/*****************************************Inicio Regra ******************************************/


//cadastrar regra
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
    if (data.success) {
           // Fecha o modal
        $('#modalCadastrarRegra').modal('hide');

           // Atualiza a lista de regras
        atualizarListaRegras();

           // Exibe uma mensagem de sucesso, se necessário
        console.log(data.message);
        
    } else {
           alert(data.message); // Mostra a mensagem de erro
    }
})
.catch(error => {
    console.error('There was a problem with the fetch operation:', error);
});
});


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
