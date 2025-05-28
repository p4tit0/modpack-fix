from typing import Dict, List, Any
from utils import read_config, load_json, save_file


class ModpackComparator:
    """Classe responsável por comparar dois modpacks e identificar elementos faltantes."""
    
    def __init__(self, config_path: str = 'config.ini'):
        self.config = self._load_config(config_path)
        self.origin_data = {}
        self.final_data = {}
        self.missing_elements = {
            'blocks': [],
            'items': [],
            'entities': []
        }

    def _load_config(self, config_path: str) -> Any:
        """Carrega a configuração do arquivo ini."""
        Folders, Output, _ = read_config(config_path)
        return {
            'folders': Folders,
            'output': Output
        }

    def load_data(self) -> None:
        """Carrega os dados dos modpacks de origem e final."""
        output = self.config['output']
        
        # Carrega dados do modpack de origem
        self.origin_data = {
            'blocks': load_json(output.BASE + output.DC_BLOCKS),
            'items': load_json(output.BASE + output.DC_ITEMS),
            'entities': load_json(output.BASE + output.DC_ENTITIES)
        }
        
        # Carrega dados do modpack final
        self.final_data = {
            'blocks': load_json(output.BASE + output.RC_BLOCKS),
            'items': load_json(output.BASE + output.RC_ITEMS),
            'entities': load_json(output.BASE + output.RC_ENTITIES)
        }

    def find_missing_elements(self) -> None:
        """Encontra todos os elementos faltantes entre os modpacks."""
        self.missing_elements['blocks'] = self._find_missing(
            self.origin_data['blocks'], 
            self.final_data['blocks'],
            'blocks'
        )
        self.missing_elements['items'] = self._find_missing(
            self.origin_data['items'], 
            self.final_data['items'],
            'items'
        )
        self.missing_elements['entities'] = self._find_missing(
            self.origin_data['entities'], 
            self.final_data['entities'],
            'entities'
        )

    def _find_missing(self, origin_elements: Dict, final_elements: Dict, element_type: str) -> List[Dict]:
        """Método genérico para encontrar elementos faltantes de um tipo específico."""
        missing_elements = []
        
        for modid, origin_data in origin_elements.items():
            # Se o mod inteiro não existe no modpack final
            if modid not in final_elements:
                for element in origin_data[element_type]:
                    element_copy = element.copy()
                    element_copy['modid'] = modid
                    missing_elements.append(element_copy)
            else:
                # Verifica elementos individuais
                final_data = final_elements[modid]
                final_ids = [elem['id'] for elem in final_data[element_type]]
                
                for origin_element in origin_data[element_type]:
                    if origin_element['id'] not in final_ids:
                        element_copy = origin_element.copy()
                        element_copy['modid'] = modid
                        missing_elements.append(element_copy)
        
        return missing_elements

    def save_results(self) -> None:
        """Salva os resultados em arquivos JSON."""
        output = self.config['output']
        
        save_file(output.BASE, self.missing_elements['blocks'], output.MISSING_BLOCKS)
        save_file(output.BASE, self.missing_elements['items'], output.MISSING_ITEMS)
        save_file(output.BASE, self.missing_elements['entities'], output.MISSING_ENTITIES)

    def print_results(self) -> None:
        """Exibe os resultados da comparação."""
        output = self.config['output']
        
        print("\nContagem de elementos faltantes:")
        print(f"- Blocos faltantes: {len(self.missing_elements['blocks'])}")
        print(f"- Itens faltantes: {len(self.missing_elements['items'])}")
        print(f"- Entidades faltantes: {len(self.missing_elements['entities'])}")

        print("\nArquivos JSON gerados:")
        print(f"- Blocos faltantes: {output.BASE + output.MISSING_BLOCKS}")
        print(f"- Itens faltantes: {output.BASE + output.MISSING_ITEMS}")
        print(f"- Entidades faltantes: {output.BASE + output.MISSING_ENTITIES}")


def main():
    try:
        comparator = ModpackComparator()
        comparator.load_data()
        comparator.find_missing_elements()
        comparator.save_results()
        comparator.print_results()
        
        print("\nProcesso concluído com sucesso.")
    except Exception as e:
        print(f"\nOcorreu um erro durante a execução: {e}")


if __name__ == "__main__":
    main()