%define name ciecplib
%define version 0.4.2
%define release 1

# -- metadata ---------------

BuildArch: noarch
Group:     Development/Libraries
License:   GPL-3.0-or-later
Name:      %{name}
Packager:  Duncan Macleod <duncan.macleod@ligo.org>
Prefix:    %{_prefix}
Release:   %{release}%{?dist}
Source0:   %pypi_source
Summary:   A python client for SAML ECP authentication
Url:       https://github.com/duncanmmacleod/ciecplib
Vendor:    Duncan Macleod <duncan.macleod@ligo.org>
Version:   %{version}

# -- build requirements -----

# macros
BuildRequires: python-srpm-macros
BuildRequires: python-rpm-macros
BuildRequires: python3-rpm-macros

# build
BuildRequires: python3
BuildRequires: python%{python3_pkgversion}-setuptools >= 30.3.0

# man pages
BuildRequires: python%{python3_pkgversion}-argparse-manpage
BuildRequires: python%{python3_pkgversion}-m2crypto
BuildRequires: python%{python3_pkgversion}-pyOpenSSL
BuildRequires: python%{python3_pkgversion}-requests
BuildRequires: python%{python3_pkgversion}-requests-ecp

# -- packages ---------------

# src.rpm
%description
The Python client for SAML ECP authentication.

%package -n python%{python3_pkgversion}-%{name}
Summary: %{summary}
Requires: python%{python3_pkgversion}-m2crypto
Requires: python%{python3_pkgversion}-pyOpenSSL
Requires: python%{python3_pkgversion}-requests
Requires: python%{python3_pkgversion}-requests-ecp
%{?python_provide:%python_provide python%{python3_pkgversion}-%{name}}
%description -n python%{python3_pkgversion}-%{name}
The Python %{python3_version} client for SAML ECP authentication.

%package -n ciecp-utils
Summary: Command line utilities for SAML ECP authentication
Requires: python%{python3_pkgversion}-%{name} = %{version}-%{release}
%description -n ciecp-utils
Command line utilities for SAML ECP authentication, including
ecp-cert-info, ecp-get-cookie, ecp-get-cert, and ecp-curl
(an ECP-aware curl alternative).

# -- build ------------------

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%clean
rm -rf $RPM_BUILD_ROOT

# -- files ------------------

%files -n python%{python3_pkgversion}-%{name}
%license LICENSE
%doc README.md
%{python3_sitelib}/*
%exclude %{python3_sitelib}/ciecplib/tool

%files -n ciecp-utils
%license LICENSE
%{_bindir}/*
%{_mandir}/man1/*.1*
%{python3_sitelib}/ciecplib/tool

# -- changelog --------------

%changelog
* Fri Mar 19 2021 Duncan Macleod <duncan.macleod@ligo.org> - 0.4.2-1
- update for 0.4.2

* Thu Oct 15 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.4.1-1
- update for 0.4.1

* Mon Sep 28 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.4.0-1
- update for 0.4.0

* Fri Jun 05 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.3.1-1
- update for 0.3.1

* Thu Apr 09 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.3.0-1
- update for 0.3.0

* Wed Mar 18 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.2.1-1
- update for 0.2.1

* Tue Mar 10 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.2.0-1
- update for 0.2.0
- remove python2 packages

* Wed Jan 22 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.1.1-1
- add python3 package for rhel/centos/epel8

* Wed Jan 22 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.1.0-1
- first release
