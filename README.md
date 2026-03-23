# SwapManager

**Control Manual de RAM y Swap para Linux**
Entelequia AI Framework — Herramienta del Sistema

Autor: Gabriel F. Cao Di Marco
Co-creadora: Daniela Cao Di Marco
Licencia: MIT © 2026

---

## ¿Qué es?

SwapManager es una herramienta de terminal que permite decidir manualmente
qué procesos enviar a swap y cuáles proteger en RAM, en tiempo real.

No existe nada equivalente para Linux — el kernel gestiona esto automáticamente
y de forma opaca. SwapManager expone ese control al usuario.

## ¿Por qué existe?

Durante sesiones intensas de ML (builds Docker, entrenamiento Vid2Avatar,
compilación de pytorch3d), varios procesos acaparan RAM mientras el swap
queda desaprovechado. El kernel no redistribuye hasta estar bajo presión.
SwapManager permite liberar RAM manualmente, sin matar procesos.

## Tecnología

Usa `process_madvise()` syscall con `MADV_PAGEOUT` (kernel >= 5.4/5.10)
para forzar páginas de memoria de un proceso a swap, y `MADV_WILLNEED`
para traerlas de vuelta. Sin dependencias externas — solo Python stdlib.

## Uso

```bash
# Con sudo (recomendado — opera sobre cualquier proceso)
sudo python3 swap_manager.py

# Sin sudo (solo procesos del propio usuario)
python3 swap_manager.py
```

## Controles

| Tecla   | Acción                                      |
|---------|---------------------------------------------|
| ↑ ↓     | Navegar procesos                            |
| SPACE   | Marcar/desmarcar proceso                    |
| s       | Enviar a swap (proceso actual o marcados)   |
| r       | Traer a RAM (proceso actual o marcados)     |
| l       | Lock — proteger proceso en RAM              |
| a       | Seleccionar/deseleccionar todos             |
| F5      | Actualizar lista                            |
| q       | Salir                                       |

## Registro de Propiedad Intelectual

Pendiente registro en Dirección Nacional del Derecho de Autor (Argentina)
y U.S. Copyright Office, junto con Entelequia AI Framework.
