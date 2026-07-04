Name:           pm-241-bt-open
Version:        1.0
Release:        1%{?dist}
Summary:        Open CUPS driver for Phomemo PM-241-BT TSPL label printers
License:        Apache-2.0
URL:            https://github.com/codewiz/PM-241-BT-open
Source0:        %{url}/archive/v%{version}/PM-241-BT-open-%{version}.tar.gz
BuildArch:      noarch
Requires:       cups
Requires:       python3

%description
CUPS filter and PPD for the Phomemo PM-241-BT thermal label printer
and other TSPL-based label printers. No proprietary binaries.

%prep
%autosetup -n PM-241-BT-open-%{version}

%install
install -D -m 755 rastertotspl %{buildroot}%{_prefix}/lib/cups/filter/rastertotspl
install -D -m 644 PM-241-BT-open.ppd %{buildroot}%{_datadir}/cups/model/PM-241-BT-open.ppd

%files
%license LICENSE
%doc README.md
%{_prefix}/lib/cups/filter/rastertotspl
%{_datadir}/cups/model/PM-241-BT-open.ppd

%changelog
* Sat Jul 04 2026 Bernie Innocenti <bernie@codewiz.org> - 1.0-1
- Initial package
