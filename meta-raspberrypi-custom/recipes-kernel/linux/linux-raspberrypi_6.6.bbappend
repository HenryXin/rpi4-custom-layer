# Extend FILESEXTRAPATHS to include the files directory for patches
FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# Try remove with exact string match (no leading space, exact format)
# Prepend our custom URL
SRC_URI:prepend:raspberrypi4-64-custom = "git://github.com/HenryXin/linux-rpi-custom.git;name=machine;branch=${LINUX_RPI_BRANCH};protocol=https"
SRC_URI:remove:raspberrypi4-64-custom = "git://github.com/raspberrypi/linux.git;name=machine;branch=${LINUX_RPI_BRANCH};protocol=https"
# Add custom device tree patch for raspberrypi4-64-custom
SRC_URI:append:raspberrypi4-64-custom = " file://0001-add-bcm2711-rpi-4-b-custom.dts.patch file://0001-a-test-patch-to-main.c.patch "
LINUX_VERSION:raspberrypi4-64-custom ?= "6.6.78"
LINUX_RPI_BRANCH:raspberrypi4-64-custom ?= "rpi-6.6.y"
SRCREV_machine:raspberrypi4-64-custom = "9afba138031d6ee69824935b507cc9339427ddaf"