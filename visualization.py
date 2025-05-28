import os
import json
import requests
from pathlib import Path
from typing import Dict, Any
import socketio

class BlockVisualizer:
    """Classe para visualização de blocos no Blockbench"""
    
    def __init__(self, texture_dir: str = "textures"):
        self.sio = socketio.Client()
        self.texture_dir = texture_dir
        self._setup_connection()
        
    def _setup_connection(self):
        try:
            self.sio.connect('http://localhost:3000')  # Porta padrão do Blockbench
        except:
            print("Blockbench não está rodando ou o plugin de integração não está instalado")

    def generate_block_model(self, block_data: Dict[str, Any], missing_block: Dict[str, Any]):
        """Gera um modelo simples para o bloco"""
        model = {
            "textures": self._get_textures(block_data, missing_block),
            "elements": [{
                "from": [0, 0, 0],
                "to": [16, 16, 16],
                "faces": {
                    "north": {"uv": [0, 0, 16, 16], "texture": "#0"},
                    "east": {"uv": [0, 0, 16, 16], "texture": "#0"},
                    "south": {"uv": [0, 0, 16, 16], "texture": "#0"},
                    "west": {"uv": [0, 0, 16, 16], "texture": "#0"},
                    "up": {"uv": [0, 0, 16, 16], "texture": "#0"},
                    "down": {"uv": [0, 0, 16, 16], "texture": "#0"}
                }
            }]
        }
        return model

    def _get_textures(self, block_data: Dict[str, Any], missing_block: Dict[str, Any]):
        """Tenta obter as texturas do bloco"""
        texture_path = os.path.join(self.texture_dir, f"{missing_block['modid']}_{missing_block['id']}.png")
        
        if not os.path.exists(texture_path):
            # Tenta baixar a textura se não existir localmente
            self._download_texture(block_data, missing_block, texture_path)
        
        return {"0": texture_path if os.path.exists(texture_path) else "missing_texture"}

    def _download_texture(self, block_data: Dict[str, Any], missing_block: Dict[str, Any], save_path: str):
        """Tenta baixar a textura do bloco"""
        try:
            # Exemplo para mods populares - você precisará adaptar para cada mod específico
            modid = missing_block['modid']
            block_id = missing_block['id']
            
            if modid == "minecraft":
                url = f"https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets/1.19/assets/minecraft/textures/block/{block_id}.png"
            else:
                # Tenta um padrão comum para mods Forge/Fabric
                url = f"https://raw.githubusercontent.com/{modid}/master/src/main/resources/assets/{modid}/textures/block/{block_id}.png"
            
            response = requests.get(url)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Não foi possível baixar a textura: {e}")

    def show_in_blockbench(self, block_data: Dict[str, Any], missing_block: Dict[str, Any]):
        """Envia o modelo para o Blockbench"""
        model = self.generate_block_model(block_data, missing_block)
        try:
            self.sio.emit('load_model', {
                'type': 'java-block',
                'model': json.dumps(model),
                'name': f"{missing_block['modid']}:{missing_block['id']}"
            })
            return True
        except:
            print("Não foi possível conectar ao Blockbench")
            return False