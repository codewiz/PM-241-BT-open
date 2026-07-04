# Draft issue for github.com/OpenPrinting/system-config-printer

Title: cupshelpers: devices with an empty MFG in their IEEE 1284 device
ID can never match any PPD

## Summary

`PPDs._init_ids()` in `cupshelpers/ppds.py` skips every PPD whose
`ppd-device-id` has an empty MFG field, while
`getPPDNamesFromDeviceID()` happily looks up the device's (also empty)
MFG in that same table. As a result, a printer that reports a blank MFG
in its IEEE 1284 device ID can never get an exact driver match, even
when a PPD carrying its verbatim device ID is installed. The name-based
fallbacks do not recover: with MFG empty, `ppdMakeModelSplit()` is
applied to the MDL string, and for single-token models like
`PM-241-BT` it returns the whole string as make and an empty model, so
the lookup dies there too and the matcher falls back to textonly.ppd.

Blank MFG fields are common on inexpensive thermal label printers.
Real-world example, a Phomemo PM-241-BT (USB ID 2e3c:5750):

    MFG: ;CMD:XPP,XL;MDL:PM-241-BT;CLS:PRINTER;DES:PM-241-BT;

This affects every frontend that uses cupshelpers for driver
recommendation: system-config-printer itself, and KDE's and GNOME's
printer settings via scp-dbus-service GetBestDrivers.

## Reproduction

1. Install a PPD whose *1284DeviceID contains the device ID above
   (with the blank MFG copied verbatim from the printer).
2. Ask for the best drivers:

    gdbus call --session \
      --dest org.fedoraproject.Config.Printing \
      --object-path /org/fedoraproject/Config/Printing \
      --method org.fedoraproject.Config.Printing.GetBestDrivers \
      'MFG: ;CMD:XPP,XL;MDL:PM-241-BT;CLS:PRINTER;DES:PM-241-BT;' \
      'PM-241-BT' 'usb:///PM-241-BT?serial=XXX'

Result: `[('drv:///cupsfilters.drv/textonly.ppd', 'none')]`.
Expected: the installed PPD with fit `exact-cmd` (its CMD field also
matches).

## Fix

Index blank-MFG PPDs under the empty make instead of dropping them.
The exact-match lookup already searches `ids[mfg][mdl]` with the
device's parsed (empty) MFG, so the match becomes symmetric. MDL is
still required to be non-empty. With this patch the device above gets
its PPD back with fit `exact-cmd`.

```diff
--- a/cupshelpers/ppds.py
+++ b/cupshelpers/ppds.py
@@ -1157,13 +1157,10 @@ class PPDs:
             lmfg = id_dict['MFG'].lower ()
             lmdl = id_dict['MDL'].lower ()

-            bad = False
-            if len (lmfg) == 0:
-                bad = True
-            if len (lmdl) == 0:
-                bad = True
-            if bad:
+            # A blank MFG is legal (some devices report one); index the
+            # PPD under the empty make so blank-MFG device IDs can match.
+            if len (lmdl) == 0:
                 continue

             if lmfg not in ids:
```

Tested on Fedora 45 with system-config-printer 1.5.18: after the
patch, system-config-printer, KDE printer settings and the D-Bus call
above all auto-select the correct PPD for this printer.
