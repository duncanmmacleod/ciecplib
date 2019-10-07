%define name ciecplib
%define version 0.1.0
%define release 1

# -- metadata ---------------

BuildArch: noarch
Group:     Development/Libraries
License:   GPL-3.0-or-later
Name:      %{name}
Packager:  Duncan Macleod <duncan.macleod@ligo.org>
Prefix:    %{_prefix}
Release:   %{release}%{?dist}
Source0:   https://pypi.io/packages/source/l/%{name}/%{name}-%{version}.tar.gz
Summary:   A python client for SAML ECP authentication
Url:       https://github.com/duncanmmacleod/ciecplib
Vendor:    Duncan Macleod <duncan.macleod@ligo.org>
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
The Python client for SAML ECP authentication.

%package -n python2-%{name}
Summary: %{summary}
Requires: m2crypto
Requires: pyOpenSSL
Requires: python
Requires: python-kerberos
Requires: python-lxml
Requires: python-pathlib
%{?python_provide:%python_provide python2-%{name}}
%description -n python2-%{name}
The Python %{python_version} client for SAML ECP authentication.

%package -n ciecp-utils
Summary: Command line utilities for SAML ECP authentication
Requires: python2-%{name} = %{version}
%description -n ciecp-utils
Command line utilities for SAML ECP authentication, including
ecp-cookit-init, ecp-proxy-init, and ecp-curl
(an ECP-aware curl alternative).

# -- build ------------------

%prep
%autosetup -n %{name}-%{version}

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
    --source %{name} \
    --version-string %{version} \
    --section 1 \
    --no-info \
    --no-discard-stderr \
    --output %{buildroot}%{_mandir}/man1/@.1 \
    %{buildroot}%{_bindir}/@

%clean
rm -rf $RPM_BUILD_ROOT

# -- files ------------------

%files -n python2-%{name}
%license LICENSE
%doc README.md
%{python2_sitelib}/*

%files -n ciecp-utils
%license LICENSE
%{_bindir}/*
%{_mandir}/man1/*.1*

# -- changelog --------------
