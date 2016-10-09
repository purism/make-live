#!/bin/sh
set -e

ln -sf /usr/share/debootstrap/scripts/testing /usr/share/debootstrap/scripts/green

debootstrap \
	--keyring=/usr/share/keyrings/pureos-archive-keyring.gpg \
	green \
	lbchroot \
	http://repo.puri.sm/pureos

chroot lbchroot 'ln -s /usr/share/debootstrap/scripts/testing /usr/share/debootstrap/scripts/green'
