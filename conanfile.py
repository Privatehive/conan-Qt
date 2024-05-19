#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import patch, load, get, rmdir, replace_in_file, copy
from conan.tools.build import cross_building, build_jobs
from conan.tools.system.package_manager import Apt
from conan.tools.env import VirtualBuildEnv
from conan.tools.scm import Git
import json, os
import shutil
import configparser
import tempfile
import http.client

required_conan_version = ">=2.0"

def getsubmodules(version, status_filter=None):
    with tempfile.TemporaryDirectory() as tmpdirname:
        config = configparser.ConfigParser()
        with open(os.path.join(tmpdirname, "qtmodules.conf"), 'wb') as f:
            conn = http.client.HTTPSConnection("code.qt.io")
            conn.request("GET", "/cgit/qt/qt5.git/plain/.gitmodules?h=%s" % str(version))
            r1 = conn.getresponse()
            f.write(r1.read())
            f.close()
            conn.close()
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
    tool_requires = ["cmake/[>=3.21.7]", "ninja/[>=1.11.1]"]
    # ---Sources---
    exports = ["info.json"]
    exports_sources = ["CMakeLists.txt", "AwesomeQtMetadataParser", "patches/*"]
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
        "widgetsstyle": [None, "android", "fusion", "mac", "stylesheet", "windows", "windowsvista"],
        "quick2style": [None, "basic", "fusion", "imagine", "ios", "macos", "material", "universal", "windows"],
        "config": ["ANY"],
        }, **{module: [True,False] for module in submodules})
    
    default_options = dict({
        "shared": True, 
        "fPIC": True,
        "opengl": "no",
        "openssl": False, 
        "GUI": False, 
        "widgets": False,
        "widgetsstyle": None,
        "quick2style": None,
        "config": "none"}, **{module: False for module in submodules})
    # ---Build---
    generators = []
    # ---Folders---
    no_copy_source = True

    def build_requirements(self):
        if cross_building(self):
            # Qt depends on itself if we are cross building. We have to provide the CMake cached variable QT_HOST_PATH
            self.tool_requires("%s/%s@%s/%s" % (self.name, self.version, self.user, self.channel), 
            options={"shared": True, "fPIC":True, "config": "host", "opengl": "desktop", "GUI": True, "widgets": True, "qtbase": True, "qtdeclarative": True, "qtshadertools": True, "qttools": True, "qttranslations": True, "qtquick3d": True, "qtremoteobjects": True}, visible=True)

    def requirements(self):
        if self.options.openssl:
            self.requires("openssl/3.2.0@%s/stable" % self.user)
        if self.options.qtmultimedia:
            self.requires("ffmpeg/6.0")

    def configure(self):
        if self.options.openssl:
            self.options["openssl"].shared = self.options.shared
        if self.options.qtmultimedia:
            self.options["ffmpeg"].shared = self.options.shared
            self.options["ffmpeg"].swresample = True
            self.options["ffmpeg"].with_asm = False
            self.options["ffmpeg"].with_sdl = False
            self.options["ffmpeg"].with_ssl = False
            self.options["ffmpeg"].with_xcb = False
            self.options["ffmpeg"].with_lzma = False
            self.options["ffmpeg"].with_opus = False
            self.options["ffmpeg"].with_zlib = False
            self.options["ffmpeg"].with_bzip2 = False
            self.options["ffmpeg"].with_pulse = False
            self.options["ffmpeg"].with_vaapi = False
            self.options["ffmpeg"].with_vdpau = False
            self.options["ffmpeg"].with_libvpx = False
            self.options["ffmpeg"].with_vorbis = False
            self.options["ffmpeg"].with_vulkan = False
            self.options["ffmpeg"].with_zeromq = False
            self.options["ffmpeg"].with_libalsa = False
            self.options["ffmpeg"].with_libwebp = False
            self.options["ffmpeg"].with_libx264 = False
            self.options["ffmpeg"].with_libx265 = False
            self.options["ffmpeg"].with_freetype = False
            self.options["ffmpeg"].with_libiconv = False
            self.options["ffmpeg"].with_openh264 = False
            self.options["ffmpeg"].with_openjpeg = False
            self.options["ffmpeg"].with_programs = False
            self.options["ffmpeg"].with_libfdk_aac = False
            self.options["ffmpeg"].with_libmp3lame = False

    def config_options(self):

        def enablemodule(self, module):
            setattr(self.options, module, True)
            for req in QtConan.submodules[module]["depends"]:
                enablemodule(self, req)

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

        if self.options.qtdeclarative is False:
            self.options.rm_safe("quick2style")

        if self.options.widgets is False:
            self.options.rm_safe("widgetsstyle")

    def system_requirements(self):
        if self.settings.os == "Linux":
            apt = Apt(self)
            pack_names = []
            if self.options.GUI:
                pack_names.extend(["libfontconfig1-dev", "libfreetype6-dev", "libx11-dev", "libx11-xcb-dev", "libxext-dev", "libxfixes-dev", "libxi-dev", "libxrender-dev", "libxcb1-dev", "libxcb-cursor-dev", "libxcb-glx0-dev", "libxcb-keysyms1-dev", "libxcb-image0-dev", "libxcb-shm0-dev", "libxcb-icccm4-dev", "libxcb-sync-dev", "libxcb-xfixes0-dev", "libxcb-shape0-dev", "libxcb-randr0-dev", "libxcb-render-util0-dev", "libxcb-util-dev", "libxcb-xinerama0-dev", "libxcb-xkb-dev", "libxkbcommon-dev", "libxkbcommon-x11-dev"])
                if self.options.opengl == "desktop":
                    pack_names.append("libgl1-mesa-dev")
            if self.options.qtmultimedia:
                pack_names.extend(["libasound2-dev", "libpulse-dev"])
            apt.install(pack_names, update=True)

    def source(self):
        #git = Git(self)
        #git.run("clone git://code.qt.io/qt/qt5.git --branch=%s --depth 1 --single-branch --no-tags --recurse-submodules --shallow-submodules --progress --jobs %u Qt" % (self.version, build_jobs(self)))
        major_version=self.version.split(".")[0]
        minor_version=self.version.split(".")[1]
        get(self, "https://download.qt.io/official_releases/qt/%s.%s/%s/single/qt-everywhere-src-%s.tar.xz" % (major_version, minor_version, self.version, self.version), destination="Qt", strip_root=True)
        replace_in_file(self, "Qt/qtbase/src/corelib/io/qfilesystemengine_unix.cpp", "QT_BEGIN_NAMESPACE", "QT_BEGIN_NAMESPACE\n#undef STATX_BASIC_STATS")
        replace_in_file(self, "Qt/qtdeclarative/src/plugins/CMakeLists.txt", "add_subdirectory(qmllint)", "if(QT_FEATURE_qml_debug AND QT_FEATURE_thread)\nadd_subdirectory(qmllint)\nendif()")
        replace_in_file(self, "Qt/qtbase/cmake/QtAutoDetectHelpers.cmake", "if(NOT android_detected)", "if(\"OFF\")")
        patch(self, base_path="Qt/qttools", patch_file=os.path.join("patches","linguist.patch"))
        #patch(self, base_path="Qt/qtbase", patch_file=os.path.join("patches", "Qt6CoreMacros_%s.cmake.patch" % self.version))
        replace_in_file(self, "Qt/qtbase/src/corelib/Qt6CoreMacros.cmake", "elseif(UNIX AND NOT APPLE AND NOT ANDROID AND NOT CMAKE_CROSSCOMPILING)", "elseif(UNIX AND NOT APPLE AND NOT ANDROID)")
        replace_in_file(self, "Qt/qtdeclarative/src/qml/Qt6QmlMacros.cmake", "elseif(UNIX AND NOT APPLE AND NOT ANDROID AND NOT CMAKE_CROSSCOMPILING", "elseif(UNIX AND NOT APPLE AND NOT ANDROID")
        #patch(self, base_path="Qt/qtbase", patch_file=os.path.join("patches", "QTBUG-117950.patch"))
        replace_in_file(self, "Qt/qtdeclarative/src/qml/Qt6QmlMacros.cmake", "string(APPEND content \"prefer :${prefix}\\n\")", "")
        #patch(self, base_path="Qt/qtdeclarative", patch_file=os.path.join("patches", "QTBUG-111570.patch"))
        #patch(self, base_path="Qt/qtdeclarative", patch_file=os.path.join("patches", "QTBUG-118470.patch"))
        #patch(self, base_path="Qt/qtdeclarative", patch_file=os.path.join("patches", "QTBUG-119715.patch"))
        patch(self, base_path="Qt/qtmultimedia", patch_file=os.path.join("patches", "ffmpeg_plugin_jni_onload_fix.patch"))
        patch(self, base_path="Qt/qtlocation", patch_file=os.path.join("patches", "disable_test_qtlocation.patch"))
        #patch(self, base_path="Qt/qtquick3d", patch_file=os.path.join("patches", "QTBUG-123015.patch"))
        
        # enable rasp-pi brcm opengl implementation (very unstable - don't use)
        #replace_in_file(self, "Qt/qtbase/src/plugins/platforms/eglfs/deviceintegration/CMakeLists.txt", "# add_subdirectory(eglfs_brcm) # TODO: QTBUG-112769", "add_subdirectory(eglfs_brcm)")
        #shutil.copyfile(os.path.join(self.source_folder, "patches", "eglfs_brcm", "CMakeLists.txt"), os.path.join(self.source_folder, "Qt", "qtbase", "src", "plugins", "platforms", "eglfs", "deviceintegration", "eglfs_brcm", "CMakeLists.txt"))
        
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
        tc.blocks.remove("find_paths") # CMAKE_FIND_PACKAGE_PREFER_CONFIG should be false (the default). We want to use Find modules first
        if cross_building(self):
            self.output.info('Building Qt submodules: %s' % module_list)
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
    
        tc.variables["FEATURE_icu"] = False # always major version breakage
        tc.variables["FEATURE_hunspell"] = False
        tc.variables["FEATURE_gssapi"] = False
        tc.variables["FEATURE_backtrace"] = False
        tc.variables["FEATURE_glib"] = False
        tc.variables["FEATURE_brotli"] = False
        tc.variables["FEATURE_slog2"] = False
        tc.variables["FEATURE_zstd"] = False
        tc.variables["FEATURE_libudev"] = False
        tc.variables["FEATURE_system_libb2"] = False
        tc.variables["FEATURE_system_pcre2"] = False
        tc.variables["TEST_libclang"] = False
        tc.variables["FEATURE_clang"] = False
        tc.variables["FEATURE_clangcpp"] = False
        tc.variables["FEATURE_testlib"] = False
        tc.variables["FEATURE_private_tests"] = False
        tc.variables["FEATURE_testlib_selfcover"] = False
        tc.variables["FEATURE_batch_test_support"] = False
        tc.variables["FEATURE_itemmodeltester"] = False
        tc.variables["FEATURE_pixeltool"] = False
        tc.variables["QT_BUILD_BENCHMARKS"] = False
        tc.variables["QT_BUILD_MANUAL_TESTS"] = False
        tc.variables["QT_BUILD_TESTS"] = False
        tc.variables["QT_USE_VCPKG"] = False
        tc.variables["QT_BUILD_TESTS_BY_DEFAULT"] = False
        tc.variables["QT_BUILD_EXAMPLES"] = False
        tc.variables["QT_BUILD_EXAMPLES_BY_DEFAULT"] = False
        if self.options.qtmultimedia:
            tc.variables["FFMPEG_DIR"] = self.dependencies["ffmpeg"].package_folder
            tc.variables["QT_DEFAULT_MEDIA_BACKEND"] = "ffmpeg"
            tc.variables["FEATURE_ffmpeg"] = True
            tc.variables["FEATURE_wmf"] = False
            tc.variables["FEATURE_gstreamer"] = False
            tc.variables["FEATURE_gstreamer_1_0"] = False
            tc.variables["FEATURE_gstreamer_app"] = False
            tc.variables["FEATURE_gstreamer_gl"] = False
            tc.variables["FEATURE_gstreamer_photography"] = False
            tc.variables["FEATURE_avfoundation"] = False
            # For Android no FEATURE_mediacodec flag exists
        if self.options.GUI:
            tc.variables["FEATURE_gui"] = True
        else:
            tc.variables["FEATURE_gui"] = False

        if self.options.widgets:
            tc.variables["FEATURE_widgets"] = True
            if self.options.widgetsstyle:
                tc.variables["FEATURE_style_android"] = False
                tc.variables["FEATURE_style_fusion"] = False
                tc.variables["FEATURE_style_mac"] = False
                tc.variables["FEATURE_style_stylesheet"] = False
                tc.variables["FEATURE_style_windows"] = False
                tc.variables["FEATURE_style_windowsvista"] = False
                tc.variables["FEATURE_style_" + str(self.options.widgetsstyle)] = True
        else:
            tc.variables["FEATURE_widgets"] = False

        if self.options.qtdeclarative:
            tc.variables["FEATURE_qml_debug"] = self.settings.build_type == "Debug"
            tc.variables["FEATURE_qml_profiler"] = self.settings.build_type == "Debug"
            if self.options.quick2style:
                tc.variables["FEATURE_quickcontrols2_basic"] = True
                tc.variables["FEATURE_quickcontrols2_fusion"] = False
                tc.variables["FEATURE_quickcontrols2_imagine"] = False
                tc.variables["FEATURE_quickcontrols2_ios"] = False
                tc.variables["FEATURE_quickcontrols2_macos"] = False
                tc.variables["FEATURE_quickcontrols2_material"] = False
                tc.variables["FEATURE_quickcontrols2_universal"] = False
                tc.variables["FEATURE_quickcontrols2_windows"] = False
                tc.variables["FEATURE_quickcontrols2_" + str(self.options.quick2style)] = True

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
            tc.variables["FEATURE_opensslv11"] = False
            tc.variables["FEATURE_opensslv30"] = True
            tc.variables["FEATURE_openssl_linked"] = True
            tc.variables["FEATURE_openssl_runtime"] = False
            tc.variables["OPENSSL_ROOT_DIR"] = self.dependencies["openssl"].package_folder
        else:
            tc.variables["FEATURE_openssl"] = False

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
