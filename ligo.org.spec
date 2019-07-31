%define origname ligo.org
%define pkgname ligo-org
%define version 0.1.0
%define release 1

# -- metadata ---------------

BuildArch: noarch
Group:     Development/Libraries
License:   GPL-3.0-or-later
Name:      %{pkgname}
Packager:  Duncan Macleod <duncan.macleod@ligo.org>
Prefix:    %{_prefix}
Release:   %{release}%{?dist}
Source0:   https://pypi.io/packages/source/l/%{origname}/%{origname}-%{version}.tar.gz
Summary:   A python client for LIGO.ORG SAML ECP authentication
Url:       https://github.com/duncanmmacleod/ligo.org
Vendor:    LIGO Scientific Collaboration <auth@ligo.org>
Version:   %{version}

# -- build requirements -----

BuildRequires: help2man
BuildRequires: python
BuildRequires: python-rpm-macros
BuildRequires: python2-rpm-macros
BuildRequires: python2-setuptools

# -- packages ---------------

# src.rpm
%description
The Python client for LIGO.ORG SAML ECP authentication.

%package -n python2-%{pkgname}
Summary: %{summary}
Requires: ligo-ca-certs
Requires: m2crypto
Requires: pyOpenSSL
Requires: python
Requires: python-kerberos
Requires: python-lxml
Requires: python-pathlib
Requires: python2-ligo-common
%{?python_provide:%python_provide python2-%{pkgname}}
%description -n python2-%{pkgname}
The Python %{python_version} client for LIGO.ORG SAML ECP authentication.

%package -n ligo-proxy-utils2
Summary: Command line utilities for LIGO.ORG SAML ECP authentication
Requires: python2-%{pkgname} = %{version}
Conflicts: ligo-proxy-utils
%description -n ligo-proxy-utils2
Command line utilities for LIGO.ORG SAML ECP authentication, including
ligo-proxy-init and ligo-curl (a LIGO.ORG-aware curl alternative).

# -- build ------------------

%prep
%autosetup -n %{origname}-%{version}

%build
%if 0%{?rhel} && 0%{?rhel} <= 7
# old setuptools does not support environment markers:
sed -i "/ ; /s/ ;.*/\",/g" setup.py
# remove winkerberos requirement
sed -i "/winkerberos/d" setup.py
# epel7 provides kerberos (not pykerberos):
sed -i "s/pykerberos/kerberos/g" setup.py
%endif
%py2_build

%install
%py2_install
# make man pages
mkdir -vp %{buildroot}%{_mandir}/man1
ls %{buildroot}%{_bindir} | \
env PYTHONPATH="%{buildroot}%{python2_sitelib}" \
xargs --verbose -I @ \
help2man \
    --source %{origname} \
    --version-string %{version} \
    --section 1 \
    --no-info \
    --no-discard-stderr \
    --output %{buildroot}%{_mandir}/man1/@.1 \
    %{buildroot}%{_bindir}/@

%clean
rm -rf $RPM_BUILD_ROOT

# -- files ------------------

%files -n python2-%{pkgname}
%license LICENSE
%doc README.md
%{python2_sitelib}/*

%files -n ligo-proxy-utils2
%license LICENSE
%{_bindir}/ligo-*
%{_mandir}/man1/ligo-*.1*


# -- changelog --------------
