import difflib
from visualization import BlockVisualizer
from typing import Dict, List, Any, Optional, Tuple
from utils import load_json, save_file, bool_input, int_range_input, read_config
from configparser import ConfigParser
import os

class BlockReplacer:
    def __init__(self, config_path: str = 'config.ini'):
        self.config = self._load_config(config_path)
        self.visualizer = BlockVisualizer()
        self.existing_blocks = None
        self.missing_blocks = None
        self.existing_block_ids = []
        self.replacement_mapping = {}
        self.progress_file = os.path.join(self.config['output'].BASE, 'replacement_progress.json')
        self.loaded_progress = False

    def _load_config(self, config_path: str) -> Tuple[Any, Any]:
        """Carrega a configuração usando a função utilitária."""
        Folders, Output, _ = read_config(config_path)
        return {
            'folders': Folders,
            'output': Output
        }

    def load_data(self) -> None:
        """Carrega os dados necessários usando as funções utilitárias."""
        output = self.config['output']
        
        # Carrega blocos existentes e faltantes
        self.existing_blocks = load_json(os.path.join(output.BASE, output.RC_BLOCKS))
        self.missing_blocks = load_json(os.path.join(output.BASE, output.MISSING_BLOCKS))
        
        if not self.existing_blocks or not self.missing_blocks:
            raise ValueError("Não foi possível carregar os dados necessários")
        
        self.existing_block_ids = self._get_all_existing_block_ids()
        self._load_progress()

    def _load_progress(self) -> None:
        """Carrega o progresso anterior se existir."""
        if os.path.exists(self.progress_file):
            progress = load_json(self.progress_file)
            if progress:
                self.replacement_mapping = progress.get('mapping', {})
                self.loaded_progress = True
                print(f"\nProgresso anterior carregado. {len(self.replacement_mapping)} substituições já feitas.")

    def _save_progress(self) -> None:
        """Salva o progresso atual."""
        progress_data = {
            'mapping': self.replacement_mapping,
            'remaining': [block for block in self.missing_blocks 
                            if f"{block['modid']}:{block['id']}" not in self.replacement_mapping]
        }
        save_file(
            base=self.config['output'].BASE,
            result=progress_data,
            file_path='replacement_progress.json'
        )

    def _get_all_existing_block_ids(self) -> List[str]:
        """Obtém todos os IDs de blocos existentes."""
        block_ids = []
        for mod in self.existing_blocks.values():
            for block in mod.get('blocks', []):
                block_ids.append(f"{mod['modid']}:{block['id']}")
        return block_ids

    def find_similar_blocks(self, missing_block: Dict[str, Any], num_matches: int = 30) -> List[Dict[str, Any]]:
        """Encontra blocos semelhantes com base no nome e ID."""
        missing_id = missing_block['id']
        missing_display_name = missing_block['display_name']
        
        all_blocks = []
        for mod in self.existing_blocks.values():
            for block in mod.get('blocks', []):
                block_copy = block.copy()
                block_copy['full_id'] = f"{mod['modid']}:{block['id']}"
                block_copy['mod_name'] = mod['name']
                all_blocks.append(block_copy)
        
        for block in all_blocks:
            id_similarity = difflib.SequenceMatcher(None, missing_id, block['id']).ratio()
            name_similarity = difflib.SequenceMatcher(
                None, 
                missing_display_name.lower(), 
                block.get('display_name', '').lower()
            ).ratio()
            block['similarity_score'] = (id_similarity * 0.6) + (name_similarity * 0.4)
        
        all_blocks.sort(key=lambda x: x['similarity_score'], reverse=True)
        return all_blocks[:num_matches]

    def display_similar_blocks(self, missing_block: Dict[str, Any], similar_blocks: List[Dict[str, Any]]) -> None:
        """Exibe os blocos semelhantes encontrados."""
        print(f"\nBloco faltante: {missing_block['modid']}:{missing_block['id']} ({missing_block['display_name']})")
        print("Blocos semelhantes encontrados:")
        for i, block in enumerate(similar_blocks, 1):
            print(f"{i}. {block['full_id']} ({block.get('display_name', 'Sem nome')}) - Similaridade: {block['similarity_score']:.2f}")
        print("0. Nenhum satisfatório - buscar com outros parâmetros")
        print("-1. Digitar ID manualmente")
        print("-2. Salvar e sair")

    def validate_manual_id(self, manual_id: str) -> bool:
        """Valida se o ID digitado manualmente existe."""
        return manual_id in self.existing_block_ids

    def get_replacement_block(self, missing_block: Dict[str, Any]) -> Optional[str]:
        """Obtém o bloco de substituição para um bloco faltante."""
        while True:
            similar_blocks = self.find_similar_blocks(missing_block)
            
            if missing_block.get('variant_info'):
                self.visualizer.show_in_blockbench(missing_block, missing_block)
            
            self.display_similar_blocks(missing_block, similar_blocks)
            
            try:
                min_choice = -2
                max_choice = len(similar_blocks)
                choice = int_range_input(min_choice, max_choice)
                
                if choice == 0:
                    print("Refazendo a busca...")
                    continue
                elif choice == -1:
                    manual_id = input("Digite o ID completo do bloco (formato 'modid:block_id'): ")
                    if self.validate_manual_id(manual_id):
                        return manual_id
                    print("ID inválido. Por favor, digite um ID existente.")
                elif choice == -2:
                    return None  # Indica que o usuário quer sair
                else:
                    return similar_blocks[choice-1]['full_id']
            except ValueError:
                print("Por favor, digite um número válido.")

    def process_replacements(self) -> None:
        """Processa todos os blocos faltantes."""
        print("\nProcesso de substituição de blocos faltantes")
        print("------------------------------------------")
        print("Durante o processo, digite '-2' para salvar e sair\n")
        
        total_blocks = len(self.missing_blocks)
        processed_count = 0
        
        # Filtra apenas os blocos que ainda não foram processados
        remaining_blocks = [
            block for block in self.missing_blocks 
            if f"{block['modid']}:{block['id']}" not in self.replacement_mapping
        ]
        
        for missing_block in remaining_blocks:
            missing_id = f"{missing_block['modid']}:{missing_block['id']}"
            print(f"\nProcessando bloco faltante ({processed_count+1}/{len(remaining_blocks)}): {missing_id} ({missing_block['display_name']})")
            
            replacement_id = self.get_replacement_block(missing_block)
            
            if replacement_id is None:  # Usuário escolheu salvar e sair
                self._save_progress()
                print("\nProgresso salvo. Você pode continuar posteriormente.")
                return
            
            self.replacement_mapping[missing_id] = replacement_id
            processed_count += 1
            
            # Salva progresso a cada 5 blocos processados
            if processed_count % 5 == 0:
                self._save_progress()
                print(f"\nProgresso salvo após {processed_count} substituições.")
        
        # Processamento completo
        self.save_final_results()
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)  # Remove o arquivo de progresso

    def save_final_results(self) -> None:
        """Salva os resultados finais usando a função utilitária."""
        output = self.config['output']
        save_file(
            base=output.BASE,
            result=self.replacement_mapping,
            file_path=output.CORRELATIONS
        )
        print("\nProcesso concluído. Mapeamento final salvo.")

def main():
    try:
        replacer = BlockReplacer()
        replacer.load_data()
        
        if replacer.loaded_progress:
            print("Deseja continuar do ponto onde parou?")
            if bool_input():
                replacer.process_replacements()
            else:
                print("Reiniciando o processo do início...")
                replacer.replacement_mapping = {}
                replacer.process_replacements()
        else:
            replacer.process_replacements()
            
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")

if __name__ == "__main__":
    main()