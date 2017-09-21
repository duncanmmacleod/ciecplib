%define name ligo-dot-org
%define version 0.1
%define unmangled_version 0.1
%define release 1

Summary: Python client for LIGO.ORG-authenticated HTTPS requests
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPLv3
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
Requires: python, python-six, python-lxml, krb5-workstation, ligo-common
BuildRequires: python-setuptools
BuildArch: noarch
Vendor: Paul Hopkins <paul.hopkins@ligo.org>
URL: https://github.com/duncanmmacleod/ligo.org

%description
This small python package provides a native Python client to access
LIGO.ORG-authenticated web content.

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
rm -rf $RPM_BUILD_ROOT/ligo_dot_org-0.1-py2.7.egg-info

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Tue Sep 12 2017 Paul Hopkins <paul.hopkins@ligo.org> - 0.1-1
- Initial version.
