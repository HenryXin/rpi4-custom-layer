SUMMARY = "Example recipe with USB flash monitor systemd service"
DESCRIPTION = "Prints 1 every second when a USB flash drive is present on a special USB port, else 0"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

inherit systemd

RDEPENDS:${PN} = "python3-core python3-cryptography"

SRC_URI = " \
    file://usb-flash-monitor.py \
    file://usb-flash-monitor.service \
    file://public_key.pem \
"
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${S}/usb-flash-monitor.py ${D}${bindir}/usb-flash-monitor.py

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${S}/usb-flash-monitor.service ${D}${systemd_system_unitdir}/usb-flash-monitor.service

    install -d ${D}${sysconfdir}/usb-validator
    install -m 0644 ${S}/public_key.pem ${D}${sysconfdir}/usb-validator/public_key.pem
}

FILES:${PN} = " \
    ${bindir}/usb-flash-monitor.py \
    ${systemd_system_unitdir}/usb-flash-monitor.service \
    ${sysconfdir}/usb-validator/public_key.pem \
"

SYSTEMD_SERVICE:${PN} = "usb-flash-monitor.service"
SYSTEMD_AUTO_ENABLE = "enable"

python do_display_banner() {
    bb.plain("***********************************************");
    bb.plain("*                                             *");
    bb.plain("*  Example recipe created by bitbake-layers   *");
    bb.plain("*                                             *");
    bb.plain("***********************************************");
}

addtask display_banner before do_build
