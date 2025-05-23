import requests
from flask import Flask, Response
import re

app = Flask(__name__)
M3U_URL = "https://raw.githubusercontent.com/LITUATUI/M3UPT/refs/heads/main/M3U/M3UPT.m3u"
DESIRED_TVG_IDS = [
    'RTP1.pt', 'RTP2.pt', 'SIC.pt', 'TVI.pt', 'SICNoticias.pt', 'CNNPortugal.pt',
    'ARTV.pt', 'SICAltaDefinicao.pt', 'PortoCanal.pt'
]

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

@app.route('/m3u')
def get_custom_m3u():
    try:
        response = requests.get(M3U_URL)
        response.raise_for_status()
        m3u_content = response.text
        custom_content = process_m3u(m3u_content)
        return Response(custom_content, mimetype='audio/x-mpegurl')
    except requests.exceptions.RequestException as e:
        return Response(f"Erro ao obter o ficheiro M3U: {e}", status=500)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 