Summary: A web-based management system for DNS, consisting of a PHP web interface and some PHP CLI components to hook into FreeRadius.
Name: namedmanager
Version: 1.9.0
Release: 2%{dist}
License: AGPLv3
URL: http://www.amberdms.com/namedmanager
Group: Applications/Internet
Source0: namedmanager-%{version}.tar.bz2

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
BuildRequires: gettext

%description
namedmanager is a web-based interface for viewing and managing DNS zones stored inside a database and generating configuration files from that.


%package www
Summary: namedmanager web-based interface and API components
Group: Applications/Internet

Requires: httpd, mod_ssl
Requires: php >= 5.3.0, php-mysql, php-ldap, php-soap, php-intl, php-xml
Requires: perl, perl-DBD-MySQL
%if 0%{?rhel} >= 7
Requires: mysql-compat-server
%else
Requires: mysql-server
%if 0%{?rhel} < 6
Prereq: httpd, php, mysql-server, php-mysql
%endif
%endif

%description www
Provides the namedmanager web-based interface and SOAP API.


%package bind
Summary:  Integration components for Bind nameservers.
Group: Applications/Internet

Requires: php-cli >= 5.3.0, php-soap, php-process, php-intl
Requires: perl, perl-DBD-MySQL
Requires: bind

%description bind
Provides applications for integrating with Bind nameservers and generating text-based configuration files from the API.


%prep
%setup -q -n namedmanager-%{version}

%build


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p -m0755 $RPM_BUILD_ROOT%{_sysconfdir}/namedmanager/
mkdir -p -m0755 $RPM_BUILD_ROOT%{_datadir}/namedmanager/

# install application files and resources
cp -pr * $RPM_BUILD_ROOT%{_datadir}/namedmanager/


# install configuration file
install -m0700 htdocs/include/sample-config.php $RPM_BUILD_ROOT%{_sysconfdir}/namedmanager/config.php
ln -s %{_sysconfdir}/namedmanager/config.php $RPM_BUILD_ROOT%{_datadir}/namedmanager/htdocs/include/config-settings.php

# install linking config file
install -m755 htdocs/include/config.php $RPM_BUILD_ROOT%{_datadir}/namedmanager/htdocs/include/config.php


# install configuration file
install -m0700 bind/include/sample-config.php $RPM_BUILD_ROOT%{_sysconfdir}/namedmanager/config-bind.php
ln -s %{_sysconfdir}/namedmanager/config-bind.php $RPM_BUILD_ROOT%{_datadir}/namedmanager/bind/include/config-settings.php

# install linking config file
install -m755 bind/include/config.php $RPM_BUILD_ROOT%{_datadir}/namedmanager/bind/include/config.php

# log directory for www app.
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/namedmanager


# install the apache configuration file
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d
install -m 644 resources/namedmanager-httpdconfig.conf $RPM_BUILD_ROOT%{_sysconfdir}/httpd/conf.d/namedmanager.conf

# install the logpush bootscript
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
install -m 755 resources/namedmanager_logpush.rcsysinit $RPM_BUILD_ROOT/etc/init.d/namedmanager_logpush

# install the cronfiles
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/
install -m 644 resources/namedmanager-www.cron $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/namedmanager-www
install -m 644 resources/namedmanager-bind.cron $RPM_BUILD_ROOT%{_sysconfdir}/cron.d/namedmanager-bind

# placeholder configuration file
touch $RPM_BUILD_ROOT%{_sysconfdir}/named.namedmanager.conf

%post www

# Reload apache
echo "Reloading httpd..."
service httpd reload

# update/install the MySQL DB
if [ $1 == 1 ];
then
	# install - requires manual user MySQL setup
	echo "Run cd %{_datadir}/namedmanager/resources/; ./autoinstall.pl to install the SQL database."
else
	# upgrade - we can do it all automatically! :-)
	echo "Automatically upgrading the MySQL database..."
	%{_datadir}/namedmanager/resources/schema_update.pl --schema=%{_datadir}/namedmanager/sql/ -v
fi


%post bind

if [ $1 == 0 ];
then
	# upgrading existing rpm
	echo "Restarting logging process..."
	service namedmanager_logpush restart
fi


if [ $1 == 1 ];
then
	# instract about named
	echo ""
	echo "BIND/NAMED CONFIGURATION"
	echo ""
	echo "NamedManager BIND components have been installed, you will need to install"
	echo "and configure bind/named to use the configuration file by adding the"
	echo "following to /etc/named.conf:"
	echo ""
	echo "#"
	echo "# Include NamedManager Configuration"
	echo "#"
	echo ""
	echo "include \"/etc/named.namedmanager.conf\";"
	echo ""

	# instruct about config file
	echo ""
	echo "NAMEDMANAGER BIND CONFIGURATION"
	echo ""
	echo "You need to set the application configuration in %{_sysconfdir}/namedmanager/config-bind.php"
	echo ""
fi


%postun www

# check if this is being removed for good, or just so that an
# upgrade can install.
if [ $1 == 0 ];
then
	# user needs to remove DB
	echo "NamedManager has been removed, but the MySQL database and user will need to be removed manually."
fi


%preun bind

# stop running process
service namedmanager_logpush stop



%clean
rm -rf $RPM_BUILD_ROOT

%files www
%defattr(-,root,root)
%config %dir %{_sysconfdir}/namedmanager
%config %{_sysconfdir}/cron.d/namedmanager-www
%attr(770,root,apache) %config(noreplace) %{_sysconfdir}/namedmanager/config.php
%attr(660,root,apache) %config(noreplace) %{_sysconfdir}/httpd/conf.d/namedmanager.conf
%{_datadir}/namedmanager/htdocs
%{_datadir}/namedmanager/resources
%{_datadir}/namedmanager/sql
%attr(755,apache,apache) %{_localstatedir}/log/namedmanager

%doc %{_datadir}/namedmanager/README.md
%doc %{_datadir}/namedmanager/docs/AUTHORS
%doc %{_datadir}/namedmanager/docs/CONTRIBUTORS
%doc %{_datadir}/namedmanager/docs/COPYING


%files bind
%defattr(-,root,root)
%config %dir %{_sysconfdir}/namedmanager
%config %{_sysconfdir}/cron.d/namedmanager-bind
%config(noreplace) %{_sysconfdir}/named.namedmanager.conf
%config(noreplace) %{_sysconfdir}/namedmanager/config-bind.php
%{_datadir}/namedmanager/bind
/etc/init.d/namedmanager_logpush


%changelog
* Sat Jan 30 2016 Frank Crawford <Frank.Crawford@ac3.com.au> 1.9.0-2
- Modified spec requirements and scripts to be more compatible with RHEL7
* Sat Mar 14 2015 Jethro Carr <jethro.carr@amberdms.com> 1.9.0
- Compilation of various bug fixes
* Sun Dec 22 2013 Jethro Carr <jethro.carr@amberdms.com> 1.8.0
- Released version 1.8.0 [stable]
- Adds Amazon AWS Route53 support
* Sat Aug 17 2013 Jethro Carr <jethro.carr@amberdms.com> 1.7.0
- Released version 1.7.0 [stable]
- New version of Amberphplib framework
- Support for MySQL 5.6+ STRICT sql mode by default
- Bug fix with IPv6 PTR
* Sun Jul 28 2013 Jethro Carr <jethro.carr@amberdms.com> 1.6.0
- Released version 1.6.0 [stable]
- Various useful bug fixes
- Addition of IPv6 PTR domain support
* Fri Feb 15 2013 Jethro Carr <jethro.carr@amberdms.com> 1.5.1
- Released version 1.5.1 [stable] [bugfixes]
* Sun Dec  9 2012 Jethro Carr <jethro.carr@amberdms.com> 1.5.0
- Released version 1.5.0 [stable]
* Fri May 18 2012 Jethro Carr <jethro.carr@amberdms.com> 1.4.2
- Released version 1.4.2 [bugfix]
* Sun May 06 2012 Jethro Carr <jethro.carr@amberdms.com> 1.4.1
- Released version 1.4.1 [stable]
* Thu Apr 26 2012 Jethro Carr <jethro.carr@amberdms.com> 1.4.0
- Released version 1.4.0 [stable]
* Wed Mar 21 2012 Jethro Carr <jethro.carr@amberdms.com> 1.3.0
- Released version 1.3.0 [stable]
* Thu Feb  9 2012 Jethro Carr <jethro.carr@amberdms.com> 1.2.0
- Released version 1.2.0 [stable]
* Tue Aug 16 2011 Jethro Carr <jethro.carr@amberdms.com> 1.1.0
- Released version 1.1.0 [stable]
* Sun Jul 24 2011 Jethro Carr <jethro.carr@amberdms.com> 1.0.0
- Released version 1.0.0 [stable]
* Thu Apr  7 2011 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_beta_2
- Released version 1.0.0_beta_2 bug fix release
* Wed Apr  6 2011 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_beta_1
- Released version 1.0.0_beta_1
* Mon Mar 28 2011 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_alpha_5
- Released version 1.0.0_alpha_5
* Tue Jun 08 2010 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_alpha_4
- Released version 1.0.0_alpha_4
* Sun May 30 2010 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_alpha_3
- Released version 1.0.0_alpha_3
* Fri May 28 2010 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_alpha_2
- Released version 1.0.0_alpha_2
* Mon May 24 2010 Jethro Carr <jethro.carr@amberdms.com> 1.0.0_alpha_1
- Inital Application Release

