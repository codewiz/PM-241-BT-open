# PM-241-BT-open - project context

Open CUPS driver for the Phomemo PM-241-BT thermal label printer
(USB 2e3c:5750, TSPL command language). Written from scratch 2026-07-04/05
to replace the proprietary vendor driver; the vendor package it replaces
lives at ~/LabelPrinter-2.3.1.001 (its unstripped x86_64/rastertolabeltspl
binary is a useful reference for TSPL command strings - read it with
`strings`, never run it).

## Architecture

- `rastertotspl`: CUPS filter, pure Python 3 stdlib. The PPD asks
  Ghostscript for 1-bit grayscale raster (cupsBitsPerColor 1,
  cupsColorSpace 0/W); CUPS raster rows are then already in TSPL BITMAP
  format (MSB-first, 0=black), so pixel data passes through unmodified,
  except that row padding bits beyond cupsWidth arrive as 0 (= black!)
  and must be forced to 1. Raster header offsets that matter:
  HWResolution=276, PageSize=352, cupsWidth=372, cupsHeight=376,
  cupsBitsPerPixel=388, cupsBytesPerLine=392. v1 header is 420 bytes,
  v2/v3 are 1796; sync word RaS2/2SaR/RaS3/3SaR decides endianness and
  compression. NOTE: the v2 (compressed) decode path has never been
  exercised - gstoraster on Fedora emits uncompressed v3.
- `PM-241-BT-open.ppd`: derived from the vendor PPD (ppds/PM-241-BT.ppd
  in the vendor package) by replacing the cupsFilter line, switching the
  Resolution entry to 1-bit, deleting cupsLanguages, setting Manufacturer
  "Phomemo", 8.3 PCFileName, LF line endings, and adding *1284DeviceID.
  The device ID's blank MFG ("MFG: ;...") is copied verbatim from the
  printer and is LOAD-BEARING for auto-detection - do not "fix" it.
- `tspl-print.py`: standalone image-to-TSPL tool (needs Pillow), talks
  straight to /dev/usb/lp0. Good for debugging without CUPS.
- Job options wired through the filter: Darkness -> DENSITY,
  zePrintRate -> SPEED, zeMediaTracking Gap/BLine/Continuous ->
  GAP/BLINE, GapHeight/GapOffset. TSPL lines end in CRLF per spec.

## Testing without a printer

    gs -q -dBATCH -dNOPAUSE -sDEVICE=cups -r203x203 \
       -dDEVICEWIDTHPOINTS=288 -dDEVICEHEIGHTPOINTS=432 \
       -dcupsBitsPerColor=1 -dcupsColorSpace=0 -dPDFFitPage \
       -sOutputFile=test.ras test.pdf
    ./rastertotspl 1 u t 1 'Darkness=8' test.ras > out.bin

Then regex out the BITMAP payload and rebuild a PNG with PIL
Image.frombytes('1', ...) to eyeball it. Full chain test:
`cupsfilter -p PM-241-BT-open.ppd -m application/vnd.cups-raster job.pdf`.

## Driver auto-detection (KDE/GNOME)

The printer reports a blank MFG in its IEEE 1284 device ID. cupshelpers
(system-config-printer) up to 1.5.18 drops blank-MFG PPDs in
PPDs._init_ids, so GetBestDrivers can never match - reported with patch
at https://github.com/OpenPrinting/system-config-printer/issues/445.
Bernie's machine has /usr/lib/python3.15/site-packages/cupshelpers/ppds.py
patched locally; ANY dnf update of system-config-printer-libs reverts it.
If auto-detection breaks again, re-check that file and issue 445.
Debug with:

    gdbus call --session --dest org.fedoraproject.Config.Printing \
      --object-path /org/fedoraproject/Config/Printing \
      --method org.fedoraproject.Config.Printing.GetBestDrivers \
      'MFG: ;CMD:XPP,XL;MDL:PM-241-BT;CLS:PRINTER;DES:PM-241-BT;' \
      'PM-241-BT' 'usb:///PM-241-BT?serial=X'

KDE fetches the FULL unfiltered PPD list over CUPS-Get-PPDs and matches
client-side via that D-Bus service; CUPS-side lpinfo tests don't
reproduce KDE behavior. CUPS logs go to the journal on Fedora
(journalctl -u cups), not /var/log/cups.

## Japanese PDFs: missing digits/romaji (fixed 2026-07-09)

Clickpost labels (and many JP PDFs) reference MS-Gothic/MS-Mincho
without embedding them. Ghostscript's fontconfig fallback substitutes
Droid Sans Fallback, which silently drops ALL halfwidth glyphs (digits,
romaji) from 90ms-RKSJ-encoded CID fonts - a printed label loses the
postcode and tracking number while kanji look fine. Poppler substitutes
correctly, so PDF viewers show nothing wrong. Affects every CUPS queue
that rasterizes via gstoraster/gs, not just this driver.

Fix on Bernie's machine: /usr/share/cups/fonts/cidfmap maps the MS font
families to ipa-gothic-fonts/ipa-mincho-fonts (both installed via dnf).
That path works because cups-filters invokes gs with
-I/usr/share/cups/fonts, and no rpm owns the directory, so it survives
updates. Env-based approaches (GS_LIB, cupsd SetEnv) do NOT work:
cfFilterGhostscript execs gs with a scrubbed environment. Verify with
cupsfilter + rastertotspl + PIL decode (see Testing above); a known-good
sample is ~/Desktop/628668669145.pdf.

Root cause is Fedora packaging: ghostscript symlinks
Resource/CIDFSubst/DroidSansFallback.ttf to DroidSansFallbackFull.ttf,
which has NO Latin glyphs (upstream's bundled copy does). Reported
2026-07-09: https://bugzilla.redhat.com/show_bug.cgi?id=2498396
(fedora-ghostscript-issue.md, minimal repro msgothic-repro.pdf).
If Fedora fixes it, the local cidfmap can stay (harmless) or go.

## Release / CI

- Remotes: github (codewiz/PM-241-BT-open, gh authed) and gitlab
  (berniecodewiz/PM-241-BT-open - NOT gitlab.com/codewiz, that is
  someone else). Push main to both.
- GitHub Actions builds rpm (fedora:latest container) + deb
  (ubuntu-latest) on every push; a `v*` tag additionally creates the
  GitHub release with rpm/srpm/deb attached. GitLab CI mirrors the
  builds; GitLab releases are created manually with `glab release
  create` uploading the GitHub-built assets.
- Gotchas already hit: deb job needs build-essential explicitly;
  debian/rules must be executable; newer CUPS makes cupstestppd fail on
  mere warnings, so CI uses `-W all`.
- License is Apache-2.0 (deliberately matching CUPS/OpenPrinting for
  upstreamability - do not add GPL code).
- v1.0 released 2026-07-05; Bernie's machine runs the rpm
  (pm-241-bt-open owns the filter and PPD system-wide now).
