# conan-Qt

[![Conan Remote Recipe](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fapi.github.com%2Frepos%2FPrivatehive%2Fconan-Qt%2Fproperties%2Fvalues&query=%24%5B0%5D.value&style=flat&logo=conan&label=conan&color=%232980b9)](https://conan.privatehive.de/ui/repos/tree/General/public-conan/de.privatehive/qt) 

#### A conan package that provides Qt

---

| os                     | arch     | CI Status                                                                                                                                                                                                                                                 |
| ---------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Linux`                | `x86_64` | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Linux (Raspberry Pi)` | `armv6`  | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Windows`              | `x86_64` | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Macos`                | `armv8`  | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `iOS`                  | `armv8`  | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Android`              | `x86`    | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Android`              | `x86_64` | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Android`              | `armv7`  | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |
| `Android`              | `armv8`  | [![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Privatehive/conan-Qt/main.yml?branch=master&style=flat&logo=github&label=create+package)](https://github.com/Privatehive/conan-Qt/actions?query=branch%3Amaster) |

### Usage

| option                                                        | values                                                                                     | default   | constraint   |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | --------- | ------------ |
| `shared`                                                      | `[True, False]`                                                                            | `True`    |              |
| `fPIC`                                                        | `[True, False]`                                                                            | `True`    |              |
| `lto`                                                         | `[True, False]`                                                                            | `False`   |              |
| `opengl`                                                      | `["no", "es2", "es3", "es31", "es32", "desktop", "dynamic"]`                               | `"no"`    |              |
| `openssl`                                                     | `[True, False]`                                                                            | `"False"` |              |
| `openssl_hash`                                                | `[True, False]`                                                                            | `"False"` | QTBUG-136223 |
| `GUI`                                                         | `[True, False]`                                                                            | `False`   |              |
| `widgets`                                                     | `[True, False]`                                                                            | `False`   |              |
| `dbus`                                                        | `[True, False]`                                                                            | `False`   | Linux only   |
| `xml`                                                         | `[True, False]`                                                                            | `False`   |              |
| `fontconfig`                                                  | `[True, False]`                                                                            | `False`   |              |
| `widgetsstyle`                                                | `[None, "android", "fusion", "mac", "stylesheet", "windows", "windowsvista"]`              | `None`    |              |
| `quick2style`                                                 | `[None, "basic", "fusion", "imagine", "ios", "macos", "material", "universal", "windows"]` | `None`    |              |
| `mmPlugin`                                                    | `[None, "ffmpeg", "gstreamer", "avfoundation", "mediacodec", "wmf"]`                       | `None`    |              |
| `qtbase`                                                      | `[True, False]`                                                                            | `True`    |              |
| [module name](https://github.com/qt/qt5/blob/dev/.gitmodules) | `[True, False]`                                                                            | `False`   |              |

Use the provided conan [profiles](./profiles) to (cross) compile Qt:

| os                     | arch     | host os   | host profile                                                                  | build profile                                                       |
| ---------------------- | -------- | --------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `Linux`                | `x86_64` | `Linux`   | *default*                                                                     | *default*                                                           |
| `Linux (Raspberry Pi)` | `armv6`  | `Linux`   | [raspberrypiosArmv6.host.profile](./profiles/raspberrypiosArmv6.host.profile) | *default*                                                           |
| `Windows`              | `x86_64` | `Windows` | [windowsMinGW.host.profile](./profiles/windowsMinGW.host.profile)             | [windowsMinGW.build.profile](./profiles/windowsMinGW.build.profile) |
| `Macos`                | `armv8`  | `Macos`   | *default*                                                                     | *default*                                                           |
| `iOS`                  | `armv8`  | `Macos`   | [iosArmv8.host.profile](./profiles/iosArmv8.host.profile)                     | *default*                                                           |
| `Android`              | `x86`    | `Linux`   | [androidx86.host.profile](./profiles/androidx86.host.profile)                 | [android.build.profile](./profiles/android.build.profile)           |
| `Android`              | `x86_64` | `Linux`   | [androidx86_64.host.profile](./profiles/androidx86_64.host.profile)           | [android.build.profile](./profiles/android.build.profile)           |
| `Android`              | `armv7`  | `Linux`   | [androidArmv7.host.profile](./profiles/androidArmv7.host.profile)             | [android.build.profile](./profiles/android.build.profile)           |
| `Android`              | `armv8`  | `Linux`   | [androidArmv8.host.profile](./profiles/androidArmv8.host.profile)             | [android.build.profile](./profiles/android.build.profile)           |
