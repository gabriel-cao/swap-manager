# SwapManager

**Manual RAM/Swap Control for Linux via `process_madvise()`**

Authors: Gabriel Cao Di Marco & Daniela Cao Di Marco  
CONICET, Buenos Aires, Argentina  
License: MIT © 2026

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19187879.svg)](https://doi.org/10.5281/zenodo.19187879)

---

## What is it?

SwapManager is a Linux tool that allows users to manually decide which processes to send to swap and which to keep in RAM, in real time.

No equivalent tool exists for Linux — the kernel manages memory automatically and opaquely. SwapManager exposes that control to the user.

## Why does it exist?

During intensive ML sessions (Docker builds, neural network training, PyTorch compilation), several processes occupy RAM while swap remains underutilized. The kernel does not redistribute memory until under pressure. SwapManager allows manual RAM liberation without killing processes.

## Technology

Uses the `process_madvise()` syscall with `MADV_PAGEOUT` (kernel >= 5.4/5.10) to force process memory pages to swap, and `MADV_WILLNEED` to bring them back. No external dependencies — Python stdlib only.

## Requirements

- Linux kernel >= 5.4 (for `MADV_PAGEOUT`)
- Python 3.6+
- GTK3 (optional, for graphical interface)
- Root privileges recommended

## Usage

```bash
# Terminal/curses interface (recommended)
sudo python3 swap_manager.py

# Without sudo (own user processes only)
python3 swap_manager.py

# GTK3 graphical interface
sudo python3 swap_manager_gtk.py
```

## Controls (terminal version)

| Key     | Action                                      |
|---------|---------------------------------------------|
| ↑ ↓     | Navigate processes                          |
| SPACE   | Mark/unmark process                         |
| s       | Send to swap (current or marked)            |
| r       | Bring back to RAM (current or marked)       |
| l       | Lock — protect process in RAM               |
| a       | Select/deselect all                         |
| F5      | Refresh list                                |
| q       | Quit                                        |

## Citation

```bibtex
@software{caoDiMarco2026swapmanager,
  author    = {Cao Di Marco, Gabriel and Cao Di Marco, Daniela},
  title     = {SwapManager: manual RAM/swap control for Linux via process\_madvise()},
  year      = {2026},
  url       = {https://github.com/gabriel-cao/swap-manager},
  doi       = {10.5281/zenodo.19187879},
  version   = {1.0.0}
}
```

## Intellectual Property

Registered with the Dirección Nacional del Derecho de Autor (DNDA), Argentina, and U.S. Copyright Office.
