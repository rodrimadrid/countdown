### README para "Countdown Timer Video Generator"

---

## Descripción

Este script genera un video que muestra un temporizador de cuenta regresiva con una alarma al final. Utiliza bibliotecas como **Pillow**, **moviepy**, y **pydub** para crear los cuadros del temporizador, agregar un sonido de alarma y combinar todo en un video final.

---

## Requisitos del sistema

Antes de ejecutar el script, asegúrate de cumplir con los siguientes requisitos:

### Dependencias de Python
- Python 3.8 o superior.
- Las bibliotecas necesarias pueden instalarse ejecutando:
  ```bash
  pip install pillow moviepy pydub
  ```

### Dependencias del sistema
- **FFmpeg**: Necesario para procesar videos y audio. Instálalo según tu sistema operativo:
  - **Ubuntu/Debian**:  
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```
  - **Windows**: Descarga el ejecutable desde [FFmpeg.org](https://ffmpeg.org/download.html) y agrégalo al `PATH`.
  - **MacOS**:  
    ```bash
    brew install ffmpeg
    ```

---

## Configuración del entorno

1. **Clona o descarga este repositorio.**
   ```bash
   git clone https://github.com/usuario/timer-generator.git
   cd timer-generator
   ```

2. **Crea un entorno virtual (opcional pero recomendado).**
   ```bash
   python -m venv venv
   source venv/bin/activate   # En Linux/MacOS
   venv\Scripts\activate      # En Windows
   ```

3. **Instala las dependencias.**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verifica que FFmpeg esté instalado correctamente.**
   Ejecuta el siguiente comando:
   ```bash
   ffmpeg -version
   ```
   Esto debería mostrar la versión de FFmpeg instalada.

---

## Uso del script

El script se ejecuta desde la línea de comandos y acepta varios argumentos:

### Sintaxis básica
```bash
python timer_generator.py -m <minutos> -s <segundos> -a <archivo_alarma> -o <archivo_salida>
```

### Argumentos disponibles
- `-m` o `--minutes`: Minutos para el temporizador (por defecto `0`).
- `-s` o `--seconds`: Segundos para el temporizador (por defecto `0`).
- `-a` o `--alarm`: Archivo de audio para la alarma (por defecto `alarm.mp3`). Si no existe, se generará un sonido de alarma predeterminado.
- `-o` o `--outputfile`: Nombre del archivo de video generado (por defecto `timer.mp4`).

### Ejemplo
```bash
python timer_generator.py -m 1 -s 30 -a custom_alarm.wav -o my_timer.mp4
```

Este comando crea un temporizador de 1 minuto y 30 segundos con la alarma `custom_alarm.wav`, y guarda el video como `my_timer.mp4`.

---

## Notas importantes

1. **Fuentes predeterminadas**: El script usa la fuente `DejaVuSans-Bold.ttf` para renderizar el texto. Si no está disponible, se usará una fuente por defecto.

---

