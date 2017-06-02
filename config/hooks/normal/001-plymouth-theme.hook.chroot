#!/bin/sh
set -e

if [ -e /usr/sbin/plymouth-set-default-theme ]
then
	if [ -e /usr/share/plymouth/themes/pureos/pureos.plymouth ]
	then
		# likely a GUI configuration, we want the nice PureOS splash
		plymouth-set-default-theme pureos
	fi
	/usr/sbin/update-initramfs -u
fi
