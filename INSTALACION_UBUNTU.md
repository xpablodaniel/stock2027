# 🐧 Guía de Instalación - Ubuntu Nativo

## 📋 Requisitos Previos

- Ubuntu 20.04 o superior
- Python 3.8 o superior
- Git instalado

## 🚀 Instalación Paso a Paso

### 1. Clonar el Repositorio

```bash
cd /home/TU_USUARIO
git clone https://github.com/hotel23demayo/recepcion2026.git
cd recepcion2026
```

### 2. Instalar Python y Dependencias del Sistema

```bash
# Actualizar repositorios
sudo apt update

# Instalar Python 3 y herramientas
sudo apt install python3 python3-pip python3-venv -y
```

### 3. Dar Permisos de Ejecución al Script

```bash
chmod +x run_hotel.sh
chmod +x iniciar_recepcion.sh
```

**IMPORTANTE**: Si clonaste desde Windows/WSL, limpia el formato de línea:
```bash
sed -i 's/\r$//' run_hotel.sh
sed -i 's/\r$//' iniciar_recepcion.sh
```

### 4. Crear Acceso Directo en el Escritorio

#### Opción A: Usando el archivo .desktop (Recomendado)

1. Edita el archivo `HotelRecepcion.desktop`:
   ```bash
   nano HotelRecepcion.desktop
   ```

2. Reemplaza `USUARIO` con tu nombre de usuario de Ubuntu:
   ```ini
   Exec=/home/TU_USUARIO/recepcion2026/run_hotel.sh
   Path=/home/TU_USUARIO/recepcion2026
   ```

3. Copia el archivo al escritorio:
   ```bash
   cp HotelRecepcion.desktop ~/Escritorio/
   # O en inglés:
   cp HotelRecepcion.desktop ~/Desktop/
   ```

4. Haz el archivo ejecutable:
   ```bash
   chmod +x ~/Escritorio/HotelRecepcion.desktop
   # O:
   chmod +x ~/Desktop/HotelRecepcion.desktop
   ```

5. **Clic derecho** sobre el icono en el escritorio → **"Allow Launching"** o **"Permitir lanzar"**

#### Opción B: Desde Terminal (Para probar primero)

```bash
cd /home/TU_USUARIO/recepcion2026
./run_hotel.sh
```

## ✅ Verificación de la Instalación

1. Al ejecutar el script, deberías ver:
   - Creación del entorno virtual (primera vez)
   - Instalación de dependencias
   - Apertura automática del navegador
   - Servidor Flask corriendo en http://localhost:5000

2. Si algo falla, revisa:
   - Que Python 3 esté instalado: `python3 --version`
   - Que el script tenga permisos: `ls -l run_hotel.sh`
   - Los logs en la terminal

## 🔧 Solución de Problemas Comunes

### Error: "python3-venv not found"
```bash
sudo apt install python3-venv
```

### Error: "bad interpreter"
```bash
sed -i 's/\r$//' run_hotel.sh
```

### El navegador no se abre automáticamente
- Verifica que `xdg-open` funcione: `which xdg-open`
- Abre manualmente: http://localhost:5000

### Error de permisos en .venv
```bash
rm -rf .venv
./run_hotel.sh
```

## 📱 Uso para Usuarios No Técnicos

Una vez configurado, los usuarios solo necesitan:

1. **Doble clic** en el icono "Sistema Recepción Hotel 2026" del escritorio
2. Esperar a que se abra el navegador automáticamente
3. Usar la aplicación web
4. Cuando terminen, cerrar la ventana de terminal (Ctrl+C)

## 🔄 Actualizar el Sistema

Para obtener la última versión del repositorio:

```bash
cd /home/TU_USUARIO/recepcion2026
git pull origin main
```

Las dependencias se actualizarán automáticamente la próxima vez que ejecutes el script.

## 📞 Soporte

Para cualquier problema, contacta al administrador del sistema.
