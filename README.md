# Open CUPS driver for the Phomemo PM-241-BT label printer

A free CUPS driver for the Phomemo PM-241-BT thermal label printer
(USB ID 2e3c:5750), with no proprietary binaries. It should be easy
to adapt to other printers that speak TSPL (Phomemo PM-241/PM-246
family, iDPRT, HPRT, TSC and many other cheap thermal label printers):
in most cases you only need a copy of the PPD with adjusted model
names and device ID.

Contents:

- `rastertotspl` - CUPS filter converting CUPS raster to TSPL.
  Pure Python 3, no dependencies outside the standard library.
- `PM-241-BT-open.ppd` - PPD for the PM-241-BT, wired to the filter
  above. Includes the printer's IEEE 1284 device ID so printer setup
  tools can auto-detect the right driver.
- `tspl-print.py` - standalone tool that prints an image directly to
  the device without CUPS (requires Pillow). Handy for debugging.

## Installation

```
sudo install -o root -g root -m 755 rastertotspl /usr/lib/cups/filter/
sudo install -o root -g root -m 644 PM-241-BT-open.ppd /usr/share/cups/model/
```

No CUPS restart is needed. Then add the printer via the CUPS web
interface (http://localhost:631/admin), your desktop's printer
settings, or:

```
sudo lpadmin -p PM241 -E -v "$(lpinfo -v | awk '/PM-241/ {print $2}')" \
     -m PM-241-BT-open.ppd
```

Set the default label size and darkness with `lpadmin -p PM241 -o
PageSize=w288h432 -o Darkness=8` or from the printer settings UI.

## Printing without CUPS

With permission to write to the USB printer device (group `lp`):

```
python3 tspl-print.py label.png -W 100 -H 150 -o /dev/usb/lp0
```

## How it works

TSPL is a simple, openly documented command language used by TSC and
many OEM label printers. The filter reads CUPS raster (as produced by
the standard CUPS/Ghostscript pipeline at 1 bit per pixel), prefixes
each page with `SIZE`/`GAP`/`DENSITY`/`SPEED` commands derived from
the job options, and wraps the bitmap in a `BITMAP` command. CUPS
raster and TSPL happen to use the same 1-bit row packing (MSB first,
0 = black), so pixel data passes through unmodified, except for
whitening the row padding bits.

## Driver auto-detection

The PM-241-BT reports a blank MFG field in its IEEE 1284 device ID.
Versions of python-cupshelpers (system-config-printer) up to at least
1.5.18 refuse to match any PPD whose device ID has an empty MFG, so
KDE/GNOME printer tools will not auto-select this driver until the fix
lands (see the bug report linked below); selecting the driver manually
works fine. The CUPS web interface is not affected.

## Authorship

This driver was 100% vibe coded by Claude (Anthropic's Claude Fable 5,
via Claude Code), from reverse-engineering the vendor driver package to
the CUPS integration and the autodetection debugging, under the
direction of Bernie Innocenti.

## License

Apache-2.0 for `rastertotspl` and `tspl-print.py` (see LICENSE),
matching CUPS and OpenPrinting so the code can be upstreamed.

`PM-241-BT-open.ppd` is mechanically derived from the PPD in the
vendor's freely distributed Linux driver package (which carries no
license statement): the proprietary filter reference was replaced, the
raster format switched to 1-bit, and the device ID added. PPDs are
essentially functional parameter tables; they are treated here as data,
not covered by the GPL.
