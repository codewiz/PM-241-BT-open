# Filed as https://bugzilla.redhat.com/show_bug.cgi?id=2498396

Summary: CIDFSubst/DroidSansFallback.ttf symlink points to a font with no
Latin glyphs; digits silently vanish from Japanese PDFs when printing

## Description

Fedora's ghostscript package replaces the upstream-bundled CID fallback
font Resource/CIDFSubst/DroidSansFallback.ttf with a symlink to
/usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf
(introduced with the fix for bug 1956246).

These two fonts are not equivalent. The copy bundled with upstream
Ghostscript contains Basic Latin (U+0020-U+007E):

    $ curl -sLO https://github.com/ArtifexSoftware/ghostpdl/raw/master/Resource/CIDFSubst/DroidSansFallback.ttf
    $ fc-query --format='%{charset}\n' DroidSansFallback.ttf | head -1
    20-7e ...

Fedora's DroidSansFallbackFull.ttf contains no Latin at all - U+0020 is
the only codepoint below U+0E3F (by design: Droid Sans Fallback was meant
to sit behind Droid Sans, which supplies the Latin range):

    $ fc-query --format='%{charset}\n' \
        /usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf | head -1
    20 e3f 1100-1112 ...

Consequence: whenever Ghostscript substitutes the fallback for a
non-embedded CJK font, every halfwidth Latin character (digits, ASCII
letters) is silently dropped from the output, while kanji/kana render
fine. No warning is emitted.

This is not a corner case. Japanese PDF generators routinely reference
MS-Gothic / MS-PGothic / MS-Mincho without embedding them. Real-world
impact: Japan Post "Clickpost" shipping labels printed through CUPS
(pdftopdf -> gstoraster -> gs) come out with the postal code, the
tracking number and all other digits missing - the label looks plausible
but is undeliverable. PDF viewers (poppler) substitute via fontconfig
and render correctly, so users only discover the damage on paper.

## Version-Release

ghostscript-10.07.1-1.fc45 (also affects released Fedora versions with
the same symlink)
google-droid-sans-fonts-20200215-*.fc45

## Steps to Reproduce

1. Save the attached msgothic-repro.pdf (a minimal PDF: one text line
   "0123456789 ABC <kanji> 0.5kg" set in non-embedded MS-Gothic with
   90ms-RKSJ-H encoding).
2. gs -dBATCH -dNOPAUSE -sDEVICE=png16m -r150 -o out.png msgothic-repro.pdf
3. Compare with: pdftoppm -r 150 -png msgothic-repro.pdf poppler

## Actual results

out.png shows only the kanji; "0123456789 ABC" and "0.5kg" are blank.
stderr shows the substitution:

    Loading CIDFont MS-Gothic substitute from
    /usr/share/ghostscript/Resource/CIDFSubst/DroidSansFallback.ttf

## Expected results

All characters render (as poppler does, and as upstream Ghostscript does
with its bundled DroidSansFallback.ttf).

## Additional info

- Verified that pointing the substitution at the upstream-bundled
  DroidSansFallback.ttf (via a cidfmap entry) renders the attached PDF
  correctly, so the regression is purely the choice of symlink target.
- Possible fixes: ship the upstream copy of the font instead of the
  symlink, or symlink to a font that covers both CJK and Basic Latin.
  Note that NotoSansCJK-VF.ttc (variable font) is not a good target:
  when mapped via cidfmap, Ghostscript renders garbled CJK glyphs from
  it. IPA Gothic (ipa-gothic-fonts, already packaged) works correctly.
- Workaround for affected users: install ipa-gothic-fonts and
  ipa-mincho-fonts and add cidfmap entries mapping the MS font family,
  e.g.:

      /MS-Gothic << /FileType /TrueType /Path (/usr/share/fonts/ipa-gothic-fonts/ipag.ttf) /SubfontID 0 /CSI [(Japan1) 6] >> ;

  (For CUPS printing the file can be dropped in /usr/share/cups/fonts/,
  which cups-filters passes to gs with -I.)
