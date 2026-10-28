# 🚀 REFERENCIA RÁPIDA - Cambio de Temporada

## 📅 ¿Cuándo cambiar?

| Mes | Temporada | Comando |
|-----|-----------|---------|
| Enero - Febrero | ACTIVOS | `./cambiar_temporada.sh activos` |
| **Marzo - Mayo** | **JUBILADOS** | `./cambiar_temporada.sh jubilados` |
| Junio - Septiembre | ACTIVOS | `./cambiar_temporada.sh activos` |
| Octubre - Diciembre | JUBILADOS | `./cambiar_temporada.sh jubilados` |

---

## ⚡ Comandos Esenciales

### 🔄 Cambiar de temporada
```bash
./cambiar_temporada.sh activos     # Para trabajadores activos
./cambiar_temporada.sh jubilados   # Para trabajadores jubilados
```

### 📍 Ver en qué temporada estoy
```bash
git branch
# La que tiene * es la actual
```

### 🔍 Ver diferencias entre sistemas
```bash
git diff temporada-activos temporada-jubilados
```

### 💾 Guardar cambios antes de cambiar temporada
```bash
git add .
git commit -m "Actualización de temporada actual"
```

---

## 🆘 Solución de Problemas

### Error: "Cambios sin guardar"
```bash
git add .
git commit -m "Guardado rápido"
./cambiar_temporada.sh [temporada]
```

### ¿Cómo sé en qué sistema estoy?

Busca en [templates/ficha_habitacion.html](templates/ficha_habitacion.html):

**JUBILADOS:** Solo muestra alerta de checkout si es el día
```html
{% if habitacion.es_checkout_hoy %}
  <!-- Mensaje de checkout -->
{% endif %}
```

**ACTIVOS:** Siempre muestra módulo de checkout anticipado
```html
{% if habitacion.es_checkout_hoy %}
  <!-- Mensaje de checkout -->
{% else %}
  <!-- Checkout anticipado -->
{% endif %}
```

### He perdido cambios
```bash
# Ver todos los commits
git log --oneline --all

# Recuperar un commit específico
git checkout <hash-del-commit>
```

---

## 📋 Checklist al Cambiar Temporada

- [ ] Guardar cambios actuales con `git commit`
- [ ] Hacer backup de `data/pasajeros.csv`
- [ ] Ejecutar `./cambiar_temporada.sh [temporada]`
- [ ] Cargar nuevo CSV de pasajeros
- [ ] Verificar que consumos estén en blanco
- [ ] Probar acceso al dashboard
- [ ] Verificar funcionalidades específicas de la temporada

---

## 🎯 Funcionalidades por Temporada

### Temporada ACTIVOS
| Funcionalidad | Estado |
|---------------|--------|
| Checkout anticipado | ✅ SÍ |
| Selector de pasajero | ❌ NO (opcional) |
| Voucher compartido | ✅ SÍ |
| Media pensión | ✅ SÍ |

### Temporada JUBILADOS
| Funcionalidad | Estado |
|---------------|--------|
| Checkout anticipado | ❌ NO |
| Selector de pasajero | ✅ SÍ |
| Voucher individual | ✅ SÍ |
| Pensión completa | ✅ SÍ |

---

## 📞 Ayuda Adicional

- **Guía completa:** [GUIA_CAMBIO_TEMPORADA.md](GUIA_CAMBIO_TEMPORADA.md)
- **Script de configuración inicial:** `./setup_temporadas.sh` (solo una vez)
- **Script de cambio:** `./cambiar_temporada.sh [activos|jubilados]`

---

**Última actualización:** 1 de Marzo 2026
