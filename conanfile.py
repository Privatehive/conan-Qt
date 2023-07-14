#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import patch, load, download, replace_in_file, copy
from conan.tools.build import cross_building, build_jobs
from conan.tools.env import VirtualBuildEnv
from conan.tools.scm import Git
import json, os
import shutil
import configparser
import tempfile
import requests

required_conan_version = ">=2.0"

def getsubmodules(version, status_filter=None):
    with tempfile.TemporaryDirectory() as tmpdirname:
        config = configparser.ConfigParser()
        r = requests.get("https://code.qt.io/cgit/qt/qt5.git/plain/.gitmodules?h=%s" % str(version), allow_redirects=True)
        with open(os.path.join(tmpdirname, "qtmodules.conf"), 'wb') as f:
            f.write(r.content)
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

class QtConan(ConanFile):

    jsonInfo = json.load(open("info.json", 'r'))
    # ---Package reference---
    name = jsonInfo["projectName"]
    version = jsonInfo["version"]
    user = jsonInfo["domain"]
    channel = "stable"
    # ---Metadata---
    description = jsonInfo["projectDescription"]
    license = jsonInfo["license"]
    author = jsonInfo["vendor"]
    topics = jsonInfo["topics"]
    homepage = jsonInfo["homepage"]
    url = jsonInfo["repository"]
    # ---Requirements---
    requires = []
    tool_requires = ["cmake/3.21.7", "ninja/1.11.1"]
    # ---Sources---
    exports = ["info.json"]
    exports_sources = ["CMakeLists.txt", "AwesomeQtMetadataParser", "patches*"]
    # ---Binary model---
    settings = "os", "compiler", "build_type", "arch"
    submodules = getsubmodules(version)
    options = dict({
        "shared": [True, False],
        "fPIC": [True, False],
        "opengl": ["no", "es2", "desktop", "dynamic"],
        "openssl": [True, False],
        "GUI": [True, False],
        "widgets": [True, False],
        "config": ["ANY"],
        }, **{module: [True,False] for module in submodules})
    
    default_options = dict({
        "shared": True, 
        "fPIC": True,
        "opengl": "no",
        "openssl": False, 
        "GUI": False, 
        "widgets": False, 
        "config": "none"}, **{module: False for module in submodules})
    # ---Build---
    generators = []
    # ---Folders---
    no_copy_source = True

    def build_requirements(self):
        if cross_building(self):
            # Qt depends on itself if we are cross building. We have to provide the CMake cached variable QT_HOST_PATH
            self.tool_requires("%s/%s@%s/%s" % (self.name, self.version, self.user, self.channel), 
            options={"shared": True, "fPIC":True, "config": "host", "opengl": "desktop", "GUI": True, "widgets": True, "qtbase": True, "qtdeclarative": True, "qtshadertools": True, "qttools": True, "qttranslations": True, "qtquick3d": True}, visible=True)

    def config_options(self):

        def enablemodule(self, module):
            setattr(self.options, module, True)
            for req in QtConan.submodules[module]["depends"]:
                enablemodule(self, req)

        if self.options.openssl:
            self.requires("OpenSSL/1.1.1b@tereius/stable")
            self.options["OpenSSL"].no_zlib = True
            if self.settings.os == 'Emscripten':
                self.options["OpenSSL"].shared = False
            else:
                self.options["OpenSSL"].shared = True
        if self.options.widgets == True or self.options.qtdeclarative == True:
            self.options.GUI = True
        if not self.options.GUI:
            self.options.opengl = "no"
        if self.settings.os == "Android":
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

        self.options.qtbase = True
        for module in QtConan.submodules:
            if getattr(self.options, module):
                enablemodule(self, module)

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
        git = Git(self)
        git.run("clone git://code.qt.io/qt/qt5.git --branch=%s --depth 1 --single-branch --no-tags --recurse-submodules --shallow-submodules --progress --jobs %u Qt" % (self.version, build_jobs(self)))
        
        replace_in_file(self, "Qt/qtbase/src/corelib/io/qfilesystemengine_unix.cpp", "QT_BEGIN_NAMESPACE", "QT_BEGIN_NAMESPACE\n#undef STATX_BASIC_STATS")
        replace_in_file(self, "Qt/qtdeclarative/src/plugins/CMakeLists.txt", "add_subdirectory(qmllint)", "if(QT_FEATURE_qml_debug AND QT_FEATURE_thread)\nadd_subdirectory(qmllint)\nendif()")
        #tools.patch(base_path="qtbase", patch_file="egl_brcm.patch")
        patch(self, base_path="Qt/qtbase", patch_file=os.path.join("patches","egl_brcm6_5.patch"))
        patch(self, base_path="Qt/qttools", patch_file=os.path.join("patches","linguist.patch"))
        patch(self, base_path="Qt/qtbase", patch_file=os.path.join("patches", "Qt6CoreMacros.cmake.patch"))
        patch(self, base_path="Qt/qtdeclarative", patch_file=os.path.join("patches", "Qt6QmlMacros.cmake.patch"))
        
        # enable rasp-pi brcm opengl implementation (very unstable - don't use)
        replace_in_file(self, "Qt/qtbase/src/plugins/platforms/eglfs/deviceintegration/CMakeLists.txt", "# add_subdirectory(eglfs_brcm) # special case TODO", "add_subdirectory(eglfs_brcm)")
        shutil.copyfile(os.path.join(self.source_folder, "patches", "eglfs_brcm", "CMakeLists.txt"), os.path.join(self.source_folder, "Qt", "qtbase", "src", "plugins", "platforms", "eglfs", "deviceintegration", "eglfs_brcm", "CMakeLists.txt"))
        
    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        ms = VirtualBuildEnv(self)
        module_list = []
        for module in QtConan.submodules:
            if getattr(self.options, module):
                module_list.append(module)
        self.output.info('Building Qt submodules: %s' % module_list)
        tc.variables["QT_BUILD_SUBMODULES"] = ";".join(module_list)
        #tc.variables["CMAKE_FIND_DEBUG_MODE"] = True
        if cross_building(self):
            self.output.info('Building Qt submodules: %s' % module_list)
            tc.blocks["find_paths"].values["cross_building"] = False # Limit the cmake search paths to sysroot only!
            tc.variables["QT_FORCE_FIND_TOOLS"] = False
            if self.settings.os == "Android":
                tc.variables["QT_QMAKE_TARGET_MKSPEC"] = "android-clang"
            else:
                # targeting raspberry pi
                tc.variables["QT_QMAKE_TARGET_MKSPEC"] = "devices/linux-rasp-pi-g++"
                tc.variables["QT_QPA_DEFAULT_PLATFORM"] = "eglfs"
                tc.variables["FEATURE_brotli"] = False
                tc.variables["FEATURE_pcre2"] = True
                #tc.variables["FEATURE_kms"] = True
                tc.variables["FEATURE_system_libb2"] = False
                #tc.variables["FEATURE_libudev"] = False
                tc.variables["FEATURE_mtdev"] = False
                tc.variables["FEATURE_tslib"] = False
                tc.variables["FEATURE_mng"] = False
                tc.variables["FEATURE_pkg_config"] = True
                #tc.variables["FEATURE_libinput"] = True
                tc.variables["FEATURE_UNITY_BUILD"] = False
                tc.variables["FEATURE_use_gold_linker"] = False
                tc.variables["FEATURE_use_gold_linker_alias"] = False
    
        tc.variables["FEATURE_hunspell"] = False
        tc.variables["TEST_libclang"] = False
        tc.variables["FEATURE_clang"] = False
        tc.variables["FEATURE_clangcpp"] = False
        tc.variables["QT_BUILD_BENCHMARKS"] = False
        tc.variables["QT_BUILD_MANUAL_TESTS"] = False
        tc.variables["QT_BUILD_TESTS"] = False
        tc.variables["QT_BUILD_TESTS_BY_DEFAULT"] = False
        tc.variables["QT_BUILD_EXAMPLES"] = False
        tc.variables["QT_BUILD_EXAMPLES_BY_DEFAULT"] = False
        if self.options.GUI:
            tc.variables["FEATURE_gui"] = True
        else:
            tc.variables["FEATURE_gui"] = False
        if self.options.widgets:
            tc.variables["FEATURE_widgets"] = True
        else:
            tc.variables["FEATURE_widgets"] = False
        if self.options.shared:
            tc.variables["BUILD_SHARED_LIBS"] = True # FEATURE_shared
        else:
            tc.variables["BUILD_SHARED_LIBS"] = False
        tc.variables["FEATURE_network"] = True
        tc.variables["FEATURE_sql"] = False
        tc.variables["FEATURE_printsupport"] = False
        #cmake.definitions["FEATURE_testlib"] = "OFF"
       
        tc.variables["FEATURE_opengl"] = False
        tc.variables["FEATURE_opengl_desktop"] = False
        tc.variables["FEATURE_opengl_dynamic"] = False
        tc.variables["FEATURE_opengles2"] = False
        tc.variables["FEATURE_opengles3"] = False
        tc.variables["FEATURE_opengles31"] = False
        tc.variables["FEATURE_opengles32"] = False

        if self.options.opengl == "es2":
            tc.variables["FEATURE_opengl"] = True
            tc.variables["FEATURE_opengles2"] = True
        elif self.options.opengl == "desktop":
            tc.variables["FEATURE_opengl"] = True
            tc.variables["FEATURE_opengl_desktop"] = True
        elif self.options.opengl == "dynamic":
            tc.variables["FEATURE_opengl"] = True
            tc.variables["FEATURE_opengl_dynamic"] = True

        if self.options.openssl:
            tc.variables["FEATURE_openssl"] = True
            tc.variables["FEATURE_openssl_linked"] = True

        tc.generate()
        ms.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(cli_args=["--log-level=STATUS --debug-trycompile"], build_script_folder="Qt")
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        if self.options.config == "host":
            self.output.info('Creating QT_HOST_PATH environment variable: %s' % self.package_folder)
            self.buildenv_info.define_path("QT_HOST_PATH", self.package_folder)
            self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
            self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "qttools", "bin"))
            self.cpp_info.includedirs = []
            self.cpp_info.libdirs = []
            self.cpp_info.bindirs = []
        else:
            self.runenv_info.prepend_path("QML_IMPORT_PATH", os.path.join(self.package_folder, "qml"))
            self.cpp_info.builddirs = ["lib/cmake"]
        
        if not cross_building(self):
            self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
            self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "qttools", "bin"))
        else:
            # Forward the build env from the Qt Host
            Qt = self.dependencies.build[self.name]
            self.output.info('Forwarding build environment from Qt Host: %s' % Qt.package_folder)
            self.buildenv_info.compose_env(Qt.buildenv_info)
