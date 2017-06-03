#!/usr/bin/env python3

import os
import math
from glob import glob
from logging import getLogger
import logging
import shutil
import parted


def check_call(args):
    import sys
    from subprocess import check_call

    return check_call(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)


class _ConsoleHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        self.setFormatter(
            logging.Formatter('{levelname} - {message}', style='{')
        )


class LibremDiskDevice(object):
    """
    A simple model of a block storage device that wraps up some examples of
    pyparted capabilities.
    """

    def __init__(self, path):
        """
        Initialize the ExampleDevice object.
        """
        self.path = path
        self.logger = getLogger(__name__)

    @property
    def partition_names(self):
        """
        @return:    A list of partition device names on the block device.
        @rtype:     str
        """
        names = glob('{}[0-9]*'.format(self.path))
        self.logger.debug('has partitions %s', names)
        return names

    def _new_partition(self, device, disk, start, length, set_boot=False):
        geometry = parted.Geometry(device=device, start=start,
                                   length=length)

        self.logger.debug('created %s', geometry)
        filesystem = parted.FileSystem(type='ext4', geometry=geometry)
        self.logger.debug('created %s', filesystem)
        partition = parted.Partition(disk=disk, type=parted.PARTITION_NORMAL,
                                     fs=filesystem, geometry=geometry)
        self.logger.debug('created %s', partition)
        disk.addPartition(partition=partition,
                          constraint=device.optimalAlignedConstraint)
        if set_boot:
            partition.setFlag(parted.PARTITION_BOOT)

        return partition

    def partition(self):
        """
        Create a partition table on the block device.
        """
        self.logger.info('Creating partitions')
        device = parted.getDevice(self.path)
        self.logger.debug('created %s', device)
        disk = parted.freshDisk(device, 'msdos')
        self.logger.debug('created %s', disk)

        # create the rescue disk partition - the size has been chosen to d-i's liking, so
        # it doesn't attempt to truncate or override the partition
        partition_size = round(2099249152 / (device.sectorSize)) # 2 GB
        self._new_partition(device, disk, 2048, partition_size, True) # 2048 padding is required to make d-i not override the rescue partition

        disk.commit()

        # for some reason, parted doesn't format this on its own, so we do it
        check_call(['mkfs.ext4', '/dev/sda1'])
        #check_call(['mkfs.ext4', '/dev/sda2'])
        check_call(['e2label', '/dev/sda1', 'rescue'])

    def wipe_dev(self, dev_path):
        """
        Wipe a device (partition or otherwise) of meta-data, be it file system,
        LVM, etc.

        @param dev_path:    Device path of the partition to be wiped.
        @type dev_path:     str
        """
        self.logger.debug('wiping %s', dev_path)
        with open(dev_path, 'wb') as p:
            p.write(bytearray(1024))

    def wipe(self):
        """
        Wipe the block device of meta-data, be it file system, LVM, etc.

        This is not intended to be secure, but rather to ensure that
        auto-discovery tools don't recognize anything here.
        """
        self.logger.info('Wiping partitions and other meta-data')
        for partition in self.partition_names:
            self.wipe_dev(partition)
        self.wipe_dev(self.path)


def pureos_oem_setup():
    OEM_DATA_PATH = '/var/lib/pureos-oem/'
    logger = getLogger(__name__)

    # create the new partition and format it
    libremhdd = LibremDiskDevice(disk_path)
    libremhdd.wipe()
    libremhdd.partition()

    # mount the setup disk
    logger.info('Mounting setup disk...')
    target = os.path.join(OEM_DATA_PATH, 'target')
    try:
        os.makedirs(target)
    except:
        pass
    check_call(['mount', '/dev/sda1', target])

    # copy PureOS image files and d-i
    logger.info('Copying PureOS install files...')
    shutil.copy(os.path.join(OEM_DATA_PATH, 'pureos.iso'), target)
    shutil.copy(os.path.join(OEM_DATA_PATH, 'initrd.gz'), target)
    shutil.copy(os.path.join(OEM_DATA_PATH, 'vmlinuz'), target)
    shutil.copy(os.path.join(OEM_DATA_PATH, 'di-preseed.cfg'), target)

    # set up GRUB
    logger.info('Creating GRUB configuration...')
    boot_dir = os.path.join(target, 'boot')
    grub_dir = os.path.join(boot_dir, 'grub')
    try:
        os.makedirs(grub_dir)
    except:
        pass
    shutil.copy(os.path.join(OEM_DATA_PATH, 'grub', 'grub.cfg'), grub_dir)
    shutil.copy(os.path.join(OEM_DATA_PATH, 'grub', 'loopback.cfg'), grub_dir)

    logger.info('Installing GRUB...')
    check_call(['grub-install', '/dev/sda', '--boot-directory=%s' % (boot_dir)])

    check_call(['umount', target])
    logger.info('Done.')

    shutdown = input('Shutdown now? [Y/n]')
    if not shutdown.strip() or shutdown.lower() == 'y':
        check_call(['systemctl', 'poweroff'])


if __name__ == '__main__':
    disk_path = '/dev/sda'

    # Set up a logger for nice visibility.
    logger = getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(_ConsoleHandler())

    pureos_oem_setup()
