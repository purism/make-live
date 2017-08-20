#!/bin/sh
set -e

debootstrap \
	--keyring=/usr/share/keyrings/pureos-archive-keyring.gpg \
	green \
	lbchroot \
	https://repo.puri.sm/pureos
