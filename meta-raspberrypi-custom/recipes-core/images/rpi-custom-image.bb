SUMMARY = "Custom Raspberry Pi 4 image"
DESCRIPTION = "A custom image for Raspberry Pi 4 with basic packages"

require recipes-core/images/rpi-test-image.bb

IMAGE_FEATURES += "ssh-server-dropbear"

IMAGE_INSTALL += " \
    kernel-modules \
"
