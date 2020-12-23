#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pprint

from conans import ConanFile, tools, CMake
from distutils.spawn import find_executable
import os
import shutil
import configparser
import tempfile


class QtConan(ConanFile):

    def getsubmodules(version, status_filter=None):
        with tempfile.TemporaryDirectory() as tmpdirname:
            config = configparser.ConfigParser()
            tools.download("https://raw.githubusercontent.com/qt/qt5/%s/.gitmodules" % str(version), os.path.join(tmpdirname, "qtmodules.conf"))
            config.read(os.path.join(tmpdirname, "qtmodules.conf"))
            res = {}
            assert config.sections()
            for s in config.sections():
                section = str(s)
                assert section.startswith("submodule ")
                assert section.count('"') == 2
                modulename = section[section.find('"') + 1 : section.rfind('"')]
                status = str(config.get(section, "status"))
                if (status_filter == None and status != "obsolete" and status != "ignore") or (status_filter != None and status == status_filter):
                    res[modulename] = {"branch":str(config.get(section, "branch")), "status":status, "path":str(config.get(section, "path"))}
                    if config.has_option(section, "depends"):
                        res[modulename]["depends"] = [str(i) for i in config.get(section, "depends").split()]
                    else:
                        res[modulename]["depends"] = []
            return res

    version = "6.0.0"
    description = "Conan.io package for Qt library."
    url = "https://github.com/Tereius/conan-Qt"
    homepage = "https://www.qt.io/"
    license = "http://doc.qt.io/qt-5/lgpl.html"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt", "fix_qqmlthread_assertion_dbg.diff", "fix_ios_appstore.diff", "android.patch", "dylibToFramework.sh", "AwesomeQtMetadataParser", "egl_brcm.patch", "eglfs_brcm/CMakeLists.txt"]
    settings = "os", "arch", "compiler", "build_type"
    submodules = getsubmodules(version)
    essential_submodules = getsubmodules(version, "essential")

    options = dict({
        "shared": [True, False],
        "fPIC": [True, False],
        "opengl": ["no", "es2", "desktop", "dynamic"],
        "openssl": [True, False],
        "GUI": [True, False],
        "widgets": [True, False],
        "config": "ANY",
        }, **{module: [True,False] for module in submodules}
    )
    no_copy_source = True
    default_options = ("shared=True", "fPIC=True", "opengl=desktop", "openssl=False", "GUI=False", "widgets=False", "config=None") + tuple(module + "=False" for module in submodules) + tuple(module + "=True" for module in essential_submodules)
    short_paths = True

    def set_name(self):

        is_build = False
        is_host = False

        if hasattr(self, 'settings_build'):
            print("----------------- settings_build")
            is_host = True

        if hasattr(self, 'settings_target'):
            print("----------------- settings_target")
            is_build = True

        self.name = "Qt"

    def build_requirements(self):
        if tools.cross_building(self):
            self.build_requires("%s/%s@%s/%s" % (self.name, self.version, self.user, self.channel))
            for essential_module in self.essential_submodules:
                if essential_module != "qtqa":
                    setattr(self.build_requires_options[self.name], essential_module, True)
        self._build_system_requirements()

    def configure(self):
        if self.options.openssl:
            self.requires("OpenSSL/1.1.1b@tereius/stable")
            self.options["OpenSSL"].no_zlib = True
            if self.settings.os == 'Emscripten':
                self.options["OpenSSL"].shared = False
            else:
                self.options["OpenSSL"].shared = True
        if self.options.widgets == True:
            self.options.GUI = True
        if not self.options.GUI:
            self.options.opengl = "no"
        if self.settings.os == "Android":
            self.options["android-ndk"].makeStandalone = False
            if self.options.opengl != "no":
                self.options.opengl = "es2"
        if self.settings.os == "iOS":
            if self.options.opengl != "no":
                self.options.opengl = "es2"
        if self.settings.os == 'Emscripten':
            self.options.shared = False
            if self.options.opengl != "no":
                self.options.opengl = "es2"

        assert QtConan.version == QtConan.submodules['qtbase']['branch']
        def enablemodule(self, module):
            setattr(self.options, module, True)
            for req in QtConan.submodules[module]["depends"]:
                enablemodule(self, req)
        self.options.qtbase = True
        for module in QtConan.submodules:
            if getattr(self.options, module):
                enablemodule(self, module)
        if self.options.qtdeclarative == True:
            self.options.GUI = True

    def _build_system_requirements(self):
        if self.settings.os == "Linux" and tools.os_info.is_linux:
            installer = tools.SystemPackageTool()
            if tools.os_info.with_apt:
                pack_names = []
                arch_suffix = ''
                if self.settings.arch == "x86":
                    arch_suffix = ':i386'
                elif self.settings.arch == "x86_64":
                    arch_suffix = ':amd64'
                if self.options.GUI:
                    pack_names.extend(["libxcb1-dev", "libx11-dev", "libfontconfig1-dev", "libfreetype6-dev", "libxext-dev", "libxfixes-dev", "libxi-dev", "libxrender-dev", "libx11-xcb-dev", "libxcb-glx0-dev", "libxkbcommon-dev"])
                    if self.options.opengl == "desktop":
                        pack_names.append("libgl1-mesa-dev")
                if self.options.qtmultimedia:
                    pack_names.extend(["libasound2-dev", "libpulse-dev", "libgstreamer1.0-dev", "libgstreamer-plugins-base1.0-dev"])
                if self.options.qtwebengine:
                    pack_names.extend(["libssl-dev", "libxcursor-dev", "libxcomposite-dev", "libxdamage-dev", "libxrandr-dev", "libdbus-1-dev", "libfontconfig1-dev", "libcap-dev", "libxtst-dev", "libpulse-dev", "libudev-dev", "libpci-dev", "libnss3-dev", "libasound2-dev", "libxss-dev", "libegl1-mesa-dev", "gperf", "bison"])       
                for package in pack_names:
                    installer.install(package + arch_suffix)
            elif tools.os_info.with_yum:
                pack_names = []
                arch_suffix = ''
                if self.settings.arch == "x86":
                    arch_suffix = '.i686'
                elif self.settings.arch == "x86_64":
                    arch_suffix = '.x86_64'
                if self.options.GUI:
                    pack_names.extend(["libxcb-devel", "libX11-devel", "fontconfig-devel", "freetype-devel", "libXext-devel", "libXfixes-devel", "libXi-devel", "libXrender-devel", "libxkbcommon-devel"])
                    if self.options.opengl == "desktop":
                        pack_names.append("mesa-libGL-devel")
                if self.options.qtmultimedia:
                    pack_names.extend(["alsa-lib-devel", "pulseaudio-libs-devel", "gstreamer-devel", "gstreamer-plugins-base-devel"])
                if self.options.qtwebengine:
                    pack_names.extend(["libgcrypt-devel", "libgcrypt", "pciutils-devel", "nss-devel", "libXtst-devel", "gperf", "cups-devel", "pulseaudio-libs-devel", "libgudev1-devel", "systemd-devel", "libcap-devel", "alsa-lib-devel", "flex", "bison", "libXrandr-devel", "libXcomposite-devel", "libXcursor-devel", "fontconfig-devel"])
                for package in pack_names:
                    installer.install(package + arch_suffix)
            else:
                self.output.warn("Couldn't install system requirements")

    def source(self):
        git = tools.Git()
        git.clone("https://github.com/qt/qt5.git", branch=self.version, shallow=True)
        git.run("submodule sync")
        git.run("submodule init")
        git.run("submodule update --recursive --depth 1")
        
        #if "RASPBIAN_ROOTFS" in os.environ:
        tools.replace_in_file("qtbase/src/corelib/io/qfilesystemengine_unix.cpp", "QT_BEGIN_NAMESPACE", "QT_BEGIN_NAMESPACE\n#undef STATX_BASIC_STATS")
        tools.replace_in_file("qtbase/cmake/3rdparty/extra-cmake-modules/find-modules/FindEGL.cmake", "cmake_pop_check_state()", "cmake_pop_check_state()\nset(HAVE_EGL ON)")
        tools.patch(base_path="qtbase", patch_file="egl_brcm.patch")
        
        tools.replace_in_file("qtbase/src/plugins/platforms/eglfs/deviceintegration/CMakeLists.txt", "# add_subdirectory(eglfs_brcm) # special case TODO", "add_subdirectory(eglfs_brcm)")
        shutil.copyfile(os.path.join(self.source_folder, "eglfs_brcm", "CMakeLists.txt"), os.path.join(self.source_folder, "qtbase", "src", "plugins", "platforms", "eglfs", "deviceintegration", "eglfs_brcm", "CMakeLists.txt"))
        shutil.rmtree(os.path.join(self.source_folder, "eglfs_brcm"))
        
        #tools.replace_in_file("qtbase/cmake/QtBuild.cmake", "function(qt_check_if_tools_will_be_built)", 'function(qt_check_if_tools_will_be_built)\nmessage(STATUS "++++++++++++ ${QT_FORCE_FIND_TOOLS}, ${CMAKE_CROSSCOMPILING}, ${QT_BUILD_TOOLS_WHEN_CROSSCOMPILING}")')
        #tools.replace_in_file("qtbase/cmake/QtBuild.cmake", 'set(QT_WILL_BUILD_TOOLS ${will_build_tools} CACHE INTERNAL "Are tools going to be built" FORCE)', 'set(QT_WILL_BUILD_TOOLS ${will_build_tools} CACHE INTERNAL "Are tools going to be built" FORCE)\nmessage(STATUS "QT_WILL_BUILD_TOOLS ${QT_WILL_BUILD_TOOLS}, QT_NO_CREATE_TARGETS ${QT_NO_CREATE_TARGETS}")')

    def build(self):

        cmake = CMake(self)
        module_list = []
        
        for module in QtConan.submodules:
            if getattr(self.options, module):
                module_list.append(module)
                
        cmake.definitions["BUILD_SUBMODULES"] = ";".join(module_list)
        #cmake.verbose = True
        if tools.cross_building(self):
            cmake.definitions["QT_HOST_PATH"] = os.environ["QT_HOST_PATH"]
            cmake.definitions["QT_FORCE_FIND_TOOLS"] = "OFF"
            cmake.definitions["QT_BUILD_TOOLS_WHEN_CROSSCOMPILING"] = "OFF"
            #cmake.definitions["QT_NO_MAKE_TESTS"] = "ON"
        cmake.definitions["BUILD_EXAMPLES"] = "OFF"
        cmake.definitions["QT_NO_MAKE_EXAMPLES"] = "ON"
        cmake.definitions["QT_NO_MAKE_TOOLS"] = "ON"
        if self.options.GUI:
            cmake.definitions["FEATURE_gui"] = "ON"
        else:
            cmake.definitions["FEATURE_gui"] = "OFF"
        if self.options.widgets:
            cmake.definitions["FEATURE_widgets"] = "ON"
        else:
            cmake.definitions["FEATURE_widgets"] = "OFF"
        if self.options.shared:
            cmake.definitions["BUILD_SHARED_LIBS"] = "ON" # FEATURE_shared
        else:
            cmake.definitions["BUILD_SHARED_LIBS"] = "OFF"
        cmake.definitions["FEATURE_network"] = "ON"
        cmake.definitions["FEATURE_sql"] = "OFF"
        cmake.definitions["FEATURE_printsupport"] = "OFF"
        #cmake.definitions["FEATURE_testlib"] = "OFF"
        
        #cmake.definitions["QT_DEBUG_QT_FIND_PACKAGE"] = 1
        #cmake.definitions["CMAKE_FIND_DEBUG_MODE"] = "ON"
        #cmake.definitions["CMAKE_VERBOSE_MAKEFILE"] = "ON"
        
        if "RASPBIAN_ROOTFS" in os.environ:
            cmake.definitions["FEATURE_libudev"] = "OFF"
            cmake.definitions["FEATURE_brotli"] = "OFF"
            cmake.definitions["FEATURE_mtdev"] = "OFF"
            cmake.definitions["FEATURE_tslib"] = "OFF"
        
        if self.options.openssl:
            cmake.definitions["FEATURE_openssl"] = "ON"
            cmake.definitions["FEATURE_openssl_linked"] = "ON"
        
        cmake.configure()
        cmake.build()
        cmake.install()

    def package(self):
        self.copy("bin/qt.conf", src="qtbase")
        if self.settings.os == "Android" and tools.os_info.is_windows:
            self.copy("libgcc_s_seh-1.dll", dst="bin", src=os.path.join(self.deps_env_info['msys2'].MSYS_ROOT, "mingw64", "bin"))
            self.copy("libstdc++-6.dll", dst="bin", src=os.path.join(self.deps_env_info['msys2'].MSYS_ROOT, "mingw64", "bin"))
            self.copy("libwinpthread-1.dll", dst="bin", src=os.path.join(self.deps_env_info['msys2'].MSYS_ROOT, "mingw64", "bin"))
        if self.settings.os == "iOS" and self.settings.build_type == "Release":
            self.run("%s/dylibToFramework.sh %s %s" % (self.source_folder, self.package_folder, os.path.join(self.source_folder, "AwesomeQtMetadataParser")))

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.path.append(os.path.join(self.package_folder, "qttools/bin"))
        self.output.info('Creating QT_HOST_PATH environment variable: %s' % self.package_folder)
        self.env_info.QT_HOST_PATH = self.package_folder
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
