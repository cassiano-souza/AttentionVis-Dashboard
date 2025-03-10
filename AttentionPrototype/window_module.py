import Quartz  # Biblioteca que fornece acesso a várias APIs de baixo nível do macOS
import time
import objc  # Biblioteca para interagir com APIs do macOS escritas em Objective-C
from urllib.parse import urlparse  # Biblioteca padrão do Python para análise de URLs


class WindowService:
    """Classe para gerenciar a captura de informações sobre a janela ativa."""

    def extract_domain(self, url):
        """ Extrai o domínio principal da URL, removendo subdomínios. """
        try:
            parsed_url = urlparse(url)
            domain_parts = parsed_url.netloc.split(".")
            if len(domain_parts) > 2:
                return ".".join(domain_parts[-2:])  # Pega apenas o domínio principal (ex.: google.com)
            return parsed_url.netloc
        except Exception:
            return ""
    
    def get_active_app(self):
        """Obtém o nome do aplicativo ativo e, se for o Safari, também a URL da aba ativa."""
        
        # Declarando variáveis locais
        active_app = None
        active_url = None

        # Obter o nome do aplicativo ativo
        windows = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
            Quartz.kCGNullWindowID
        )
        for window in windows:
            if window.get('kCGWindowLayer') == 0 and window.get('kCGWindowOwnerName') != 'Finder':
                active_app = window.get('kCGWindowOwnerName')

        # Obter o URL da aba ativa no Safari
        if active_app == "Safari":
            # AppleScript para obter a URL da aba ativa no Safari
            script = '''
            tell application "Safari"
                set currentTab to front document
                return URL of currentTab
            end tell
            '''
            # Executa o AppleScript usando a biblioteca objc
            apple_script = objc.lookUpClass('NSAppleScript')
            script_obj = apple_script.alloc().initWithSource_(script)
            result, _ = script_obj.executeAndReturnError_(None)
            if result:
                full_url = result.stringValue()
                active_url = self.extract_domain(full_url)  # Armazena apenas o domínio

        # Gerar o timestamp
        timestamp = time.strftime("%H:%M:%S %d/%m/%Y")

        # Retornar as informações
        return {
            "Janela Ativa": active_app,
            "URL": active_url,
            "Timestamp": timestamp
        }

