import os
import zipfile
import json
import toml
from typing import Dict, List, Any, Tuple, Optional
from utils import read_config, load_json, save_file


class ModExtractor:
    """Classe responsável por extrair informações de mods Minecraft."""

    DEFAULT_MOD_INFO = {
        'name': 'Unknown',
        'creator': 'Unknown',
        'modid': 'Unknown',
        'version': 'Unknown',
        'blocks': [],
        'items': [],
        'entities': []
    }

    def __init__(self):
        self.lang_cache = {}

    def extract_mod_info(self, mod_path: str) -> Dict[str, Any]:
        """Extrai informações principais de um arquivo de mod."""
        mod_info = self.DEFAULT_MOD_INFO.copy()

        try:
            with zipfile.ZipFile(mod_path, 'r') as jar:
                self._extract_metadata(jar, mod_info)
                self._extract_game_content(jar, mod_info)

        except zipfile.BadZipFile:
            print(f"Erro: O arquivo {mod_path} não é um JAR válido.")
        except Exception as e:
            print(f"Erro ao processar o mod {mod_path}: {e}")

        return mod_info

    def extract_client_content(self, client_path: str) -> Dict[str, Any]:
        """Extrai conteúdo do client.jar (blocos, itens e entidades do Minecraft)."""
        client_info = {
            'name': 'Minecraft',
            'creator': 'Mojang',
            'modid': 'minecraft',
            'version': 'Unknown',
            'blocks': [],
            'items': [],
            'entities': []
        }

        try:
            with zipfile.ZipFile(client_path, 'r') as jar:
                self._load_lang_files(jar, 'minecraft')
                client_info['blocks'] = self._extract_blocks(jar, 'minecraft')
                client_info['items'] = self._extract_items(jar, 'minecraft')
                client_info['entities'] = self._extract_entities(jar, 'minecraft')

        except zipfile.BadZipFile:
            print(f"Erro: O arquivo {client_path} não é um JAR válido.")
        except Exception as e:
            print(f"Erro ao processar o client {client_path}: {e}")

        return client_info

    def _extract_metadata(self, jar: zipfile.ZipFile, mod_info: Dict[str, Any]) -> None:
        """Extrai metadados do mod (nome, autor, etc.)."""
        if 'META-INF/mods.toml' in jar.namelist():
            with jar.open('META-INF/mods.toml') as mods_toml:
                toml_content = mods_toml.read().decode('utf-8')
                data = toml.loads(toml_content)

                if 'mods' in data and isinstance(data['mods'], list):
                    mod_entry = data['mods'][0]  # Pega o primeiro mod
                    mod_info.update({
                        'name': mod_entry.get('displayName', mod_info['name']),
                        'modid': mod_entry.get('modId', mod_info['modid']),
                        'version': mod_entry.get('version', mod_info['version']),
                        'creator': self._format_authors(mod_entry.get('authors', mod_info['creator']))
                    })

    def _format_authors(self, authors: Any) -> str:
        """Formata a informação de autores para string."""
        if isinstance(authors, list):
            return ', '.join(authors)
        return str(authors)

    def _extract_game_content(self, jar: zipfile.ZipFile, mod_info: Dict[str, Any]) -> None:
        """Extrai conteúdo do jogo (blocos, itens, entidades)."""
        self._load_lang_files(jar, mod_info['modid'])
        
        mod_info.update({
            'blocks': self._extract_blocks(jar, mod_info['modid']),
            'items': self._extract_items(jar, mod_info['modid']),
            'entities': self._extract_entities(jar, mod_info['modid'])
        })

    def _load_lang_files(self, jar: zipfile.ZipFile, modid: str) -> None:
        """Carrega arquivos de tradução para cache."""
        self.lang_cache[modid] = {}
        for lang_file in jar.namelist():
            if self._is_lang_file(lang_file, modid):
                with jar.open(lang_file) as f:
                    lang_content = f.read().decode('utf-8')
                    self.lang_cache[modid].update(json.loads(lang_content))

    def _is_lang_file(self, path: str, modid: str) -> bool:
        """Verifica se o arquivo é um arquivo de linguagem válido."""
        parts = path.split('/')
        return (len(parts) > 3 and 
                parts[0] == 'assets' and 
                parts[1] == modid and 
                'lang' in parts and 
                'en_us' in parts and 
                path.endswith('.json'))

    def _extract_blocks(self, jar: zipfile.ZipFile, modid: str) -> List[Dict[str, Any]]:
        """Extrai informações sobre blocos do mod."""
        blocks = []
        for file in jar.namelist():
            if self._is_block_file(file, modid):
                block_id = file.split('/')[-1].replace('.json', '')
                block_info = {
                    'id': block_id,
                    'display_name': self._get_display_name('block', modid, block_id),
                    'variant_info': self._extract_block_variants(jar, file)
                }
                blocks.append(block_info)
        return blocks

    def _is_block_file(self, path: str, modid: str) -> bool:
        """Verifica se o arquivo é um arquivo de blockstate válido."""
        parts = path.split('/')
        return (len(parts) > 3 and
                parts[0] == 'assets' and
                parts[1] == modid and
                'blockstates' in parts and
                path.endswith('.json'))

    def _extract_block_variants(self, jar: zipfile.ZipFile, block_file: str) -> Dict[str, List[str]]:
        """Extrai variantes de um bloco."""
        variant_info = {}
        with jar.open(block_file) as f:
            block_data = json.loads(f.read().decode('utf-8'))
            
            if 'variants' in block_data:
                for variant_key, _ in block_data['variants'].items():
                    if variant_key:
                        self._process_variant_key(variant_key, variant_info)
        for key in variant_info:
            variant_info[key] = list(variant_info[key])
        
        return variant_info

    def _process_variant_key(self, variant_key: str, variant_info: Dict[str, set]) -> None:
        """Processa uma chave de variante e atualiza o dicionário."""
        for keyval in variant_key.split(','):
            key, val = keyval.split('=')
            if key not in variant_info.keys():
                variant_info[key] = set()
            print
            variant_info[key].add(val)

    def _extract_items(self, jar: zipfile.ZipFile, modid: str) -> List[Dict[str, Any]]:
        """Extrai informações sobre itens do mod."""
        items = []
        for file in jar.namelist():
            if self._is_item_file(file, modid):
                item_id = file.split('/')[-1].replace('.json', '')
                items.append({
                    'id': item_id,
                    'display_name': self._get_display_name('item', modid, item_id)
                })
        return items

    def _is_item_file(self, path: str, modid: str) -> bool:
        """Verifica se o arquivo é um arquivo de item válido."""
        parts = path.split('/')
        return (len(parts) > 3 and
                parts[0] == 'assets' and
                parts[1] == modid and
                'models/item' in '/'.join(parts[2:4]) and
                path.endswith('.json'))

    def _extract_entities(self, jar: zipfile.ZipFile, modid: str) -> List[Dict[str, Any]]:
        """Extrai informações sobre entidades do mod."""
        entities = []
        for file in jar.namelist():
            if self._is_entity_file(file, modid):
                entity_id = file.split('/')[-1].replace('.json', '')
                entities.append({
                    'id': entity_id,
                    'display_name': self._get_display_name('entity', modid, entity_id)
                })
        return entities

    def _is_entity_file(self, path: str, modid: str) -> bool:
        """Verifica se o arquivo é um arquivo de entidade válido."""
        parts = path.split('/')
        return (len(parts) > 3 and
                parts[0] == 'assets' and
                parts[1] == modid and
                'entity' in parts and
                path.endswith('.json'))

    def _get_display_name(self, prefix: str, modid: str, element_id: str) -> str:
        """Obtém o nome de exibição a partir dos arquivos de linguagem."""
        lang_key = f"{prefix}.{modid}.{element_id}"
        return self.lang_cache.get(modid, {}).get(lang_key, 'Unknown')


class ModPackProcessor:
    """Classe responsável por processar pacotes de mods."""

    def __init__(self, extractor: ModExtractor):
        self.extractor = extractor

    def generate_mods_list(self, mods_folder: str, client_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Gera uma lista de todos os mods na pasta especificada, incluindo o client se fornecido."""
        mods = [
            self.extractor.extract_mod_info(os.path.join(mods_folder, mod_file))
            for mod_file in os.listdir(mods_folder)
            if mod_file.endswith('.jar')
        ]
        
        if client_path and os.path.exists(client_path):
            client_info = self.extractor.extract_client_content(client_path)
            mods.append(client_info)
        
        return mods

    def split_mods_data(self, mods_list: List[Dict[str, Any]]) -> Tuple[Dict, Dict, Dict]:
        """Separa os dados de blocos, itens e entidades em listas distintas."""
        blocks, items, entities = {}, {}, {}
        
        for mod in mods_list:
            mod_data = {
                'name': mod['name'],
                'creator': mod['creator'],
                'modid': mod['modid']
            }
            blocks[mod['modid']] = {**mod_data, 'blocks': mod['blocks']}
            items[mod['modid']] = {**mod_data, 'items': mod['items']}
            entities[mod['modid']] = {**mod_data, 'entities': mod['entities']}
            
        return blocks, items, entities

    def process_modpack(self, mods_folder: str, output_base: str, output_files: Dict[str, str], 
                        client_path: Optional[str] = None) -> None:
        """Processa um pacote de mods completo, opcionalmente incluindo o client."""
        mods_list = self.generate_mods_list(mods_folder, client_path)
        blocks, items, entities = self.split_mods_data(mods_list)

        save_file(output_base, blocks, output_files['blocks'])
        save_file(output_base, items, output_files['items'])
        save_file(output_base, entities, output_files['entities'])

        print(f"\nProcesso concluído para {mods_folder}. Arquivos gerados:")
        for name, path in output_files.items():
            print(f"- {name.capitalize()}: {os.path.join(output_base, path)}")
        
        if client_path:
            print(f"(Incluído conteúdo do client: {client_path})")


def main():
    # Configuração inicial
    Folders, Output, Clients = read_config('config.ini')
    extractor = ModExtractor()
    processor = ModPackProcessor(extractor)

    # Processa o primeiro pack (RC) incluindo o client
    processor.process_modpack(
        mods_folder=Folders.RC_MODS,
        output_base=Output.BASE,
        output_files={
            'blocks': Output.RC_BLOCKS,
            'items': Output.RC_ITEMS,
            'entities': Output.RC_ENTITIES
        },
        client_path=Clients.FINAL  # Assumindo que RC_KUBE aponta para o client.jar
    )

    # Processa o segundo pack (DC) sem o client
    processor.process_modpack(
        mods_folder=Folders.DC_MODS,
        output_base=Output.BASE,
        output_files={
            'blocks': Output.DC_BLOCKS,
            'items': Output.DC_ITEMS,
            'entities': Output.DC_ENTITIES
        },
        client_path=Clients.ORIGINAL
    )


if __name__ == "__main__":
    main()