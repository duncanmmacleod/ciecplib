%define srcname ciecplib
%define version 0.7.2
%define release 1

# -- metadata ---------------

Name:      %{srcname}
Version:   %{version}
Release:   %{release}%{?dist}
Summary:   A python client for SAML ECP authentication

Source0:   %pypi_source
License:   GPL-3.0-or-later
Url:       https://github.com/duncanmmacleod/ciecplib

Packager:  Duncan Macleod <duncan.macleod@ligo.org>
Vendor:    Duncan Macleod <duncan.macleod@ligo.org>

BuildArch: noarch
Prefix:    %{_prefix}

# -- build requirements -----

# macros
BuildRequires: python-rpm-macros
BuildRequires: python3-rpm-macros

# build
BuildRequires: python3 >= 3.6.0
BuildRequires: python%{python3_pkgversion}-setuptools >= 30.3.0
BuildRequires: python%{python3_pkgversion}-wheel

# man pages
%if 0%{?fedora} >= 26 || 0%{?rhel} >= 8
BuildRequires: python%{python3_pkgversion}-argparse-manpage
%endif
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
BuildRequires: python%{python3_pkgversion}-cryptography >= 36.0.0
%else
BuildRequires: python%{python3_pkgversion}-cryptography
BuildRequires: python%{python3_pkgversion}-pyOpenSSL >= 17.1.0
%endif
BuildRequires: python%{python3_pkgversion}-requests
BuildRequires: python%{python3_pkgversion}-requests-ecp

# tests
%if 0%{?fedora} >= 30 || 0%{?rhel} >= 9
BuildRequires: python%{python3_pkgversion}-pytest >= 3.9.0
%endif

# -- packages ---------------

# src.rpm
%description
The Python client for SAML ECP authentication.

%package -n python%{python3_pkgversion}-%{srcname}
Summary: %{summary}
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
Requires: python%{python3_pkgversion}-cryptography >= 36.0.0
%else
Requires: python%{python3_pkgversion}-cryptography
Requires: python%{python3_pkgversion}-pyOpenSSL >= 17.1.0
%endif
Requires: python%{python3_pkgversion}-requests
Requires: python%{python3_pkgversion}-requests-ecp
Conflicts: ciecp-utils < 0.4.3-1
%{?python_provide:%python_provide python%{python3_pkgversion}-%{srcname}}
%description -n python%{python3_pkgversion}-%{srcname}
The Python %{python3_version} client for SAML ECP authentication.

%package -n ciecp-utils
Summary: Command line utilities for SAML ECP authentication
Requires: python%{python3_pkgversion}-%{srcname} = %{version}-%{release}
%description -n ciecp-utils
Command line utilities for SAML ECP authentication, including
ecp-cert-info, ecp-get-cookie, ecp-get-cert, and ecp-curl
(an ECP-aware curl alternative).

# -- build ------------------

%prep
%autosetup -n %{srcname}-%{version}

# add pyOpenSSL to python metadata
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
%else
sed -i '/\tcryptography >=/c\\tcryptography\n\tpyOpenSSL >= 17.1.0' setup.cfg
%endif

%build
%py3_build_wheel

%install
%py3_install_wheel %{srcname}-%{version}-*.whl

%check
export PYTHONPATH="%{buildroot}%{python3_sitelib}"
export PATH="%{buildroot}%{_bindir}:${PATH}"
ecp-cert-info --help
ecp-curl --help
ecp-get-cert --help
ecp-get-cookie --help
%if 0%{?fedora} >= 30 || 0%{?rhel} >= 9
%{__python3} -m pytest %{?_pytest_options}%{?!_pytest_options:--verbose -ra --pyargs requests_ecp}
%endif

%clean
rm -rf $RPM_BUILD_ROOT

# -- files ------------------

%files -n python%{python3_pkgversion}-%{srcname}
%doc README.md
%license LICENSE
%{python3_sitelib}/*

%files -n ciecp-utils
%doc README.md
%license LICENSE
%{_bindir}/*
%if 0%{?fedora} >= 26 || 0%{?rhel} >= 8
%{_mandir}/man1/*.1*
%endif

# -- changelog --------------

%changelog
* Thu Apr 20 2023 Duncan Macleod <duncan.macleod@ligo.org> - 0.7.2-1
- update for 0.7.2

* Tue Nov 15 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.7.1-1
- update for 0.7.1

* Wed Nov 02 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.7.0-2
- fix metadata sed hack for RHEL<9

* Thu Oct 27 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.7.0-1
- update for 0.7.0
- replace python3-m2cypro with python3-cryprography/python3-openssl
- update conditionals for requirements and testing

* Wed Oct 19 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.6.0-1
- update for 0.6.0

* Tue Jun 07 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.5.1-1
- update for 0.5.1

* Wed Apr 13 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.5.0-1
- update for 0.5.0

* Thu Jan 13 2022 Duncan Macleod <duncan.macleod@ligo.org> - 0.4.4-1
- update for 0.4.4

* Tue Mar 30 2021 Duncan Macleod <duncan.macleod@ligo.org> - 0.4.3-2
- exclude man pages on el7, no argparse-manpage

* Tue Mar 23 2021 Duncan Macleod <duncan.macleod@ligo.org> - 0.4.3-1
- update for 0.4.3

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
