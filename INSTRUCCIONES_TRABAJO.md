# 📝 INSTRUCCIONES PARA INSTALAR EN LA PC DEL TRABAJO

## ✅ Cambios Subidos al Repositorio

Se han agregado los siguientes archivos al repositorio:
- `requirements.txt` - Dependencias del proyecto
- `run_hotel.sh` - Script automatizado de instalación y ejecución
- `HotelRecepcion.desktop` - Acceso directo para el escritorio
- `INSTALACION_UBUNTU.md` - Guía completa paso a paso
- `README.md` - Actualizado con referencias a la nueva guía

## 🚀 PASOS A SEGUIR EN LA PC DEL TRABAJO (Ubuntu nativo)

### 1. Clonar el Repositorio

```bash
cd /home/TU_USUARIO
git clone https://github.com/hotel23demayo/recepcion2026.git
cd recepcion2026
```

### 2. Instalar Dependencias del Sistema (si no están)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

### 3. Dar Permisos de Ejecución

```bash
chmod +x run_hotel.sh
chmod +x iniciar_recepcion.sh
sed -i 's/\r$//' run_hotel.sh
sed -i 's/\r$//' iniciar_recepcion.sh
```

### 4. Probar que Funciona

```bash
./run_hotel.sh
```

Esto debería:
- ✅ Crear automáticamente el entorno virtual `.venv`
- ✅ Instalar todas las dependencias (Flask, pandas, openpyxl)
- ✅ Abrir el navegador en http://localhost:5000
- ✅ Iniciar el servidor Flask

### 5. Crear Acceso Directo en el Escritorio

```bash
# Editar el archivo .desktop con tu nombre de usuario
nano HotelRecepcion.desktop
```

Reemplaza `USUARIO` con tu nombre de usuario real en ambas líneas:
```ini
Exec=/home/TU_USUARIO/recepcion2026/run_hotel.sh
Path=/home/TU_USUARIO/recepcion2026
```

Luego copia al escritorio:
```bash
cp HotelRecepcion.desktop ~/Escritorio/
# O si está en inglés:
cp HotelRecepcion.desktop ~/Desktop/

# Dar permisos
chmod +x ~/Escritorio/HotelRecepcion.desktop
```

Finalmente, **clic derecho** en el icono → **"Allow Launching"**

## 🎯 Resultado Final

Los usuarios NO técnicos podrán:
1. Hacer **doble clic** en el icono del escritorio
2. Ver la aplicación abrirse automáticamente en el navegador
3. Trabajar normalmente
4. Cerrar la terminal cuando terminen (Ctrl+C)

## 📋 Ventajas de Esta Solución

- ✅ **Portátil**: Funciona en WSL y Ubuntu nativo
- ✅ **Automático**: Crea venv e instala dependencias automáticamente
- ✅ **Amigable**: Los usuarios no tocan la terminal
- ✅ **Actualizable**: `git pull` y listo
- ✅ **Aislado**: No contamina Python del sistema

## 🔧 Solución de Problemas

Si algo no funciona, consulta el archivo **INSTALACION_UBUNTU.md** que tiene:
- Solución a errores comunes
- Verificaciones paso a paso
- Comandos de diagnóstico

---

**Repositorio**: https://github.com/hotel23demayo/recepcion2026
**Commit**: 7c9c87e - "feat: Añadir soporte completo para Ubuntu nativo"
