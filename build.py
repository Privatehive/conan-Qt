from conan.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add(settings={"os": "Android", "os.api_level": 21, "arch": "armv7", "compiler": "gcc", "compiler.version": "4.9", "compiler.libcxx": "libstdc++"}, options={}, env_vars={}, build_requires={})
    builder.run()
