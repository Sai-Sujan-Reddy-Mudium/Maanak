import re

with open('api.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_logic = """        # --- DOMAIN 2: OUTPUT PROCESSING ---
        # (Disabled for now as requested - just passing the raw English answer back)
        translated_answer = english_answer
        audio_base64 = ""  # Skipping TTS

        return GatewayResponse(translated_text=translated_answer, audio_base64=audio_base64)"""

content = re.sub(r'# --- DOMAIN 2: OUTPUT PROCESSING ---.*return GatewayResponse\(translated_text=translated_answer, audio_base64=audio_base64\)', new_logic, content, flags=re.DOTALL)

with open('api.py', 'w', encoding='utf-8') as f:
    f.write(content)
