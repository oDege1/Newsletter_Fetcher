#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newsletter Fetcher - Busca newsletters do Gmail e salva como TXT/PDF.

Uso:
    python newsletter_fetcher.py

Requisitos:
    1. Coloque o arquivo 'credentials.json' (OAuth do Google Cloud Console)
       na mesma pasta deste script.
    2. Instale as dependências: pip install -r requirements.txt
    3. Execute o script. Na primeira vez, ele abrirá o navegador para
       autorizar o acesso ao Gmail.
"""

import os
import sys
import re
import shutil
import base64
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

from config import (
    CREDENTIALS_FILE,
    TOKEN_FILE,
    OUTPUT_DIR,
    OUTPUT_FORMAT,
    NEWSLETTER_SENDERS,
    NEWSLETTER_KEYWORDS,
    FETCH_ALL_TODAY,
    MAX_RESULTS,
)

# Permissão de leitura do Gmail
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


# ============================================================
# Autenticação OAuth2
# ============================================================

def authenticate_gmail():
    """Autentica no Gmail via OAuth2 e retorna o serviço da API."""
    creds = None

    # Verifica se já existe um token salvo
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Se não há credenciais válidas, faz login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token de acesso...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("❌ Erro: Arquivo 'credentials.json' não encontrado!")
                print("   Coloque o arquivo na pasta:", os.path.dirname(CREDENTIALS_FILE))
                sys.exit(1)

            print("🌐 Abrindo navegador para autorização...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva o token para uso futuro
        with open(TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())
        print("✅ Token salvo com sucesso!")

    service = build("gmail", "v1", credentials=creds)
    return service


# ============================================================
# Busca de Emails
# ============================================================

def build_search_query():
    """Constrói a query de busca para o Gmail baseada nas configurações."""
    today = datetime.now().strftime("%Y/%m/%d")
    
    # Base: emails de hoje
    query_parts = [f"after:{today}"]

    if FETCH_ALL_TODAY:
        return " ".join(query_parts)

    # Filtro por remetentes específicos
    sender_filters = []
    if NEWSLETTER_SENDERS:
        sender_filters = [f"from:{sender}" for sender in NEWSLETTER_SENDERS]

    # Filtro por palavras-chave no assunto
    keyword_filters = []
    if NEWSLETTER_KEYWORDS:
        keywords_query = " OR ".join(NEWSLETTER_KEYWORDS)
        keyword_filters = [f"subject:({keywords_query})"]

    # Combina filtros: remetentes OU palavras-chave
    if sender_filters and keyword_filters:
        combined = " OR ".join(sender_filters) + " OR " + " OR ".join(keyword_filters)
        query_parts.append(f"({combined})")
    elif sender_filters:
        combined = " OR ".join(sender_filters)
        query_parts.append(f"({combined})")
    elif keyword_filters:
        query_parts.append(f"({keyword_filters[0]})")
    else:
        # Sem filtros definidos, busca tudo de hoje
        pass

    return " ".join(query_parts)


def fetch_emails(service):
    """Busca emails do Gmail com base nos filtros configurados."""
    query = build_search_query()
    print(f"🔍 Buscando com query: {query}")

    results = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=MAX_RESULTS,
    ).execute()

    messages = results.get("messages", [])

    if not messages:
        print("📭 Nenhuma newsletter encontrada para hoje.")
        return []

    print(f"📬 Encontrados {len(messages)} email(s)!")

    emails = []
    for i, msg_ref in enumerate(messages, 1):
        msg = service.users().messages().get(
            userId="me",
            id=msg_ref["id"],
            format="full",
        ).execute()

        email_data = parse_email(msg)
        if email_data:
            emails.append(email_data)
            print(f"   [{i}/{len(messages)}] ✉️  {email_data['subject']}")

    return emails


# ============================================================
# Parsing de Email
# ============================================================

def parse_email(msg):
    """Extrai informações relevantes de um email."""
    headers = msg.get("payload", {}).get("headers", [])

    # Extrai headers
    subject = ""
    sender = ""
    date_str = ""

    for header in headers:
        name = header["name"].lower()
        if name == "subject":
            subject = header["value"]
        elif name == "from":
            sender = header["value"]
        elif name == "date":
            date_str = header["value"]

    # Extrai o corpo do email
    body_html = ""
    body_text = ""
    payload = msg.get("payload", {})

    body_html, body_text = extract_body(payload)

    # Converte HTML para texto limpo se necessário
    if body_html and not body_text:
        body_text = html_to_text(body_html)
    elif not body_text:
        body_text = "(Sem conteúdo de texto)"

    return {
        "id": msg["id"],
        "subject": subject or "(Sem assunto)",
        "sender": sender,
        "date": date_str,
        "body_text": body_text,
        "body_html": body_html,
    }


def extract_body(payload):
    """Extrai o corpo HTML e texto de um payload de email (recursivo)."""
    body_html = ""
    body_text = ""

    mime_type = payload.get("mimeType", "")

    # Corpo direto
    if "body" in payload and payload["body"].get("data"):
        data = payload["body"]["data"]
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        if "html" in mime_type:
            body_html = decoded
        else:
            body_text = decoded

    # Partes multipart
    if "parts" in payload:
        for part in payload["parts"]:
            part_mime = part.get("mimeType", "")

            if part_mime == "text/html":
                if "body" in part and part["body"].get("data"):
                    data = part["body"]["data"]
                    body_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif part_mime == "text/plain":
                if "body" in part and part["body"].get("data"):
                    data = part["body"]["data"]
                    body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif "multipart" in part_mime:
                # Recursão para multipart aninhado
                sub_html, sub_text = extract_body(part)
                if sub_html:
                    body_html = sub_html
                if sub_text:
                    body_text = sub_text

    return body_html, body_text


def html_to_text(html_content):
    """Converte HTML para texto limpo e legível."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove scripts e styles
    for tag in soup(["script", "style", "head", "meta", "link"]):
        tag.decompose()

    # Adiciona quebras de linha para elementos de bloco
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all(["p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"]):
        p.insert_before("\n")
        p.insert_after("\n")

    # Extrai links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if text and href and not href.startswith("#"):
            a.replace_with(f"{text} [{href}]")

    text = soup.get_text()

    # Limpa espaços excessivos
    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        lines.append(cleaned)

    # Remove linhas vazias consecutivas (max 2)
    result = []
    empty_count = 0
    for line in lines:
        if line == "":
            empty_count += 1
            if empty_count <= 2:
                result.append(line)
        else:
            empty_count = 0
            result.append(line)

    return "\n".join(result).strip()


# ============================================================
# Salvar Newsletters
# ============================================================

def sanitize_filename(name):
    """Limpa um nome para uso como nome de arquivo."""
    # Remove caracteres inválidos para nomes de arquivo
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Limita o tamanho
    name = name[:80].strip()
    return name or "sem_titulo"


def clear_output_folder():
    """Apaga o conteúdo anterior da pasta de saída."""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
        print(f"🗑️  Pasta anterior limpa: {OUTPUT_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"📁 Pasta de saída criada: {OUTPUT_DIR}")


def save_as_txt(email_data, index):
    """Salva o email como arquivo TXT."""
    filename = f"{index:02d}_{sanitize_filename(email_data['subject'])}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    content = []
    content.append("=" * 70)
    content.append(f"NEWSLETTER: {email_data['subject']}")
    content.append("=" * 70)
    content.append(f"De: {email_data['sender']}")
    content.append(f"Data: {email_data['date']}")
    content.append("-" * 70)
    content.append("")
    content.append(email_data["body_text"])
    content.append("")
    content.append("=" * 70)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    return filepath


def save_as_pdf(email_data, index):
    """Salva o email como arquivo PDF."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("⚠️  fpdf2 não instalado. Pulando geração de PDF.")
        return None

    filename = f"{index:02d}_{sanitize_filename(email_data['subject'])}.pdf"
    filepath = os.path.join(OUTPUT_DIR, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Tenta usar uma fonte com suporte a Unicode
    try:
        # Tenta carregar fonte com suporte a caracteres especiais
        pdf.add_font("DejaVu", "", os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf"), uni=True)
        pdf.set_font("DejaVu", size=10)
        has_unicode_font = True
    except Exception:
        # Fallback para Helvetica (sem suporte completo a Unicode)
        pdf.set_font("Helvetica", size=10)
        has_unicode_font = False

    # Título
    pdf.set_font_size(16)
    title = email_data["subject"]
    if not has_unicode_font:
        title = title.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 10, title)
    pdf.ln(5)

    # Metadados
    pdf.set_font_size(9)
    sender = f"De: {email_data['sender']}"
    date = f"Data: {email_data['date']}"
    if not has_unicode_font:
        sender = sender.encode("latin-1", errors="replace").decode("latin-1")
        date = date.encode("latin-1", errors="replace").decode("latin-1")
    pdf.cell(0, 6, sender, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, date, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Linha separadora
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    # Corpo
    pdf.set_font_size(10)
    body = email_data["body_text"]
    if not has_unicode_font:
        body = body.encode("latin-1", errors="replace").decode("latin-1")
    pdf.multi_cell(0, 5, body)

    pdf.output(filepath)
    return filepath


def save_newsletters(emails):
    """Salva todas as newsletters nos formatos configurados."""
    if not emails:
        return

    saved_files = []

    for i, email_data in enumerate(emails, 1):
        if OUTPUT_FORMAT in ("txt", "ambos"):
            path = save_as_txt(email_data, i)
            if path:
                saved_files.append(path)

        if OUTPUT_FORMAT in ("pdf", "ambos"):
            path = save_as_pdf(email_data, i)
            if path:
                saved_files.append(path)

    return saved_files


# ============================================================
# Relatório Final
# ============================================================

def print_summary(emails, saved_files):
    """Imprime um relatório final."""
    print("\n" + "=" * 70)
    print("📊 RELATÓRIO - Newsletter Fetcher")
    print("=" * 70)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📬 Newsletters encontradas: {len(emails)}")
    print(f"💾 Arquivos salvos: {len(saved_files or [])}")
    print(f"📁 Pasta de saída: {OUTPUT_DIR}")

    if emails:
        print("\n📋 Newsletters processadas:")
        for i, email in enumerate(emails, 1):
            print(f"   {i}. {email['subject']}")
            print(f"      De: {email['sender']}")

    print("=" * 70)


# ============================================================
# Execução Principal
# ============================================================

def main():
    print("=" * 70)
    print("📰 Newsletter Fetcher - Buscando newsletters de hoje...")
    print("=" * 70)
    print()

    # 1. Autenticar
    print("🔐 Autenticando no Gmail...")
    service = authenticate_gmail()
    print("✅ Autenticado com sucesso!\n")

    # 2. Limpar pasta de saída
    clear_output_folder()
    print()

    # 3. Buscar emails
    emails = fetch_emails(service)
    print()

    # 4. Salvar newsletters
    saved_files = []
    if emails:
        print("💾 Salvando newsletters...")
        saved_files = save_newsletters(emails)
        print(f"✅ {len(saved_files)} arquivo(s) salvo(s)!\n")

    # 5. Relatório
    print_summary(emails, saved_files)


if __name__ == "__main__":
    main()
