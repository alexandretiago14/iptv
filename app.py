import requests
from flask import Flask
import re
import os
import time
from threading import Thread, Event

app = Flask(__name__, static_folder='static', static_url_path='')
M3U_URL = "https://raw.githubusercontent.com/LITUATUI/M3UPT/refs/heads/main/M3U/M3UPT.m3u"
OUTPUT_FILENAME = "m3upt_atualizado.m3u"
OUTPUT_DIR = "static"
UPDATE_INTERVAL_SECONDS = 3 * 60 * 60  # 3 horas em segundos
DESIRED_TVG_IDS = [
    'RTP1.pt', 'RTP2.pt', 'SIC.pt', 'TVI.pt', 'SICNoticias.pt', 'CNNPortugal.pt',
    'ARTV.pt', 'SICAltaDefinicao.pt', 'PortoCanal.pt'
]

stop_event = Event()

def process_m3u(m3u_content):
    """
    Filtra canais por tvg-id e formata um ficheiro M3U a partir do conteúdo.

    Args:
        m3u_content (str): O conteúdo do ficheiro M3U original.

    Returns:
        str: O conteúdo M3U personalizado.
    """
    lines = m3u_content.splitlines()
    customized_lines = ['#EXTM3U']
    add_url = False
    current_channel_info = None

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#EXTVLCOPT') or line.startswith('#KODIPROP'):
            continue

        if line.startswith('#EXTINF'):
            match = re.search(r'tvg-id="([^"]*)"', line, re.IGNORECASE)
            if match and match.group(1).lower() in [tid.lower() for tid in DESIRED_TVG_IDS]:
                customized_lines.append(line)
                add_url = True
                current_channel_info = line
            else:
                add_url = False
                current_channel_info = None
        elif add_url and current_channel_info:
            customized_lines.append(line)
            add_url = False
            current_channel_info = None

    return "\n".join(customized_lines)

def update_m3u_file():
    """
    Busca, processa e guarda o ficheiro M3U no servidor no diretório estático.
    """
    try:
        response = requests.get(M3U_URL)
        response.raise_for_status()
        m3u_content = response.text
        custom_content = process_m3u(m3u_content)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(custom_content)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ficheiro M3U atualizado e guardado em: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Erro ao obter o ficheiro M3U: {e}")
        return False
    except IOError as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Erro ao guardar o ficheiro M3U: {e}")
        return False

def run_update_loop():
    while not stop_event.is_set():
        update_m3u_file()
        stop_event.wait(UPDATE_INTERVAL_SECONDS)
    print("[{time.strftime('%Y-%m-%d %H:%M:%S')}] Loop de atualização terminado.")

if __name__ == '__main__':
    # Inicializa a aplicação Flask configurando o diretório estático
    app = Flask(__name__, static_folder='static', static_url_path='')

    # Inicia o loop de atualização em uma thread separada
    update_thread = Thread(target=run_update_loop)
    update_thread.daemon = True
    update_thread.start()

    # Atualiza o ficheiro M3U na primeira execução
    update_m3u_file()

    app.run(debug=True, host='0.0.0.0', port=5000) # Alteração da porta para 5001

    stop_event.set()
    update_thread.join()