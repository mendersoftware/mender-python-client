SYSTEMD_AUTO_ENABLE_${PN} = "disable"

FILES_${PN} += "${datadir}/mender/install \
                /data/mender/device_type"

FILESEXTRAPATHS_prepend := "${THISDIR}/files:"
SRC_URI_append = " file://mender.conf"

do_install_append() {
    if ${@bb.utils.contains('DISTRO_FEATURES', 'mender-image', 'true', 'false', d)}; then
        install -m 755 -d ${D}/data/mender
        install -m 444 ${B}/device_type ${D}/data/mender/
        ln -s ${bindir}/mender-sub-updater ${D}${datadir}/mender/install
    else
        bbwarn "mender-image feature not set in DISTRO_FEATURES"
    fi

}
