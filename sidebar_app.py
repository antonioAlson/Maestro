import customtkinter as ctk
from PIL import Image
import os


class SidebarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Home")
        self.root.geometry("1000x500")
        # Configurar tema
        ctk.set_appearance_mode("dark")  # "light" ou "dark"
        ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
        
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
    
    def load_images(self):
        """Carrega as imagens dos ícones"""
        self.images = {}
        img_dir = "img"
        icon_size = (24, 24)
        
        # Mapeamento de ícones
        image_files = {
            "home": "home.png",
            "insights": "insigths.png",
            "edit": "edit.png",
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
            corner_radius=0
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
            corner_radius=8
        )
        self.toggle_btn.pack(pady=15, padx=10)
        
        # Container para os botões do menu (parte superior)
        self.menu_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_container.pack(fill="both", expand=True, pady=10)
        
        # Itens do menu principal (imagem_key, texto, comando)
        menu_items = [
            ("home", "Home", self.home_action),
            ("insights", "Insights", self.dashboard_action),
            ("edit", "Editar", self.files_action),
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
        self.exit_btn_data = (self.exit_btn, "exit", "Sair")
    
    def create_menu_button(self, container, img_key, text, command):
        """Cria um botão do menu"""
        img = self.images.get(img_key)
        
        btn = ctk.CTkButton(
            container,
            text=f"  {text}",
            image=img,
            command=command,
            anchor="w",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=13),
            compound="left"
        )
        btn.pack(fill="x", pady=3, padx=8)
        
        return btn
    
    def toggle_sidebar(self):
        """Alterna entre sidebar aberta e fechada"""
        if self.sidebar_expanded:
            # Fechar sidebar - mostrar apenas ícones
            self.sidebar.configure(width=self.sidebar_width_collapsed)
            for btn, img_key, text in self.menu_buttons:
                btn.configure(text="")
            # Atualizar botão Exit também
            self.exit_btn.configure(text="")
        else:
            # Abrir sidebar - mostrar ícones + texto
            self.sidebar.configure(width=self.sidebar_width_expanded)
            for btn, img_key, text in self.menu_buttons:
                btn.configure(text=f"  {text}")
            # Atualizar botão Exit também
            self.exit_btn.configure(text="  Sair")
        
        self.sidebar_expanded = not self.sidebar_expanded
    
    def create_content_area(self):
        """Cria a área de conteúdo principal"""
        self.content_area = ctk.CTkFrame(self.main_container, corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Título da área de conteúdo
        title_label = ctk.CTkLabel(
            self.content_area,
            text="Área de Conteúdo Principal",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=30)
        
        # Texto informativo
        info_label = ctk.CTkLabel(
            self.content_area,
            text="Clique nos itens do menu para alterar o conteúdo",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        info_label.pack()
        
        # Frame para exibir conteúdo dinâmico
        self.dynamic_content = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.dynamic_content.pack(fill="both", expand=True, padx=20, pady=20)
    
    def clear_content(self):
        """Limpa o conteúdo dinâmico"""
        for widget in self.dynamic_content.winfo_children():
            widget.destroy()
    
    def show_content(self, title, description):
        """Mostra conteúdo na área principal"""
        self.clear_content()
        
        # Card de conteúdo
        card = ctk.CTkFrame(self.dynamic_content, corner_radius=15)
        card.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Título do card
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=30)
        
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
            "🏠 Home",
            "Bem-vindo à página inicial! Aqui você pode ver um resumo geral do sistema."
        )
    
    def dashboard_action(self):
        self.show_content(
            "📊 Dashboard",
            "Dashboard com métricas e estatísticas importantes do sistema."
        )
    
    def files_action(self):
        self.show_content(
            "📁 Arquivos",
            "Gerenciador de arquivos - visualize e organize seus documentos."
        )
    
    def settings_action(self):
        self.show_content(
            "⚙️ Configurações",
            "Configure as preferências do sistema de acordo com suas necessidades."
        )
    
    def reports_action(self):
        self.show_content(
            "📈 Relatórios",
            "Acesse relatórios detalhados e análises de dados."
        )
    
    def profile_action(self):
        self.show_content(
            "👤 Perfil",
            "Visualize e edite as informações do seu perfil de usuário."
        )
    
    def help_action(self):
        self.show_content(
            "❓ Ajuda",
            "Encontre ajuda e documentação sobre como usar o sistema."
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
