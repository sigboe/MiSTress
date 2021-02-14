#!/usr/bin/env bash

set -e


if [[ "${EUID}" -ne "0" ]]; then 
	echo "Please run as root"
	exit
fi

if [[ -z "${1}" ]]; then
	
	# set up image as loop device
	kpartx -d /dev/loop0
	kpartx -avs ./2017-09-07-raspbian-stretch-lite.img

	# mount partition
	mount -o rw /dev/mapper/loop0p2  /mnt/raspbian
	mount -o rw /dev/mapper/loop0p1 /mnt/raspbian/boot
	
	# mount binds
	mount --bind /dev /mnt/raspbian/dev/
	mount --bind /sys /mnt/raspbian/sys/
	mount --bind /proc /mnt/raspbian/proc/
	mount --bind /dev/pts /mnt/raspbian/dev/pts

	echo "mounted, you may chroot into: chroot /mnt/raspbian /bin/bash"

fi

if [[ "${1}" == "unmount" ]]; then
	# unmount everything
	umount /mnt/raspbian/{dev/pts,dev,sys,proc,boot,}
	kpartx -d /dev/loop0
fi
