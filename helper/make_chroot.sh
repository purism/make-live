#!/bin/sh
set -e

debootstrap \
	--keyring=/usr/share/keyrings/pureos-archive-keyring.gpg \
	green \
	lbchroot \
	http://repo.puri.sm/pureos
