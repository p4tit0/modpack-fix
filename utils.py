from configparser import ConfigParser
from enum import StrEnum
import json
import os


def read_config(config_path):
    config = ConfigParser()
    config.read(config_path)

    class Clients(StrEnum):
        FINAL = config['DEFAULT'].get('final_pack_client'),
        ORIGINAL = config['DEFAULT'].get('origin_pack_client'),
    
    class Folders(StrEnum):
        RC_MODS = config['DEFAULT'].get('final_pack_mods'),
        DC_MODS = config['DEFAULT'].get('origin_pack_mods'),
        RC_KUBE = config['DEFAULT'].get('final_pack_kube')

    class Output(StrEnum):
        BASE = config['OUTPUT'].get('base'),
        RC_BLOCKS = config['OUTPUT'].get('final_pack_blocks'),
        DC_BLOCKS = config['OUTPUT'].get('origin_pack_blocks'),
        RC_ITEMS = config['OUTPUT'].get('final_pack_items'),
        DC_ITEMS = config['OUTPUT'].get('origin_pack_items'),
        RC_ENTITIES = config['OUTPUT'].get('final_pack_entities'),
        DC_ENTITIES = config['OUTPUT'].get('origin_pack_entities'),
        BLOCK_REQ = config['OUTPUT'].get('modpack_block_req'),
        ITEM_REQ = config['OUTPUT'].get('modpack_item_req'),
        ENTITIES_REQ = config['OUTPUT'].get('modpack_entity_req'),
        MISSING_BLOCKS = config['OUTPUT'].get('missing_blocks'),
        MISSING_ITEMS = config['OUTPUT'].get('missing_items'),
        MISSING_ENTITIES = config['OUTPUT'].get('missing_entities'),
        CORRELATIONS = config['OUTPUT'].get('correlations'),

    return  Folders, Output, Clients



def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Erro: Arquivo {file_path} não encontrado.")
        return None
    except json.JSONDecodeError:
        print(f"Erro: O arquivo {file_path} contém um JSON inválido.")
        return None
    
def get_type(value: str):
    if value in ['true', 'false']:
        return "boolean"
    elif str.isnumeric(value):
        return "number"
    elif isinstance(value, str):
        return "string"
    else:
        return "unknown"
    
def save_file(base, result, file_path):
    try:
        if not os.path.exists(base):
            os.makedirs(base)
        with open(base + file_path, 'w', encoding='utf-8') as arquivo:
            json.dump(result, arquivo, indent=4, ensure_ascii=False)
        print(f"\nResultado salvo em: {file_path}")
    except Exception as e:
        print(f"\nErro ao salvar o arquivo: {e}")

def bool_input():
    while True:
        try:
            answer = input("Digite 's' para sim ou 'n' para não: ").strip().lower()
            if answer == 's':
                return True
            elif answer == 'n':
                return False
            else:
                print("Entrada inválida. Por favor, digite 's' para sim ou 'n' para não.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}. Tente novamente.")

def int_range_input(min, max):
    while True:
        try:
            user_input = input(f"Digite um número inteiro entre {min} e {max}: ").strip()
            num = int(user_input)
            if min <= num <= max:
                return num
            else:
                print(f"Por favor, insira um número entre {min} e {max}.")
        except ValueError:
            print("Entrada inválida. Certifique-se de digitar um número inteiro.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}. Tente novamente.")
