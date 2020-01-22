%define name ciecplib
%define version 0.1.0
%define release 1
%define author Duncan Macleod
%define email duncan.macleod@ligo.org

# -- metadata ---------------

BuildArch: noarch
Group:     Development/Libraries
License:   GPL-3.0-or-later
Name:      %{name}
Packager:  %{author} <%{email}>
Prefix:    %{_prefix}
Release:   %{release}%{?dist}
Source0:   https://pypi.io/packages/source/l/%{name}/%{name}-%{version}.tar.gz
Summary:   A python client for SAML ECP authentication
Url:       https://github.com/duncanmmacleod/ciecplib
Vendor:    Duncan Macleod <duncan.macleod@ligo.org>
Version:   %{version}

# -- build requirements -----

BuildRequires: argparse-manpage
BuildRequires: python
BuildRequires: python-rpm-macros
BuildRequires: python2-rpm-macros
BuildRequires: python2-setuptools

# build requires all runtime dependencies for argparse-manpage
BuildRequires: m2crypto
BuildRequires: pyOpenSSL
BuildRequires: python
BuildRequires: python-kerberos
BuildRequires: python-lxml

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
%{?python_provide:%python_provide python2-%{name}}
%description -n python2-%{name}
The Python %{python_version} client for SAML ECP authentication.

%package -n ciecp-utils
Summary: Command line utilities for SAML ECP authentication
Requires: python2-%{name} = %{version}-%{release}
%description -n ciecp-utils
Command line utilities for SAML ECP authentication, including
ecp-cert-info, ecp-cookit-init, ecp-get-cert, and ecp-curl
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
# centos/epel provides kerberos (not pykerberos):
sed -i "s/pykerberos/kerberos/g" setup.py
%endif
%py2_build

%install
%py2_install

# make man pages
mkdir -vp %{buildroot}%{_mandir}/man1
export PYTHONPATH="%{buildroot}%{python2_sitelib}"
argparse-manpage \
    --author "%{author}" --author-email "%{email}" \
    --function create_parser --project-name %{name} --url %{url} \
    --module ciecplib.tool.ecp_cert_info > %{buildroot}%{_mandir}/man1/ecp-cert-info.1
argparse-manpage \
    --author "%{author}" --author-email "%{email}" \
    --function create_parser --project-name %{name} --url %{url} \
    --module ciecplib.tool.ecp_cookie_init > %{buildroot}%{_mandir}/man1/ecp-cookie-init.1
argparse-manpage \
    --author "%{author}" --author-email "%{email}" \
    --function create_parser --project-name %{name} --url %{url} \
    --module ciecplib.tool.ecp_curl > %{buildroot}%{_mandir}/man1/ecp-curl.1
argparse-manpage \
    --author "%{author}" --author-email "%{email}" \
    --function create_parser --project-name %{name} --url %{url} \
    --module ciecplib.tool.ecp_get_cert > %{buildroot}%{_mandir}/man1/ecp-cet-cert.1

%clean
rm -rf $RPM_BUILD_ROOT

# -- files ------------------

%files -n python2-%{name}
%license LICENSE
%doc README.md
%{python2_sitelib}/*
%exclude %{python2_sitelib}/ciecplib/tool

%files -n ciecp-utils
%license LICENSE
%{_bindir}/*
%{_mandir}/man1/*.1*
%{python2_sitelib}/ciecplib/tool

# -- changelog --------------

%changelog
* Wed Jan 22 2020 Duncan Macleod <duncan.macleod@ligo.org> - 0.1.0-1
- first release
