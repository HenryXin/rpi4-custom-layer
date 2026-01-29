FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

do_deploy:append:raspberrypi4-64-custom() {
    echo "device_tree=bcm2711-rpi-4-b-custom.dtb" >> ${DEPLOYDIR}/${BOOTFILES_DIR_NAME}/config.txt
    echo "dtparam=pwr_led_trigger=none" >> ${DEPLOYDIR}/${BOOTFILES_DIR_NAME}/config.txt
    echo "dtparam=pwr_led_activelow=off" >> ${DEPLOYDIR}/${BOOTFILES_DIR_NAME}/config.txt
    echo "dtparam=act_led_trigger=default-on" >> ${DEPLOYDIR}/${BOOTFILES_DIR_NAME}/config.txt
    echo "dtparam=act_led_activelow=off" >> ${DEPLOYDIR}/${BOOTFILES_DIR_NAME}/config.txt
}
