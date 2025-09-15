
import os
import pandas as pd
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
import google.generativeai as genai
from io import BytesIO
from PIL import Image

# Configura las claves de API
GEMINI_API_KEY = "AIzaSyBWewrnTWZVr853xKtOGt-DHQzN60QRQHA"  # Reemplaza con tu clave de Gemini
STABILITY_API_KEY = "sk-KT6ZbSc2iOrtarB3bDBCyjqANg8It2AzbKapFRe5nVAht5tK"  # Reemplaza con tu clave de Stability AI

# Configura Gemini
genai.configure(api_key=GEMINI_API_KEY)
modelo = genai.GenerativeModel('gemini-1.5-flash')

# Configura Stability AI
stability_api = client.StabilityInference(
    key=STABILITY_API_KEY,
    verbose=True,
    engine="stable-diffusion-xl-1024-v1-0"
)
# Introducción
## Problemática
"""La generación manual de catálogos de productos textiles es un proceso lento y costoso, especialmente para pequeñas empresas que manejan inventarios grandes. Esto incluye escribir descripciones atractivas y crear imágenes profesionales, lo que puede tomar días o semanas.

## Solución
Este proyecto utiliza IA para automatizar esta tarea. Google Gemini genera descripciones con un prompt optimizado, mientras que Stability AI crea imágenes realistas. Los prompts usan la técnica de few-shot para garantizar consistencia y calidad.
"""
## Prompt de texto-texto (Gemini)

# Lista de SKUs (ejemplo)
skus = [
    {"producto": "Boxer Niña Pima Sueltos Talla 10", "talla": "10", "proveedor": "INDUSTRIA TEXTIL MUNDO MAGICO S.A.C.", "precio": 40},
    {"producto": "Medias Melcans Algodon Talla 12-20", "talla": "12-20", "proveedor": "INVERSIONES LENCIMODA S.A.C.", "precio": 40}
]

# Función para generar descripciones con Gemini
def generar_descripcion(sku):
    prompt = f"""
    Genera una descripción de producto atractiva para marketing.
    Input: Producto = {sku['producto']}, Talla = {sku['talla']}, Proveedor = {sku['proveedor']}, Precio por docena = {sku['precio']}.
    Few-shot example:
    Input: Producto = Boxer Niña Pima Sueltos Talla 10, Talla = 10, Proveedor = INDUSTRIA TEXTIL MUNDO MAGICO S.A.C., Precio = 40.
    Output: 'Boxer para niña de algodón Pima suelto, talla 10, cómodo y suave. Proveedor: INDUSTRIA TEXTIL MUNDO MAGICO S.A.C. Precio por docena: $40. Ideal para uso diario.'
    Mantén el output corto, en español, enfocado en beneficios.
    """
    try:
        response = modelo.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error al generar descripción para {sku['producto']}: {e}")
        return "Descripción no generada"

# Función para generar imágenes con Stability AI
def generar_imagen(descripcion):
    prompt = f"""
    A realistic studio photograph of a clothing product based on: {descripcion}.
    Style: high-resolution, vibrant colors, white background, suitable for children if applicable.
    Example: For 'Boxer Niña Pima Sueltos Talla 10': 'Photograph of loose Pima cotton boxer for girls, size 10, blue color, on a white background.'
    """
    try:
        # Generar imagen con Stability AI
        answers = stability_api.generate(
            prompt=prompt,
            samples=1,
            steps=30,
            cfg_scale=7.0,
            width=1024,
            height=1024,
            sampler=generation.SAMPLER_K_DPMPP_2M
        )
        for resp in answers:
            for artifact in resp.artifacts:
                if artifact.type == generation.ARTIFACT_IMAGE:
                    img = Image.open(BytesIO(artifact.binary))
                    img_filename = f"imagen_{descripcion[:30].replace(' ', '_')}.png"
                    img.save(img_filename)
                    return img_filename
        return "No se generó imagen"
    except Exception as e:
        print(f"Error al generar imagen: {e}")
        return "Error en generación de imagen"

# Generar descripciones e imágenes
print("Iniciando la generación de descripciones e imágenes...")
for sku in skus:
    # Generar descripción
    descripcion = generar_descripcion(sku)
    sku['descripcion'] = descripcion
    print(f"Descripción para {sku['producto']}: {descripcion}")

    # Generar imagen
    image_path = generar_imagen(descripcion)
    sku['imagen_path'] = image_path
    print(f"Imagen para {sku['producto']}: {image_path}")

# Exportar resultados a Excel
df = pd.DataFrame(skus)
df.to_excel('generated_skus_catalog.xlsx', index=False)
print("Resultados exportados a 'generated_skus_catalog.xlsx'.")

# Nota: Si estás en Google Colab, puedes descargar el archivo
try:
    from google.colab import files
    files.download('generated_skus_catalog.xlsx')
    for sku in skus:
        if os.path.exists(sku['imagen_path']):
            files.download(sku['imagen_path'])
except ImportError:
    print("No estás en Google Colab. Los archivos se guardaron localmente.")
