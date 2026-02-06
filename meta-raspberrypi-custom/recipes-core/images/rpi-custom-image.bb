SUMMARY = "Custom Raspberry Pi 4 image"
DESCRIPTION = "A custom image for Raspberry Pi 4 with basic packages"

require recipes-core/images/rpi-test-image.bb

WKS_FILE = "sdimage-raspberrypi-custom.wks"

IMAGE_FEATURES:append = " ssh-server-openssh x11-base"

IMAGE_INSTALL:append = " kernel-modules openssh openssh-sftp-server xserver-xorg xinit matchbox-terminal matchbox-wm xf86-video-fbdev example"
