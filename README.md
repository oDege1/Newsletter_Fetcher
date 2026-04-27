📰 Newsletter Fetcher
O Newsletter Fetcher é um script em Python desenvolvido para acessar sua conta do Gmail, buscar os emails (newsletters) recebidos no dia atual e salvá-los localmente em formatos fáceis de ler (TXT e PDF).

✨ Funcionalidades
Busca Inteligente: Filtra emails por remetentes específicos ou palavras-chave no assunto (ex: "newsletter", "digest", "briefing").

Limpeza de HTML: Converte o corpo do email em texto limpo e legível, removendo scripts e estilos extras usando a biblioteca BeautifulSoup.

Múltiplos Formatos: Salva os arquivos extraídos na pasta de saída em .txt, .pdf, ou ambos.

Autenticação Segura: Utiliza o padrão OAuth2 do Google para acessar o Gmail de forma segura e com permissão apenas de leitura (https://www.googleapis.com/auth/gmail.readonly).

🛠️ Pré-requisitos
Para rodar este projeto, você precisará de:

Python 3 instalado em sua máquina.

Uma conta no Google Cloud Console para gerar as credenciais da API do Gmail.

Um arquivo credentials.json válido salvo na raiz do projeto.

🚀 Instalação
Clone ou faça o download deste repositório.

Instale as dependências necessárias através do arquivo requirements.txt. No terminal, execute:

Bash
pip install -r requirements.txt
(Isso instalará as bibliotecas necessárias, incluindo google-api-python-client, beautifulsoup4 e fpdf2)

Baixe uma fonte com suporte a Unicode (como a DejaVuSans.ttf) e coloque na raiz do projeto para garantir a geração correta de PDFs com caracteres especiais (o sistema fará um fallback para a fonte Helvetica caso a fonte não seja encontrada, o que pode causar perda de formatação em caracteres acentuados).

⚙️ Configuração (config.py)
Antes de executar, você pode personalizar o comportamento do script editando as variáveis no arquivo config.py:

OUTPUT_FORMAT: Escolha o formato de saída dos arquivos. As opções são "txt", "pdf" ou "ambos".

OUTPUT_DIR: Define o nome da pasta de saída onde os arquivos serão salvos (o padrão é "newsletters_hoje").

NEWSLETTER_SENDERS: Lista onde você pode adicionar os endereços de email específicos de onde você recebe suas newsletters.

NEWSLETTER_KEYWORDS: Palavras-chave para buscar no assunto do email. O padrão já inclui termos comuns em português e inglês.

FETCH_ALL_TODAY: Mude para True caso queira ignorar os filtros acima e baixar absolutamente todos os emails recebidos no dia atual.

MAX_RESULTS: Define o limite máximo de emails a serem processados por vez (o padrão é 50).

🏃‍♂️ Como Usar
Com as dependências instaladas e o credentials.json na pasta correta, execute o script principal pelo terminal:

Bash
python newsletter_fetcher.py
No primeiro acesso:

O script abrirá o seu navegador padrão pedindo autorização para acessar sua conta do Gmail de forma segura.

Após conceder o acesso, um arquivo token.json será gerado automaticamente. Assim, você não precisará fazer login manualmente nas próximas vezes.

O script apagará qualquer conteúdo anterior da sua pasta de saída para mantê-la limpa, buscará as edições do dia e gerará um relatório final no terminal.

📝 Notas e Resolução de Problemas
Erro "Arquivo credentials.json não encontrado": Certifique-se de que o arquivo baixado do Google Cloud Console possui exatamente este nome e está localizado na mesma pasta do script newsletter_fetcher.py.

Renovação de Token: Se o seu token de acesso expirar, o script tentará renová-lo automaticamente nos bastidores. Caso isso falhe por algum motivo, basta deletar o arquivo token.json da sua pasta e rodar o script novamente para forçar uma nova janela de login.
