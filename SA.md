# Recocido Simulado (SA) – Descripción técnica

Este documento resume la metaheurística de recocido simulado utilizada en el proyecto de asignación de puestos híbridos. El algoritmo pertenece a la **Entrega 1 / 2** y opera sobre la representación estándar del problema (`assignment[día][empleado] = escritorio/None`).

## 1. Operador de vecindad: `generar_vecino_swap`

1. Seleccionar un día aleatorio de la instancia.
2. Tomar dos empleados asignados ese día (si hay al menos dos).
3. Intercambiar los escritorios de ambos empleados.

Matemáticamente, si la solución actual es \(S\) y \(N\) es el operador de vecindad, el vecino se expresa como:
\[
S' = N(S)
\]
donde \(N\) realiza un swap entre dos empleados dentro del mismo día.

## 2. Función `simulated_annealing(...)`

Parámetros principales:

- \(T_\text{inicial}\): temperatura inicial.
- \(T_\text{final}\): temperatura mínima o criterio de parada.
- \(\alpha\): factor de enfriamiento (0 < \(\alpha\) < 1) para el esquema geométrico.
- `iter_por_temp`: número de iteraciones por cada temperatura.

### Flujo general

1. **Inicialización:** partir de la solución constructiva \(S_0\) y evaluar \(f(S_0)\). Guardar también la mejor solución \(S^*\).
2. **Bucle principal:** mientras \(T > T_\text{final}\):
   - Repetir `iter_por_temp` veces:
     - Generar un vecino \(S'\) con `generar_vecino_swap`.
     - Calcular \(\Delta = f(S') - f(S)\).
     - Si \(\Delta > 0\), aceptar el vecino.  
       Si \(\Delta \le 0\), aceptar con probabilidad \(P = e^{\Delta/T}\) para favorecer la exploración.
     - Actualizar \(S^*\) si se obtiene una solución mejor.
   - Reducir la temperatura: \(T \leftarrow \alpha \cdot T\).
3. **Parada:** cuando \(T \le T_\text{final}\) se devuelve la mejor solución encontrada \(S^*\).

### Pseudocódigo
```
S  = solucion_inicial
best = S
T  = T_inicial

while T > T_final:
    for i in range(iter_por_temp):
        S' = generar_vecino(S)
        Δ  = evaluar(S') - evaluar(S)
        if Δ > 0 or random() < exp(Δ / T):
            S = S'
            if evaluar(S) > evaluar(best):
                best = S
    T = α * T

return best
```

## 3. Conclusión

El esquema mantiene un balance entre **exploración** (temperaturas altas aceptan soluciones peores con mayor probabilidad) y **explotación** (temperaturas bajas privilegian mejoras). El operador swap respeta la factibilidad del problema y, en combinación con la evaluación lexicográfica `(C1, C2, C3)`, permite refinar la solución constructiva inicial para satisfacer más preferencias y mejorar la cohesión por zonas.
