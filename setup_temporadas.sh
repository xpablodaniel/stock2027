#!/bin/bash

# 🏗️ Script de Configuración Inicial del Sistema de Temporadas
# Este script se ejecuta UNA SOLA VEZ para configurar los branches

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  🏗️  CONFIGURACIÓN INICIAL - SISTEMA DE TEMPORADAS       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar que estamos en un repositorio Git
if [ ! -d .git ]; then
    echo -e "${RED}❌ Error: No estás en un repositorio Git${NC}"
    exit 1
fi

BRANCH_ACTUAL=$(git branch --show-current)
echo -e "${BLUE}📍 Branch actual:${NC} ${YELLOW}$BRANCH_ACTUAL${NC}"
echo ""

# Información sobre el proceso
echo -e "${YELLOW}Este script configurará el sistema para manejar DOS temporadas:${NC}"
echo ""
echo -e "  ${GREEN}1. temporada-jubilados${NC} (Estado actual)"
echo -e "     • Sin checkout anticipado"
echo -e "     • Consumos individuales por pasajero"
echo -e "     • Traslado incluido"
echo ""
echo -e "  ${GREEN}2. temporada-activos${NC} (Se restaurará después)"
echo -e "     • Con checkout anticipado"
echo -e "     • Voucher compartido por sede"
echo -e "     • Sin traslado incluido"
echo ""
echo -e "${YELLOW}¿Deseas continuar con la configuración?${NC}"
read -p "Presiona Enter para continuar o Ctrl+C para cancelar..."

# Paso 1: Guardar cambios actuales
echo ""
echo -e "${BLUE}📦 Paso 1: Guardando cambios actuales...${NC}"
git add .
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
git commit -m "💾 Estado actual del sistema - Configuración de temporadas - $TIMESTAMP" 2>/dev/null || echo "No hay cambios nuevos"
echo -e "${GREEN}✅ Cambios guardados${NC}"

# Paso 2: Crear branch temporada-jubilados
echo ""
echo -e "${BLUE}📦 Paso 2: Creando branch 'temporada-jubilados'...${NC}"

if git show-ref --verify --quiet "refs/heads/temporada-jubilados"; then
    echo -e "${YELLOW}⚠️  El branch temporada-jubilados ya existe${NC}"
    git checkout temporada-jubilados
else
    git checkout -b temporada-jubilados
    git commit --allow-empty -m "✅ Sistema configurado para temporada JUBILADOS

Características implementadas:
- Consumos individuales por pasajero
- Detección de vouchers separados
- Sin checkout anticipado (traslado incluido)
- Pensión completa
- Selector de pasajero en formulario de consumos
- Totales separados por pasajero

Período: Marzo-Mayo, Octubre-Diciembre"
    echo -e "${GREEN}✅ Branch temporada-jubilados creado${NC}"
fi

# Paso 3: Información sobre temporada-activos
echo ""
echo -e "${BLUE}📦 Paso 3: Configuración de branch 'temporada-activos'...${NC}"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} El branch ${GREEN}temporada-activos${NC} debe crearse cuando:"
echo -e "  1. Termine el período de jubilados (Mayo o Diciembre)"
echo -e "  2. Necesites restaurar las funcionalidades de trabajadores activos"
echo ""
echo -e "${YELLOW}Para crear temporada-activos necesitarás:${NC}"
echo -e "  • Restaurar el módulo de checkout anticipado en templates/ficha_habitacion.html"
echo -e "  • Restaurar las alertas de checkout anticipado en templates/checkout.html"
echo -e "  • Opcional: Simplificar consumos (sin selector de pasajero individual)"
echo ""
echo -e "${YELLOW}¿Quieres que te ayude a crear el branch temporada-activos AHORA?${NC}"
echo -e "${YELLOW}(Esto revertirá los cambios de jubilados temporalmente)${NC}"
read -p "Escribe 'SI' para crear ahora, o Enter para omitir: " RESPUESTA

if [ "$RESPUESTA" = "SI" ] || [ "$RESPUESTA" = "si" ]; then
    echo ""
    echo -e "${BLUE}🔧 Creando branch temporada-activos...${NC}"
    
    # Volver a main o commit anterior
    git checkout main 2>/dev/null || git checkout master 2>/dev/null
    
    # Buscar commit antes de eliminar checkout anticipado
    echo -e "${BLUE}🔍 Buscando commits anteriores...${NC}"
    git log --oneline --all -10
    
    echo ""
    echo -e "${YELLOW}Revisa los commits anteriores.${NC}"
    echo -e "${YELLOW}¿Cuál es el hash del commit ANTES de eliminar checkout anticipado?${NC}"
    read -p "Ingresa el hash (primeros 7 caracteres) o Enter para usar el actual: " COMMIT_HASH
    
    if [ -n "$COMMIT_HASH" ]; then
        git checkout "$COMMIT_HASH"
    fi
    
    git checkout -b temporada-activos
    git commit --allow-empty -m "✅ Sistema configurado para temporada ACTIVOS

Características implementadas:
- Checkout anticipado disponible
- Voucher compartido por sede
- Media pensión
- Alertas de checkout anticipado
- Sin consumos individuales obligatorios

Período: Enero-Febrero, Junio-Septiembre"
    
    echo -e "${GREEN}✅ Branch temporada-activos creado${NC}"
    
    # Volver a temporada-jubilados
    git checkout temporada-jubilados
else
    echo -e "${YELLOW}⏭️  Omitido. Crearás temporada-activos cuando lo necesites.${NC}"
fi

# Resumen final
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ CONFIGURACIÓN COMPLETADA                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Estado actual:${NC}"
git branch -a
echo ""
echo -e "${BLUE}📝 Próximos pasos:${NC}"
echo ""
echo -e "   ${GREEN}Para cambiar entre temporadas, usa:${NC}"
echo -e "   ./cambiar_temporada.sh jubilados"
echo -e "   ./cambiar_temporada.sh activos"
echo ""
echo -e "   ${GREEN}Para ver diferencias entre temporadas:${NC}"
echo -e "   git diff temporada-activos temporada-jubilados"
echo ""
echo -e "   ${GREEN}Para ver en qué branch estás:${NC}"
echo -e "   git branch"
echo ""
echo -e "${YELLOW}📖 Consulta GUIA_CAMBIO_TEMPORADA.md para más información${NC}"
echo ""
