# 🏁 Análisis de Sectores - Guía de Uso

## 🎯 ¿Qué hace el Análisis de Sectores?

El análisis de sectores te permite **identificar exactamente dónde pierdes o ganas tiempo** en cada vuelta comparándola con tu mejor vuelta. El circuito se divide en sectores configurables (5-20) y puedes ver:

- ✅ **Delta por sector**: Cuánto tiempo pierdes/ganas en cada parte del circuito
- ✅ **Deltas acumulados**: Cómo evoluciona tu tiempo vuelta a vuelta
- ✅ **Mapa 2D del circuito**: Visualización con sectores coloreados
- ✅ **Velocidades comparadas**: Gráfico punto a punto vs tu mejor vuelta
- ✅ **Estadísticas detalladas**: Velocidad media, mínima, uso de frenos

## 📊 Componentes de la Interfaz

### 1. **Mapa del Circuito 2D** (Arriba)
```
🟢 Verde  = Ganas tiempo en ese sector
🟡 Amarillo = Similar (~0.02s)
🔴 Rojo = Pierdes tiempo en ese sector
```

**Características interactivas:**
- 🖱️ **Click en sectores** → Selecciona y resalta en tabla
- 🎯 **Hover** → Muestra tooltip con delta, velocidad
- 📍 **Números** → Identificador de cada sector
- 🏁 **Bandera** → Línea de meta/salida

### 2. **Tabla de Deltas** (Medio)
Cada fila muestra un sector con:
- **Sector**: Número (1-10 por defecto)
- **Zona**: Porcentaje del circuito (0-10%, 10-20%, etc.)
- **Delta**: Tiempo perdido/ganado vs mejor vuelta
  - 🟢 Verde si ganas tiempo
  - 🔴 Rojo si pierdes tiempo
- **Acumulado**: Delta total hasta ese punto
- **Vel. Media**: Diferencia de velocidad promedio
- **Vel. Mín**: Velocidad mínima (útil para identificar frenadas)

### 3. **Gráfico de Barras** (Abajo izquierda)
Visualiza deltas de forma clara:
- Barras rojas: Pierdes tiempo
- Barras verdes: Ganas tiempo
- Altura = magnitud del delta

### 4. **Gráfico de Velocidad** (Abajo derecha)
Compara velocidades punto a punto:
- Línea verde: Tu mejor vuelta
- Línea roja: Vuelta analizada
- Eje X: Posición en circuito (0-100%)
- Eje Y: Velocidad (km/h)

## 🚀 Cómo Usar

### Paso 1: Cargar Telemetría
```
1. Click en "📂 Cargar Telemetría"
2. Selecciona archivo telemetry.json
3. Espera a que se procese
```

El sistema automáticamente:
- Detecta todas las vueltas
- Identifica la mejor vuelta (🏆)
- Genera el mapa del circuito
- Muestra delta de cada vuelta vs mejor

### Paso 2: Seleccionar Vuelta
```
1. En lista "Vueltas Disponibles"
2. Click en vuelta a analizar
3. Vueltas muestran: Nº, tiempo, delta vs mejor
```

**Ejemplo:**
```
Vuelta 1: 01:48.234 (+0.567s)
Vuelta 2: 01:47.667 (BEST)  🏆
Vuelta 3: 01:48.891 (+1.224s)
```

### Paso 3: Configurar Sectores
```
1. En "Análisis por Sectores"
2. Ajusta "Dividir vuelta en: X sectores"
   - Menos sectores (5) = visión general
   - Más sectores (20) = análisis detallado
```

**Recomendaciones:**
- **10 sectores** → Ideal para análisis general
- **15-20 sectores** → Para circuitos largos o análisis fino
- **5 sectores** → Vista rápida de grandes zonas

### Paso 4: Analizar
```
1. Click "🔍 Analizar vs Mejor Vuelta"
2. Observa mapa, tabla y gráficos actualizarse
```

## 💡 Casos de Uso Prácticos

### Caso 1: Identificar Curva Problemática

**Síntoma:** Pierdes mucho tiempo en sector 5

**Lectura de datos:**
```
Sector 5 (40-50%):
- Delta: +0.156s  🔴
- Vel. Media: -7.2 km/h
- Vel. Mín: 82 km/h vs 95 km/h en mejor vuelta
```

**Diagnóstico:**
- Estás frenando MUCHO más fuerte (82 vs 95 km/h)
- Pierdes 7.2 km/h de velocidad media
- Total: 0.156s perdidos solo en esta curva

**Solución:** Frenar más tarde o menos fuerte

---

### Caso 2: Curva Bien Ejecutada

**Síntoma:** Ganas tiempo en sector 3

**Lectura:**
```
Sector 3 (20-30%):
- Delta: -0.089s  🟢
- Vel. Media: +4.3 km/h
- Vel. Mín: 145 km/h vs 138 km/h
```

**Diagnóstico:**
- Mantienes más velocidad mínima (+7 km/h)
- Resultado: ganas casi 0.1s

**Aplicación:** Replicar esta técnica en otras curvas similares

---

### Caso 3: Deltas Acumulados

**Escenario:**
```
S1: +0.034s → Pierdes un poco
S2: +0.098s → Sigue perdiendo (+0.064s más)
S3: +0.045s → Recuperas tiempo (-0.053s)
S4: +0.156s → Gran pérdida (+0.111s)
```

**Conclusión:**
- Sector 4 es el problema principal
- Sector 3 va bien (recuperas)
- Trabaja en sector 4 primero

---

### Caso 4: Usar Gráfico de Velocidad

**Situación:** Mapa muestra sector 7 en rojo

**En gráfico de velocidad:**
```
Posición 60-70%:
- Línea verde (mejor): mantiene 180-200 km/h
- Línea roja (actual): baja a 160 km/h
```

**Identificación:**
- Levantaste el pie del acelerador muy pronto
- O frenaste anticipadamente para siguiente curva

---

## 🎓 Tips de Análisis Avanzado

### 1. **Patrón de Frenada**
Si `Vel. Mín` es muy baja comparado con mejor vuelta:
→ Frenas demasiado fuerte o muy temprano

### 2. **Patrón de Aceleración**
Si `Vel. Media` es baja pero `Vel. Mín` es similar:
→ Sales de la curva más lento (aceleras tarde o suave)

### 3. **Deltas Acumulados Crecientes**
Si acumulado crece continuamente:
→ Problema de ritmo general, no una curva específica

### 4. **Deltas Alternantes (+, -, +, -)**
→ Inconsistencia, trabaja en repetibilidad

### 5. **Click en Sectores del Mapa**
- Haz click en sector problemático
- Se resalta en tabla automáticamente
- Revisa estadísticas detalladas

## 📋 Ejemplo Completo de Análisis

**Objetivo:** Mejorar Vuelta 5 que tiene +0.845s vs mejor

### Paso 1: Ver Mapa General
```
Observo: Sectores 4, 7 y 9 en rojo intenso
```

### Paso 2: Revisar Tabla
```
S4 (30-40%): +0.234s  🔴 ← MAYOR PÉRDIDA
S7 (60-70%): +0.187s  🔴
S9 (80-90%): +0.156s  🔴
```

### Paso 3: Analizar S4 (peor sector)
```
Vel. Media: -12.4 km/h  ← MUY LENTO
Vel. Mín: 67 km/h vs 89 km/h  ← FRENO DEMASIADO
```

### Paso 4: Ver Gráfico de Velocidad
```
Posición 30-40%:
- Mejor vuelta: baja a 89 km/h, sube rápido
- Mi vuelta: baja a 67 km/h, sube lento
```

### Conclusión y Acción
```
Problema: Freno demasiado en curva del 30-40%
Solución:
1. Frenar más tarde
2. Frenar menos fuerte
3. Acelerar antes saliendo de curva
```

### Siguiente Sesión
```
Enfoco en mejorar S4
Si mejoro 0.234s ahí, ya estoy a solo +0.611s de mi mejor
```

## 🔧 Configuración Óptima

### Para Análisis Rápido
- **Sectores:** 5-8
- **Objetivo:** Visión general de zonas

### Para Análisis Detallado
- **Sectores:** 15-20
- **Objetivo:** Identificar curvas específicas

### Para Circuitos Largos (>5km)
- **Sectores:** 15-20
- Cada sector = ~300-400m

### Para Circuitos Cortos (<3km)
- **Sectores:** 8-12
- Evitar demasiada granularidad

## 🎯 Objetivos de Mejora

### Nivel Principiante
```
Meta: Reducir deltas >0.15s a <0.10s
Enfoque: 2-3 sectores más problemáticos
```

### Nivel Intermedio
```
Meta: Todos los sectores <0.08s
Enfoque: Consistencia en toda la vuelta
```

### Nivel Avanzado
```
Meta: Optimizar sectores con delta <0.05s
Enfoque: Ajustes finos de trazada
```

## ❓ Preguntas Frecuentes

**P: ¿Qué número de sectores es mejor?**
R: 10 sectores es ideal para empezar. Sube a 15-20 si quieres más detalle.

**P: ¿Por qué algunos sectores están vacíos?**
R: Si la vuelta no tiene datos en esa zona (pit, abandono), aparece vacío.

**P: ¿Cómo sé qué sector es qué curva?**
R: Usa el mapa 2D y los números. Con práctica reconocerás patrones.

**P: ¿Puedo comparar dos vueltas que no sean vs la mejor?**
R: Actualmente solo vs mejor vuelta. Próximamente comparación libre.

**P: ¿El mapa es preciso?**
R: Es aproximado (basado en normalized_position). Suficiente para análisis.

---

## 🏆 Workflow de Mejora Continua

```
1. Grabar sesión de práctica
   ↓
2. Cargar en Análisis de Sectores
   ↓
3. Identificar 2-3 sectores problemáticos
   ↓
4. Anotar qué hacer diferente
   ↓
5. Próxima sesión: enfocarse en esos sectores
   ↓
6. Repetir hasta dominar circuito
```

¡Ahora tienes todas las herramientas para mejorar sistemáticamente tus tiempos por vuelta! 🚀
