#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools, AutoToolsBuildEnvironment
from distutils.spawn import find_executable
import os
import shutil
import configparser


class QtConan(ConanFile):

    def getsubmodules():
        config = configparser.ConfigParser()
        config.read('qtmodules.conf')
        res = {}
        assert config.sections()
        for s in config.sections():
            section = str(s)
            assert section.startswith("submodule ")
            assert section.count('"') == 2
            modulename = section[section.find('"') + 1 : section.rfind('"')]
            status = str(config.get(section, "status"))
            if status != "obsolete" and status != "ignore":
                res[modulename] = {"branch":str(config.get(section, "branch")), "status":status, "path":str(config.get(section, "path"))}
                if config.has_option(section, "depends"):
                    res[modulename]["depends"] = [str(i) for i in config.get(section, "depends").split()]
                else:
                    res[modulename]["depends"] = []
        return res
    submodules = getsubmodules()

    name = "Qt"
    version = "5.12.3"
    description = "Conan.io package for Qt library."
    url = "https://github.com/Tereius/conan-Qt"
    homepage = "https://www.qt.io/"
    license = "http://doc.qt.io/qt-5/lgpl.html"
    exports = ["LICENSE.md", "qtmodules.conf"]
    exports_sources = ["CMakeLists.txt", "fix_compile_issue_gcc9.diff"]
    settings = "os", "arch", "compiler", "build_type", "os_build", "arch_build"

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
    default_options = ("shared=True", "fPIC=True", "opengl=desktop", "openssl=False", "GUI=True", "widgets=True", "config=None") + tuple(module + "=False" for module in submodules)
    short_paths = True

    def build_requirements(self):
        self._build_system_requirements()
        if self.settings.os == 'Android':
            self.build_requires("android-ndk/r17b@tereius/stable")
            self.build_requires("android-sdk/26.1.1@tereius/stable")
            self.build_requires("java_installer/8.0.144@tereius/stable")
            if self.settings.os_build == 'Windows':
                self.build_requires("strawberryperl/5.26.0@conan/stable")
                self.build_requires("msys2/20161025@tereius/stable")
                self.build_requires_options['msys2'].provideMinGW = True

    def configure(self):
        if self.options.openssl:
            self.requires("OpenSSL/1.1.1b@tereius/stable")
            self.options["OpenSSL"].no_zlib = True
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

        assert QtConan.version == QtConan.submodules['qtbase']['branch']
        def enablemodule(self, module):
            setattr(self.options, module, True)
            for req in QtConan.submodules[module]["depends"]:
                enablemodule(self, req)
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
        url = "http://download.qt.io/official_releases/qt/{0}/{1}/single/qt-everywhere-src-{1}"\
            .format(self.version[:self.version.rfind('.')], self.version)
        if tools.os_info.is_windows:
            tools.get("%s.zip" % url)
        else:
            tools.get("%s.tar.xz" % url)
            #self.run("wget -qO- %s.tar.xz | tar -xJ " % url)
        shutil.move("qt-everywhere-src-%s" % self.version, "qt5")

        #ios patches
        tools.replace_in_file("qt5/qtbase/src/plugins/platforms/ios/qioseventdispatcher.mm", "namespace", "Q_LOGGING_CATEGORY(lcEventDispatcher, \"qt.eventdispatcher\"); \n namespace")
        tools.replace_in_file("qt5/qtdeclarative/tools/qmltime/qmltime.pro", "QT += quick-private", "QT += quick-private\nios{\nCONFIG -= bitcode\n}")
        
        # fix error with mersenne_twisters
        # https://codereview.qt-project.org/c/qt/qtbase/+/245425
        # should not needed in Qt >= 5.12.1
        tools.patch(patch_file="fix_compile_issue_gcc9.diff", base_path="qt5/qtbase/")

    def _toUnixPath(self, paths):
        if self.settings.os == "Android" and tools.os_info.is_windows:
            if(isinstance(paths, list)):
                return list(map(lambda x: tools.unix_path(x), paths))
            else:
                return tools.unix_path(paths)
        else:
            return paths

    def build(self):
        args = ["-v", "-opensource", "-confirm-license", "-nomake examples", "-nomake tests",
                "-prefix %s" % self._toUnixPath(self.package_folder)]
        if not self.options.GUI:
            args.append("-no-gui")
        if not self.options.widgets:
            args.append("-no-widgets")
        if not self.options.shared:
            args.insert(0, "-static")
            if self.settings.os == "Windows":
                if self.settings.compiler.runtime == "MT" or self.settings.compiler.runtime == "MTd":
                    args.append("-static-runtime")
        else:
            args.insert(0, "-shared")
        if self.settings.build_type == "Debug":
            args.append("-debug")
        else:
            args.append("-release")
        for module in QtConan.submodules:
            if not getattr(self.options, module) and os.path.isdir(os.path.join(self.source_folder, 'qt5', QtConan.submodules[module]['path'])):
                args.append("-skip " + module)

        # openGL
        if self.options.opengl == "no":
            args += ["-no-opengl"]
        elif self.options.opengl == "es2":
            args += ["-opengl es2"]
        elif self.options.opengl == "desktop":
            args += ["-opengl desktop"]
        if self.settings.os == "Windows":
            if self.options.opengl == "dynamic":
                args += ["-opengl dynamic"]

        # openSSL
        if not self.options.openssl:
            args += ["-no-openssl"]
        else:
            if self.options["OpenSSL"].shared:
                args += ["-openssl-linked"]
            else:
                args += ["-openssl"]
            args += ["-I %s" % i for i in self._toUnixPath(self.deps_cpp_info["OpenSSL"].include_paths)]
            libs = self._toUnixPath(self.deps_cpp_info["OpenSSL"].libs)
            lib_paths = self._toUnixPath(self.deps_cpp_info["OpenSSL"].lib_paths)
            os.environ["OPENSSL_LIBS"] = " ".join(["-L"+i for i in lib_paths] + ["-l"+i for i in libs])
            os.environ["OPENSSL_LIBS_DEBUG"] = " ".join(["-L"+i for i in lib_paths] + ["-l"+i for i in libs])
            os.environ["LD_RUN_PATH"] = " ".join([i+":" for i in lib_paths]) # Needed for secondary (indirect) dependency resolving of gnu ld
            os.environ["LD_LIBRARY_PATH"] = " ".join([i+":" for i in lib_paths]) # Needed for secondary (indirect) dependency resolving of gnu ld

        if self.options.config:
            args.append(str(self.options.config))

        if self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                self._build_msvc(args)
            else:
                self._build_mingw(args)
        elif self.settings.os == "Android":
            self._build_android(args)
        elif self.settings.os == "iOS":
            self._build_ios(args)
        else:
            self._build_unix(args)

        with open('qtbase/bin/qt.conf', 'w') as f:
            f.write('[Paths]\nPrefix = ..')

    def _build_msvc(self, args):
        build_command = find_executable("jom.exe")
        if build_command:
            build_args = ["-j", str(tools.cpu_count())]
        else:
            build_command = "nmake.exe"
            build_args = []
        self.output.info("Using '%s %s' to build" % (build_command, " ".join(build_args)))


        with tools.vcvars(self.settings):
            self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)))
            self.run("%s %s" % (build_command, " ".join(build_args)))
            self.run("%s install" % build_command)

    def _build_mingw(self, args):
        # Workaround for configure using clang first if in the path
        new_path = []
        for item in os.environ['PATH'].split(';'):
            if item != 'C:\\Program Files\\LLVM\\bin':
                new_path.append(item)
        os.environ['PATH'] = ';'.join(new_path)
        # end workaround
        args += ["-xplatform win32-g++"]

        with tools.environment_append({"MAKEFLAGS":"-j %d" % tools.cpu_count()}):
            self.output.info("Using '%d' threads" % tools.cpu_count())
            self.run("%s/qt5/configure.bat %s" % (self.source_folder, " ".join(args)))
            self.run("mingw32-make")
            self.run("mingw32-make install")

    def _build_unix(self, args):
        if self.settings.os == "Linux":
            args.append("-no-use-gold-linker") # QTBUG-65071
            if self.options.GUI:
                args.append("-qt-xcb")
            if self.settings.arch == "x86":
                args += ["-xplatform linux-g++-32"]
            elif self.settings.arch == "armv6":
                args += ["-xplatform linux-arm-gnueabi-g++"]
            elif self.settings.arch == "armv7":
                args += ["-xplatform linux-arm-gnueabi-g++"]
        else:
            args += ["-no-framework"]
            if self.settings.arch == "x86":
                args += ["-xplatform macx-clang-32"]

        env_build = AutoToolsBuildEnvironment(self)
        self.run("%s/qt5/configure %s" % (self.source_folder, " ".join(args)))
        env_build.make()
        env_build.install()

    def _build_ios(self, args):
        # end workaround
        args += ["--disable-rpath", "-skip qttranslations", "-skip qtserialport"]
        args += ["-xplatform macx-ios-clang"]
        args += ["-sdk iphoneos"]
        #args += ["-sysroot " + tools.unix_path(self.deps_env_info['android-ndk'].SYSROOT)]
        if self.settings.build_type == "Debug":
            args += ["-no-framework"]

        with tools.environment_append({"MAKEFLAGS":"-j %d" % tools.cpu_count()}):
            self.output.info("Using '%d' threads" % tools.cpu_count())
            self.run(("%s/qt5/configure " % self.source_folder) + " ".join(args))
            self.run("make")
            self.run("make install")

    def _build_android(self, args):
        # end workaround
        args += ["--disable-rpath", "-skip qttranslations", "-skip qtserialport"]
        if tools.os_info.is_windows:
            args += ["-platform win32-g++"]
        
        if self.settings.compiler == 'gcc':
            args += ["-xplatform android-g++"]
        else:
            args += ["-xplatform android-clang"]
        args += ["-android-ndk-platform android-%s" % (str(self.settings.os.api_level))]
        args += ["-android-ndk " + self._toUnixPath(self.deps_env_info['android-ndk'].NDK_ROOT)]
        args += ["-android-sdk " + self._toUnixPath(self.deps_env_info['android-sdk'].SDK_ROOT)]
        args += ["-android-ndk-host %s-%s" % (str(self.settings.os_build).lower(), str(self.settings.arch_build))]
        args += ["-android-toolchain-version " + self.deps_env_info['android-ndk'].TOOLCHAIN_VERSION]
        #args += ["-sysroot " + tools.unix_path(self.deps_env_info['android-ndk'].SYSROOT)]
        args += ["-device-option CROSS_COMPILE=" + self.deps_env_info['android-ndk'].CHOST + "-"]

        if str(self.settings.arch).startswith('x86'):
            args.append('-android-arch x86')
        elif str(self.settings.arch).startswith('x86_64'):
            args.append('-android-arch x86_64')
        elif str(self.settings.arch).startswith('armv6'):
            args.append('-android-arch armeabi')
        elif str(self.settings.arch).startswith('armv7'):
            args.append("-android-arch armeabi-v7a")
        elif str(self.settings.arch).startswith('armv8'):
            args.append("-android-arch arm64-v8a")

        self.output.info("Using '%d' threads" % tools.cpu_count())
        with tools.environment_append({
                # The env. vars set by conan android-ndk. Configure doesn't read them (on windows they contain backslashes).
                "NDK_ROOT": self._toUnixPath(tools.get_env("NDK_ROOT")),
                "ANDROID_NDK_ROOT": self._toUnixPath(tools.get_env("NDK_ROOT")),
                "SYSROOT": self._toUnixPath(tools.get_env("SYSROOT"))
            }):
            self.run(self._toUnixPath("%s/qt5/configure " % self.source_folder) + " ".join(args), win_bash=tools.os_info.is_windows, msys_mingw=tools.os_info.is_windows)
            self.run("make", win_bash=tools.os_info.is_windows)
            self.run("make install", win_bash=tools.os_info.is_windows)

    def package(self):
        self.copy("bin/qt.conf", src="qtbase")
        if self.settings.os == "Android" and tools.os_info.is_windows:
            self.copy("libgcc_s_seh-1.dll", dst="bin", src=os.path.join(self.deps_env_info['msys2'].MSYS_ROOT, "mingw64", "bin"))
            self.copy("libstdc++-6.dll", dst="bin", src=os.path.join(self.deps_env_info['msys2'].MSYS_ROOT, "mingw64", "bin"))
            self.copy("libwinpthread-1.dll", dst="bin", src=os.path.join(self.deps_env_info['msys2'].MSYS_ROOT, "mingw64", "bin"))

    def package_info(self):
        self.env_info.path.append(os.path.join(self.package_folder, "bin"))
        self.env_info.path.append(os.path.join(self.package_folder, "qttools/bin"))
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
