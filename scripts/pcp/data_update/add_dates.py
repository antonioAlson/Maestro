import sys
import io

# Configurar saída UTF-8 para Windows (apenas se ainda não foi configurado)
if sys.platform == 'win32':
    try:
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not isinstance(sys.stderr, io.TextIOWrapper) or sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Já configurado ou não é necessário

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from dotenv import load_dotenv
import os
import customtkinter as ctk

load_dotenv()

# CONFIGURAÇÕES
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("API_TOKEN")

# FILTRO JQL - buscar apenas cartões SEM data de previsão de entrega
jql = '((project = MANTA AND status IN ("A Produzir", "Liberado Engenharia")) OR (project = TENSYLON AND status IN ("A Produzir", "Liberado Engenharia", "Aguardando Acabamento", "Aguardando Autoclave", "Aguardando Corte", "Aguardando montagem"))) AND customfield_10245 is EMPTY'

url = f"{JIRA_URL}/rest/api/3/search/jql"

headers = {
    "Accept": "application/json"
}

auth = HTTPBasicAuth(EMAIL, API_TOKEN)

# ============================================================================
# FUNCAO PARA GERAR DADOS DE UPDATE
# ============================================================================

def gerar_update_cards():
    """Gera DataFrame com cartoes sem previsao de entrega"""
    print("Buscando dados do Jira...")

    next_page = None
    all_rows = []

    while True:
        params = {
            "jql": jql,
            "maxResults": 100,
            "fields": [
                "issuetype",
                "summary",
                "status",
                "customfield_10039",   # SITUAÇÃO
                "customfield_11298",   # VEÍCULO
                "customfield_10245"    # DT PREVISÃO ENTREGA
            ]
        }

        if next_page:
            params["nextPageToken"] = next_page

        response = requests.get(
            url,
            headers=headers,
            params=params,
            auth=auth
        )

        if response.status_code != 200:
            print(f"Erro na requisição: {response.status_code}")
            print(response.text)
            break

        data = response.json()
        issues = data.get("issues", [])

        if not issues:
            break

        for issue in issues:
            fields = issue.get("fields", {})

            # Tipo
            tipo = fields.get("issuetype", {}).get("name", "")

            # Chave e link
            key = issue.get("key", "")
            link = f"{JIRA_URL}/browse/{key}"

            # Campos padrão
            resumo = fields.get("summary", "")
            status = fields.get("status", {}).get("name", "")

            # SITUAÇÃO (dropdown Jira)
            situacao_raw = fields.get("customfield_10039")
            if isinstance(situacao_raw, dict):
                situacao = situacao_raw.get("value", "")
            else:
                situacao = situacao_raw or ""
            
            # Filtrar apenas situações desejadas
            situacoes_validas = [
                "⚪️RECEBIDO ENCAMINHADO",
                "🟢RECEBIDO LIBERADO",
                "⚫Aguardando entrada",
            ]
            if situacao not in situacoes_validas:
                continue

            # Abreviar situação
            if situacao == "⚪️RECEBIDO ENCAMINHADO":
                situacao = "⚪️REC. Encaminhado"
            elif situacao == "🟢RECEBIDO LIBERADO":
                situacao = "🟢REC. Liberado"

            # VEÍCULO
            veiculo_raw = fields.get("customfield_11298")
            if isinstance(veiculo_raw, dict):
                veiculo = veiculo_raw.get("value", "")
            else:
                veiculo = veiculo_raw or ""

            # DT PREVISÃO ENTREGA
            dt_previsao_raw = fields.get("customfield_10245", "")
            if dt_previsao_raw:
                try:
                    dt_previsao = datetime.strptime(dt_previsao_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
                except:
                    dt_previsao = dt_previsao_raw
            else:
                dt_previsao = ""

            all_rows.append({
                "ID": key,
                "Tipo de issue": tipo,
                "Chave": link,
                "Resumo": resumo,
                "Status": status,
                "SITUAÇÃO": situacao,
                "Veículo": veiculo,
                "Prev. de Entrega": dt_previsao
            })

        print("Cartões coletados:", len(all_rows))

        if data.get("isLast"):
            break

        next_page = data.get("nextPageToken")

    print(f"Total de cartões sem previsão de entrega: {len(all_rows)}")

    # Criar DataFrame
    if len(all_rows) == 0:
        # Se não há dados, criar DataFrame vazio com as colunas corretas
        cards_update = pd.DataFrame(columns=[
            "ID",
            "Tipo de issue",
            "Chave",
            "Resumo",
            "Status",
            "SITUAÇÃO",
            "Veículo",
            "Prev. de Entrega"
        ])
    else:
        df = pd.DataFrame(all_rows)
        # Selecionar apenas as colunas desejadas
        cards_update = df[[
            "ID",
            "Tipo de issue",
            "Chave",
            "Resumo",
            "Status",
            "SITUAÇÃO",
            "Veículo",
            "Prev. de Entrega"
        ]]

    print("Dados carregados em memoria com sucesso!")
    return cards_update

# ============================================================================
# FUNÇÃO PARA MÁSCARA DE DATA
# ============================================================================

def aplicar_mascara_data(entry_widget):
    """Aplica máscara DD/MM/YYYY no campo de entrada de data com visualização constante"""
    
    # Configurar valor inicial
    valor_inicial = entry_widget.get()
    if valor_inicial and valor_inicial.strip():
        # Se já tem valor, extrair apenas números e reformatar
        apenas_numeros = ''.join(filter(str.isdigit, valor_inicial))
        if apenas_numeros:
            mascara = list("__/__/____")
            posicoes = [0, 1, 3, 4, 6, 7, 8, 9]
            for i, num in enumerate(apenas_numeros[:8]):
                mascara[posicoes[i]] = num
            entry_widget.delete(0, "end")
            entry_widget.insert(0, ''.join(mascara))
        else:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, "__/__/____")
    else:
        # Campo vazio, mostrar máscara
        entry_widget.delete(0, "end")
        entry_widget.insert(0, "__/__/____")
        entry_widget.icursor(0)
    
    def formatar_mascara(texto):
        """Formata o texto aplicando a máscara DD/MM/YYYY"""
        apenas_numeros = ''.join(filter(str.isdigit, texto))[:8]
        mascara = list("__/__/____")
        posicoes = [0, 1, 3, 4, 6, 7, 8, 9]
        for i, num in enumerate(apenas_numeros):
            mascara[posicoes[i]] = num
        return ''.join(mascara), apenas_numeros
    
    def on_key_release(event):
        """Atualiza a máscara após cada tecla (exceto comandos Ctrl)"""
        # Ignorar se está usando Ctrl (para permitir Ctrl+C, Ctrl+V, etc.)
        if event.state & 0x4 or event.state & 0x40004:  # Control ou Control+Shift
            return
        
        # Ignorar teclas de navegação
        if event.keysym in ['Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Tab', 
                            'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
            return
        
        # Aplicar formatação
        current_text = entry_widget.get()
        texto_formatado, apenas_numeros = formatar_mascara(current_text)
        
        if texto_formatado != current_text:
            # Atualizar o texto
            entry_widget.delete(0, "end")
            entry_widget.insert(0, texto_formatado)
            
            # Reposicionar cursor de forma inteligente
            posicoes = [0, 1, 3, 4, 6, 7, 8, 9]
            if len(apenas_numeros) < 8:
                entry_widget.icursor(posicoes[len(apenas_numeros)])
            else:
                entry_widget.icursor(10)
    
    # Handler para Ctrl+V (colar)
    def on_paste(event):
        try:
            # Pegar texto da área de transferência
            clipboard_text = entry_widget.clipboard_get()
            texto_formatado, apenas_numeros = formatar_mascara(clipboard_text)
            
            # Atualizar o campo
            entry_widget.delete(0, "end")
            entry_widget.insert(0, texto_formatado)
            
            # Posicionar cursor
            posicoes = [0, 1, 3, 4, 6, 7, 8, 9]
            if len(apenas_numeros) < 8:
                entry_widget.icursor(posicoes[len(apenas_numeros)])
            else:
                entry_widget.icursor(10)
            
            return "break"
        except:
            return "break"
    
    # Ao clicar no campo, posicionar no primeiro underscore disponível
    def on_focus(event):
        current = entry_widget.get()
        apenas_numeros = ''.join(filter(str.isdigit, current))
        if len(apenas_numeros) < 8:
            posicoes = [0, 1, 3, 4, 6, 7, 8, 9]
            if apenas_numeros:
                entry_widget.icursor(posicoes[len(apenas_numeros)])
            else:
                entry_widget.icursor(0)
    
    # Bindings
    entry_widget.bind('<KeyRelease>', on_key_release)
    entry_widget.bind('<<Paste>>', on_paste)
    entry_widget.bind('<Control-v>', on_paste)
    entry_widget.bind('<FocusIn>', on_focus)

# ============================================================================
# FUNÇÕES PARA SALVAR E ATUALIZAR JIRA
# ============================================================================

def mostrar_popup_carregamento_jira(excel_window):
    """Mostra popup de carregamento durante a atualização no Jira."""
    popup = ctk.CTkToplevel(excel_window)
    popup.title("Aguarde")
    popup.geometry("360x160")
    popup.resizable(False, False)

    popup.update_idletasks()
    excel_window.update_idletasks()

    width = 360
    height = 160
    x = excel_window.winfo_x() + (excel_window.winfo_width() - width) // 2
    y = excel_window.winfo_y() + (excel_window.winfo_height() - height) // 2
    popup.geometry(f"{width}x{height}+{x}+{y}")

    popup.transient(excel_window)
    popup.lift()
    popup.focus_force()
    popup.attributes('-topmost', True)
    popup.after(100, lambda: popup.attributes('-topmost', False))

    ctk.CTkLabel(
        popup,
        text="Salvando alterações e atualizando Jira...",
        font=ctk.CTkFont(size=14, weight="bold")
    ).pack(pady=(24, 12))

    progress = ctk.CTkProgressBar(popup, mode="indeterminate", width=280)
    progress.pack(pady=(0, 12))
    progress.start()

    ctk.CTkLabel(
        popup,
        text="Isso pode levar alguns segundos.",
        font=ctk.CTkFont(size=11),
        text_color="gray70"
    ).pack()

    return popup


def fechar_popup_carregamento_jira(popup):
    """Fecha popup de carregamento de forma segura."""
    try:
        if popup is not None and popup.winfo_exists():
            popup.destroy()
    except Exception:
        pass

def salvar_e_atualizar_jira(df_source, entries_data, card, excel_window):
    """Aplica alteracoes no DataFrame em memoria e atualiza no Jira"""
    loading_popup = mostrar_popup_carregamento_jira(excel_window)

    def executar_fluxo_salvar_atualizar():
        try:
            from datetime import datetime
            
            # Trabalhar com copia para nao alterar referencia original inesperadamente
            df = df_source.copy()
            
            # Converter a coluna de data para datetime se necessário
            if "Prev. de Entrega" in df.columns:
                df["Prev. de Entrega"] = pd.to_datetime(df["Prev. de Entrega"], errors='coerce')
            
            # Atualizar todos os valores
            for row_idx, column, entry in entries_data:
                new_value = entry.get().strip()
                if column == "Prev. de Entrega" and ("_" in new_value or new_value == "__/__/____"):
                    new_value = ""
                
                if column == "Prev. de Entrega":
                    if new_value:
                        try:
                            if "/" in new_value:
                                date_obj = datetime.strptime(new_value, "%d/%m/%Y")
                            elif "-" in new_value and len(new_value) == 10:
                                try:
                                    date_obj = datetime.strptime(new_value, "%Y-%m-%d")
                                except:
                                    date_obj = datetime.strptime(new_value, "%d-%m-%Y")
                            else:
                                date_obj = pd.to_datetime(new_value)
                            
                            df.at[row_idx, column] = pd.Timestamp(date_obj)
                        except (ValueError, Exception):
                            print(f"Aviso: Formato de data inválido '{new_value}' na linha {row_idx}")
                            df.at[row_idx, column] = pd.NaT
                    else:
                        df.at[row_idx, column] = pd.NaT
                else:
                    df.at[row_idx, column] = new_value if new_value else ""

            print("✓ Dados atualizados em memoria!")
            
            # Atualizar Jira
            atualizar_jira_dates(df, card, excel_window, loading_popup)
            
        except Exception as e:
            fechar_popup_carregamento_jira(loading_popup)
            print(f"Erro ao salvar alterações: {e}")
            import traceback
            traceback.print_exc()

    # Aguarda um ciclo de UI para garantir que o popup apareça antes do processamento.
    excel_window.after(50, executar_fluxo_salvar_atualizar)


def atualizar_jira_dates(df, card, excel_window, loading_popup=None):
    """Atualiza as datas no Jira baseado no DataFrame em memoria"""
    try:
        from datetime import datetime
        
        CAMPO_PREVISAO = "customfield_10245"
        
        # Filtrar apenas linhas com ID e data preenchidos
        df_update = df[df["ID"].notna() & df["Prev. de Entrega"].notna()].copy()
        
        if len(df_update) == 0:
            print("Nenhuma data para atualizar no Jira")
            fechar_popup_carregamento_jira(loading_popup)
            mostrar_resultado_jira(0, 0, card, excel_window)
            return
        
        print(f"Atualizando {len(df_update)} issues no Jira...")
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        auth = HTTPBasicAuth(EMAIL, API_TOKEN)
        
        success_count = 0
        error_count = 0
        
        for index, row in df_update.iterrows():
            issue_id = row["ID"]
            data_entrega = row["Prev. de Entrega"]
            
            # Converter para formato YYYY-MM-DD
            try:
                if isinstance(data_entrega, pd.Timestamp):
                    data_formatada = data_entrega.strftime("%Y-%m-%d")
                elif isinstance(data_entrega, str):
                    if "/" in data_entrega:
                        date_obj = datetime.strptime(data_entrega, "%d/%m/%Y")
                    else:
                        date_obj = datetime.strptime(data_entrega, "%Y-%m-%d")
                    data_formatada = date_obj.strftime("%Y-%m-%d")
                else:
                    print(f"Formato não reconhecido para {issue_id}: {data_entrega}")
                    error_count += 1
                    continue
                
                # Fazer requisição ao Jira
                url = f"{JIRA_URL}/rest/api/3/issue/{issue_id}"
                payload = {
                    "fields": {
                        CAMPO_PREVISAO: data_formatada
                    }
                }
                
                response = requests.put(url, headers=headers, auth=auth, json=payload)
                
                if response.status_code == 204:
                    print(f"✓ {issue_id} atualizado para {data_formatada}")
                    success_count += 1
                else:
                    print(f"✗ Erro ao atualizar {issue_id}: {response.status_code} - {response.text}")
                    error_count += 1
                    
            except Exception as e:
                print(f"✗ Erro ao processar {issue_id}: {e}")
                error_count += 1
        
        # Mostrar resultado
        print(f"\nAtualização concluída: {success_count} sucesso, {error_count} erros")
        fechar_popup_carregamento_jira(loading_popup)
        mostrar_resultado_jira(success_count, error_count, card, excel_window)
        
    except Exception as e:
        fechar_popup_carregamento_jira(loading_popup)
        print(f"Erro ao atualizar Jira: {e}")
        import traceback
        traceback.print_exc()


def mostrar_resultado_jira(success_count, error_count, card, excel_window):
    """Mostra resultado da atualização do Jira em um popup"""
    # Criar popup de resultado
    result_popup = ctk.CTkToplevel(excel_window)
    result_popup.title("Resultado da Atualização")
    result_popup.geometry("420x240")
    result_popup.resizable(False, False)
    
    # Centralizar popup em relação à janela de visualização
    result_popup.update_idletasks()
    excel_window.update_idletasks()
    
    width = 420
    height = 240
    
    # Obter posição e tamanho da janela de visualização
    window_x = excel_window.winfo_x()
    window_y = excel_window.winfo_y()
    window_width = excel_window.winfo_width()
    window_height = excel_window.winfo_height()
    
    # Calcular posição centralizada em relação à janela de visualização
    x = window_x + (window_width - width) // 2
    y = window_y + (window_height - height) // 2
    
    result_popup.geometry(f"{width}x{height}+{x}+{y}")
    
    # Trazer para frente
    result_popup.transient(excel_window)
    result_popup.lift()
    result_popup.focus_force()
    result_popup.attributes('-topmost', True)
    result_popup.after(100, lambda: result_popup.attributes('-topmost', False))
    result_popup.grab_set()
    
    # Título
    title = "✓ Atualização Concluída!" if error_count == 0 else "⚠️ Atualização Parcial"
    color = "#90EE90" if error_count == 0 else "orange"
    
    title_label = ctk.CTkLabel(
        result_popup,
        text=title,
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=color
    )
    title_label.pack(pady=(24, 16))
    
    # Detalhes
    detail_text = f"✓ Sucesso: {success_count}\n✗ Erros: {error_count}"
    detail_label = ctk.CTkLabel(
        result_popup,
        text=detail_text,
        font=ctk.CTkFont(size=16)
    )
    detail_label.pack(pady=(0, 12))
    
    # Mensagem adicional
    if error_count == 0:
        msg = "Todas as datas foram atualizadas com sucesso no Jira!"
    else:
        msg = "Algumas datas apresentaram erro. Verifique o console."
    
    msg_label = ctk.CTkLabel(
        result_popup,
        text=msg,
        font=ctk.CTkFont(size=11),
        text_color="gray70",
        wraplength=350
    )
    msg_label.pack(pady=(0, 18))
    
    # Função para fechar popup e depois a janela
    def fechar_tudo():
        try:
            result_popup.grab_release()
        except Exception:
            pass
        if result_popup.winfo_exists():
            result_popup.destroy()
        if excel_window.winfo_exists():
            excel_window.after(100, excel_window.destroy)

    # Fechar pelo X da janela segue a mesma regra do botão OK
    result_popup.protocol("WM_DELETE_WINDOW", fechar_tudo)
    
    # Botão fechar (fecha popup e janela de visualização)
    close_btn = ctk.CTkButton(
        result_popup,
        text="OK",
        command=fechar_tudo,
        width=180,
        height=50,
        corner_radius=10,
        font=ctk.CTkFont(size=16, weight="bold"),
        fg_color="#2a9d2a" if error_count == 0 else "gray40",
        hover_color="#238a23" if error_count == 0 else "gray50"
    )
    close_btn.pack(pady=(0, 16), padx=20)


# ============================================================================
# FUNÇÃO PARA ABRIR JANELA DE VISUALIZAÇÃO
# ============================================================================

def abrir_janela_visualizacao(main_app, df=None):
    """Abre janela de visualizacao dos dados em memoria
    Args:
        main_app: Instância do app principal
        df: DataFrame com os dados para exibicao
    """
    try:
        print(f"Iniciando visualização de dados...")

        if df is None:
            print("Nenhum DataFrame fornecido para visualizacao")
            return

        print(f"Usando DataFrame fornecido")
            
        print(f"{len(df)} linhas encontradas")
        
        # Verificar se há dados
        if len(df) == 0:
            print("Nenhum item encontrado")
            # Criar janela com mensagem de aviso
            excel_window = ctk.CTkToplevel(main_app.root)
            excel_window.title("Visualização de Dados")
            excel_window.geometry("900x500")
            
            # Centralizar a janela
            excel_window.update_idletasks()
            width = 900
            height = 500
            screen_width = excel_window.winfo_screenwidth()
            screen_height = excel_window.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            excel_window.geometry(f"{width}x{height}+{x}+{y}")
            
            # Trazer janela para frente
            excel_window.lift()
            excel_window.focus_force()
            excel_window.attributes('-topmost', True)
            excel_window.after(100, lambda: excel_window.attributes('-topmost', False))
            
            # Card de conteúdo
            card = ctk.CTkFrame(excel_window, corner_radius=10)
            card.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Ícone de aviso
            warning_label = ctk.CTkLabel(
                card,
                text="⚠️",
                font=ctk.CTkFont(size=48)
            )
            warning_label.pack(pady=(30, 10))
            
            # Mensagem principal
            message_label = ctk.CTkLabel(
                card,
                text="Nenhum item encontrado",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color="orange"
            )
            message_label.pack(pady=10)
            
            # Descrição
            desc_label = ctk.CTkLabel(
                card,
                text="Nao ha registros para exibir.\nVerifique os filtros e tente novamente.",
                font=ctk.CTkFont(size=12),
                text_color="gray70",
                wraplength=400
            )
            desc_label.pack(pady=10)
            
            # Botão fechar
            close_btn = ctk.CTkButton(
                card,
                text="Fechar",
                command=excel_window.destroy,
                width=120,
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="gray40",
                hover_color="gray50"
            )
            close_btn.pack(pady=20)
            
            return
        
        # Criar cópia para visualização
        df_visual = df.copy()
        
        # Lista para armazenar referências aos campos editáveis
        entries_data = []
        
        # Variáveis para controle de ordenação e filtros
        current_sort_column = None
        current_sort_ascending = True
        column_filters = {}  # {coluna: [valores_selecionados]}
        filterable_columns = {"Tipo - OS", "Status"}
        
        # Combinar Tipo de issue e Resumo em uma única coluna
        if "Tipo de issue" in df_visual.columns and "Resumo" in df_visual.columns:
            df_visual["Tipo - OS"] = df_visual["Tipo de issue"].astype(str) + " - " + df_visual["Resumo"].astype(str)
            df_visual = df_visual.drop(columns=["Tipo de issue", "Resumo"])
        elif "Issue" in df_visual.columns and "Tipo - OS" not in df_visual.columns:
            df_visual = df_visual.rename(columns={"Issue": "Tipo - OS"})
        elif "OS" in df_visual.columns and "Tipo - OS" not in df_visual.columns:
            df_visual = df_visual.rename(columns={"OS": "Tipo - OS"})
        
        # Filtrar colunas (remover ID e Chave)
        columns_to_hide = ["ID", "Chave"]
        display_columns = [col for col in df_visual.columns if col not in columns_to_hide]
        
        # Reorganizar para colocar Tipo - OS em primeiro
        if "Tipo - OS" in display_columns:
            display_columns.remove("Tipo - OS")
            display_columns.insert(0, "Tipo - OS")
        
        print(f"Colunas a exibir: {display_columns}")
        print("Criando nova janela...")
        
        # Criar nova janela
        excel_window = ctk.CTkToplevel(main_app.root)
        excel_window.title("Visualização de Dados")
        excel_window.geometry("900x500")
        
        # Centralizar a nova janela
        excel_window.update_idletasks()
        width = 900
        height = 500
        screen_width = excel_window.winfo_screenwidth()
        screen_height = excel_window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        excel_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Trazer janela para frente
        excel_window.lift()
        excel_window.focus_force()
        excel_window.attributes('-topmost', True)
        excel_window.after(100, lambda: excel_window.attributes('-topmost', False))

        def build_visual_df(source_df):
            """Retorna DataFrame com transformações de visualização aplicadas."""
            result_df = source_df.copy()
            if "Tipo de issue" in result_df.columns and "Resumo" in result_df.columns:
                result_df["Tipo - OS"] = result_df["Tipo de issue"].astype(str) + " - " + result_df["Resumo"].astype(str)
                result_df = result_df.drop(columns=["Tipo de issue", "Resumo"])
            elif "Issue" in result_df.columns and "Tipo - OS" not in result_df.columns:
                result_df = result_df.rename(columns={"Issue": "Tipo - OS"})
            elif "OS" in result_df.columns and "Tipo - OS" not in result_df.columns:
                result_df = result_df.rename(columns={"OS": "Tipo - OS"})
            return result_df
        
        # Variáveis que serão modificadas pelas funções
        table_frame_ref = [None]  # Usar lista para permitir modificação em closures
        
        def aplicar_filtros_e_ordenacao():
            """Aplica filtros e ordenação ao DataFrame"""
            nonlocal df_visual
            try:
                df_filtrado = build_visual_df(df)
                
                # Aplicar filtros
                for coluna, valores in column_filters.items():
                    if valores and coluna in df_filtrado.columns:
                        if coluna == "Tipo - OS":
                            selected = {str(v).strip().lower() for v in valores}
                            mask = pd.Series(False, index=df_filtrado.index, dtype=bool)

                            # Texto base para detecção de projeto (chave + issue)
                            base_text = df_filtrado["Tipo - OS"].astype(str)
                            if "Chave" in df_filtrado.columns:
                                base_text = df_filtrado["Chave"].astype(str) + " " + base_text
                            base_text = base_text.str.lower()

                            if "manta" in selected:
                                mask = mask | base_text.str.contains("manta", na=False)

                            if "tensylon" in selected:
                                mask = mask | base_text.str.contains("tensylon", na=False)

                            df_filtrado = df_filtrado[mask]
                        else:
                            df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin(valores)]
                
                # Aplicar ordenação
                if current_sort_column and current_sort_column in df_filtrado.columns:
                    try:
                        if current_sort_column == "Prev. de Entrega":
                            # Ordenar datas de forma robusta mesmo com vazios/textos
                            ordem_data = pd.to_datetime(df_filtrado[current_sort_column], errors="coerce")
                            df_filtrado = df_filtrado.assign(_ordem_tmp=ordem_data).sort_values(
                                by="_ordem_tmp",
                                ascending=current_sort_ascending,
                                na_position="last",
                                kind="stable"
                            ).drop(columns=["_ordem_tmp"])
                        else:
                            # Ordenar texto de forma estável e case-insensitive para evitar erro de tipos mistos
                            df_filtrado = df_filtrado.sort_values(
                                by=current_sort_column,
                                ascending=current_sort_ascending,
                                na_position="last",
                                kind="stable",
                                key=lambda s: s.fillna("").astype(str).str.lower()
                            )
                    except Exception as sort_error:
                        print(f"Aviso: falha ao ordenar coluna '{current_sort_column}': {sort_error}")
                
                df_visual = df_filtrado
                return df_filtrado
            except Exception as e:
                print(f"Erro ao aplicar filtros/ordenação: {e}")
                return build_visual_df(df)

        def ordenar_por_clique(coluna):
            """Ordena imediatamente ao clicar no cabeçalho (estilo Excel)."""
            nonlocal current_sort_column, current_sort_ascending
            if current_sort_column == coluna:
                current_sort_ascending = not current_sort_ascending
            else:
                current_sort_column = coluna
                current_sort_ascending = True
            reconstruir_tabela()
        
        def reconstruir_tabela():
            """Reconstrói a tabela com dados filtrados/ordenados"""
            nonlocal entries_data
            try:
                # Aplicar filtros e ordenação
                df_atualizado = aplicar_filtros_e_ordenacao()

                # Limpar tabela existente por completo
                for widget in table_container.winfo_children():
                    widget.destroy()
                table_frame_ref[0] = None
                
                # Limpar lista de entries
                entries_data.clear()
                
                # Definir colunas válidas para renderização
                valid_columns = [column for column in display_columns if column in df_atualizado.columns]

                def largura_coluna(coluna):
                    if coluna == "Tipo - OS":
                        return 98
                    if coluna == "Status":
                        return 114
                    if coluna == "SITUAÇÃO":
                        return 120
                    if coluna == "Veículo":
                        return 240
                    if coluna == "Prev. de Entrega":
                        return 150
                    return 200

                header_col_widths = [largura_coluna(col) for col in valid_columns]
                body_col_widths = [320 if col == "Veículo" else header_col_widths[idx] for idx, col in enumerate(valid_columns)]
                
                # Criar frame fixo para o cabeçalho
                header_container = ctk.CTkFrame(table_container, fg_color="#2b2b2b")
                header_container.grid(row=0, column=0, sticky="nw", padx=(6, 0))
                
                for col_idx, col_width in enumerate(header_col_widths):
                    header_container.grid_columnconfigure(col_idx, weight=0, minsize=col_width)
                header_container.grid_rowconfigure(0, minsize=38)
                
                # Cabeçalho fixo
                for col_grid_idx, column in enumerate(valid_columns):
                    header_frame = ctk.CTkFrame(
                        header_container,
                        fg_color="gray25",
                        border_width=1,
                        border_color="gray40",
                        width=header_col_widths[col_grid_idx],
                        height=38
                    )
                    header_frame.grid(row=0, column=col_grid_idx, padx=1, pady=1, sticky="nsew")
                    header_frame.grid_propagate(False)
                    header_frame.pack_propagate(False)
                    
                    # Texto do cabeçalho com indicador de ordenação
                    header_text = str(column)
                    if current_sort_column == column:
                        header_text += " ▼" if not current_sort_ascending else " ▲"
                    if column in column_filters and column_filters[column]:
                        header_text += " *"
                    
                    header_btn = ctk.CTkButton(
                        header_frame,
                        text=header_text,
                        font=ctk.CTkFont(size=12, weight="bold"),
                        fg_color="gray25",
                        hover_color="gray35",
                        text_color="white",
                        anchor="w",
                        command=lambda col=column: mostrar_filtro(col) if col in filterable_columns else ordenar_por_clique(col)
                    )
                    header_btn.pack(padx=2, pady=2, fill="both", expand=True)
                
                # Criar frame scrollável para os dados
                table_frame = ctk.CTkScrollableFrame(table_container, fg_color="#2b2b2b")
                table_frame.grid(row=1, column=0, sticky="nsew")
                table_frame_ref[0] = table_frame
                
                # Configurar larguras das colunas do corpo
                for col_idx, body_width in enumerate(body_col_widths):
                    table_frame.grid_columnconfigure(col_idx, weight=0, minsize=body_width)
                
                # Preencher dados do corpo
                max_rows = min(len(df_atualizado), 100)
                
                if max_rows == 0:
                    ctk.CTkLabel(
                        table_frame,
                        text="Nenhum item encontrado para os filtros selecionados.",
                        text_color="#ffb347",
                        font=ctk.CTkFont(size=12, weight="bold")
                    ).grid(row=0, column=0, columnspan=max(1, len(valid_columns)), padx=10, pady=12, sticky="w")

                for row_idx in range(max_rows):
                    table_frame.grid_rowconfigure(row_idx, minsize=34)
                    original_index = df_atualizado.index[row_idx]
                    for col_idx, column in enumerate(valid_columns):
                        value = df_atualizado[column].iloc[row_idx]
                        cell_text = str(value) if pd.notna(value) else ""
                        if column == "Tipo - OS" and len(cell_text) > 20:
                            cell_text = cell_text[:17] + "..."
                        elif column == "Veículo" and len(cell_text) > 50:
                            cell_text = cell_text[:47] + "..."
                        elif len(cell_text) > 50 and column != "Prev. de Entrega":
                            cell_text = cell_text[:47] + "..."
                        
                        # Largura fixa de célula do corpo por coluna
                        cell_width = body_col_widths[col_idx]
                        
                        cell_frame = ctk.CTkFrame(
                            table_frame,
                            fg_color="gray20",
                            border_width=1,
                            border_color="gray30",
                            width=cell_width,
                            height=34
                        )
                        cell_frame.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky="nsew")
                        cell_frame.grid_propagate(False)
                        
                        if column == "Prev. de Entrega":
                            entry = ctk.CTkEntry(
                                cell_frame,
                                font=ctk.CTkFont(size=11),
                                height=28,
                                justify="center"
                            )
                            entry.insert(0, cell_text)
                            entry.pack(padx=4, pady=2, fill="both", expand=True)
                            aplicar_mascara_data(entry)
                            entries_data.append((original_index, column, entry))
                        else:
                            cell = ctk.CTkLabel(
                                cell_frame,
                                text=cell_text,
                                font=ctk.CTkFont(size=11),
                                anchor="w"
                            )
                            cell.pack(padx=8, pady=4, fill="both", expand=True)
                
                # Atualizar contador
                info_label.configure(text=f"Registros carregados: {len(df_atualizado)}")
                
                # Forçar atualização da interface
                table_frame.update_idletasks()
                table_container.update_idletasks()

                table_container.grid_columnconfigure(0, weight=1)
                table_container.grid_rowconfigure(0, weight=0)
                table_container.grid_rowconfigure(1, weight=1)

                # Garantir posição inicial do scroll no topo após qualquer filtro/ordenação
                try:
                    table_frame._parent_canvas.yview_moveto(0)
                except Exception:
                    pass
                excel_window.after(10, lambda: getattr(table_frame, "_parent_canvas", None) and table_frame._parent_canvas.yview_moveto(0))
                
            except Exception as rebuild_error:
                print(f"Erro ao reconstruir tabela: {rebuild_error}")
                for widget in table_container.winfo_children():
                    widget.destroy()
                error_frame = ctk.CTkFrame(table_container, fg_color="#2b2b2b")
                error_frame.grid(row=0, column=0, sticky="nsew")
                table_frame_ref[0] = error_frame
                ctk.CTkLabel(
                    error_frame,
                    text="Erro ao exibir dados. Tente fechar e abrir novamente.",
                    text_color="#ff6b6b",
                    font=ctk.CTkFont(size=13, weight="bold")
                ).pack(pady=20, anchor="n")
        
        def mostrar_menu_coluna(coluna):
            """Mostra menu com opções de ordenação e filtro"""
            menu = ctk.CTkToplevel(excel_window)
            menu.title(f"Opções - {coluna}")
            menu.geometry("250x200")
            menu.resizable(False, False)
            
            # Centralizar menu
            menu.update_idletasks()
            menu_width = 250
            menu_height = 200
            x = excel_window.winfo_x() + (excel_window.winfo_width() - menu_width) // 2
            y = excel_window.winfo_y() + (excel_window.winfo_height() - menu_height) // 2
            menu.geometry(f"{menu_width}x{menu_height}+{x}+{y}")
            menu.transient(excel_window)
            menu.grab_set()
            
            # Título
            titulo = ctk.CTkLabel(
                menu,
                text=f"Coluna: {coluna}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            titulo.pack(pady=(15, 10))
            
            # Botões de ordenação
            ctk.CTkButton(
                menu,
                text="⬆️ Ordenar A → Z",
                command=lambda: [ordenar_coluna(coluna, True), menu.destroy()],
                width=200
            ).pack(pady=5)
            
            ctk.CTkButton(
                menu,
                text="⬇️ Ordenar Z → A",
                command=lambda: [ordenar_coluna(coluna, False), menu.destroy()],
                width=200
            ).pack(pady=5)
            
            # Botão de filtro
            ctk.CTkButton(
                menu,
                text="🔍 Filtrar valores",
                command=lambda: [menu.destroy(), mostrar_filtro(coluna)],
                width=200
            ).pack(pady=5)
            
            # Botão limpar
            ctk.CTkButton(
                menu,
                text="🗑️ Limpar filtros",
                command=lambda: [limpar_filtros(coluna), menu.destroy()],
                width=200,
                fg_color="gray40",
                hover_color="gray50"
            ).pack(pady=5)
        
        def ordenar_coluna(coluna, ascendente):
            """Ordena por uma coluna"""
            nonlocal current_sort_column, current_sort_ascending
            current_sort_column = coluna
            current_sort_ascending = ascendente
            reconstruir_tabela()
        
        def limpar_filtros(coluna):
            """Remove filtros de uma coluna"""
            if coluna in column_filters:
                del column_filters[coluna]
            reconstruir_tabela()
        
        def mostrar_filtro(coluna):
            """Mostra janela de filtro com checkboxes"""
            if coluna not in filterable_columns:
                return

            # Obter valores únicos da coluna
            df_base_filtro = build_visual_df(df)
            if coluna not in df_base_filtro.columns:
                return
            if coluna == "Tipo - OS":
                valores_unicos = ["Manta", "Tensylon"]
            else:
                valores_unicos = sorted(df_base_filtro[coluna].astype(str).unique())
            
            filtro_window = ctk.CTkToplevel(excel_window)
            filtro_window.title(f"Filtrar - {coluna}")
            filtro_window.geometry("300x133")
            
            # Centralizar
            filtro_window.update_idletasks()
            x = excel_window.winfo_x() + (excel_window.winfo_width() - 300) // 2
            y = excel_window.winfo_y() + (excel_window.winfo_height() - 133) // 2
            filtro_window.geometry(f"300x133+{x}+{y}")
            filtro_window.transient(excel_window)
            filtro_window.grab_set()
            
            # Título
            ctk.CTkLabel(
                filtro_window,
                text=f"Selecione os valores para filtrar:",
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(pady=10)
            
            # Frame scrollable para checkboxes
            scroll_frame = ctk.CTkScrollableFrame(filtro_window, height=83)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Dicionário para armazenar variáveis dos checkboxes
            check_vars = {}
            valores_atuais = set(column_filters.get(coluna, valores_unicos))
            
            for valor in valores_unicos:
                var = ctk.BooleanVar(value=(valor in valores_atuais))
                check_vars[valor] = var
                ctk.CTkCheckBox(
                    scroll_frame,
                    text=valor[:50],  # Limitar tamanho
                    variable=var
                ).pack(anchor="w", pady=2, padx=5)
            
            # Botão aplicar
            def aplicar():
                valores_selecionados = [v for v, var in check_vars.items() if var.get()]
                if valores_selecionados and set(valores_selecionados) != set(valores_unicos):
                    column_filters[coluna] = valores_selecionados
                elif coluna in column_filters:
                    del column_filters[coluna]
                reconstruir_tabela()
                filtro_window.destroy()

            def limpar_este_filtro():
                if coluna in column_filters:
                    del column_filters[coluna]
                reconstruir_tabela()
                filtro_window.destroy()
            
            ctk.CTkButton(
                filtro_window,
                text="✓ Aplicar Filtro",
                command=aplicar,
                width=200,
                fg_color="#2a9d2a",
                hover_color="#238a23"
            ).pack(pady=10)

            ctk.CTkButton(
                filtro_window,
                text="🗑 Limpar Filtro",
                command=limpar_este_filtro,
                width=200,
                fg_color="gray40",
                hover_color="gray50"
            ).pack(pady=(0, 10))
        
        # Card de conteúdo
        card = ctk.CTkFrame(excel_window, corner_radius=10)
        card.pack(fill="both", expand=True, padx=10, pady=10)
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        
        # Cabeçalho
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        
        # Título
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Visualização de Dados",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Info do arquivo
        info_label = ctk.CTkLabel(
            header_frame,
            text=f"Registros carregados: {len(df_visual)}",
            font=ctk.CTkFont(size=11),
            text_color="gray65"
        )
        info_label.pack(anchor="w", pady=(4, 0))

        filtro_hint_label = ctk.CTkLabel(
            header_frame,
            text="Para filtrar, clique no cabeçalho da coluna.",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        filtro_hint_label.pack(anchor="w", pady=(2, 0))

        # Container da tabela (cabeçalho fixo + corpo rolável)
        table_container = ctk.CTkFrame(card, fg_color="transparent")
        table_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(5, 10))
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(0, weight=0)
        table_container.grid_rowconfigure(1, weight=1)
        
        # Construir tabela pela primeira vez
        reconstruir_tabela()
        
        # Aviso se houver mais linhas
        if len(df) > 100:
            warning_label = ctk.CTkLabel(
                card,
                text=f"⚠️ Exibindo apenas as primeiras 100 linhas de {len(df)}",
                font=ctk.CTkFont(size=10),
                text_color="#ff9800"
            )
            warning_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 5))
        
        # Container para botões
        buttons_container = ctk.CTkFrame(card, fg_color="transparent")
        buttons_container.grid(row=3, column=0, sticky="ew", padx=20, pady=(5, 15))
        
        # Botão Salvar e Atualizar Jira
        save_btn = ctk.CTkButton(
            buttons_container,
            text="💾 Salvar e Atualizar Jira",
            command=lambda: salvar_e_atualizar_jira(df, entries_data, card, excel_window),
            width=190,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2a9d2a",
            hover_color="#238a23",
            corner_radius=8
        )
        save_btn.pack(side="left", padx=(0, 8))
        
        # Botão Fechar
        close_btn = ctk.CTkButton(
            buttons_container,
            text="✕ Fechar",
            command=excel_window.destroy,
            width=110,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="gray40",
            hover_color="gray50",
            corner_radius=8
        )
        close_btn.pack(side="left")
        
        print("Janela de visualização criada com sucesso!")
        
    except Exception as e:
        import traceback
        print(f"Erro ao visualizar dados: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Script executado diretamente - carregando dados em memoria")
    df = gerar_update_cards()
    print(f"Concluido! {len(df)} registros carregados")