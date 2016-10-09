#!/bin/sh

sudo debootstrap \
	--keyring=/usr/share/keyrings/pureos-archive-keyring.gpg \
	green \
	lbchroot \
	http://repo.puri.sm/pureos

sudo chroot lbchroot 'ln /usr/share/debootstrap/scripts/testing /usr/share/debootstrap/scripts/green'
