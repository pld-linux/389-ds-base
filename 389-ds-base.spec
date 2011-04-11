# TODO
# - selinux_variants macro missing. something from fedora?
# - merge with fedora-ds-base.spec
#
# Conditional build:
%bcond_with	selinux		# build with selinux

#%define		subver	.a1
#%define		rel		0.1

Summary:	389 Directory Server (base)
Name:		389-ds-base
Version:	1.2.8.1
Release:	0
License:	GPL v2 with exceptions
Group:		Daemons
URL:		http://directory.fedoraproject.org/
Source0:	http://directory.fedoraproject.org/sources/%{name}-%{version}.tar.bz2
# Source0-md5:	d12829ca71b28222fbe66b0939d2af4f
BuildRequires:	cyrus-sasl-devel
BuildRequires:	db-devel
BuildRequires:	libicu-devel
BuildRequires:	libnl-devel
BuildRequires:	libstdc++-devel
BuildRequires:	mozldap-devel
BuildRequires:	nspr-devel
BuildRequires:	nss-devel
BuildRequires:	pcre-devel
BuildRequires:	perl-devel
BuildRequires:	pkgconfig
BuildRequires:	rpm-pythonprov
BuildRequires:	rpmbuild(macros) >= 1.268
BuildRequires:	svrcore-devel
%ifnarch sparc sparc64 ppc ppc64 s390 s390x
BuildRequires:	lm_sensors-devel
%endif
BuildRequires:	bzip2-devel
BuildRequires:	openssl-devel
BuildRequires:	zlib-devel
# The following are needed to build the snmp ldap-agent
BuildRequires:	net-snmp-devel
# The following are needed to build the SELinux policy
%if %{with selinux}
BuildRequires:	checkpolicy
BuildRequires:	policycoreutils
%endif
# the following is for the pam passthru auth plug-in
BuildRequires:	pam-devel
# the following are needed for some of our scripts
Requires:	mozldap-tools
Requires:	perl-Mozilla-LDAP
# this is needed to setup SSL if you are not using the
# administration server package
Requires:	nss-tools
# these are not found by the auto-dependency method
# they are required to support the mandatory LDAP SASL mechs
Requires:	cyrus-sasl-digest-md5
Requires:	cyrus-sasl-gssapi
# this is needed for verify-db.pl
Requires(post,preun):	/sbin/chkconfig
Requires:	db-utils
Requires:	rc-scripts
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
389 Directory Server is an LDAPv3 compliant server. The base package
includes the LDAP server and command line utilities for server
administration.

%package devel
Summary:	Development libraries for 389 Directory Server
Group:		Development/Libraries
Requires:	%{name} = %{version}-%{release}
Requires:	mozldap-devel

%description      devel
Development Libraries and headers for the 389 Directory Server base
package.

%package selinux
Summary:	SELinux policy for 389 Directory Server
Group:		Daemons
Requires:	%{name} = %{version}-%{release}
Requires:	selinux-policy

%description selinux
SELinux policy for the 389 Directory Server base package.

%package selinux-devel
Summary:	Development interface for 389 Directory Server base SELinux policy
Group:		Development/Libraries

%description selinux-devel
SELinux policy interface for the 389 Directory Server base package.

%prep
%setup -q

%build
%configure \
	--enable-autobind \
	--without-kerberos \
	%{?with_selinux:--with-selinux}

# Generate symbolic info for debuggers
export XCFLAGS="%{rpmcflags}"

%ifarch x86_64 ppc64 ia64 s390x sparc64
export USE_64=1
%endif

%{__make}

%if %{with selinux}
# Build the SELinux policy module for each variant
cd selinux-built
for selinuxvariant in %{selinux_variants}; do
	%{__make} NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
	mv dirsrv.pp dirsrv.pp.${selinuxvariant}
	%{__make} NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
done
cd -
%endif

%install
rm -rf $RPM_BUILD_ROOT

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT/var/log/dirsrv
install -d $RPM_BUILD_ROOT/var/lib/dirsrv
install -d $RPM_BUILD_ROOT/var/lock/dirsrv
install -d $RPM_BUILD_ROOT%{_includedir}/dirsrv

# remove libtool and static libs
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/*.la
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/plugins/*.a
rm -f $RPM_BUILD_ROOT%{_libdir}/dirsrv/plugins/*.la

install -p ldap/servers/slapd/slapi-plugin.h $RPM_BUILD_ROOT%{_includedir}/dirsrv/
install -p ldap/servers/plugins/replication/winsync-plugin.h $RPM_BUILD_ROOT%{_includedir}/dirsrv/

# make sure perl scripts have a proper shebang
sed -i -e 's|#{{PERL-EXEC}}|#!/usr/bin/perl|' $RPM_BUILD_ROOT%{_datadir}/dirsrv/script-templates/template-*.pl

%if %{with selinux}
# Install the SELinux policy
cd selinux-built
for selinuxvariant in %{selinux_variants}; do
	install -d $RPM_BUILD_ROOT%{_datadir}/selinux/${selinuxvariant}
	install -p -m 644 dirsrv.pp.${selinuxvariant} \
	$RPM_BUILD_ROOT%{_datadir}/selinux/${selinuxvariant}/dirsrv.pp
done
cd -

# Install the SELinux policy interface
cd selinux-built
install -d $RPM_BUILD_ROOT%{_datadir}/dirsrv-selinux
install -p dirsrv.if $RPM_BUILD_ROOT%{_datadir}/dirsrv-selinux/dirsrv.if
install -p dirsrv.te $RPM_BUILD_ROOT%{_datadir}/dirsrv-selinux/dirsrv.te
install -p dirsrv.fc $RPM_BUILD_ROOT%{_datadir}/dirsrv-selinux/dirsrv.fc
cd -
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add dirsrv
/sbin/chkconfig --add dirsrv-snmp
if [ ! -e %{_localstatedir}/run/dirsrv ]; then
	install -d %{_localstatedir}/run/dirsrv
fi

%preun
if [ "$1" = 0 ]; then
	%service dirsrv stop
	/sbin/chkconfig --del dirsrv
	%service dirsrv-snmp stop
	/sbin/chkconfig --del dirsrv-snmp
fi

%post selinux
if [ "$1" -le "1" ] ; then # First install
	for selinuxvariant in %{selinux_variants}; do
		semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/dirsrv.pp 2>/dev/null || :
	done
	fixfiles -R %{name} restore || :
	/sbin/service dirsrv condrestart > /dev/null 2>&1 || :
	/sbin/service dirsrv-snmp condrestart > /dev/null 2>&1 || :
fi

%preun selinux
if [ "$1" -lt "1" ]; then # Final removal
	for selinuxvariant in %{selinux_variants}; do
		semodule -s ${selinuxvariant} -r dirsrv 2>/dev/null || :
	done
	fixfiles -R %{name} restore || :
	%service dirsrv condrestart > /dev/null 2>&1 || :
	%service dirsrv-snmp condrestart > /dev/null 2>&1 || :
fi

%postun selinux
if [ "$1" -ge "1" ]; then # Upgrade
	for selinuxvariant in %{selinux_variants}; do
		semodule -s ${selinuxvariant} -i %{_datadir}/selinux/${selinuxvariant}/dirsrv.pp 2>/dev/null || :
	done
fi

%files
%defattr(644,root,root,755)
%doc LICENSE EXCEPTION LICENSE.GPLv2
%dir %{_sysconfdir}/dirsrv
%dir %{_sysconfdir}/dirsrv/schema
%dir %{_sysconfdir}/dirsrv/config
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/dirsrv/schema/*.ldif
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/dirsrv/config/slapd-collations.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/dirsrv/config/certmap.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/dirsrv/config/ldap-agent.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/dirsrv/config/template-initconfig
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/dirsrv
%{_datadir}/dirsrv
%attr(754,root,root) /etc/rc.d/init.d/dirsrv
%attr(754,root,root) /etc/rc.d/init.d/dirsrv-snmp
%attr(755,root,root) %{_bindir}/*
%attr(755,root,root) %{_sbindir}/*
%dir %{_libdir}/dirsrv
%attr(755,root,root) %{_libdir}/dirsrv/*.so.*
%{_libdir}/dirsrv/perl
%dir %{_libdir}/dirsrv/plugins
%{_libdir}/dirsrv/plugins/*.so
%dir %{_localstatedir}/lib/dirsrv
%dir %{_localstatedir}/log/dirsrv
%dir %{_localstatedir}/lock/dirsrv
%{_mandir}/man1/*
%{_mandir}/man8/*

%files devel
%defattr(644,root,root,755)
%{_includedir}/dirsrv
%{_libdir}/dirsrv/*.so
%{_pkgconfigdir}/dirsrv.pc

%if %{with selinux}
%files selinux
%defattr(644,root,root,755)
%{_datadir}/selinux/*/dirsrv.pp

%files selinux-devel
%defattr(644,root,root,755)
%{_datadir}/dirsrv-selinux
%endif
