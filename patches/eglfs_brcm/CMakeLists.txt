# Generated from eglfs_brcm.pro.

#####################################################################
## QEglFSBrcmIntegrationPlugin Plugin:
#####################################################################

qt_internal_add_plugin(QEglFSBrcmIntegrationPlugin
    OUTPUT_NAME qeglfs-brcm-integration
    TYPE egldeviceintegrations
    SOURCES
        qeglfsbrcmintegration.cpp qeglfsbrcmintegration.h
        qeglfsbrcmmain.cpp
    DEFINES
        QT_EGL_NO_X11
    INCLUDE_DIRECTORIES
        ../../api
    PUBLIC_LIBRARIES
        Qt::Core
        Qt::CorePrivate
        Qt::EglFSDeviceIntegrationPrivate
        Qt::Gui
        Qt::GuiPrivate
        bcm_host
)

#### Keys ignored in scope 1:.:.:eglfs_brcm.pro:<TRUE>:
# OTHER_FILES = "$$PWD/eglfs_brcm.json"
