%define srcname ciecplib
%define version 0.8.2
%define release 1

# -- metadata ---------------

Name:      python-%{srcname}
Version:   %{version}
Release:   %{release}%{?dist}
Summary:   A python client for SAML ECP authentication

Source0:   %pypi_source
License:   GPLv3+
Url:       https://github.com/duncanmmacleod/ciecplib

Packager:  Duncan Macleod <duncan.macleod@ligo.org>
Vendor:    Duncan Macleod <duncan.macleod@ligo.org>

BuildArch: noarch
Prefix:    %{_prefix}

# -- build requirements -----

# build
BuildRequires: python3-devel >= 3.6.0
BuildRequires: python3dist(pip)
BuildRequires: python3dist(setuptools) >= 30.3.0
BuildRequires: python3dist(wheel)

# man pages
BuildRequires: python3dist(argparse-manpage)
%if 0%{?fedora} >= 36 || 0%{?rhel} >= 9
BuildRequires: python3dist(cryptography) >= 36.0.0
%else
BuildRequires: python3dist(cryptography)
BuildRequires: python3dist(pyopenssl) >= 17.1.0
%endif
BuildRequires: python3dist(requests)
BuildRequires: python3dist(requests-ecp)

# tests
%if 0%{?fedora} >= 30 || 0%{?rhel} >= 9
BuildRequires: python3dist(pytest)
BuildRequires: python3dist(requests-mock)
%endif

# -- packages ---------------

# src.rpm
%description
The Python client for SAML ECP authentication.

%package -n python3-%{srcname}
Summary: %{summary}
Conflicts: ciecp-utils < 0.4.3-1
Recommends: python3dist(gssapi)
Recommends: python3dist(requests-gssapi)
%description -n python3-%{srcname}
The Python %{python3_version} client for SAML ECP authentication.
%files -n python3-%{srcname}
%doc README.md
%license LICENSE
%{python3_sitelib}/*

%package -n ciecp-utils
Summary: Command line utilities for SAML ECP authentication
Requires: python3-%{srcname} = %{version}-%{release}
%description -n ciecp-utils
Command line utilities for SAML ECP authentication, including
ecp-cert-info, ecp-get-cookie, ecp-get-cert, and ecp-curl
(an ECP-aware curl alternative).
%files -n ciecp-utils
%doc README.md
%license LICENSE
%{_bindir}/*
%{_mandir}/man1/*.1*

# -- build ------------------

%prep
%autosetup -n %{srcname}-%{version}
# for RHEL < 9 hack together setup.{cfg,py} for old setuptools
%if 0%{?rhel} && 0%{?rhel} < 10
cat > setup.cfg << SETUP_CFG
[metadata]
name = %{srcname}
version = %{version}
author-email = %{packager}
description = %{summary}
license = %{license}
license_files = LICENSE
url = %{url}
[options]
packages = find:
python_requires = >=3.6
install_requires =
  cryptography
  pyOpenSSL >= 17.1.0
  requests
  requests-ecp
[options.entry_points]
console_scripts =
  ecp-cert-info = ciecplib.tool.ecp_cert_info:main
  ecp-curl = ciecplib.tool.ecp_curl:main
  ecp-get-cert = ciecplib.tool.ecp_get_cert:main
  ecp-get-cookie = ciecplib.tool.ecp_get_cookie:main
[build_manpages]
manpages =
  man/ecp-cert-info.1:function=create_parser:module=ciecplib.tool.ecp_cert_info
  man/ecp-curl.1:function=create_parser:module=ciecplib.tool.ecp_curl
  man/ecp-get-cert.1:function=create_parser:module=ciecplib.tool.ecp_get_cert
  man/ecp-get-cookie.1:function=create_parser:module=ciecplib.tool.ecp_get_cookie
SETUP_CFG
%endif
%if %{undefined pyproject_wheel}
cat > setup.py << SETUP_PY
from setuptools import setup
setup()
SETUP_PY
%endif

%build
%if %{defined pyproject_wheel}
%pyproject_wheel
%else
%py3_build_wheel
%endif
# generate manuals
%python3 -c "from setuptools import setup; setup()" \
  --command-packages=build_manpages \
  build_manpages \
;

%install
%if %{defined pyproject_install}
%pyproject_install
%else
%py3_install_wheel *.whl
%endif
%__mkdir -p -v %{buildroot}%{_mandir}/man1
%__install -m 644 -p -v man/*.1* %{buildroot}%{_mandir}/man1/

%check
export PYTHONPATH="%{buildroot}%{python3_sitelib}"
export PATH="%{buildroot}%{_bindir}:${PATH}"
ecp-cert-info --help
ecp-curl --help
ecp-get-cert --help
ecp-get-cookie --help
%if 0%{?fedora} >= 30 || 0%{?rhel} >= 9
%pytest --verbose -ra --pyargs ciecplib
%endif

# -- changelog --------------

%changelog
* Wed Sep 11 2024 Duncan Macleod <duncan.macleod@ligo.org> - 0.8.2-1
- update for 0.8.2

* Wed Aug 21 2024 Duncan Macleod <duncan.macleod@ligo.org> - 0.8.1-1
- update for 0.8.1
- update prep/build/install stages to use pyproject.toml

* Mon Aug 07 2023 Duncan Macleod <duncan.macleod@ligo.org> - 0.8.0-2
- add python3-pip build requirement (explicit on rhel9)

* Thu Aug 03 2023 Duncan Macleod <duncan.macleod@ligo.org> - 0.8.0-1
- update for 0.8.0
- add python3-devel build requirement
- add python3-gssapi requirement
- add python3-requests-mock build requirement for testing

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
