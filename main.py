import customtkinter as ctk
from PIL import Image
import os
import subprocess
import threading


class SidebarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Home")
        self.root.geometry("1000x500")
        # Configurar tema
        ctk.set_appearance_mode("dark")  # "light" ou "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
        # Centralizar janela na tela
        self.center_window(1000, 500)
        
        # Estado da sidebar (True = aberta, False = fechada)
        self.sidebar_expanded = True
        
        # Larguras da sidebar
        self.sidebar_width_expanded = 200
        self.sidebar_width_collapsed = 60
        
        # Carregar imagens
        self.load_images()
        
        # Criar container principal
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # Criar sidebar
        self.create_sidebar()
        
        # Criar área de conteúdo
        self.create_content_area()
    
    def center_window(self, width, height):
        """Centraliza a janela na tela"""
        # Obter dimensões da tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calcular posição x e y para centralizar
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # Definir geometria com posição
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def load_images(self):
        """Carrega as imagens dos ícones"""
        self.images = {}
        img_dir = "img"
        icon_size = (24, 24)
        
        # Mapeamento de ícones
        image_files = {
            "home": "home.png",
            "dashboard": "dashboard.png",
            "pcp": "pcp.png",
            "settings": "settings.png",
            "exit": "exit.png"
        }
        
        for key, filename in image_files.items():
            img_path = os.path.join(img_dir, filename)
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    self.images[key] = ctk.CTkImage(light_image=img, dark_image=img, size=icon_size)
                except Exception as e:
                    print(f"Erro ao carregar imagem {filename}: {e}")
                    self.images[key] = None
            else:
                print(f"Imagem não encontrada: {img_path}")
                self.images[key] = None
        
    def create_sidebar(self):
        """Cria a sidebar com menu"""
        self.sidebar = ctk.CTkFrame(
            self.main_container,
            width=self.sidebar_width_expanded,
            corner_radius=0,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Botão de toggle no topo
        self.toggle_btn = ctk.CTkButton(
            self.sidebar,
            text="☰",
            command=self.toggle_sidebar,
            width=40,
            height=40,
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=8,
            fg_color="transparent",
            hover_color="#3a3a5e"
        )
        self.toggle_btn.pack(pady=15, padx=10, anchor="w")
        
        # Container para os botões do menu (parte superior)
        self.menu_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_container.pack(fill="both", expand=True, pady=10)
        
        # Itens do menu principal (imagem_key, texto, comando)
        menu_items = [
            ("home", "Home", self.home_action),
            ("dashboard", "Dashboard", self.dashboard_action),
            ("pcp", "PCP", self.pcp_action),
            ("settings", "Configurações", self.settings_action),
        ]
        
        # Criar botões do menu
        self.menu_buttons = []
        for img_key, text, command in menu_items:
            btn = self.create_menu_button(self.menu_container, img_key, text, command)
            self.menu_buttons.append((btn, img_key, text))
        
        # Container para o botão Exit (parte inferior)
        self.exit_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.exit_container.pack(side="bottom", fill="x", pady=10)
        
        # Criar botão Exit
        self.exit_btn = self.create_menu_button(self.exit_container, "exit", "Sair", self.exit_action)
    
    def create_menu_button(self, container, img_key, text, command):
        """Cria um botão do menu"""
        img = self.images.get(img_key)
        
        # Frame wrapper para controlar overflow
        btn_wrapper = ctk.CTkFrame(container, fg_color="transparent")
        btn_wrapper.pack(fill="x", pady=3, padx=8)
        
        btn = ctk.CTkButton(
            btn_wrapper,
            text=f"  {text}",
            image=img,
            command=command,
            anchor="w",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            compound="left",
            fg_color="transparent",
            hover_color="#3a3a5e"
        )
        btn.pack(fill="x")
        
        return btn
    
    def toggle_sidebar(self):
        """Alterna entre sidebar aberta e fechada"""
        if self.sidebar_expanded:
            # Fechar sidebar - mostrar apenas ícones
            self.sidebar.configure(width=self.sidebar_width_collapsed)
            self.update_button_texts("")
        else:
            # Abrir sidebar - expande primeiro, depois mostra texto
            self.sidebar.configure(width=self.sidebar_width_expanded)
            self.root.after(50, lambda: self.update_button_texts("show"))
        
        self.sidebar_expanded = not self.sidebar_expanded
    
    def update_button_texts(self, mode):
        """Atualiza os textos dos botões"""
        if mode == "":
            # Esconder textos
            for btn, img_key, text in self.menu_buttons:
                btn.configure(text="")
            self.exit_btn.configure(text="")
        else:
            # Mostrar textos
            for btn, img_key, text in self.menu_buttons:
                btn.configure(text=f"  {text}")
            self.exit_btn.configure(text="  Sair")
    
    def create_content_area(self):
        """Cria a área de conteúdo principal"""
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="#3d3d3d")
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Frame para exibir conteúdo dinâmico
        self.dynamic_content = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.dynamic_content.pack(fill="both", expand=True, padx=10, pady=10)
    
    def clear_content(self):
        """Limpa o conteúdo dinâmico"""
        for widget in self.dynamic_content.winfo_children():
            widget.destroy()
    
    def show_content(self, title, description, title_anchor="center", title_img=None):
        """Mostra conteúdo na área principal"""
        self.clear_content()
        
        # Card de conteúdo
        card = ctk.CTkFrame(self.dynamic_content, corner_radius=10)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Título do card com imagem
        # Adicionar espaçamento entre imagem e texto
        title_text = f"  {title}" if title_img else title
        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold"),
            image=title_img,
            compound="left"
        )
        title_label.pack(pady=30, anchor=title_anchor, padx=30)
        
        # Descrição
        desc_label = ctk.CTkLabel(
            card,
            text=description,
            font=ctk.CTkFont(size=14),
            wraplength=500,
            text_color="gray70"
        )
        desc_label.pack(pady=10, padx=30)
    
    # Ações dos botões do menu
    def home_action(self):
        self.show_content(
            "Home",
            "Bem-vindo à página inicial! Aqui você pode ver um resumo geral do sistema.",
            title_anchor="w",
            title_img=self.images.get("home")
        )
    
    def dashboard_action(self):
        self.show_content(
            "Dashboard",
            "Dashboard com métricas e estatísticas importantes do sistema.",
            title_anchor="w",
            title_img=self.images.get("dashboard")
        )
    
    def pcp_action(self):
        """Mostra conteúdo PCP com 6 botões em grade 2x3"""
        self.clear_content()
        
        # Card de conteúdo
        card = ctk.CTkFrame(self.dynamic_content, corner_radius=10)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Título do card com imagem
        title_text = f"  PCP"
        title_label = ctk.CTkLabel(
            card,
            text=title_text,
            font=ctk.CTkFont(size=24, weight="bold"),
            image=self.images.get("pcp"),
            compound="left"
        )
        title_label.pack(pady=30, anchor="w", padx=30)
        
        # Descrição
        desc_label = ctk.CTkLabel(
            card,
            text="Rotinas - realize as rotinas conforme necessário.",
            font=ctk.CTkFont(size=14),
            wraplength=500,
            text_color="gray70"
        )
        desc_label.pack(pady=10, padx=30, anchor="w")
        
        # Container para os botões com grid 2x3
        buttons_container = ctk.CTkFrame(card, fg_color="transparent")
        buttons_container.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Definir botões
        button_names = [
            "Gerar Relatório",
            "Adicionar Datas",
            "Reprogramar Atrasos",
            "Imprimir OPs"
        ]
        
        # Criar botões em grade 2x2 (2 colunas, 2 linhas)
        for i, btn_name in enumerate(button_names):
            row = i // 2  # 2 linhas
            col = i % 2   # 2 colunas
            btn = ctk.CTkButton(
                buttons_container,
                text=btn_name,
                width=200,
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                corner_radius=8,
                command=lambda name=btn_name: self.pcp_routine_action(name)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
    
    def show_loading_popup(self, message="Processando..."):
        """Mostra popup de carregamento centralizado"""
        self.loading_popup = ctk.CTkToplevel(self.root)
        self.loading_popup.title("Aguarde")
        self.loading_popup.geometry("350x180")
        self.loading_popup.resizable(False, False)
        
        # Centralizar baseado na janela principal
        self.loading_popup.transient(self.root)
        self.loading_popup.grab_set()
        
        # Atualizar para garantir que as dimensões estejam corretas
        self.loading_popup.update_idletasks()
        
        # Calcular posição central
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        popup_width = 350
        popup_height = 180
        
        x = root_x + (root_width - popup_width) // 2
        y = root_y + (root_height - popup_height) // 2
        
        self.loading_popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        
        # Mensagem
        label = ctk.CTkLabel(
            self.loading_popup,
            text=message,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(pady=20)
        
        # Progress bar determinada
        self.progress_bar = ctk.CTkProgressBar(self.loading_popup, mode="determinate")
        self.progress_bar.pack(pady=10, padx=40, fill="x")
        self.progress_bar.set(0)
        
        # Label de porcentagem
        self.progress_label = ctk.CTkLabel(
            self.loading_popup,
            text="0%",
            font=ctk.CTkFont(size=14)
        )
        self.progress_label.pack(pady=5)
        
        return self.loading_popup
    
    def update_progress(self, value):
        """Atualiza a barra de progresso e o label"""
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.set(value)
        if hasattr(self, 'progress_label') and self.progress_label:
            self.progress_label.configure(text=f"{int(value * 100)}%")
    
    def show_success_message(self, script_name, file_path=None):
        """Mostra mensagem de sucesso no popup"""
        if hasattr(self, 'loading_popup') and self.loading_popup:
            # Ajustar altura do popup para caber todos os elementos
            self.loading_popup.geometry("350x220")
            
            # Limpar widgets existentes
            for widget in self.loading_popup.winfo_children():
                widget.destroy()
            
            # Mensagem de sucesso
            success_label = ctk.CTkLabel(
                self.loading_popup,
                text="✓ Concluído com sucesso!",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#90EE90"
            )
            success_label.pack(pady=25)
            
            # Detalhes
            detail_label = ctk.CTkLabel(
                self.loading_popup,
                text=f"{script_name} executado com sucesso.",
                font=ctk.CTkFont(size=13)
            )
            detail_label.pack(pady=5)
            
            # Container para botões
            buttons_frame = ctk.CTkFrame(self.loading_popup, fg_color="transparent")
            buttons_frame.pack(pady=20)
            
            # Botão abrir arquivo (se houver caminho)
            if file_path:
                open_btn = ctk.CTkButton(
                    buttons_frame,
                    text="Abrir Arquivo",
                    command=lambda: self.open_file(file_path),
                    width=120,
                    height=35,
                    font=ctk.CTkFont(size=13, weight="bold")
                )
                open_btn.pack(side="left", padx=5)
            
            # Botão fechar
            close_btn = ctk.CTkButton(
                buttons_frame,
                text="Fechar",
                command=self.close_loading_popup,
                width=120,
                height=35,
                font=ctk.CTkFont(size=13, weight="bold")
            )
            close_btn.pack(side="left", padx=5)
    
    def open_file(self, file_path):
        """Abre o arquivo com o aplicativo padrão do sistema"""
        try:
            if os.path.exists(file_path):
                os.startfile(file_path)  # Windows
                print(f"Abrindo arquivo: {file_path}")
            else:
                print(f"Arquivo não encontrado: {file_path}")
        except Exception as e:
            print(f"Erro ao abrir arquivo: {e}")
    
    def close_loading_popup(self):
        """Fecha o popup de carregamento"""
        if hasattr(self, 'loading_popup') and self.loading_popup:
            self.loading_popup.destroy()
            self.loading_popup = None
    
    def run_script_with_loading(self, script_path, script_name, output_file=None):
        """Executa script em thread separada com popup de carregamento"""
        self.script_running = True
        
        def simulate_progress():
            """Simula progresso enquanto o script está rodando"""
            progress = 0
            while self.script_running and progress < 0.95:
                progress += 0.05
                self.root.after(0, lambda p=progress: self.update_progress(p))
                threading.Event().wait(0.3)  # Atualizar a cada 300ms
        
        def execute():
            try:
                result = subprocess.run(["python", script_path], 
                                      capture_output=True, 
                                      text=True,
                                      shell=True)
                print(f"Script {script_name} finalizado!")
                if result.stdout:
                    print(f"Saída: {result.stdout}")
                if result.stderr:
                    print(f"Erros: {result.stderr}")
            except Exception as e:
                print(f"Erro ao executar o script: {e}")
            finally:
                # Parar simulação, completar progresso e mostrar mensagem de sucesso
                self.script_running = False
                self.root.after(0, lambda: self.update_progress(1.0))
                self.root.after(500, lambda: self.show_success_message(script_name, output_file))
        
        # Mostrar popup e iniciar execução em thread separada
        self.show_loading_popup(f"Executando {script_name}...")
        
        # Iniciar thread de execução
        exec_thread = threading.Thread(target=execute, daemon=True)
        exec_thread.start()
        
        # Iniciar thread de simulação de progresso
        progress_thread = threading.Thread(target=simulate_progress, daemon=True)
        progress_thread.start()
    
    def pcp_routine_action(self, routine_name):
        """Ação executada ao clicar em uma rotina PCP"""
        print(f"Rotina selecionada: {routine_name}")
        
        if routine_name == "Gerar Relatório":
            # Executar o script generate_archives.py com popup de carregamento
            script_path = os.path.join("scripts", "generate_archives.py")
            output_file = os.path.join("src", "jira_cards.xlsx")
            self.run_script_with_loading(script_path, "Gerar Relatório", output_file)
        
        elif routine_name == "Adicionar Datas":
            # Executar o script atualizar_jira.py para gerar update_cards.xlsx
            script_path = os.path.join("scripts", "data_update", "atualizar_jira.py")
            output_file = os.path.join("src", "data_update", "update_cards.xlsx")
            self.run_script_with_loading(script_path, "Adicionar Datas", output_file)
        
        # Adicione aqui a lógica específica para outras rotinas
    
    def settings_action(self):
        self.show_content(
            "Configurações",
            "Configure as preferências do sistema de acordo com suas necessidades.",
            title_anchor="w",
            title_img=self.images.get("settings")
        )
    
    def exit_action(self):
        """Fecha a aplicação"""
        self.root.quit()

def main():
    root = ctk.CTk()
    app = SidebarApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
